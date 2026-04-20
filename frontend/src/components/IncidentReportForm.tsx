import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { publicApi } from "../api/public";
import { Form, FormField, FormLabel, FormError } from "./ui/form";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Select } from "./ui/select";
import { Button } from "./ui/button";
import { Turnstile } from "./Turnstile";
import type {
    IncidentCategory,
    IncidentCreateRequest,
    IncidentSeverity,
} from "../types/incident";

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || "";

interface Props {
    /** Prefill coordinates (e.g. from map click) */
    defaultCoordinates?: { latitude: number; longitude: number };
    /** Called with the new incident after successful submission */
    onSuccess?: (incident: { id: string; incident_number?: string }) => void;
    /** Shown only when embedded outside of the /public/report page */
    hideLookup?: boolean;
}

const IncidentReportForm: React.FC<Props> = ({
    defaultCoordinates,
    onSuccess,
    hideLookup,
}) => {
    const [formData, setFormData] = useState<Partial<IncidentCreateRequest>>({
        title: "",
        description: "",
        category: "other",
        severity: "medium",
        location: {
            address: "",
            coordinates: {
                longitude: defaultCoordinates?.longitude ?? 0,
                latitude: defaultCoordinates?.latitude ?? 0,
            },
        },
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [turnstileToken, setTurnstileToken] = useState("");
    const [submitted, setSubmitted] = useState<{
        id: string;
        incident_number?: string;
    } | null>(null);

    const createMutation = useMutation({
        mutationFn: (data: IncidentCreateRequest) =>
            publicApi.createAnonymousIncident(data, turnstileToken),
        onSuccess: (incident) => {
            setSubmitted({
                id: incident.id,
                incident_number: incident.incident_number,
            });
            onSuccess?.(incident);
        },
        onError: (error: unknown) => {
            const detail = (error as { response?: { data?: { detail?: string } } })
                .response?.data?.detail;
            if (detail) setErrors({ submit: detail });
            else setErrors({ submit: "Gửi báo cáo thất bại. Thử lại sau." });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});
        if (!formData.title?.trim()) return setErrors({ title: "Tiêu đề là bắt buộc" });
        if (!formData.description?.trim())
            return setErrors({ description: "Mô tả là bắt buộc" });
        if (!formData.category) return setErrors({ category: "Loại sự cố là bắt buộc" });
        if (!formData.location?.address?.trim())
            return setErrors({ address: "Địa chỉ là bắt buộc" });
        if (TURNSTILE_SITE_KEY && !turnstileToken)
            return setErrors({ captcha: "Vui lòng hoàn thành xác thực captcha" });

        createMutation.mutate({
            title: formData.title.trim(),
            description: formData.description.trim(),
            category: formData.category,
            severity: formData.severity || "medium",
            location: {
                address: formData.location?.address?.trim(),
                geometry: {
                    type: "Point",
                    coordinates: [
                        formData.location?.coordinates?.longitude || 0,
                        formData.location?.coordinates?.latitude || 0,
                    ],
                },
            },
        });
    };

    if (submitted) {
        return (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-5 text-center">
                <div className="text-3xl mb-2">✅</div>
                <h3 className="font-bold text-slate-900 mb-1">Đã gửi báo cáo</h3>
                <p className="text-sm text-slate-600 mb-3">
                    Cảm ơn bạn đã đóng góp thông tin. Mã tra cứu:
                </p>
                <div className="inline-block bg-white border border-slate-200 rounded-lg px-4 py-2 font-mono text-sm font-semibold text-slate-800 mb-3">
                    {submitted.incident_number || submitted.id.slice(-8).toUpperCase()}
                </div>
                <p className="text-xs text-slate-500">
                    Vui lòng lưu lại mã này để tra cứu trạng thái sau.
                </p>
            </div>
        );
    }

    return (
        <Form onSubmit={handleSubmit}>
            {!hideLookup && (
                <p className="text-sm text-slate-500 mb-3">
                    Ghi nhận nhanh sự cố tại khu vực bạn đang sinh sống để chính quyền xử lý kịp thời.
                </p>
            )}

            <FormField>
                <FormLabel required>Bạn gặp sự cố gì?</FormLabel>
                <Input
                    value={formData.title || ""}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Ví dụ: cây đổ chắn đường, ngập sâu..."
                />
                {errors.title && <FormError>{errors.title}</FormError>}
            </FormField>

            <FormField>
                <FormLabel required>Chi tiết</FormLabel>
                <Textarea
                    value={formData.description || ""}
                    onChange={(e) =>
                        setFormData({ ...formData, description: e.target.value })
                    }
                    placeholder="Mô tả chi tiết về sự cố..."
                    rows={4}
                />
                {errors.description && <FormError>{errors.description}</FormError>}
            </FormField>

            <div className="grid grid-cols-2 gap-3">
                <FormField>
                    <FormLabel required>Loại</FormLabel>
                    <Select
                        value={formData.category || "other"}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                category: e.target.value as IncidentCategory,
                            })
                        }
                    >
                        <option value="malfunction">Không hoạt động</option>
                        <option value="damage">Hư hỏng</option>
                        <option value="safety_hazard">Nguy hiểm</option>
                        <option value="vandalism">Phá hoại</option>
                        <option value="other">Khác</option>
                    </Select>
                </FormField>

                <FormField>
                    <FormLabel required>Mức độ</FormLabel>
                    <Select
                        value={formData.severity || "medium"}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                severity: e.target.value as IncidentSeverity,
                            })
                        }
                    >
                        <option value="low">Thấp</option>
                        <option value="medium">Trung bình</option>
                        <option value="high">Cao</option>
                        <option value="critical">Nguy kịch</option>
                    </Select>
                </FormField>
            </div>

            <FormField>
                <FormLabel required>Địa điểm</FormLabel>
                <Input
                    value={formData.location?.address || ""}
                    onChange={(e) =>
                        setFormData({
                            ...formData,
                            location: {
                                ...formData.location!,
                                address: e.target.value,
                            },
                        })
                    }
                    placeholder="Địa chỉ hoặc mô tả vị trí"
                />
                {errors.address && <FormError>{errors.address}</FormError>}
            </FormField>

            <div className="grid grid-cols-2 gap-3">
                <FormField>
                    <FormLabel>Vĩ độ</FormLabel>
                    <Input
                        type="number"
                        step="any"
                        value={formData.location?.coordinates?.latitude || ""}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                location: {
                                    ...formData.location!,
                                    coordinates: {
                                        ...formData.location!.coordinates!,
                                        latitude: parseFloat(e.target.value) || 0,
                                    },
                                },
                            })
                        }
                        placeholder="16.0471"
                    />
                </FormField>
                <FormField>
                    <FormLabel>Kinh độ</FormLabel>
                    <Input
                        type="number"
                        step="any"
                        value={formData.location?.coordinates?.longitude || ""}
                        onChange={(e) =>
                            setFormData({
                                ...formData,
                                location: {
                                    ...formData.location!,
                                    coordinates: {
                                        ...formData.location!.coordinates!,
                                        longitude: parseFloat(e.target.value) || 0,
                                    },
                                },
                            })
                        }
                        placeholder="108.2062"
                    />
                </FormField>
            </div>

            {errors.submit && <FormError>{errors.submit}</FormError>}

            {TURNSTILE_SITE_KEY && (
                <FormField>
                    <FormLabel required>Xác minh</FormLabel>
                    <Turnstile
                        siteKey={TURNSTILE_SITE_KEY}
                        onVerify={(token) => setTurnstileToken(token)}
                        onExpire={() => setTurnstileToken("")}
                        onError={() =>
                            setErrors({
                                captcha: "Xác thực captcha thất bại. Thử lại.",
                            })
                        }
                        theme="auto"
                    />
                    {errors.captcha && <FormError>{errors.captcha}</FormError>}
                </FormField>
            )}

            <Button
                type="submit"
                disabled={createMutation.isPending}
                className="w-full mt-2"
            >
                {createMutation.isPending ? "Đang gửi..." : "Gửi báo cáo"}
            </Button>
        </Form>
    );
};

export default IncidentReportForm;
