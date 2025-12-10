import { Button } from "../ui/button";
import { Select } from "../ui/select";
import type { Incident, IncidentStatus } from "../../types/incident";
import {
    CheckCircle,
    User,
    Wrench,
    X,
    XCircle,
    Archive,
    ShieldCheck,
} from "lucide-react";
import { useState } from "react";

interface IncidentActionsProps {
    incident: Incident;
    onAcknowledge: () => Promise<void>;
    onAssign: (userId: string) => Promise<void>;
    onResolve: (
        notes: string,
        type: "fixed" | "duplicate" | "invalid" | "deferred"
    ) => Promise<void>;
    onClose?: (notes?: string) => Promise<void>;
    onReject?: (reason: string) => Promise<void>;
    onVerify?: () => Promise<void>;
    availableUsers?: Array<{ id: string; full_name: string }>;
    canAcknowledge?: boolean;
    canAssign?: boolean;
    canResolve?: boolean;
    canClose?: boolean;
    canReject?: boolean;
    canVerify?: boolean;
}

export const IncidentActions: React.FC<IncidentActionsProps> = ({
    incident,
    onAcknowledge,
    onAssign,
    onResolve,
    onClose,
    onReject,
    onVerify,
    availableUsers = [],
    canAcknowledge = false,
    canAssign = false,
    canResolve = false,
    canClose = false,
    canReject = false,
    canVerify = false,
}) => {
    const [selectedUserId, setSelectedUserId] = useState("");
    const [resolutionNotes, setResolutionNotes] = useState("");
    const [resolutionType, setResolutionType] = useState<
        "fixed" | "duplicate" | "invalid" | "deferred"
    >("fixed");
    const [rejectReason, setRejectReason] = useState("");
    const [closeNotes, setCloseNotes] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [showRejectForm, setShowRejectForm] = useState(false);
    const [showCloseForm, setShowCloseForm] = useState(false);

    const handleAcknowledge = async () => {
        setIsProcessing(true);
        try {
            await onAcknowledge();
        } finally {
            setIsProcessing(false);
        }
    };

    const handleAssign = async () => {
        if (!selectedUserId) return;
        setIsProcessing(true);
        try {
            await onAssign(selectedUserId);
            setSelectedUserId("");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleResolve = async () => {
        if (!resolutionNotes.trim()) return;
        setIsProcessing(true);
        try {
            await onResolve(resolutionNotes, resolutionType);
            setResolutionNotes("");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleClose = async () => {
        if (!onClose) return;
        setIsProcessing(true);
        try {
            await onClose(closeNotes || undefined);
            setCloseNotes("");
            setShowCloseForm(false);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleReject = async () => {
        if (!onReject || !rejectReason.trim()) return;
        setIsProcessing(true);
        try {
            await onReject(rejectReason);
            setRejectReason("");
            setShowRejectForm(false);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="space-y-4">
            {/* Verify Button - for to_be_verified incidents */}
            {incident.ai_verification_status === "to_be_verified" &&
                canVerify &&
                onVerify && (
                    <Button
                        onClick={async () => {
                            setIsProcessing(true);
                            try {
                                await onVerify();
                            } finally {
                                setIsProcessing(false);
                            }
                        }}
                        disabled={isProcessing}
                        className="w-full bg-green-600 hover:bg-green-700"
                    >
                        <ShieldCheck className="h-4 w-4 mr-2" />
                        Verify as Legitimate
                    </Button>
                )}

            {incident.status === "reported" && canAcknowledge && (
                <Button
                    onClick={handleAcknowledge}
                    disabled={isProcessing}
                    className="w-full"
                >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Acknowledge Incident
                </Button>
            )}

            {incident.status === "acknowledged" && canAssign && (
                <div className="space-y-2">
                    <Select
                        value={selectedUserId}
                        onChange={(e) => setSelectedUserId(e.target.value)}
                        placeholder="Select technician..."
                    >
                        <option value="">Select technician...</option>
                        {availableUsers.map((user) => (
                            <option key={user.id} value={user.id}>
                                {user.full_name}
                            </option>
                        ))}
                    </Select>
                    <Button
                        onClick={handleAssign}
                        disabled={!selectedUserId || isProcessing}
                        className="w-full"
                    >
                        <User className="h-4 w-4 mr-2" />
                        Assign to Technician
                    </Button>
                </div>
            )}

            {incident.status === "investigating" && canResolve && (
                <div className="space-y-2">
                    <Select
                        value={resolutionType}
                        onChange={(e) =>
                            setResolutionType(e.target.value as any)
                        }
                    >
                        <option value="fixed">Fixed</option>
                        <option value="duplicate">Duplicate</option>
                        <option value="invalid">Invalid</option>
                        <option value="deferred">Deferred</option>
                    </Select>
                    <textarea
                        value={resolutionNotes}
                        onChange={(e) => setResolutionNotes(e.target.value)}
                        placeholder="Resolution notes..."
                        rows={3}
                        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                    />
                    <Button
                        onClick={handleResolve}
                        disabled={!resolutionNotes.trim() || isProcessing}
                        className="w-full"
                    >
                        <Wrench className="h-4 w-4 mr-2" />
                        Resolve Incident
                    </Button>
                </div>
            )}

            {/* Close Button - for resolved incidents */}
            {incident.status === "resolved" && canClose && onClose && (
                <div className="space-y-2">
                    {showCloseForm ? (
                        <>
                            <textarea
                                value={closeNotes}
                                onChange={(e) => setCloseNotes(e.target.value)}
                                placeholder="Closing notes (optional)..."
                                rows={2}
                                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                            />
                            <div className="flex gap-2">
                                <Button
                                    onClick={handleClose}
                                    disabled={isProcessing}
                                    className="flex-1 bg-green-600 hover:bg-green-700"
                                >
                                    <Archive className="h-4 w-4 mr-2" />
                                    Close Ticket
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => setShowCloseForm(false)}
                                    className="flex-1"
                                >
                                    Cancel
                                </Button>
                            </div>
                        </>
                    ) : (
                        <Button
                            onClick={() => setShowCloseForm(true)}
                            className="w-full bg-green-600 hover:bg-green-700"
                        >
                            <Archive className="h-4 w-4 mr-2" />
                            Close Ticket
                        </Button>
                    )}
                </div>
            )}

            {/* Reject Button - for reported/acknowledged incidents */}
            {(incident.status === "reported" ||
                incident.status === "acknowledged") &&
                canReject &&
                onReject && (
                    <div className="space-y-2 pt-2 border-t border-slate-200">
                        {showRejectForm ? (
                            <>
                                <textarea
                                    value={rejectReason}
                                    onChange={(e) =>
                                        setRejectReason(e.target.value)
                                    }
                                    placeholder="Reason for rejection (required)..."
                                    rows={2}
                                    className="w-full rounded-md border border-red-200 px-3 py-2 text-sm"
                                />
                                <div className="flex gap-2">
                                    <Button
                                        onClick={handleReject}
                                        disabled={
                                            !rejectReason.trim() || isProcessing
                                        }
                                        className="flex-1 bg-red-600 hover:bg-red-700"
                                    >
                                        <XCircle className="h-4 w-4 mr-2" />
                                        Confirm Reject
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={() => setShowRejectForm(false)}
                                        className="flex-1"
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <Button
                                variant="outline"
                                onClick={() => setShowRejectForm(true)}
                                className="w-full text-red-600 border-red-200 hover:bg-red-50"
                            >
                                <XCircle className="h-4 w-4 mr-2" />
                                Reject Ticket
                            </Button>
                        )}
                    </div>
                )}
        </div>
    );
};
