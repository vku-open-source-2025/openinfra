"""Unit tests for emergency notifier fallback orchestration."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.infrastructure.notifications.emergency_notifier import EmergencyNotifier


@dataclass
class FakeUser:
    id: str


class FakeUserService:
    """Simple user service stub returning users by role."""

    def __init__(self, role_users: dict[str, list[FakeUser]]):
        self.role_users = role_users

    async def list_users(self, skip: int, limit: int, role: str, status: str):
        return self.role_users.get(role, [])


class FakeNotificationService:
    """Notification service stub with deterministic channel outcomes."""

    def __init__(self, outcomes: dict[tuple[str, str], bool]):
        self.outcomes = outcomes
        self.calls: list[tuple[str, str]] = []

    async def create_notification_with_delivery_status(self, notification_data):
        user_id = notification_data.user_id
        channel = notification_data.channels[0].value
        self.calls.append((user_id, channel))
        delivered = self.outcomes.get((user_id, channel), False)
        return object(), delivered


class FakeLegacyNotificationService:
    """Legacy notification service without delivery status helper."""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def create_notification(self, notification_data):
        user_id = notification_data.user_id
        channel = notification_data.channels[0].value
        self.calls.append((user_id, channel))
        return object()


@pytest.mark.asyncio
async def test_broadcast_alert_uses_ordered_fallback_and_aggregates_stats():
    user_service = FakeUserService(
        {
            "admin": [FakeUser("u1"), FakeUser("u2")],
            "technician": [FakeUser("u2"), FakeUser("u3"), FakeUser("u4")],
        }
    )
    notification_service = FakeNotificationService(
        {
            ("u1", "push"): False,
            ("u1", "email"): True,
            ("u2", "push"): True,
            ("u3", "push"): False,
            ("u3", "email"): False,
            ("u3", "in_app"): True,
            ("u4", "push"): False,
            ("u4", "email"): False,
            ("u4", "in_app"): False,
        }
    )

    notifier = EmergencyNotifier(notification_service, user_service)
    stats = await notifier.broadcast_alert(
        title="Storm Warning",
        message="Strong wind expected in district center",
        severity="critical",
        target_roles=["admin", "technician"],
        metadata={"hazard_id": "hz-001"},
    )

    assert stats["total"] == 4
    assert stats["attempted"] == 4
    assert stats["sent"] == 3
    assert stats["failed"] == 1
    assert stats["fallback_used"] == 2
    summary = stats["delivery_summary"]
    assert summary["total_attempts"] == 9
    assert summary["total_success"] == 3
    assert summary["total_failure"] == 6
    assert summary["channels"]["push"] == {
        "attempts": 4,
        "success": 1,
        "failure": 3,
    }
    assert summary["channels"]["email"] == {
        "attempts": 3,
        "success": 1,
        "failure": 2,
    }
    assert summary["channels"]["in_app"] == {
        "attempts": 2,
        "success": 1,
        "failure": 1,
    }

    u1_attempts = notifier.last_user_attempts["u1"]["attempts"]
    assert [item["channel"] for item in u1_attempts] == ["push", "email"]
    assert [item["status"] for item in u1_attempts] == ["failed", "sent"]

    u2_attempts = notifier.last_user_attempts["u2"]["attempts"]
    assert [item["channel"] for item in u2_attempts] == ["push"]
    assert [item["status"] for item in u2_attempts] == ["sent"]

    u3_attempts = notifier.last_user_attempts["u3"]["attempts"]
    assert [item["channel"] for item in u3_attempts] == ["push", "email", "in_app"]
    assert [item["status"] for item in u3_attempts] == ["failed", "failed", "sent"]

    u4_attempts = notifier.last_user_attempts["u4"]["attempts"]
    assert [item["channel"] for item in u4_attempts] == ["push", "email", "in_app"]
    assert [item["status"] for item in u4_attempts] == ["failed", "failed", "failed"]


@pytest.mark.asyncio
async def test_broadcast_alert_dry_run_skips_delivery_calls():
    user_service = FakeUserService(
        {
            "admin": [FakeUser("u1")],
            "technician": [FakeUser("u2")],
        }
    )
    notification_service = FakeNotificationService({})

    notifier = EmergencyNotifier(notification_service, user_service)
    stats = await notifier.broadcast_alert(
        title="Maintenance Notice",
        message="This is a dry-run validation",
        target_roles=["admin", "technician"],
        dry_run=True,
    )

    assert stats["total"] == 2
    assert stats["attempted"] == 2
    assert stats["sent"] == 0
    assert stats["failed"] == 0
    assert stats["fallback_used"] == 0
    assert stats["delivery_summary"]["total_attempts"] == 0
    assert stats["delivery_summary"]["total_success"] == 0
    assert stats["delivery_summary"]["total_failure"] == 0
    for channel in ["push", "email", "in_app"]:
        assert stats["delivery_summary"]["channels"][channel] == {
            "attempts": 0,
            "success": 0,
            "failure": 0,
        }
    assert notification_service.calls == []

    for user_id in ["u1", "u2"]:
        user_result = notifier.last_user_attempts[user_id]
        assert user_result["status"] == "dry_run"
        assert [item["channel"] for item in user_result["attempts"]] == [
            "push",
            "email",
            "in_app",
        ]
        assert all(item["status"] == "planned" for item in user_result["attempts"])


@pytest.mark.asyncio
async def test_broadcast_alert_falls_back_to_legacy_create_notification():
    user_service = FakeUserService(
        {
            "admin": [FakeUser("u1")],
        }
    )
    notification_service = FakeLegacyNotificationService()

    notifier = EmergencyNotifier(notification_service, user_service)
    stats = await notifier.broadcast_alert(
        title="Legacy Alert",
        message="Verify compatibility path",
        target_roles=["admin"],
        metadata={"request_id": "req-123", "event_id": "evt-456"},
    )

    assert notification_service.calls == [("u1", "push")]
    assert stats["total"] == 1
    assert stats["attempted"] == 1
    assert stats["sent"] == 1
    assert stats["failed"] == 0
    assert stats["fallback_used"] == 0
    assert stats["delivery_summary"]["total_attempts"] == 1
    assert stats["delivery_summary"]["total_success"] == 1
    assert stats["delivery_summary"]["total_failure"] == 0
    assert stats["delivery_summary"]["channels"]["push"] == {
        "attempts": 1,
        "success": 1,
        "failure": 0,
    }
    assert stats["delivery_summary"]["channels"]["email"] == {
        "attempts": 0,
        "success": 0,
        "failure": 0,
    }
    assert stats["delivery_summary"]["channels"]["in_app"] == {
        "attempts": 0,
        "success": 0,
        "failure": 0,
    }
    user_result = notifier.last_user_attempts["u1"]
    assert user_result["status"] == "sent"
    assert [item["channel"] for item in user_result["attempts"]] == ["push"]
    assert [item["status"] for item in user_result["attempts"]] == ["sent"]
