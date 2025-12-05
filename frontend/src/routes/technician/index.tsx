import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import { incidentsApi } from '../../api/incidents';
import { useAuthStore } from '../../stores/authStore';
import { IncidentCard } from '../../components/incidents/IncidentCard';
import { Loader2 } from 'lucide-react';

export const Route = createFileRoute('/technician/')({
    component: TechnicianTaskList,
});

function TechnicianTaskList() {
    const { user } = useAuthStore();
    const navigate = useNavigate();

    // Fetch assigned incidents
    const { data: assignments, isLoading } = useQuery({
        queryKey: ['my-assignments', user?.id],
        queryFn: () => incidentsApi.list({ assigned_to: user?.id, status: 'assigned' }), // Also in_progress?
        // Note: API might need 'in_progress' too. Ideally backend supports list of statuses or client filters.
        // For now assuming we primarily look for new assignments, but ideally we want active.
        enabled: !!user?.id,
    });

    // Fetch in-progress items separately or client filter if list supports multiple stats?
    // Let's assume list supports status filtering, but maybe we want all assigned to me regardless of status first?
    // incidentsApi.list only supports single status string in type definition.
    // We might want to clear status filter to get all for this user.
    const { data: allMyTasks, isLoading: loadingAll } = useQuery({
        queryKey: ['my-tasks-all', user?.id],
        queryFn: async () => {
            // Fetch all for user, then filter client side for relevant ones
            // Or update API to support multiple statuses. For MVP, fetch without status filter and filter client side.
            const tasks = await incidentsApi.list({ assigned_to: user?.id });
            return tasks.filter(t => ['assigned', 'in_progress', 'waiting_approval'].includes(t.status));
        },
        enabled: !!user?.id
    });

    if (loadingAll) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="space-y-4">
            <h2 className="font-bold text-xl mb-4">My Tasks</h2>

            {allMyTasks && allMyTasks.length > 0 ? (
                <div className="space-y-4">
                    {allMyTasks.map(task => (
                        <div key={task.id} onClick={() => navigate({ to: `/technician/tasks/${task.id}` })}>
                            {/* Reusing IncidentCard but logic might be slightly different for tech view */}
                            <IncidentCard incident={task} />
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center p-8 text-slate-500 bg-white rounded-lg border border-slate-200">
                    <p>No active tasks assigned to you.</p>
                </div>
            )}
        </div>
    );
}
