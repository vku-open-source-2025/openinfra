import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { publicApi, type PublicAssetInfo } from '../../api/public';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import { Turnstile } from '../../components/Turnstile';

import { Loader2, Camera, Upload } from 'lucide-react';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || "";

export const Route = createFileRoute('/public/report/$assetId')({
    component: ReportIncidentPage,
});

function ReportIncidentPage() {
    const { assetId } = Route.useParams();
    const navigate = useNavigate();
    const [asset, setAsset] = useState<PublicAssetInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [photos, setPhotos] = useState<File[]>([]);
    const [turnstileToken, setTurnstileToken] = useState<string>("");
    const [captchaError, setCaptchaError] = useState<string>("");
    const [incidentData, setIncidentData] = useState({
        title: 'Báo cáo sự cố',
        description: '',
        severity: 'medium',
        category: 'malfunction',
        reporter_name: '',
        reporter_contact: ''
    });

    useEffect(() => {
        const fetchAsset = async () => {
            try {
                const data = await publicApi.getPublicAsset(assetId);
                setAsset(data);
            } catch (error) {
                console.error('Failed to fetch asset', error);
            } finally {
                setLoading(false);
            }
        };
        fetchAsset();
    }, [assetId]);

    const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setPhotos(Array.from(e.target.files));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setCaptchaError("");
        
        // Validate captcha
        if (TURNSTILE_SITE_KEY && !turnstileToken) {
            setCaptchaError("Vui lòng hoàn thành xác minh captcha");
            return;
        }
        
        setSubmitting(true);
        try {
            // 1. Create Incident
            const incident = await publicApi.createAnonymousIncident({
                title: incidentData.title,
                description: `${incidentData.description}\n\nReporter: ${incidentData.reporter_name} (${incidentData.reporter_contact})`,
                severity: incidentData.severity as any,
                asset_id: assetId,
                location: asset?.location ? {
                    address: asset.location.address,
                    geometry: {
                        type: 'Point',
                        coordinates: [asset.location.coordinates.longitude, asset.location.coordinates.latitude]
                    }
                } : undefined
            }, turnstileToken);

            // 2. Upload Photos
            if (photos.length > 0 && incident.id) {
                await publicApi.uploadPhotos(incident.id, photos);
            }

            navigate({ to: '/public/incidents/$incidentId', params: { incidentId: incident.id } });
        } catch (error) {
            console.error('Failed to report incident', error);
            alert('Gửi báo cáo thất bại. Vui lòng thử lại.');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
    if (!asset) return <div className="p-8 text-center text-red-500">Không tìm thấy tài sản</div>;

    return (
        <div className="max-w-md mx-auto p-4 space-y-6">
            <div className="bg-slate-100 p-4 rounded-lg">
                <h2 className="font-bold text-lg">{asset.name}</h2>
                <p className="text-sm text-slate-600">{asset.asset_code}</p>
                <p className="text-sm text-slate-500">{asset.feature_type} • {asset.location?.address}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <Label htmlFor="category">Loại sự cố</Label>
                    <select
                        id="category"
                        className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1"
                        value={incidentData.category}
                        onChange={(e) => setIncidentData(prev => ({ ...prev, category: e.target.value }))}
                    >
                        <option value="" disabled>Chọn loại sự cố</option>
                        <option value="malfunction">Không hoạt động / Hỏng</option>
                        <option value="damage">Hư hỏng vật lý</option>
                        <option value="safety_hazard">Nguy hiểm an toàn</option>
                        <option value="other">Khác</option>
                    </select>
                </div>

                <div>
                    <Label htmlFor="description">Mô tả</Label>
                    <Textarea
                        id="description"
                        placeholder="Mô tả vấn đề..."
                        value={incidentData.description}
                        onChange={e => setIncidentData({ ...incidentData, description: e.target.value })}
                        required
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <Label htmlFor="reporter_name">Tên bạn (Tùy chọn)</Label>
                        <Input
                            id="reporter_name"
                            value={incidentData.reporter_name}
                            onChange={e => setIncidentData({ ...incidentData, reporter_name: e.target.value })}
                        />
                    </div>
                    <div>
                        <Label htmlFor="reporter_contact">Liên hệ (Tùy chọn)</Label>
                        <Input
                            id="reporter_contact"
                            placeholder="Số điện thoại / Email"
                            value={incidentData.reporter_contact}
                            onChange={e => setIncidentData({ ...incidentData, reporter_contact: e.target.value })}
                        />
                    </div>
                </div>

                <div>
                    <Label>Ảnh</Label>
                    <div className="mt-2 flex items-center gap-4">
                        <Button type="button" variant="outline" className="w-full" onClick={() => document.getElementById('photo-upload')?.click()}>
                            <Camera className="mr-2 h-4 w-4" />
                            Chụp / Tải ảnh lên
                        </Button>
                        <input
                            id="photo-upload"
                            type="file"
                            accept="image/*"
                            multiple
                            className="hidden"
                            onChange={handlePhotoChange}
                        />
                    </div>
                    {photos.length > 0 && (
                        <p className="text-sm text-green-600 mt-2">Đã chọn {photos.length} ảnh</p>
                    )}
                </div>

                {/* Cloudflare Turnstile Captcha */}
                {TURNSTILE_SITE_KEY && (
                    <div>
                        <Label>Xác minh bạn là con người</Label>
                        <Turnstile
                            siteKey={TURNSTILE_SITE_KEY}
                            onVerify={(token) => setTurnstileToken(token)}
                            onExpire={() => setTurnstileToken("")}
                            onError={() => setCaptchaError("Xác minh captcha thất bại. Vui lòng thử lại.")}
                            theme="auto"
                            className="mt-2"
                        />
                        {captchaError && (
                            <p className="text-sm text-red-500 mt-1">{captchaError}</p>
                        )}
                    </div>
                )}

                    <Button type="submit" className="w-full" disabled={submitting || (TURNSTILE_SITE_KEY ? !turnstileToken : false)}>
                    {submitting ? <Loader2 className="animate-spin mr-2" /> : null}
                    Gửi báo cáo
                </Button>
            </form>
        </div>
    );
}
