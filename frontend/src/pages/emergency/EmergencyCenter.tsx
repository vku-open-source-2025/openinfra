import React from 'react';
import { Link } from '@tanstack/react-router';

import { afterActionApi } from '@/api/after-action-reports';
import { dispatchApi } from '@/api/dispatch';
import { emergencyApi, type SosTimelineItem } from '@/api/emergency';
import { eopApi } from '@/api/eop';
import { hazardsApi, type DeployHazardResponse } from '@/api/hazards';
import { resourcesApi } from '@/api/resources';
import { sitrepApi } from '@/api/sitrep';
import { useAuthStore } from '@/stores';
import HazardLiveMap from '@/components/emergency/HazardLiveMap';
import DeployEopModal from '@/components/emergency/DeployEopModal';
import type { AfterActionReport } from '@/types/after-action-report';
import type { DispatchOrder } from '@/types/dispatch';
import type { EmergencyEvent } from '@/types/emergency';
import type { EOPPlan } from '@/types/eop';
import type { Hazard, RecentHazardItem } from '@/types/hazard';
import type { ResourceUnit } from '@/types/resource-unit';
import type { Sitrep } from '@/types/sitrep';
import { parseHazardStreamPayload } from './hazardStream';

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

const EVENT_STATUS_CLASS: Record<string, string> = {
  monitoring: 'bg-slate-100 text-slate-700',
  active: 'bg-red-100 text-red-700',
  contained: 'bg-blue-100 text-blue-700',
  resolved: 'bg-emerald-100 text-emerald-700',
  canceled: 'bg-zinc-100 text-zinc-700',
};

const SEVERITY_CLASS: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const EOP_STATUS_CLASS: Record<string, string> = {
  draft: 'bg-amber-100 text-amber-700',
  review_pending: 'bg-sky-100 text-sky-700',
  approved: 'bg-emerald-100 text-emerald-700',
  published: 'bg-indigo-100 text-indigo-700',
  archived: 'bg-zinc-100 text-zinc-700',
};
const HAZARD_STREAM_PATH = '/api/v1/emergency/stream/hazards';
const HAZARD_POLL_INTERVAL_MS = 30000;

function getHazardStreamUrl(): string {
  const accessToken = useAuthStore.getState().accessToken;

  if (typeof window === 'undefined') {
    return HAZARD_STREAM_PATH;
  }

  const buildUrl = (origin: string) => {
    const url = new URL(HAZARD_STREAM_PATH, origin);
    if (accessToken) {
      url.searchParams.set('access_token', accessToken);
    }
    return url.toString();
  };

  const configuredBaseUrl = import.meta.env.VITE_BASE_API_URL as string | undefined;
  if (!configuredBaseUrl) {
    return buildUrl(window.location.origin);
  }

  try {
    const parsedBaseUrl = new URL(configuredBaseUrl, window.location.origin);
    return buildUrl(parsedBaseUrl.origin);
  } catch {
    return buildUrl(window.location.origin);
  }
}

const EmergencyCenter: React.FC = () => {
  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = React.useState<string>('');
  const [lastHazardRefresh, setLastHazardRefresh] = React.useState<Date | null>(null);

  const [events, setEvents] = React.useState<EmergencyEvent[]>([]);
  const [eopPlans, setEopPlans] = React.useState<EOPPlan[]>([]);
  const [dispatchOrders, setDispatchOrders] = React.useState<DispatchOrder[]>([]);
  const [resources, setResources] = React.useState<ResourceUnit[]>([]);
  const [sitreps, setSitreps] = React.useState<Sitrep[]>([]);
  const [hazards, setHazards] = React.useState<Hazard[]>([]);
  const [recentHazardItems, setRecentHazardItems] = React.useState<RecentHazardItem[]>([]);
  const [sosTimeline, setSosTimeline] = React.useState<SosTimelineItem[]>([]);
  const [afterActionReports, setAfterActionReports] = React.useState<AfterActionReport[]>([]);

  // Deploy modal state
  const [deployModalData, setDeployModalData] = React.useState<DeployHazardResponse | null>(null);
  const [deployingHazardId, setDeployingHazardId] = React.useState<string | null>(null);

  const refreshHazards = React.useCallback(async () => {
    const [hazardData, recentItems] = await Promise.all([
      hazardsApi.list({ limit: 200, is_active: true }),
      hazardsApi.listRecentItems({ hours: 24, limit: 200 }),
    ]);
    setHazards(hazardData);
    setRecentHazardItems(recentItems);
    setLastHazardRefresh(new Date());
  }, []);

  const loadData = React.useCallback(
    async (withLoading = true) => {
      if (withLoading) {
        setLoading(true);
      }
      setError(null);

      try {
        const [eventData, eopData, dispatchData, resourceData, sitrepData, hazardData, aarData, timelineData, recentHazardData] =
          await Promise.all([
            emergencyApi.list({ limit: 80 }),
            eopApi.list({ limit: 80 }),
            dispatchApi.list({ limit: 100 }),
            resourcesApi.list({ limit: 120 }),
            sitrepApi.list({ limit: 80 }),
            hazardsApi.list({ limit: 200, is_active: true }),
            afterActionApi.list({ limit: 60 }),
            emergencyApi.getSosTimeline({ limit: 30 }),
            hazardsApi.listRecentItems({ hours: 24, limit: 200 }),
          ]);

        setEvents(eventData);
        setEopPlans(eopData);
        setDispatchOrders(dispatchData);
        setResources(resourceData);
        setSitreps(sitrepData);
        setHazards(hazardData);
        setAfterActionReports(aarData);
        setSosTimeline(timelineData);
        setRecentHazardItems(recentHazardData);
        setLastHazardRefresh(new Date());

        if (!selectedEventId && eventData.length > 0) {
          const firstActiveEvent = eventData.find((event) => event.status === 'active') || eventData[0];
          setSelectedEventId(firstActiveEvent.id);
        }
      } catch (err) {
        console.error(err);
        setError('Không thể tải dữ liệu trung tâm điều hành.');
      } finally {
        if (withLoading) {
          setLoading(false);
        }
      }
    },
    [selectedEventId]
  );

  React.useEffect(() => {
    void loadData();
  }, [loadData]);

  React.useEffect(() => {
    let pollingIntervalId: number | null = null;
    let hazardStream: EventSource | null = null;

    const stopPolling = () => {
      if (pollingIntervalId !== null) {
        window.clearInterval(pollingIntervalId);
        pollingIntervalId = null;
      }
    };

    const startPolling = () => {
      if (pollingIntervalId !== null) {
        return;
      }

      void refreshHazards().catch((err) => {
        console.error(err);
      });

      pollingIntervalId = window.setInterval(() => {
        void refreshHazards().catch((err) => {
          console.error(err);
        });
      }, HAZARD_POLL_INTERVAL_MS);
    };

    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      startPolling();
      return () => {
        stopPolling();
      };
    }

    try {
      hazardStream = new EventSource(getHazardStreamUrl());
    } catch (err) {
      console.error('Hazard SSE init failed, fallback to polling.', err);
      startPolling();
      return () => {
        stopPolling();
      };
    }

    hazardStream.onopen = () => {
      stopPolling();
    };

    const handleHazardStreamEvent = (event: MessageEvent<string>) => {
      const payload = parseHazardStreamPayload(event.data);
      if (!payload) {
        return;
      }

      setHazards((previousHazards) => {
        if (payload.snapshot !== undefined) {
          return payload.snapshot.filter((hazard) => hazard.is_active);
        }

        if (!payload.delta) {
          return previousHazards;
        }

        const nextHazard = payload.delta;
        const hazardsWithoutCurrent = previousHazards.filter((item) => item.id !== nextHazard.id);

        if (!nextHazard.is_active) {
          return hazardsWithoutCurrent;
        }

        return [nextHazard, ...hazardsWithoutCurrent];
      });
      setLastHazardRefresh(new Date());
    };

    hazardStream.onmessage = handleHazardStreamEvent;

    const namedHazardEventListener: EventListener = (event) => {
      handleHazardStreamEvent(event as MessageEvent<string>);
    };
    hazardStream.addEventListener('hazards', namedHazardEventListener);

    hazardStream.onerror = (event) => {
      console.error('Hazard SSE unavailable, fallback to polling.', event);
      if (hazardStream) {
        hazardStream.close();
        hazardStream = null;
      }
      startPolling();
    };

    return () => {
      if (hazardStream) {
        hazardStream.removeEventListener('hazards', namedHazardEventListener);
        hazardStream.close();
      }
      stopPolling();
    };
  }, [refreshHazards]);

  const selectedEvent = React.useMemo(
    () => events.find((event) => event.id === selectedEventId) || null,
    [events, selectedEventId]
  );

  const summary = React.useMemo(() => {
    const activeEvents = events.filter((event) => event.status === 'active').length;
    const criticalHazards = hazards.filter((hazard) => hazard.severity === 'critical').length;
    const draftEops = eopPlans.filter((plan) => plan.status === 'draft').length;
    const openDispatch = dispatchOrders.filter(
      (order) => !['completed', 'canceled'].includes(order.status)
    ).length;
    const availableResources = resources.filter((resource) => resource.status === 'available').length;
    const publishedAfterAction = afterActionReports.filter((report) => report.status === 'published').length;

    return {
      activeEvents,
      criticalHazards,
      draftEops,
      openDispatch,
      availableResources,
      publishedAfterAction,
    };
  }, [afterActionReports, dispatchOrders, eopPlans, events, hazards, resources]);

  const runAction = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      await action();
    } catch (err) {
      console.error(err);
      setError('Thao tác thất bại. Vui lòng thử lại.');
    } finally {
      setBusy(false);
    }
  };

  const handleDeployHazard = async (hazardId: string) => {
    setDeployingHazardId(hazardId);
    setError(null);
    try {
      const result = await hazardsApi.deploy(hazardId);
      setDeployModalData(result);
      // Refresh recent hazards to reflect linked_event_id
      void hazardsApi.listRecentItems({ hours: 24, limit: 200 }).then(setRecentHazardItems);
    } catch (err) {
      console.error(err);
      setError('Triển khai thất bại. Vui lòng thử lại.');
    } finally {
      setDeployingHazardId(null);
    }
  };

  const handleGenerateEopDraft = async () => {
    if (!selectedEventId) {
      setError('Vui lòng chọn một sự kiện để tạo EOP draft.');
      return;
    }
    await runAction(async () => {
      await eopApi.generateDraft({
        emergency_event_id: selectedEventId,
        force_new_version: true,
      });
      setInfo('Đã tạo EOP draft bằng AI + fallback an toàn.');
      await loadData(false);
    });
  };

  const handleOptimizeDispatch = async () => {
    await runAction(async () => {
      const result = await dispatchApi.optimize({
        max_orders: 250,
        force_reestimate_eta: true,
      });
      setInfo(
        `Optimizer v2: optimized ${result.optimized}, auto_assigned ${result.auto_assigned}, stale ${result.stale_flagged}`
      );
      await loadData(false);
    });
  };

  const handleResolveEvent = async (eventId: string) => {
    await runAction(async () => {
      await emergencyApi.resolve(eventId, 'Resolved from command center board');
      setInfo('Đã resolve sự kiện. AAR sẽ tự động được tạo ở backend nếu chưa có.');
      await loadData(false);
    });
  };

  const handleGenerateAfterAction = async (eventId: string) => {
    await runAction(async () => {
      await afterActionApi.generate({ emergency_event_id: eventId, force_regenerate: true });
      setInfo('Đã tạo mới After-Action report.');
      await loadData(false);
    });
  };

  const handlePublishAfterAction = async (reportId: string) => {
    await runAction(async () => {
      await afterActionApi.publish(reportId);
      setInfo('Đã publish After-Action report.');
      await loadData(false);
    });
  };

  const selectedEventDispatch = React.useMemo(
    () => dispatchOrders.filter((order) => order.emergency_event_id === selectedEventId),
    [dispatchOrders, selectedEventId]
  );

  const selectedEventEops = React.useMemo(
    () => eopPlans.filter((plan) => plan.emergency_event_id === selectedEventId),
    [eopPlans, selectedEventId]
  );

  const resolvedEvents = React.useMemo(
    () => events.filter((event) => ['resolved', 'canceled'].includes(event.status)),
    [events]
  );

  return (
    <div className="space-y-6 p-4 md:p-6">
      <header className="rounded-xl bg-gradient-to-r from-slate-900 via-red-900 to-orange-700 p-5 text-white shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold md:text-3xl">Trung tâm chỉ huy khẩn cấp</h1>
            <p className="mt-2 text-sm text-white/90 md:text-base">
              Bảng điều hành thống nhất cho Event, EOP, Dispatch, Hazard realtime và After-Action KPI.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadData()}
            disabled={busy}
            className="rounded-lg border border-white/40 bg-white/10 px-3 py-1.5 text-sm text-white hover:bg-white/20 disabled:opacity-60"
          >
            Làm mới
          </button>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <Link
            to="/admin/emergency-center/before"
            className="inline-flex rounded-lg border border-white/35 bg-white/10 px-3 py-1.5 text-xs font-medium text-white hover:bg-white/20"
          >
            Bảng trước thiên tai
          </Link>
          <Link
            to="/admin/emergency-center/during"
            className="inline-flex rounded-lg border border-white/35 bg-white/10 px-3 py-1.5 text-xs font-medium text-white hover:bg-white/20"
          >
            Bảng trong thiên tai
          </Link>
          <Link
            to="/admin/emergency-center/after"
            className="inline-flex rounded-lg border border-white/35 bg-white/10 px-3 py-1.5 text-xs font-medium text-white hover:bg-white/20"
          >
            Bảng sau thiên tai
          </Link>
        </div>
      </header>

      {error ? (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}

      {info ? (
        <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {info}
        </div>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <article className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-red-700">Sự kiện đang xử lý</p>
          <p className="mt-2 text-2xl font-bold text-red-800">{summary.activeEvents}</p>
        </article>
        <article className="rounded-lg border border-rose-200 bg-rose-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-rose-700">Nguy hiểm nghiêm trọng</p>
          <p className="mt-2 text-2xl font-bold text-rose-800">{summary.criticalHazards}</p>
        </article>
        <article className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-amber-700">EOP nháp</p>
          <p className="mt-2 text-2xl font-bold text-amber-800">{summary.draftEops}</p>
        </article>
        <article className="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-blue-700">Điều phối đang mở</p>
          <p className="mt-2 text-2xl font-bold text-blue-800">{summary.openDispatch}</p>
        </article>
        <article className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-emerald-700">Nguồn lực sẵn sàng</p>
          <p className="mt-2 text-2xl font-bold text-emerald-800">{summary.availableResources}</p>
        </article>
        <article className="rounded-lg border border-slate-200 bg-slate-50 p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-700">Báo cáo đã xuất bản</p>
          <p className="mt-2 text-2xl font-bold text-slate-800">{summary.publishedAfterAction}</p>
        </article>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Bản đồ nguy hiểm thời gian thực</h2>
              <span className="text-xs text-slate-500">
                Last sync: {lastHazardRefresh ? lastHazardRefresh.toLocaleTimeString('vi-VN') : '--'}
              </span>
            </div>
            <HazardLiveMap hazards={hazards} />
            <div className="mt-3 max-h-44 space-y-2 overflow-auto pr-1 text-sm">
              {recentHazardItems.length === 0 && !loading ? (
                <p className="text-slate-500">Không có hazard 24h gần đây.</p>
              ) : null}
              {recentHazardItems.slice(0, 10).map((hazard) => {
                const isDeployed = !!hazard.linked_event_id;
                const isDeploying = deployingHazardId === hazard.id;
                return (
                  <div key={hazard.id} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900 truncate">{hazard.title}</p>
                      <p className="text-xs text-slate-500">
                        {hazard.event_type} • {hazard.severity} • {hazard.district || 'N/A'}
                      </p>
                    </div>
                    {isDeployed ? (
                      <Link
                        to="/admin/emergency-center/operations/$eventId"
                        params={{ eventId: hazard.linked_event_id! }}
                        className="shrink-0 rounded-md border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100 whitespace-nowrap"
                      >
                        Đã triển khai →
                      </Link>
                    ) : (
                      <button
                        type="button"
                        disabled={busy || isDeploying}
                        onClick={() => void handleDeployHazard(hazard.id)}
                        className="shrink-0 rounded-md border border-red-300 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-100 disabled:opacity-60 whitespace-nowrap"
                      >
                        {isDeploying ? '...' : '🚀 Tạo kế hoạch'}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">Sự kiện khẩn cấp</h2>
              <select
                value={selectedEventId}
                onChange={(event) => setSelectedEventId(event.target.value)}
                className="rounded-md border border-slate-300 px-2 py-1 text-sm"
              >
                <option value="">Chọn sự kiện</option>
                {events.map((event) => (
                  <option key={event.id} value={event.id}>
                    {event.event_code || event.id} - {event.title}
                  </option>
                ))}
              </select>
            </div>

            {loading ? (
              <p className="text-sm text-slate-500">Đang tải sự kiện...</p>
            ) : (
              <div className="space-y-2 text-sm">
                {events.slice(0, 10).map((event) => (
                  <article key={event.id} className="rounded-md border border-slate-200 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-slate-900">{event.title}</p>
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-medium ${EVENT_STATUS_CLASS[event.status] || 'bg-slate-100 text-slate-700'}`}
                      >
                        {event.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {event.event_type} • {event.severity} • cập nhật {formatDate(event.updated_at)}
                    </p>
                    {!['resolved', 'canceled'].includes(event.status) ? (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void handleResolveEvent(event.id)}
                        className="mt-2 rounded-md border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
                      >
                        Đóng sự kiện
                      </button>
                    ) : null}
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">SOS Timeline</h2>
              <span className="text-xs text-slate-500">{sosTimeline.length} sự kiện gần nhất</span>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-xs text-slate-700 md:text-sm">
                <thead className="border-y border-slate-200 bg-slate-50 text-slate-600">
                  <tr>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Sự kiện</th>
                    <th className="min-w-56 px-3 py-2 font-medium">Tiêu đề</th>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Mức độ</th>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Trạng thái</th>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Tạo lúc</th>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Nguồn tham chiếu</th>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Vi phạm SLA</th>
                    <th className="whitespace-nowrap px-3 py-2 font-medium">Cập nhật cuối</th>
                  </tr>
                </thead>
                <tbody>
                  {sosTimeline.map((item) => (
                    <tr key={item.event_id} className="border-b border-slate-100 align-top last:border-b-0">
                      <td className="whitespace-nowrap px-3 py-2 font-medium text-slate-900">
                        {item.event_code || item.event_id.slice(-8)}
                      </td>
                      <td className="px-3 py-2 text-slate-800">{item.title}</td>
                      <td className="whitespace-nowrap px-3 py-2">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            SEVERITY_CLASS[item.severity] || 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {item.severity}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-3 py-2">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            EVENT_STATUS_CLASS[item.status] || 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-3 py-2">{formatDate(item.created_at)}</td>
                      <td className="whitespace-nowrap px-3 py-2">{item.source_ref || '--'}</td>
                      <td className="whitespace-nowrap px-3 py-2 font-semibold text-slate-900">{item.sla_breach_count}</td>
                      <td className="whitespace-nowrap px-3 py-2">{formatDate(item.last_update)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {sosTimeline.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">Chưa có sự kiện SOS nào trong timeline.</p>
            ) : null}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Khu vực cứu hộ hiện tại</h2>
              <button
                type="button"
                onClick={() => void handleGenerateEopDraft()}
                disabled={busy || !selectedEventId}
                className="rounded-md border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 hover:bg-amber-100 disabled:opacity-60"
              >
                Tạo bản nháp AI
              </button>
            </div>

            <div className="max-h-72 space-y-2 overflow-auto pr-1 text-sm">
              {selectedEventEops.slice(0, 8).map((plan) => (
                <Link
                  key={plan.id}
                  to="/admin/emergency-center/operations/$eventId"
                  params={{ eventId: plan.emergency_event_id }}
                  className="block rounded-md border border-slate-200 p-3 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-slate-900">v{plan.version} - {plan.title}</p>
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${EOP_STATUS_CLASS[plan.status] || 'bg-slate-100 text-slate-700'}`}
                    >
                      {plan.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Updated {formatDate(plan.updated_at)} · Bấm để quản lý task →
                  </p>
                </Link>
              ))}
              {selectedEventEops.length === 0 ? <p className="text-slate-500">Chưa có EOP cho sự kiện đã chọn.</p> : null}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Bảng điều phối</h2>
              <button
                type="button"
                onClick={() => void handleOptimizeDispatch()}
                disabled={busy}
                className="rounded-md border border-blue-300 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-60"
              >
                Tối ưu hóa v2
              </button>
            </div>

            <div className="max-h-64 space-y-2 overflow-auto pr-1 text-sm">
              {selectedEventDispatch.slice(0, 10).map((order) => (
                <article key={order.id} className="rounded-md border border-slate-200 p-3">
                  <p className="font-medium text-slate-900">{order.task_title}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {order.status} • {order.priority} • ETA {order.eta_minutes ?? '--'} phút
                  </p>
                </article>
              ))}
              {selectedEventDispatch.length === 0 ? (
                <p className="text-slate-500">Chưa có lệnh điều phối cho sự kiện đã chọn.</p>
              ) : null}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">Báo cáo sau sự kiện</h2>
            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              {resolvedEvents.slice(0, 4).map((event) => (
                <button
                  key={event.id}
                  type="button"
                  disabled={busy}
                  onClick={() => void handleGenerateAfterAction(event.id)}
                  className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-left text-xs text-emerald-700 hover:bg-emerald-100 disabled:opacity-60"
                >
                  Tạo báo cáo: {event.event_code || event.id}
                </button>
              ))}
            </div>

            <div className="max-h-64 space-y-2 overflow-auto pr-1 text-sm">
              {afterActionReports.slice(0, 8).map((report) => (
                <article key={report.id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium text-slate-900">{report.report_code}</p>
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        report.status === 'published'
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {report.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    KPI tổng thể: {report.kpi.overall_score.toFixed(2)} • {formatDate(report.updated_at)}
                  </p>
                  {report.status === 'draft' ? (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void handlePublishAfterAction(report.id)}
                      className="mt-2 rounded-md border border-indigo-300 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-60"
                    >
                      Xuất bản báo cáo
                    </button>
                  ) : null}
                </article>
              ))}
              {afterActionReports.length === 0 ? <p className="text-slate-500">Chưa có báo cáo sau sự kiện.</p> : null}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-2 text-lg font-semibold text-slate-900">Tín hiệu vận hành nhanh</h2>
            <ul className="space-y-2 text-sm text-slate-700">
              <li>Báo cáo đã xuất bản: {sitreps.filter((item) => item.status === 'published').length}</li>
              <li>Nguồn lực đã triển khai: {resources.filter((item) => item.status === 'deployed').length}</li>
              <li>Nguồn lực sẵn sàng: {resources.filter((item) => item.status === 'available').length}</li>
              <li>Sự kiện đã chọn: {selectedEvent ? selectedEvent.title : 'Chưa chọn'}</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Deploy EOP modal */}
      {deployModalData && (
        <DeployEopModal
          deployData={deployModalData}
          onClose={() => setDeployModalData(null)}
          onSubmitted={() => {
            void loadData(false);
          }}
        />
      )}
    </div>
  );
};

export default EmergencyCenter;
