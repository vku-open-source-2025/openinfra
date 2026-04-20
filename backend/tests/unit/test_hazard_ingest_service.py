"""Unit tests for hazard ingest service health/readiness checks."""

import pytest

from app.services.hazard_ingest_service import HazardIngestService


class _FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


@pytest.fixture(autouse=True)
def reset_last_feed_checks():
    """Ensure test isolation for cached reachability status."""
    HazardIngestService._last_feed_checks = {}


@pytest.mark.asyncio
async def test_ingest_status_reports_not_configured_when_feed_urls_missing(monkeypatch):
    """Health endpoint should report missing feed URLs as not configured."""
    monkeypatch.delenv("NCHMF_FEED_URL", raising=False)
    monkeypatch.delenv("VNDMS_FEED_URL", raising=False)

    service = HazardIngestService()

    status = await service.get_ingest_status(check_reachability=False)

    assert status["feeds"]["nchmf"]["configured"] is False
    assert status["feeds"]["nchmf"]["url_present"] is False
    assert status["feeds"]["nchmf"]["last_check"]["status"] == "missing_url"

    assert status["feeds"]["vndms"]["configured"] is False
    assert status["feeds"]["vndms"]["url_present"] is False
    assert status["feeds"]["vndms"]["last_check"]["status"] == "missing_url"

    assert status["overall"]["status"] == "not_configured"
    assert status["overall"]["ready"] is False
    assert status["overall"]["configured_feeds"] == 0


@pytest.mark.asyncio
async def test_ingest_status_reports_configured_when_urls_present_and_not_checked(monkeypatch):
    """With URLs present and checks disabled, status should remain configured."""
    monkeypatch.setenv("NCHMF_FEED_URL", "https://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")

    service = HazardIngestService()

    status = await service.get_ingest_status(check_reachability=False)

    assert status["feeds"]["nchmf"]["configured"] is True
    assert status["feeds"]["nchmf"]["url_present"] is True
    assert status["feeds"]["nchmf"]["last_check"]["status"] == "not_checked"
    assert status["feeds"]["nchmf"]["last_check"]["reachable"] is None

    assert status["feeds"]["vndms"]["configured"] is True
    assert status["feeds"]["vndms"]["url_present"] is True
    assert status["feeds"]["vndms"]["last_check"]["status"] == "not_checked"
    assert status["feeds"]["vndms"]["last_check"]["reachable"] is None

    assert status["overall"]["status"] == "configured"
    assert status["overall"]["ready"] is False
    assert status["overall"]["reachability_checked"] is False


@pytest.mark.asyncio
async def test_ingest_status_reports_invalid_url_when_present_but_malformed(monkeypatch):
    """Malformed URL should be present but not configured."""
    monkeypatch.setenv("NCHMF_FEED_URL", "http://nchmf.example.com:badport/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")

    service = HazardIngestService()

    status = await service.get_ingest_status(check_reachability=False)

    assert status["feeds"]["nchmf"]["url_present"] is True
    assert status["feeds"]["nchmf"]["configured"] is False
    assert status["feeds"]["nchmf"]["last_check"]["status"] == "invalid_url"
    assert status["feeds"]["nchmf"]["last_check"]["error"]

    assert status["feeds"]["vndms"]["configured"] is True
    assert status["overall"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_ingest_status_marks_non_http_url_as_invalid_without_probing(monkeypatch):
    """Non-http URLs should be rejected as invalid before any HTTP probe."""
    monkeypatch.setenv("NCHMF_FEED_URL", "ftp://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")
    calls = []

    class ProbeCaptureAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            calls.append(("HEAD", url))
            return _FakeResponse(200)

        async def get(self, url):
            calls.append(("GET", url))
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", ProbeCaptureAsyncClient)

    service = HazardIngestService()
    status = await service.get_ingest_status(check_reachability=True)

    assert status["feeds"]["nchmf"]["url_present"] is True
    assert status["feeds"]["nchmf"]["configured"] is False
    assert status["feeds"]["nchmf"]["last_check"]["status"] == "invalid_url"
    assert status["feeds"]["nchmf"]["last_check"]["checked"] is False
    assert "http/https" in status["feeds"]["nchmf"]["last_check"]["error"]

    assert status["feeds"]["vndms"]["configured"] is True
    assert status["feeds"]["vndms"]["last_check"]["status"] == "reachable"
    assert calls == [("HEAD", "https://vndms.example.com/feed")]
    assert status["overall"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_ingest_status_reachability_true_reports_ready(monkeypatch):
    """Reachability checks should mark service ready when both feeds are reachable."""
    monkeypatch.setenv("NCHMF_FEED_URL", "https://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")

    class ReachableAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            return _FakeResponse(200)

        async def get(self, url):
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", ReachableAsyncClient)

    service = HazardIngestService()
    status = await service.get_ingest_status(check_reachability=True)

    assert status["feeds"]["nchmf"]["last_check"]["reachable"] is True
    assert status["feeds"]["nchmf"]["last_check"]["method"] == "HEAD"
    assert status["feeds"]["vndms"]["last_check"]["reachable"] is True
    assert status["feeds"]["vndms"]["last_check"]["method"] == "HEAD"
    assert status["overall"]["status"] == "ready"
    assert status["overall"]["ready"] is True


@pytest.mark.asyncio
async def test_ingest_status_not_checked_does_not_report_ready_from_cached_reachability(monkeypatch):
    """Cached probe results must not mark readiness when checks are disabled."""
    monkeypatch.setenv("NCHMF_FEED_URL", "https://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")

    class ReachableAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            return _FakeResponse(200)

        async def get(self, url):
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", ReachableAsyncClient)

    service = HazardIngestService()

    checked_status = await service.get_ingest_status(check_reachability=True)
    assert checked_status["overall"]["status"] == "ready"
    assert checked_status["overall"]["ready"] is True

    skipped_status = await service.get_ingest_status(check_reachability=False)

    assert skipped_status["feeds"]["nchmf"]["last_check"]["checked"] is True
    assert skipped_status["feeds"]["vndms"]["last_check"]["checked"] is True
    assert skipped_status["overall"]["reachability_checked"] is False
    assert skipped_status["overall"]["status"] == "configured"
    assert skipped_status["overall"]["ready"] is False


@pytest.mark.asyncio
async def test_timeout_override_is_applied_to_reachability_checks(monkeypatch):
    """Request timeout override should be used for all feed probes."""
    monkeypatch.setenv("NCHMF_FEED_URL", "https://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")
    captured_timeouts = []

    class TimeoutCaptureAsyncClient:
        def __init__(self, *args, **kwargs):
            captured_timeouts.append(kwargs.get("timeout"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            return _FakeResponse(200)

        async def get(self, url):
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", TimeoutCaptureAsyncClient)

    service = HazardIngestService()
    status = await service.get_ingest_status(check_reachability=True, timeout_seconds=3.5)

    assert captured_timeouts == [3.5, 3.5]
    assert status["feeds"]["nchmf"]["last_check"]["timeout_seconds"] == 3.5
    assert status["feeds"]["vndms"]["last_check"]["timeout_seconds"] == 3.5


@pytest.mark.asyncio
async def test_invalid_timeout_env_falls_back_to_default_timeout(monkeypatch):
    """Invalid timeout from env should fall back to default 20 seconds."""
    monkeypatch.setenv("NCHMF_FEED_URL", "https://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")
    monkeypatch.setenv("HAZARD_FEED_TIMEOUT", "not-a-number")
    captured_timeouts = []

    class TimeoutCaptureAsyncClient:
        def __init__(self, *args, **kwargs):
            captured_timeouts.append(kwargs.get("timeout"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            return _FakeResponse(200)

        async def get(self, url):
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", TimeoutCaptureAsyncClient)

    service = HazardIngestService()
    status = await service.get_ingest_status(check_reachability=True)

    assert service.feed_timeout_seconds == 20.0
    assert captured_timeouts == [20.0, 20.0]
    assert status["feeds"]["nchmf"]["last_check"]["timeout_seconds"] == 20.0
    assert status["feeds"]["vndms"]["last_check"]["timeout_seconds"] == 20.0


@pytest.mark.asyncio
async def test_invalid_timeout_override_falls_back_to_configured_timeout(monkeypatch):
    """Non-positive timeout override should gracefully fall back to configured timeout."""
    monkeypatch.setenv("NCHMF_FEED_URL", "https://nchmf.example.com/feed")
    monkeypatch.setenv("VNDMS_FEED_URL", "https://vndms.example.com/feed")
    monkeypatch.setenv("HAZARD_FEED_TIMEOUT", "7")
    captured_timeouts = []

    class TimeoutCaptureAsyncClient:
        def __init__(self, *args, **kwargs):
            captured_timeouts.append(kwargs.get("timeout"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            return _FakeResponse(200)

        async def get(self, url):
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", TimeoutCaptureAsyncClient)

    service = HazardIngestService()
    status = await service.get_ingest_status(check_reachability=True, timeout_seconds=0)

    assert captured_timeouts == [7.0, 7.0]
    assert status["feeds"]["nchmf"]["last_check"]["timeout_seconds"] == 7.0
    assert status["feeds"]["vndms"]["last_check"]["timeout_seconds"] == 7.0


@pytest.mark.asyncio
async def test_reachability_falls_back_to_get_when_head_not_supported(monkeypatch):
    """HEAD 405 should fallback to GET when enabled."""
    calls = []

    class FallbackAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            calls.append(("HEAD", url))
            return _FakeResponse(405)

        async def get(self, url):
            calls.append(("GET", url))
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", FallbackAsyncClient)

    service = HazardIngestService()
    result = await service._check_feed_reachability(
        "nchmf",
        "https://nchmf.example.com/feed",
        check_reachability=True,
        timeout_seconds=None,
        allow_get_fallback=True,
    )

    assert calls == [
        ("HEAD", "https://nchmf.example.com/feed"),
        ("GET", "https://nchmf.example.com/feed"),
    ]
    assert result["status"] == "reachable"
    assert result["reachable"] is True
    assert result["method"] == "GET"
    assert result["status_code"] == 200
    assert result["error"] is None


@pytest.mark.asyncio
async def test_reachability_without_fallback_keeps_http_error_and_error_field(monkeypatch):
    """Without fallback, HEAD 405 should remain HTTP error with populated error field."""

    class HeadOnlyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            return _FakeResponse(405)

        async def get(self, url):
            raise AssertionError("GET should not be called when fallback is disabled")

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", HeadOnlyAsyncClient)

    service = HazardIngestService()
    result = await service._check_feed_reachability(
        "nchmf",
        "https://nchmf.example.com/feed",
        check_reachability=True,
        timeout_seconds=None,
        allow_get_fallback=False,
    )

    assert result["status"] == "http_error"
    assert result["reachable"] is False
    assert result["method"] == "HEAD"
    assert result["status_code"] == 405
    assert "405" in result["error"]


@pytest.mark.asyncio
async def test_reachability_handles_unexpected_exception_with_error_details(monkeypatch):
    """Unexpected probe exceptions should not bubble and must include error details."""

    class CrashingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def head(self, url):
            raise RuntimeError("socket exploded")

        async def get(self, url):
            return _FakeResponse(200)

    monkeypatch.setattr("app.services.hazard_ingest_service.httpx.AsyncClient", CrashingAsyncClient)

    service = HazardIngestService()
    result = await service._check_feed_reachability(
        "nchmf",
        "https://nchmf.example.com/feed",
        check_reachability=True,
        timeout_seconds=None,
        allow_get_fallback=True,
    )

    assert result["status"] == "unexpected_error"
    assert result["reachable"] is False
    assert result["method"] == "HEAD"
    assert "socket exploded" in result["error"]
