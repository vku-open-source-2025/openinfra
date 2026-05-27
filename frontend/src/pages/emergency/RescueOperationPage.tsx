import React, { useState, useCallback } from 'react';
import { useParams, Link } from '@tanstack/react-router';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Loader2, Check, X, Pencil, User } from 'lucide-react';

import { emergencyApi } from '@/api/emergency';
import { eopApi } from '@/api/eop';
import { dispatchApi } from '@/api/dispatch';
import { usersApi } from '@/api/users';
import DeployEopModal from '@/components/emergency/DeployEopModal';
import type { DispatchOrder } from '@/types/dispatch';
import type { DeployHazardResponse } from '@/api/hazards';

// ── Badge helpers ─────────────────────────────────────────────────────────────

const SEVERITY_CLASS: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const STATUS_CLASS: Record<string, string> = {
  pending: 'bg-slate-100 text-slate-700',
  assigned: 'bg-blue-100 text-blue-700',
  in_transit: 'bg-sky-100 text-sky-700',
  on_scene: 'bg-indigo-100 text-indigo-700',
  completed: 'bg-emerald-100 text-emerald-700',
  canceled: 'bg-zinc-100 text-zinc-700',
  reassigned: 'bg-amber-100 text-amber-700',
};

const STATUS_LABEL: Record<string, string> = {
  pending: 'Chờ duyệt',
  assigned: 'Đã phân công',
  in_transit: 'Đang di chuyển',
  on_scene: 'Tại hiện trường',
  completed: 'Hoàn thành',
  canceled: 'Đã từ chối',
  reassigned: 'Phân công lại',
};

// ── Task row ──────────────────────────────────────────────────────────────────

interface TaskRowProps {
  order: DispatchOrder;
  volunteers: { id: string; full_name: string; username: string }[];
  onApprove: (orderId: string, userId: string) => Promise<void>;
  onReject: (orderId: string) => Promise<void>;
}

const TaskRow: React.FC<TaskRowProps> = ({ order, volunteers, onApprove, onReject }) => {
  const [selectedUserId, setSelectedUserId] = useState<string>(
    order.assigned_user_id ??
      order.assignments.find((a) => a.assigned_user_id)?.assigned_user_id ??
      '',
  );
  const [busy, setBusy] = useState(false);

  const isDone = ['completed', 'canceled', 'assigned'].includes(order.status);

  return (
    <article
      className={`rounded-lg border p-4 ${
        isDone ? 'border-slate-200 bg-slate-50 opacity-80' : 'border-slate-200 bg-white shadow-sm'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-900 text-sm">{order.task_title}</p>
          {order.task_description && (
            <p className="text-xs text-slate-600 mt-0.5">{order.task_description}</p>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_CLASS[order.priority] ?? 'bg-slate-100 text-slate-700'}`}>
            {order.priority}
          </span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASS[order.status] ?? 'bg-slate-100 text-slate-700'}`}>
            {STATUS_LABEL[order.status] ?? order.status}
          </span>
        </div>
      </div>

      {!isDone && (
        <div className="flex items-center gap-2 mt-3">
          <User size={13} className="text-slate-400 shrink-0" />
          <select
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            disabled={busy}
            className="flex-1 text-xs rounded-md border border-slate-300 px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-60"
          >
            <option value="">Chọn tình nguyện viên...</option>
            {volunteers.map((v) => (
              <option key={v.id} value={v.id}>
                {v.full_name} (@{v.username})
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={busy || !selectedUserId}
            onClick={async () => {
              setBusy(true);
              try { await onApprove(order.id, selectedUserId); } finally { setBusy(false); }
            }}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60 transition-colors"
          >
            {busy ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
            Duyệt
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try { await onReject(order.id); } finally { setBusy(false); }
            }}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-red-50 border border-red-300 text-red-700 hover:bg-red-100 disabled:opacity-60 transition-colors"
          >
            {busy ? <Loader2 size={12} className="animate-spin" /> : <X size={12} />}
            Từ chối
          </button>
        </div>
      )}

      {order.status === 'assigned' && (
        <div className="mt-2 text-xs text-blue-700 font-medium">
          ✔ Đã phân công →{' '}
          {volunteers.find(
            (v) =>
              v.id === (order.assigned_user_id ?? order.assignments.find((a) => a.assigned_user_id)?.assigned_user_id),
          )?.full_name ?? 'Tình nguyện viên'}
        </div>
      )}
    </article>
  );
};

// ── Page ──────────────────────────────────────────────────────────────────────

const RescueOperationPage: React.FC = () => {
  const { eventId } = useParams({ from: '/admin/emergency-center/operations/$eventId' });
  const qc = useQueryClient();

  const [editEopModal, setEditEopModal] = useState<DeployHazardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const { data: event, isLoading: eventLoading } = useQuery({
    queryKey: ['emergency', 'event', eventId],
    queryFn: () => emergencyApi.getById(eventId),
    staleTime: 60_000,
  });

  const { data: eopPlans = [], isLoading: eopLoading } = useQuery({
    queryKey: ['eop', 'event', eventId],
    queryFn: () => eopApi.list({ emergency_event_id: eventId, limit: 10 }),
    staleTime: 30_000,
  });

  const { data: orders = [], isLoading: ordersLoading } = useQuery({
    queryKey: ['dispatch', 'event', eventId],
    queryFn: () => dispatchApi.list({ emergency_event_id: eventId, limit: 200 }),
    staleTime: 30_000,
    refetchInterval: 30_000,
  });

  const { data: volunteers = [] } = useQuery({
    queryKey: ['users', 'volunteers'],
    queryFn: () => usersApi.listVolunteers('active'),
    staleTime: 5 * 60_000,
  });

  const invalidate = useCallback(() => {
    void qc.invalidateQueries({ queryKey: ['dispatch', 'event', eventId] });
  }, [qc, eventId]);

  const handleApprove = useCallback(
    async (orderId: string, userId: string) => {
      setError(null);
      try {
        await dispatchApi.approve(orderId, userId);
        setInfo('Đã duyệt và phân công task.');
        invalidate();
      } catch (err) {
        console.error(err);
        setError('Không thể duyệt task. Vui lòng thử lại.');
      }
    },
    [invalidate],
  );

  const handleReject = useCallback(
    async (orderId: string) => {
      setError(null);
      try {
        await dispatchApi.reject(orderId);
        setInfo('Đã từ chối task.');
        invalidate();
      } catch (err) {
        console.error(err);
        setError('Không thể từ chối task. Vui lòng thử lại.');
      }
    },
    [invalidate],
  );

  const latestEop = eopPlans[0] ?? null;

  const pendingOrders = orders.filter((o) => o.status === 'pending');
  const activeOrders = orders.filter((o) =>
    ['assigned', 'in_transit', 'on_scene'].includes(o.status),
  );
  const doneOrders = orders.filter((o) => ['completed', 'canceled'].includes(o.status));

  const isLoading = eventLoading || eopLoading || ordersLoading;

  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* Header */}
      <header className="flex items-center gap-4">
        <Link
          to="/admin/emergency-center"
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft size={16} />
          Trở về Command Center
        </Link>
      </header>

      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 size={32} className="animate-spin text-slate-400" />
        </div>
      ) : (
        <>
          {/* Event info banner */}
          {event && (
            <div className="rounded-xl bg-gradient-to-r from-slate-900 via-red-900 to-orange-700 p-5 text-white shadow-lg">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${SEVERITY_CLASS[event.severity] ?? 'bg-slate-100 text-slate-700'}`}>
                      {event.severity}
                    </span>
                    <span className="text-xs text-white/70">{event.event_type}</span>
                  </div>
                  <h1 className="text-xl font-bold md:text-2xl">{event.title}</h1>
                  {event.location?.district && (
                    <p className="text-sm text-white/80 mt-1">
                      📍 {[event.location.address, event.location.ward, event.location.district, event.location.city]
                        .filter(Boolean)
                        .join(', ')}
                    </p>
                  )}
                </div>
                <div className="text-right text-sm text-white/70">
                  <p>
                    {orders.length} task · {pendingOrders.length} chờ · {activeOrders.length} đang thực hiện
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
          )}
          {info && (
            <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{info}</div>
          )}

          <div className="grid gap-6 xl:grid-cols-[1fr_1.5fr]">
            {/* Left: EOP markdown */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-slate-900">Kế hoạch ứng phó (EOP)</h2>
                {latestEop && (
                  <button
                    type="button"
                    onClick={() =>
                      setEditEopModal({
                        hazard_id: '',
                        event_id: eventId,
                        eop_plan_id: latestEop.id,
                        markdown_body: latestEop.markdown_body ?? '',
                      })
                    }
                    className="flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors"
                  >
                    <Pencil size={12} />
                    Sửa
                  </button>
                )}
              </div>

              {latestEop ? (
                <>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs font-medium text-slate-600">v{latestEop.version}</span>
                    <span className="text-xs text-slate-400">·</span>
                    <span className="text-xs text-slate-600">{latestEop.title}</span>
                  </div>
                  {latestEop.markdown_body ? (
                    <pre className="whitespace-pre-wrap text-xs text-slate-700 font-mono leading-relaxed bg-slate-50 rounded-lg p-4 overflow-auto max-h-[60vh]">
                      {latestEop.markdown_body}
                    </pre>
                  ) : (
                    <p className="text-sm text-slate-500 italic">
                      Chưa có nội dung markdown. Nhấn <strong>Sửa</strong> để thêm nội dung.
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-slate-500">Chưa có EOP plan cho sự kiện này.</p>
              )}
            </div>

            {/* Right: Task list */}
            <div className="space-y-5">
              {/* Pending tasks */}
              <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-base font-semibold text-slate-900 mb-3">
                  ⏳ Chờ duyệt ({pendingOrders.length})
                </h3>
                {pendingOrders.length === 0 ? (
                  <p className="text-sm text-slate-500">Không có task nào đang chờ duyệt.</p>
                ) : (
                  <div className="space-y-3">
                    {pendingOrders.map((order) => (
                      <TaskRow
                        key={order.id}
                        order={order}
                        volunteers={volunteers}
                        onApprove={handleApprove}
                        onReject={handleReject}
                      />
                    ))}
                  </div>
                )}
              </section>

              {/* Active tasks */}
              {activeOrders.length > 0 && (
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-900 mb-3">
                    🚀 Đang triển khai ({activeOrders.length})
                  </h3>
                  <div className="space-y-3">
                    {activeOrders.map((order) => (
                      <TaskRow
                        key={order.id}
                        order={order}
                        volunteers={volunteers}
                        onApprove={handleApprove}
                        onReject={handleReject}
                      />
                    ))}
                  </div>
                </section>
              )}

              {/* Done tasks */}
              {doneOrders.length > 0 && (
                <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-700 mb-3">
                    ✅ Đã xong / Từ chối ({doneOrders.length})
                  </h3>
                  <div className="space-y-3">
                    {doneOrders.map((order) => (
                      <TaskRow
                        key={order.id}
                        order={order}
                        volunteers={volunteers}
                        onApprove={handleApprove}
                        onReject={handleReject}
                      />
                    ))}
                  </div>
                </section>
              )}

              {orders.length === 0 && (
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-slate-400">
                  <p className="text-sm">Chưa có task nào được tạo.</p>
                  <p className="text-xs mt-1">
                    Submit EOP để AI sinh task tự động.
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Edit EOP modal */}
      {editEopModal && (
        <DeployEopModal
          deployData={editEopModal}
          onClose={() => setEditEopModal(null)}
          onSubmitted={() => {
            void qc.invalidateQueries({ queryKey: ['eop', 'event', eventId] });
            void qc.invalidateQueries({ queryKey: ['dispatch', 'event', eventId] });
          }}
        />
      )}
    </div>
  );
};

export default RescueOperationPage;
