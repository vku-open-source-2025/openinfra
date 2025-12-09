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
}

const workflowSteps = [
    {
        status: "reported",
        label: "Reported",
        icon: AlertTriangle,
        color: "text-yellow-600",
        bgColor: "bg-yellow-50",
        borderColor: "border-yellow-200",
        description:
            "Incident has been reported by a citizen or staff member. AI verification may be in progress.",
        actions: ["Acknowledge", "Reject", "Manual Verify"],
    },
    {
        status: "acknowledged",
        label: "Acknowledged",
        icon: CheckCircle,
        color: "text-blue-600",
        bgColor: "bg-blue-50",
        borderColor: "border-blue-200",
        description:
            "Incident has been reviewed and confirmed as valid by admin/manager.",
        actions: ["Assign to Technician", "Reject"],
    },
    {
        status: "investigating",
        label: "Investigating",
        icon: Wrench,
        color: "text-purple-600",
        bgColor: "bg-purple-50",
        borderColor: "border-purple-200",
        description:
            "A technician has been assigned and is investigating the issue. Maintenance work order may be created if linked to an asset.",
        actions: ["Resolve"],
    },
    {
        status: "resolved",
        label: "Resolved",
        icon: CheckCircle,
        color: "text-green-600",
        bgColor: "bg-green-50",
        borderColor: "border-green-200",
        description:
            "The issue has been fixed by the technician. If maintenance costs are pending, approval is required before closing.",
        actions: ["Approve Cost", "Close"],
    },
    {
        status: "closed",
        label: "Closed",
        icon: Archive,
        color: "text-slate-600",
        bgColor: "bg-slate-50",
        borderColor: "border-slate-200",
        description: "Incident is complete and archived.",
        actions: [],
    },
];

export const IncidentWorkflowInfo: React.FC<IncidentWorkflowInfoProps> = ({
    currentStatus,
}) => {
    const [isOpen, setIsOpen] = useState(false);

    const currentStepIndex = workflowSteps.findIndex(
        (s) => s.status === currentStatus
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
                View Workflow
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
                                Incident Workflow
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
                                Each incident goes through the following stages.
                                Actions available depend on the current status.
                            </p>

                            <div className="space-y-3">
                                {workflowSteps.map((step, index) => {
                                    const Icon = step.icon;
                                    const isCurrentStep =
                                        step.status === currentStatus;
                                    const isPastStep = index < currentStepIndex;
                                    const isFutureStep =
                                        index > currentStepIndex;

                                    return (
                                        <div
                                            key={step.status}
                                            className="relative"
                                        >
                                            {/* Connector line */}
                                            {index <
                                                workflowSteps.length - 1 && (
                                                <div
                                                    className={`absolute left-5 top-12 w-0.5 h-6 ${
                                                        isPastStep
                                                            ? "bg-green-300"
                                                            : "bg-slate-200"
                                                    }`}
                                                />
                                            )}

                                            <div
                                                className={`
                        flex items-start gap-4 p-4 rounded-lg border-2 transition-all
                        ${
                            isCurrentStep
                                ? `${step.bgColor} ${step.borderColor} ring-2 ring-offset-2 ring-blue-400`
                                : isPastStep
                                ? "bg-green-50 border-green-200"
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
                                  ? "bg-green-100 text-green-600"
                                  : "bg-slate-100 text-slate-400"
                          }
                        `}
                                                >
                                                    {isPastStep ? (
                                                        <CheckCircle className="h-5 w-5" />
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
                                                                Current
                                                            </span>
                                                        )}
                                                        {isPastStep && (
                                                            <span className="px-2 py-0.5 text-xs font-medium bg-green-600 text-white rounded-full">
                                                                Complete
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
                                        action === "Reject"
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
                                    Special Actions
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                                    <div className="flex items-center gap-2">
                                        <XCircle className="h-4 w-4 text-red-500" />
                                        <span className="text-slate-600">
                                            <strong>Reject:</strong> Mark as
                                            invalid/spam
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Archive className="h-4 w-4 text-green-600" />
                                        <span className="text-slate-600">
                                            <strong>Close:</strong> Archive
                                            completed incident
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <ShieldCheck className="h-4 w-4 text-blue-600" />
                                        <span className="text-slate-600">
                                            <strong>Verify:</strong> Manually
                                            verify incident
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <CheckCircle className="h-4 w-4 text-yellow-600" />
                                        <span className="text-slate-600">
                                            <strong>Approve Cost:</strong>{" "}
                                            Approve maintenance costs
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
                                Got it
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
