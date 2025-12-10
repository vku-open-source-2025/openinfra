import { useState } from "react";
import { Button } from "../ui/button";
import {
    X,
    HelpCircle,
    ArrowRight,
    CheckCircle,
    AlertTriangle,
    XCircle,
    Archive,
    Clock,
    User,
    Wrench,
    ShieldCheck,
} from "lucide-react";

interface IncidentWorkflowInfoProps {
    currentStatus: string;
    resolutionType?: string;
    resolutionNotes?: string;
}

const workflowSteps = [
    {
        status: "reported",
        label: "Đã báo cáo",
        icon: AlertTriangle,
        color: "text-yellow-600",
        bgColor: "bg-yellow-50",
        borderColor: "border-yellow-200",
        description:
            "Sự cố đã được báo cáo bởi người dân hoặc nhân viên. Việc xác minh bằng AI có thể đang tiến hành.",
        actions: ["Xác nhận", "Từ chối", "Xác minh thủ công"],
    },
    {
        status: "acknowledged",
        label: "Đã nhận",
        icon: CheckCircle,
        color: "text-blue-600",
        bgColor: "bg-blue-50",
        borderColor: "border-blue-200",
        description:
            "Sự cố đã được xem xét và xác nhận bởi quản trị/ quản lý.",
        actions: ["Giao kỹ thuật viên", "Từ chối"],
    },
    {
        status: "investigating",
        label: "Đang điều tra",
        icon: Wrench,
        color: "text-purple-600",
        bgColor: "bg-purple-50",
        borderColor: "border-purple-200",
        description:
            "Kỹ thuật viên đã được phân công và đang điều tra sự cố. Có thể tạo lệnh bảo trì nếu liên quan tới tài sản.",
        actions: ["Xử lý"],
    },
    {
        status: "resolved",
        label: "Đã xử lý",
        icon: CheckCircle,
        color: "text-green-600",
        bgColor: "bg-green-50",
        borderColor: "border-green-200",
        description:
            "Vấn đề đã được kỹ thuật viên sửa chữa.",
        actions: ["Đóng"],
    },
    {
        status: "closed",
        label: "Đã đóng",
        icon: Archive,
        color: "text-slate-600",
        bgColor: "bg-slate-50",
        borderColor: "border-slate-200",
        description: "Sự cố đã hoàn tất và được lưu trữ.",
        actions: [],
    },
    {
        status: "rejected",
        label: "Đã từ chối",
        icon: XCircle,
        color: "text-red-600",
        bgColor: "bg-red-50",
        borderColor: "border-red-200",
        description: "Sự cố đã bị từ chối vì không hợp lệ hoặc không đủ xác thực.",
        actions: [],
    },
];

export const IncidentWorkflowInfo: React.FC<IncidentWorkflowInfoProps> = ({
    currentStatus,
    resolutionType,
    resolutionNotes,
}) => {
    const [isOpen, setIsOpen] = useState(false);

    // Check if incident is rejected
    const isRejected = resolutionNotes?.toLowerCase().includes('rejected') || 
                      resolutionNotes?.toLowerCase().includes('từ chối') ||
                      resolutionType === 'not_an_issue' || 
                      resolutionType === 'invalid';

    // If rejected, show rejected status instead of normal workflow
    const displayStatus = isRejected ? 'rejected' : currentStatus;

    const currentStepIndex = workflowSteps.findIndex(
        (s) => s.status === displayStatus
    );

    return (
        <>
            <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(true)}
                className="text-slate-500 hover:text-slate-700"
            >
                <HelpCircle className="h-4 w-4 mr-1" />
                    Xem quy trình
            </Button>

            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Modal */}
                    <div className="relative bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b border-slate-200">
                            <h2 className="text-xl font-bold text-slate-900">
                                Quy trình xử lý sự cố
                            </h2>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1 rounded-lg hover:bg-slate-100 transition-colors"
                            >
                                <X className="h-5 w-5 text-slate-500" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                            <p className="text-sm text-slate-600 mb-6">
                                Mỗi sự cố sẽ trải qua các giai đoạn sau.
                                Các hành động khả dụng phụ thuộc vào trạng thái hiện tại.
                            </p>

                            <div className="space-y-3">
                                {workflowSteps
                                    .filter(step => {
                                        // Hide rejected step if not rejected, hide normal steps if rejected
                                        if (step.status === 'rejected') {
                                            return isRejected;
                                        }
                                        return !isRejected;
                                    })
                                    .map((step, index, filteredSteps) => {
                                    const Icon = step.icon;
                                    const isCurrentStep =
                                        step.status === displayStatus;
                                    const currentFilteredIndex = filteredSteps.findIndex(s => s.status === displayStatus);
                                    const isPastStep = index < currentFilteredIndex;
                                    const isFutureStep =
                                        index > currentFilteredIndex;

                                    return (
                                        <div
                                            key={step.status}
                                            className="relative"
                                        >
                                            {/* Connector line */}
                                            {index <
                                                filteredSteps.length - 1 && (
                                                <div
                                                    className={`absolute left-5 top-12 w-0.5 h-6 ${
                                                        isPastStep
                                                            ? isRejected && step.status === 'rejected'
                                                                ? "bg-red-300"
                                                                : "bg-green-300"
                                                            : "bg-slate-200"
                                                    }`}
                                                />
                                            )}

                                            <div
                                                className={`
                        flex items-start gap-4 p-4 rounded-lg border-2 transition-all
                        ${
                            isCurrentStep
                                ? `${step.bgColor} ${step.borderColor} ring-2 ring-offset-2 ${isRejected && step.status === 'rejected' ? 'ring-red-400' : 'ring-blue-400'}`
                                : isPastStep
                                ? isRejected && step.status === 'rejected'
                                    ? "bg-red-50 border-red-200"
                                    : "bg-green-50 border-green-200"
                                : "bg-slate-50 border-slate-200 opacity-60"
                        }
                      `}
                                            >
                                                <div
                                                    className={`
                          shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                          ${
                              isCurrentStep
                                  ? `${step.bgColor} ${step.color}`
                                  : isPastStep
                                  ? isRejected && step.status === 'rejected'
                                      ? "bg-red-100 text-red-600"
                                      : "bg-green-100 text-green-600"
                                  : "bg-slate-100 text-slate-400"
                          }
                        `}
                                                >
                                                    {isPastStep ? (
                                                        isRejected && step.status === 'rejected' ? (
                                                            <XCircle className="h-5 w-5" />
                                                        ) : (
                                                            <CheckCircle className="h-5 w-5" />
                                                        )
                                                    ) : (
                                                        <Icon className="h-5 w-5" />
                                                    )}
                                                </div>

                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <h3
                                                            className={`font-semibold ${
                                                                isCurrentStep
                                                                    ? step.color
                                                                    : isPastStep
                                                                    ? "text-green-700"
                                                                    : "text-slate-500"
                                                            }`}
                                                        >
                                                            {step.label}
                                                        </h3>
                                                        {isCurrentStep && (
                                                            <span className="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded-full">
                                                                Hiện tại
                                                            </span>
                                                        )}
                                                        {isPastStep && (
                                                            <span className={`px-2 py-0.5 text-xs font-medium text-white rounded-full ${
                                                                isRejected && step.status === 'rejected'
                                                                    ? 'bg-red-600'
                                                                    : 'bg-green-600'
                                                            }`}>
                                                                {isRejected && step.status === 'rejected' ? 'Đã từ chối' : 'Hoàn thành'}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-slate-600 mt-1">
                                                        {step.description}
                                                    </p>

                                                    {step.actions.length >
                                                        0 && (
                                                        <div className="flex flex-wrap gap-2 mt-2">
                                                            {step.actions.map(
                                                                (action) => (
                                                                    <span
                                                                        key={
                                                                            action
                                                                        }
                                                                        className={`
                                    px-2 py-1 text-xs rounded-md
                                    ${
                                        ["Reject", "Từ chối"].includes(action)
                                            ? "bg-red-100 text-red-700"
                                            : "bg-slate-100 text-slate-600"
                                    }
                                  `}
                                                                    >
                                                                        {action}
                                                                    </span>
                                                                )
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Legend */}
                            <div className="mt-6 pt-4 border-t border-slate-200">
                                <h4 className="text-sm font-semibold text-slate-700 mb-2">
                                    Hành động đặc biệt
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                                    <div className="flex items-center gap-2">
                                        <XCircle className="h-4 w-4 text-red-500" />
                                        <span className="text-slate-600">
                                            <strong>Từ chối:</strong> Đánh dấu là
                                            không hợp lệ/ rác
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Archive className="h-4 w-4 text-green-600" />
                                        <span className="text-slate-600">
                                            <strong>Đóng:</strong> Lưu trữ sự cố hoàn
                                            tất
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <ShieldCheck className="h-4 w-4 text-blue-600" />
                                        <span className="text-slate-600">
                                            <strong>Xác minh:</strong> Xác minh
                                            thủ công sự cố
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-slate-200 bg-slate-50">
                            <Button
                                onClick={() => setIsOpen(false)}
                                className="w-full"
                            >
                                Đã hiểu
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
