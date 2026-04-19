import React from 'react';

import { emergencyApi } from '@/api/emergency';
import type {
  EmergencyEvent,
  EmergencyEventCreateRequest,
  EmergencySeverity,
  EmergencyStatus,
} from '@/types/emergency';

const defaultDraft: EmergencyEventCreateRequest = {
  title: '',
  description: '',
  event_type: 'flood',
  severity: 'high',
  source: 'manual',
  instructions: [],
  tags: [],
};

const severityClass: Record<EmergencySeverity, string> = {
  low: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  medium: 'bg-amber-100 text-amber-800 border-amber-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  critical: 'bg-rose-100 text-rose-800 border-rose-300',
};

const statusClass: Record<EmergencyStatus, string> = {
  monitoring: 'bg-slate-100 text-slate-700 border-slate-300',
  active: 'bg-red-100 text-red-700 border-red-300',
  contained: 'bg-sky-100 text-sky-700 border-sky-300',
  resolved: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  canceled: 'bg-zinc-100 text-zinc-600 border-zinc-300',
};

function formatDate(value?: string): string {
  if (!value) {
    return '--';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '--';
  }
  return date.toLocaleString('vi-VN');
}

const EmergencyCommandCenter: React.FC = () => {
  const [events, setEvents] = React.useState<EmergencyEvent[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [draft, setDraft] = React.useState<EmergencyEventCreateRequest>(defaultDraft);

  const loadEvents = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await emergencyApi.list({ limit: 100 });
      setEvents(data);
    } catch (err) {
      console.error(err);
      setError('Không thể tải dữ liệu điều hành khẩn cấp.');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const summary = React.useMemo(() => {
    const total = events.length;
    const active = events.filter((event) => event.status === 'active').length;
    const monitoring = events.filter((event) => event.status === 'monitoring').length;
    const resolved = events.filter((event) => event.status === 'resolved').length;
    const critical = events.filter((event) => event.severity === 'critical').length;

    return { total, active, monitoring, resolved, critical };
  }, [events]);

  const handleDraftChange = <K extends keyof EmergencyEventCreateRequest>(
    key: K,
    value: EmergencyEventCreateRequest[K]
  ) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  const handleCreateEvent = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft.title?.trim()) {
      setError('Vui lòng nhập tiêu đề cho sự kiện.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await emergencyApi.create({
        ...draft,
        title: draft.title.trim(),
        description: draft.description?.trim() || undefined,
      });
      setDraft(defaultDraft);
      await loadEvents();
    } catch (err) {
      console.error(err);
      setError('Không thể tạo sự kiện mới.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolveEvent = async (eventId: string) => {
    try {
      await emergencyApi.resolve(eventId, 'Đóng sự kiện từ trung tâm điều hành');
      await loadEvents();
    } catch (err) {
      console.error(err);
      setError('Không thể cập nhật trạng thái sự kiện.');
    }
  };

  return (
    <div className="space-y-6 p-4 md:p-6">
      <header className="rounded-xl bg-gradient-to-r from-red-700 via-orange-600 to-amber-500 p-5 text-white shadow-lg">
        <h1 className="text-2xl font-bold md:text-3xl">Trung tâm điều hành khẩn cấp</h1>
        <p className="mt-2 text-sm md:text-base text-white/90">
          Theo dõi tín hiệu từ SOSCONN, cập nhật trạng thái sự kiện và điều phối xử lý theo thời gian thực.
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 md:grid-cols-5">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Tổng sự kiện</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{summary.total}</p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-red-600">Đang khẩn cấp</p>
          <p className="mt-2 text-2xl font-bold text-red-700">{summary.active}</p>
        </div>
        <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-sky-700">Đang theo dõi</p>
          <p className="mt-2 text-2xl font-bold text-sky-800">{summary.monitoring}</p>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-emerald-700">Đã xử lý</p>
          <p className="mt-2 text-2xl font-bold text-emerald-800">{summary.resolved}</p>
        </div>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-rose-700">Mức nghiêm trọng</p>
          <p className="mt-2 text-2xl font-bold text-rose-800">{summary.critical}</p>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <form
          onSubmit={handleCreateEvent}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4"
        >
          <h2 className="text-lg font-semibold text-slate-900">Tạo sự kiện khẩn cấp</h2>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Tiêu đề</label>
            <input
              value={draft.title}
              onChange={(e) => handleDraftChange('title', e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-200"
              placeholder="Ví dụ: Ngập cục bộ tại quận Hải Châu"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Mô tả</label>
            <textarea
              value={draft.description || ''}
              onChange={(e) => handleDraftChange('description', e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-200"
              placeholder="Mô tả nhanh bối cảnh và hướng xử lý ban đầu"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Loại sự kiện</label>
              <select
                value={draft.event_type}
                onChange={(e) => handleDraftChange('event_type', e.target.value as EmergencyEventCreateRequest['event_type'])}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-200"
              >
                <option value="flood">Ngập lụt</option>
                <option value="storm">Bão</option>
                <option value="landslide">Sạt lở</option>
                <option value="fire">Hỏa hoạn</option>
                <option value="outage">Mất điện/hạ tầng</option>
                <option value="pollution">Ô nhiễm</option>
                <option value="other">Khác</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Mức độ</label>
              <select
                value={draft.severity}
                onChange={(e) => handleDraftChange('severity', e.target.value as EmergencyEventCreateRequest['severity'])}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-200"
              >
                <option value="low">Thấp</option>
                <option value="medium">Trung bình</option>
                <option value="high">Cao</option>
                <option value="critical">Khẩn cấp</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Đang tạo sự kiện...' : 'Tạo sự kiện'}
          </button>
        </form>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Danh sách sự kiện</h2>
            <button
              type="button"
              onClick={() => void loadEvents()}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
            >
              Làm mới
            </button>
          </div>

          {loading ? (
            <div className="space-y-3">
              <div className="h-16 animate-pulse rounded-lg bg-slate-100" />
              <div className="h-16 animate-pulse rounded-lg bg-slate-100" />
              <div className="h-16 animate-pulse rounded-lg bg-slate-100" />
            </div>
          ) : events.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
              Chưa có sự kiện khẩn cấp nào.
            </div>
          ) : (
            <div className="space-y-3">
              {events.map((event) => (
                <article
                  key={event.id}
                  className="rounded-lg border border-slate-200 bg-slate-50/60 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        {event.event_code || 'EMERGENCY'}
                      </p>
                      <h3 className="mt-1 text-base font-semibold text-slate-900">{event.title}</h3>
                    </div>
                    <div className="flex gap-2">
                      <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${severityClass[event.severity]}`}>
                        {event.severity}
                      </span>
                      <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${statusClass[event.status]}`}>
                        {event.status}
                      </span>
                    </div>
                  </div>

                  {event.description ? (
                    <p className="mt-2 text-sm text-slate-700">{event.description}</p>
                  ) : null}

                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                    <span>Loại: {event.event_type}</span>
                    <span>Nguồn: {event.source}</span>
                    <span>Cập nhật: {formatDate(event.updated_at)}</span>
                  </div>

                  {event.status !== 'resolved' && event.status !== 'canceled' ? (
                    <div className="mt-3">
                      <button
                        type="button"
                        onClick={() => void handleResolveEvent(event.id)}
                        className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-100"
                      >
                        Đánh dấu đã xử lý
                      </button>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default EmergencyCommandCenter;
