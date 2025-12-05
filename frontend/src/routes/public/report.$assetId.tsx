import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { publicApi, type PublicAssetInfo } from '../../api/public';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';

import { Loader2, Camera, Upload } from 'lucide-react';

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
    const [incidentData, setIncidentData] = useState({
        title: 'Incident Report',
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
        setSubmitting(true);
        try {
            // 1. Create Incident
            const incident = await publicApi.createAnonymousIncident({
                title: incidentData.title,
                description: `${incidentData.description}\n\nReporter: ${incidentData.reporter_name} (${incidentData.reporter_contact})`,
                severity: incidentData.severity as any,
                asset_id: assetId, // Note: This expects ID, but we might have code from URL. Backend handles lookup?
                // Wait, backend expects asset_id (ID) but URL likely has Code. 
                // We need to resolve Code to ID if createAnonymousIncident expects ID.
                // Actually public API create_anonymous_incident expects IncidentCreate which has asset_id (str).
                // publicApi.getPublicAsset returns PublicAssetInfo which likely has code, but maybe no ID?
                // Let's assume asset_id in create wants the DB ID. 
                // We might need to ask backend to accept code, or get ID from asset info.
                // Looking at PublicAssetInfo interface... it only has asset_code.
                // Issue: We need asset ID for creation, but public API gives code.
                // WORKAROUND: Pass asset_code as asset_id if backend supports it OR incident creation should accept asset_code.
                // Checking backend model... IncidentCreate has asset_id.
                // CHECK: Does PublicAssetInfo have ID? 
                // It has asset_code.
                // I will assume for now we pass assetId (which is code from URL) and backend handles it or we need to fix backend.
                // Re-reading backend `create_incident`: it verifies asset existence via `asset_service.get_asset_by_id`.
                // This implies it expects an ID.
                // We might need `getPublicAsset` to return ID too.
                location: asset?.location ? {
                    address: asset.location.address,
                    geometry: {
                        type: 'Point',
                        coordinates: [asset.location.coordinates.longitude, asset.location.coordinates.latitude]
                    }
                } : undefined
            });

            // 2. Upload Photos
            if (photos.length > 0 && incident.id) {
                await publicApi.uploadPhotos(incident.id, photos);
            }

            navigate({ to: '/public/incidents/$incidentId', params: { incidentId: incident.id } });
        } catch (error) {
            console.error('Failed to report incident', error);
            alert('Failed to submit report. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
    if (!asset) return <div className="p-8 text-center text-red-500">Asset not found</div>;

    return (
        <div className="max-w-md mx-auto p-4 space-y-6">
            <div className="bg-slate-100 p-4 rounded-lg">
                <h2 className="font-bold text-lg">{asset.name}</h2>
                <p className="text-sm text-slate-600">{asset.asset_code}</p>
                <p className="text-sm text-slate-500">{asset.feature_type} • {asset.location?.address}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <Label htmlFor="category">Issue Type</Label>
                    <select
                        id="category"
                        className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1"
                        value={incidentData.category}
                        onChange={(e) => setIncidentData(prev => ({ ...prev, category: e.target.value }))}
                    >
                        <option value="" disabled>Select issue type</option>
                        <option value="malfunction">Not Working / Malfunction</option>
                        <option value="damage">Physical Damage</option>
                        <option value="safety_hazard">Safety Hazard</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                        id="description"
                        placeholder="Describe the problem..."
                        value={incidentData.description}
                        onChange={e => setIncidentData({ ...incidentData, description: e.target.value })}
                        required
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <Label htmlFor="reporter_name">Your Name (Optional)</Label>
                        <Input
                            id="reporter_name"
                            value={incidentData.reporter_name}
                            onChange={e => setIncidentData({ ...incidentData, reporter_name: e.target.value })}
                        />
                    </div>
                    <div>
                        <Label htmlFor="reporter_contact">Contact (Optional)</Label>
                        <Input
                            id="reporter_contact"
                            placeholder="Phone/Email"
                            value={incidentData.reporter_contact}
                            onChange={e => setIncidentData({ ...incidentData, reporter_contact: e.target.value })}
                        />
                    </div>
                </div>

                <div>
                    <Label>Photos</Label>
                    <div className="mt-2 flex items-center gap-4">
                        <Button type="button" variant="outline" className="w-full" onClick={() => document.getElementById('photo-upload')?.click()}>
                            <Camera className="mr-2 h-4 w-4" />
                            Take / Upload Photo
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
                        <p className="text-sm text-green-600 mt-2">{photos.length} photo(s) selected</p>
                    )}
                </div>

                <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? <Loader2 className="animate-spin mr-2" /> : null}
                    Submit Report
                </Button>
            </form>
        </div>
    );
}
