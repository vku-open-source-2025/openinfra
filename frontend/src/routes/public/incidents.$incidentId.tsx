import { createFileRoute } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { publicApi } from '../../api/public';
import type { Incident } from '../../types/incident';
import { Loader2, CheckCircle, Clock, Wrench } from 'lucide-react';
import { Button } from '../../components/ui/button';

export const Route = createFileRoute('/public/incidents/$incidentId')({
    component: IncidentStatusPage,
});

function IncidentStatusPage() {
    const { incidentId } = Route.useParams();
    const [incident, setIncident] = useState<Incident | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchIncident = async () => {
            try {
                const data = await publicApi.getPublicIncident(incidentId);
                setIncident(data);
            } catch (error) {
                console.error('Failed to fetch incident', error);
            } finally {
                setLoading(false);
            }
        };
        fetchIncident();
    }, [incidentId]);

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
    if (!incident) return <div className="p-8 text-center text-red-500">Incident not found</div>;

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'reported': return <Clock className="h-12 w-12 text-blue-500" />;
            case 'resolved': return <CheckCircle className="h-12 w-12 text-green-500" />;
            case 'in_progress':
            case 'investigating': return <Wrench className="h-12 w-12 text-orange-500" />;
            default: return <Clock className="h-12 w-12 text-gray-400" />;
        }
    };

    return (
        <div className="max-w-md mx-auto p-4 space-y-8 text-center">
            <div className="flex flex-col items-center space-y-4">
                {getStatusIcon(incident.status)}
                <div>
                    <h1 className="text-2xl font-bold capitalize">{incident.status.replace('_', ' ')}</h1>
                    <p className="text-slate-500">Ticket #{incident.incident_code || incident.id.substring(0, 8)}</p>
                </div>
            </div>

            <div className="bg-slate-50 p-6 rounded-lg text-left space-y-4">
                <div>
                    <h3 className="text-sm font-semibold text-slate-500 uppercase">Issue</h3>
                    <p className="font-medium">{incident.title}</p>
                </div>
                {incident.location?.address && (
                    <div>
                        <h3 className="text-sm font-semibold text-slate-500 uppercase">Location</h3>
                        <p>{incident.location.address}</p>
                    </div>
                )}
                <div>
                    <h3 className="text-sm font-semibold text-slate-500 uppercase">Reported At</h3>
                    <p>{new Date(incident.created_at).toLocaleString()}</p>
                </div>
                {incident.resolution_notes && (
                    <div className="bg-green-100 p-3 rounded">
                        <h3 className="text-sm font-semibold text-green-800 uppercase">Resolution</h3>
                        <p className="text-green-900">{incident.resolution_notes}</p>
                    </div>
                )}
            </div>

            {incident.photos && incident.photos.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-left font-semibold">Photos</h3>
                    <div className="grid grid-cols-2 gap-2">
                        {incident.photos.map((url, i) => (
                            <img key={i} src={url} alt="Incident" className="rounded-lg object-cover h-32 w-full" />
                        ))}
                    </div>
                </div>
            )}

            <Button variant="outline" onClick={() => window.location.reload()}>Refresh Status</Button>
        </div>
    );
}
