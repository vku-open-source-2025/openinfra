import React, { useState, useRef } from "react";
import {
    X,
    Send,
    AlertTriangle,
    Upload,
    User,
    Phone,
    CreditCard,
    Smartphone,
    CheckCircle,
} from "lucide-react";
import {
    createIncident,
    IncidentCategory,
    IncidentSeverity,
    type Asset,
    type ContactInfo,
} from "../api";
import { Turnstile } from "./Turnstile";

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || "";

interface ReportModalProps {
    isOpen: boolean;
    onClose: () => void;
    asset: Asset | null;
}

const ReportModal: React.FC<ReportModalProps> = ({
    isOpen,
    onClose,
    asset,
}) => {
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [category, setCategory] = useState<IncidentCategory>(
        IncidentCategory.MALFUNCTION
    );
    const [severity, setSeverity] = useState<IncidentSeverity>(
        IncidentSeverity.LOW
    );
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    // Contact information
    const [contactName, setContactName] = useState("");
    const [phoneNumber, setPhoneNumber] = useState("");

    // Vietnamese ID Card (CCCD/CMND) - REQUIRED for verification
    const [idCardNumber, setIdCardNumber] = useState("");
    const [idCardError, setIdCardError] = useState<string>("");
    const [isVNeIDVerified, setIsVNeIDVerified] = useState(false);
    const [showVNeIDModal, setShowVNeIDModal] = useState(false);
    const [vneidVerifying, setVneidVerifying] = useState(false);

    // Image upload
    const [image, setImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Turnstile captcha
    const [turnstileToken, setTurnstileToken] = useState<string>("");
    const [captchaError, setCaptchaError] = useState<string>("");

    // Image validation
    const [imageError, setImageError] = useState<string>("");

    // Validate Vietnamese ID Card format (CCCD: 12 digits, CMND: 9 digits)
    const validateVietnameseID = (id: string): boolean => {
        // Remove spaces and dashes
        const cleaned = id.replace(/[\s-]/g, "");
        // Check if it's 9 digits (CMND) or 12 digits (CCCD)
        return /^\d{9}$/.test(cleaned) || /^\d{12}$/.test(cleaned);
    };

    const handleIdCardChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.replace(/\D/g, ""); // Only allow digits
        setIdCardNumber(value);
        setIdCardError("");
        setIsVNeIDVerified(false); // Reset VNeID verification if manually entered
    };

    const handleVNeIDVerify = async () => {
        setShowVNeIDModal(true);
        setVneidVerifying(true);

        // Simulate VNeID verification process
        // In production, this would integrate with VNeID API
        setTimeout(() => {
            // Mock: Generate a random valid ID for demo purposes
            // In production, this would come from VNeID API response
            const mockVerifiedID = "001234567890"; // 12-digit CCCD format
            setIdCardNumber(mockVerifiedID);
            setIsVNeIDVerified(true);
            setVneidVerifying(false);
            setShowVNeIDModal(false);
            setIdCardError("");
        }, 2000);
    };

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setImage(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const removeImage = () => {
        setImage(null);
        setImagePreview(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    if (!isOpen || !asset) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setCaptchaError("");
        setImageError("");
        setIdCardError("");

        // Validate Vietnamese ID Card (REQUIRED)
        if (!idCardNumber) {
            setIdCardError("Vui lòng nhập số CCCD/CMND để xác thực danh tính");
            return;
        }

        if (!validateVietnameseID(idCardNumber)) {
            setIdCardError(
                "Số CCCD/CMND không hợp lệ. Vui lòng nhập 9 số (CMND) hoặc 12 số (CCCD)"
            );
            return;
        }

        // Validate image is uploaded
        if (!image) {
            setImageError("Please upload an image of the issue");
            return;
        }

        // Validate captcha
        if (TURNSTILE_SITE_KEY && !turnstileToken) {
            setCaptchaError("Please complete the captcha verification");
            return;
        }

        setIsSubmitting(true);

        try {
            const contactInfo: ContactInfo = {};
            if (contactName) contactInfo.name = contactName;
            if (phoneNumber) contactInfo.phone_number = phoneNumber;
            if (idCardNumber) contactInfo.id_card_number = idCardNumber;

            await createIncident(
                {
                    asset_id: asset.id || asset._id,
                    title,
                    description,
                    category,
                    severity,
                    reported_via: "web",
                    public_visible: true,
                    contact_info:
                        Object.keys(contactInfo).length > 0
                            ? contactInfo
                            : undefined,
                },
                image || undefined,
                turnstileToken || undefined
            );
            setSuccess(true);
            setTimeout(() => {
                onClose();
                setSuccess(false);
                setTitle("");
                setDescription("");
                setCategory(IncidentCategory.MALFUNCTION);
                setSeverity(IncidentSeverity.LOW);
                setContactName("");
                setPhoneNumber("");
                setIdCardNumber("");
                setImage(null);
                setImagePreview(null);
            }, 2000);
        } catch (err) {
            console.error("Failed to submit report:", err);
            setError("Failed to submit report. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (success) {
        return (
            <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden p-8 text-center animate-in fade-in zoom-in duration-200">
                    <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Send size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-800 mb-2">
                        Report Submitted
                    </h3>
                    <p className="text-slate-500">
                        Thank you for your report. We will investigate the
                        issue.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
                <div className="flex justify-between items-center p-4 border-b border-slate-100 shrink-0">
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="text-amber-500" size={20} />
                        <h3 className="font-bold text-lg text-slate-800">
                            Report Issue
                        </h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto">
                    <div className="mb-6 bg-slate-50 p-3 rounded-lg border border-slate-100 text-sm">
                        <p className="font-medium text-slate-700">
                            Reporting for: {asset.feature_type}
                        </p>
                        <p className="text-slate-500 font-mono text-xs mt-1">
                            ID: {asset._id}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Issue Title
                            </label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                placeholder="e.g., Broken Equipment"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Category
                            </label>
                            <select
                                value={category}
                                onChange={(e) =>
                                    setCategory(
                                        e.target.value as IncidentCategory
                                    )
                                }
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
                            >
                                {Object.values(IncidentCategory).map((cat) => (
                                    <option key={cat} value={cat}>
                                        {cat.charAt(0).toUpperCase() +
                                            cat.slice(1).replace("_", " ")}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Severity
                            </label>
                            <select
                                value={severity}
                                onChange={(e) =>
                                    setSeverity(
                                        e.target.value as IncidentSeverity
                                    )
                                }
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
                            >
                                {Object.values(IncidentSeverity).map((sev) => (
                                    <option key={sev} value={sev}>
                                        {sev.charAt(0).toUpperCase() +
                                            sev.slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Description
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                required
                                rows={4}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
                                placeholder="Please describe the issue in detail..."
                            />
                        </div>

                        {/* Image Upload - REQUIRED */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Upload Image{" "}
                                <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleImageChange}
                                accept="image/*"
                                className="hidden"
                            />
                            {imagePreview ? (
                                <div className="relative">
                                    <img
                                        src={imagePreview}
                                        alt="Preview"
                                        className="w-full h-32 object-cover rounded-lg border border-slate-300"
                                    />
                                    <button
                                        type="button"
                                        onClick={removeImage}
                                        className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            ) : (
                                <button
                                    type="button"
                                    onClick={() =>
                                        fileInputRef.current?.click()
                                    }
                                    className="w-full py-4 border-2 border-dashed border-slate-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-all flex flex-col items-center gap-2 text-slate-500"
                                >
                                    <Upload size={24} />
                                    <span className="text-sm">
                                        Click to upload image (required)
                                    </span>
                                </button>
                            )}
                            {imageError && (
                                <p className="text-sm text-red-500 mt-1">
                                    {imageError}
                                </p>
                            )}
                        </div>

                        {/* Vietnamese ID Verification Section - REQUIRED */}
                        <div className="border-t border-slate-200 pt-4 mt-4">
                            <div className="mb-3">
                                <h4 className="text-sm font-medium text-slate-700 mb-1">
                                    Xác thực danh tính{" "}
                                    <span className="text-red-500">*</span>
                                </h4>
                                <p className="text-xs text-slate-500">
                                    Vui lòng nhập số CCCD/CMND hoặc xác thực qua
                                    VNeID để xác thực danh tính và tránh spam
                                </p>
                            </div>

                            {/* VNeID Verification Button */}
                            <div className="mb-3">
                                <button
                                    type="button"
                                    onClick={handleVNeIDVerify}
                                    disabled={isVNeIDVerified || vneidVerifying}
                                    className={`w-full py-3 px-4 rounded-lg border-2 transition-all flex items-center justify-center gap-2 font-medium text-sm ${
                                        isVNeIDVerified
                                            ? "bg-green-50 border-green-300 text-green-700 cursor-not-allowed"
                                            : vneidVerifying
                                            ? "bg-blue-50 border-blue-300 text-blue-700 cursor-not-allowed"
                                            : "bg-white border-blue-500 text-blue-600 hover:bg-blue-50 hover:border-blue-600"
                                    }`}
                                >
                                    {isVNeIDVerified ? (
                                        <>
                                            <CheckCircle size={18} />
                                            <span>Đã xác thực qua VNeID</span>
                                        </>
                                    ) : vneidVerifying ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                                            <span>Đang xác thực VNeID...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Smartphone size={18} />
                                            <span>Xác thực qua VNeID</span>
                                        </>
                                    )}
                                </button>
                                {isVNeIDVerified && (
                                    <p className="text-xs text-green-600 mt-1 text-center">
                                        ✓ Đã xác thực thành công qua VNeID
                                    </p>
                                )}
                            </div>

                            {/* Divider */}
                            <div className="relative my-4">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-slate-200"></div>
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-white px-2 text-slate-500">
                                        Hoặc
                                    </span>
                                </div>
                            </div>

                            {/* Manual ID Input */}
                            <div className="relative">
                                <CreditCard
                                    size={16}
                                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                                />
                                <input
                                    type="text"
                                    value={idCardNumber}
                                    onChange={handleIdCardChange}
                                    maxLength={12}
                                    required
                                    disabled={isVNeIDVerified}
                                    className={`w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all ${
                                        idCardError
                                            ? "border-red-300 bg-red-50"
                                            : isVNeIDVerified
                                            ? "border-green-300 bg-green-50 cursor-not-allowed"
                                            : "border-slate-300"
                                    }`}
                                    placeholder={
                                        isVNeIDVerified
                                            ? "Đã xác thực qua VNeID"
                                            : "Nhập số CCCD (12 số) hoặc CMND (9 số)"
                                    }
                                />
                                {idCardError && (
                                    <p className="text-sm text-red-500 mt-1">
                                        {idCardError}
                                    </p>
                                )}
                                {!isVNeIDVerified && (
                                    <p className="text-xs text-slate-400 mt-1">
                                        Định dạng: CCCD (12 số) hoặc CMND (9 số)
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Contact Information Section */}
                        <div className="border-t border-slate-200 pt-4 mt-4">
                            <h4 className="text-sm font-medium text-slate-700 mb-3">
                                Thông tin liên hệ (Tùy chọn)
                            </h4>

                            <div className="space-y-3">
                                <div className="relative">
                                    <User
                                        size={16}
                                        className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                                    />
                                    <input
                                        type="text"
                                        value={contactName}
                                        onChange={(e) =>
                                            setContactName(e.target.value)
                                        }
                                        className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        placeholder="Họ và tên"
                                    />
                                </div>

                                <div className="relative">
                                    <Phone
                                        size={16}
                                        className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                                    />
                                    <input
                                        type="tel"
                                        value={phoneNumber}
                                        onChange={(e) =>
                                            setPhoneNumber(e.target.value)
                                        }
                                        className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        placeholder="Số điện thoại"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Cloudflare Turnstile Captcha */}
                        {TURNSTILE_SITE_KEY && (
                            <div className="border-t border-slate-200 pt-4 mt-4">
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Verify you're human
                                </label>
                                <Turnstile
                                    siteKey={TURNSTILE_SITE_KEY}
                                    onVerify={(token) =>
                                        setTurnstileToken(token)
                                    }
                                    onExpire={() => setTurnstileToken("")}
                                    onError={() =>
                                        setCaptchaError(
                                            "Captcha verification failed. Please try again."
                                        )
                                    }
                                    theme="auto"
                                />
                                {captchaError && (
                                    <p className="text-sm text-red-500 mt-1">
                                        {captchaError}
                                    </p>
                                )}
                            </div>
                        )}

                        {error && (
                            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">
                                {error}
                            </div>
                        )}

                        <div className="pt-2">
                            <button
                                type="submit"
                                disabled={
                                    isSubmitting ||
                                    !idCardNumber ||
                                    (TURNSTILE_SITE_KEY
                                        ? !turnstileToken
                                        : false)
                                }
                                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors shadow-sm"
                            >
                                {isSubmitting ? (
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <Send size={18} />
                                        Submit Report
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* VNeID Verification Modal */}
            {showVNeIDModal && (
                <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
                        <div className="flex justify-between items-center p-4 border-b border-slate-100">
                            <div className="flex items-center gap-2">
                                <Smartphone
                                    className="text-blue-500"
                                    size={20}
                                />
                                <h3 className="font-bold text-lg text-slate-800">
                                    Xác thực VNeID
                                </h3>
                            </div>
                            <button
                                onClick={() => {
                                    setShowVNeIDModal(false);
                                    setVneidVerifying(false);
                                }}
                                className="text-slate-400 hover:text-slate-600 transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-6 text-center">
                            {vneidVerifying ? (
                                <>
                                    <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
                                    </div>
                                    <h4 className="text-lg font-semibold text-slate-800 mb-2">
                                        Đang xác thực...
                                    </h4>
                                    <p className="text-sm text-slate-500">
                                        Vui lòng hoàn tất xác thực trên ứng dụng
                                        VNeID của bạn
                                    </p>
                                </>
                            ) : (
                                <>
                                    <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <CheckCircle size={32} />
                                    </div>
                                    <h4 className="text-lg font-semibold text-slate-800 mb-2">
                                        Xác thực thành công
                                    </h4>
                                    <p className="text-sm text-slate-500">
                                        Thông tin danh tính đã được xác thực qua
                                        VNeID
                                    </p>
                                </>
                            )}
                        </div>

                        {!vneidVerifying && (
                            <div className="px-6 pb-6">
                                <button
                                    onClick={() => setShowVNeIDModal(false)}
                                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                                >
                                    Đóng
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ReportModal;
