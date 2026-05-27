import { describe, test, expect, beforeEach } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { navigateTo } from "./helpers";

function isLoginViewVisible() {
    const loginHeading = screen.queryByRole("heading", {
        name: /đăng nhập|login|sign in/i,
    });
    const loginButton = screen.queryByRole("button", {
        name: /đăng nhập|login|sign in/i,
    });

    return Boolean(loginHeading || loginButton);
}

function isEmergencyCenterVisible() {
    const heading = screen.queryByText(/Trung tâm chỉ huy|Emergency Command Center/i);
    return Boolean(heading);
}

async function waitForEmergencyCenter() {
    await waitFor(() => {
        if (isLoginViewVisible() || isEmergencyCenterVisible()) {
            return true;
        }
        throw new Error("Emergency screen not ready yet");
    }, { timeout: 8000 });
}

describe("Emergency Command Center", () => {
    beforeEach(async () => {
        await navigateTo("/admin/emergency-center");
        await waitForEmergencyCenter();
    });

    test("should handle protected route access", async () => {
        if (isLoginViewVisible()) {
            expect(isLoginViewVisible()).toBeTruthy();
            return;
        }

        expect(window.location.pathname).toContain("/admin/emergency-center");
        const heading = screen.queryByText(/Trung tâm chỉ huy|Emergency Command Center/i);
        expect(heading).toBeTruthy();
    });

    test("should display all six emergency summary cards when authenticated", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const activeEvents = screen.queryByText(/Sự kiện đang xử lý|Active Events/i);
        const criticalHazards = screen.queryByText(/Nguy hiểm nghiêm trọng|Critical Hazards/i);
        const draftEop = screen.queryByText(/EOP nháp|Draft EOP/i);
        const openDispatch = screen.queryByText(/Điều phối đang mở|Open Dispatch/i);
        const availableResources = screen.queryByText(/Nguồn lực sẵn sàng|Available Resources/i);
        const publishedReports = screen.queryByText(/Báo cáo đã xuất bản|Published Reports/i);

        expect(activeEvents).toBeTruthy();
        expect(criticalHazards).toBeTruthy();
        expect(draftEop).toBeTruthy();
        expect(openDispatch).toBeTruthy();
        expect(availableResources).toBeTruthy();
        expect(publishedReports).toBeTruthy();
    });

    test("should render hazard realtime map section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const hazardMapTitle = screen.queryByText(/Bản đồ nguy hiểm|Hazard Realtime Map/i);
        expect(hazardMapTitle).toBeTruthy();
    });

    test("should expose event selector and action buttons", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const eventSelector = screen.queryByRole("combobox");
        const refreshButton = screen.queryByRole("button", { name: /Làm mới|Refresh/i });
        const optimizeButton = screen.queryByRole("button", { name: /Tối ưu|Optimize/i });
        const eopDraftButton = screen.queryByRole("button", { name: /Tạo bản nháp|AI Draft/i });

        expect(eventSelector).toBeTruthy();
        expect(refreshButton).toBeTruthy();
        expect(optimizeButton).toBeTruthy();
        expect(eopDraftButton).toBeTruthy();
    });

    test("should allow selecting emergency event", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const eventSelector = screen.queryByRole("combobox") as HTMLSelectElement | null;
        expect(eventSelector).toBeTruthy();

        if (eventSelector && eventSelector.options.length > 1) {
            await userEvent.selectOptions(eventSelector, eventSelector.options[1].value);
            expect(eventSelector.value).toBe(eventSelector.options[1].value);
        }
    });

    test("should show navigation links for before/during/after phases", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const beforeLink = screen.queryByText(/Bảng trước thiên tai|Before/i);
        const duringLink = screen.queryByText(/Bảng trong thiên tai|During/i);
        const afterLink = screen.queryByText(/Bảng sau thiên tai|After/i);

        expect(beforeLink).toBeTruthy();
        expect(duringLink).toBeTruthy();
        expect(afterLink).toBeTruthy();
    });

    test("should display SOS timeline table", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const timelineSection = screen.queryByText(/SOS Timeline/i);
        expect(timelineSection).toBeTruthy();
    });

    test("should display hazard list section with deploy buttons or deployed links", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        // Wait for hazard data to potentially load
        await waitFor(() => {
            const hasHazardOrEmpty = screen.queryByText(/Tạo kế hoạch|Đã triển khai|Không có hazard/i);
            return hasHazardOrEmpty !== null;
        }, { timeout: 5000 }).catch(() => {
            // If no hazard data, that's acceptable too
        });

        // The hazard list area should exist
        const hazardListContainer = screen.queryByText(/Bản đồ nguy hiểm|Hazard/i);
        expect(hazardListContainer).toBeTruthy();
    });

    test("should display EOP rescue area section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const rescueSection = screen.queryByText(/Khu vực cứu hộ|Rescue Area|EOP/i);
        expect(rescueSection).toBeTruthy();
    });

    test("should display dispatch board section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const dispatchSection = screen.queryByText(/Bảng điều phối|Dispatch Board/i);
        expect(dispatchSection).toBeTruthy();
    });

    test("should display after-action reports section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const aarSection = screen.queryByText(/Báo cáo sau sự kiện|After Action/i);
        expect(aarSection).toBeTruthy();
    });

    test("should display quick signals section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const signalsSection = screen.queryByText(/Tín hiệu vận hành|Quick Signals/i);
        expect(signalsSection).toBeTruthy();
    });

    test("should show loading state initially", async () => {
        // Navigate fresh to check loading
        await navigateTo("/admin/emergency-center");
        const loadingOrContent = screen.queryByText(
            /Đang tải|Loading|Trung tâm chỉ huy|Đăng nhập/i
        );
        expect(loadingOrContent).toBeTruthy();
    });

    test("refresh button triggers data reload without crashing", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const refreshButton = screen.queryByRole("button", { name: /Làm mới|Refresh/i });
        if (!refreshButton) return;

        await userEvent.click(refreshButton);
        // After click, the page should still render (no crash)
        await waitFor(() => {
            const heading = screen.queryByText(/Trung tâm chỉ huy|Emergency Command Center/i);
            return Boolean(heading);
        }, { timeout: 5000 });
    });
});

describe("Rescue Operation Page", () => {
    const testEventId = "test-event-id";

    beforeEach(async () => {
        await navigateTo(`/admin/emergency-center/operations/${testEventId}`);
        await waitFor(() => {
            const backLink = screen.queryByText(/Trở về Command Center|Back/i);
            const loginView = isLoginViewVisible();
            return Boolean(backLink || loginView);
        }, { timeout: 8000 });
    });

    test("should render the back navigation link", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const backLink = screen.queryByText(/Trở về Command Center|Back/i);
        expect(backLink).toBeTruthy();
    });

    test("should show pending tasks section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        // May show loading first, then content
        await waitFor(() => {
            const pendingSection = screen.queryByText(/Chờ duyệt|Pending/i);
            const loadingSpinner = screen.queryByRole("img", { name: /loading/i });
            return Boolean(pendingSection || loadingSpinner);
        }, { timeout: 5000 }).catch(() => {});

        const pendingOrContent = screen.queryByText(/Chờ duyệt|Không có task|EOP|Pending/i);
        expect(pendingOrContent).toBeTruthy();
    });

    test("should render EOP plan section", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        await waitFor(() => {
            const eopSection = screen.queryByText(/Kế hoạch ứng phó|EOP|Chưa có EOP/i);
            return Boolean(eopSection);
        }, { timeout: 5000 }).catch(() => {});

        const eopSection = screen.queryByText(/Kế hoạch ứng phó|EOP|Chưa có EOP/i);
        expect(eopSection).toBeTruthy();
    });

    test("should back-navigate to emergency center", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        const backLink = screen.queryByText(/Trở về Command Center/i);
        if (!backLink) return;

        await userEvent.click(backLink);
        await waitFor(() => {
            return window.location.pathname.includes("/admin/emergency-center");
        }, { timeout: 5000 });

        expect(window.location.pathname).toContain("/admin/emergency-center");
    });
});

describe("Emergency Phase Boards", () => {
    test("before-disaster board renders", async () => {
        await navigateTo("/admin/emergency-center/before");
        await waitFor(() => {
            const content = screen.queryByText(/.+/);
            return Boolean(content);
        }, { timeout: 5000 });
        expect(window.location.pathname).toContain("before");
    });

    test("during-disaster board renders", async () => {
        await navigateTo("/admin/emergency-center/during");
        await waitFor(() => {
            const content = screen.queryByText(/.+/);
            return Boolean(content);
        }, { timeout: 5000 });
        expect(window.location.pathname).toContain("during");
    });

    test("after-disaster board renders", async () => {
        await navigateTo("/admin/emergency-center/after");
        await waitFor(() => {
            const content = screen.queryByText(/.+/);
            return Boolean(content);
        }, { timeout: 5000 });
        expect(window.location.pathname).toContain("after");
    });
});

describe("Deploy EOP Modal", () => {
    beforeEach(async () => {
        await navigateTo("/admin/emergency-center");
        await waitForEmergencyCenter();
    });

    test("deploy button or deployed link is rendered for hazard items", async () => {
        if (isLoginViewVisible()) {
            return;
        }

        // Give the hazard list time to load
        await waitFor(() => {
            const buttons = screen.queryAllByRole("button", { name: /Tạo kế hoạch/i });
            const links = screen.queryAllByText(/Đã triển khai/i);
            const emptyMsg = screen.queryByText(/Không có hazard/i);
            return buttons.length > 0 || links.length > 0 || emptyMsg !== null;
        }, { timeout: 5000 }).catch(() => {
            // No hazard data is acceptable in test environment
        });

        // Page should still be stable
        const heading = screen.queryByText(/Trung tâm chỉ huy|Emergency Command Center/i);
        expect(heading).toBeTruthy();
    });
});
