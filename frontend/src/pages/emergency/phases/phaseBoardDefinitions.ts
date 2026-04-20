import type { DisasterPhase, PhaseBoardDefinition } from '@/types/emergency-phase-board';

export const phaseBoardDefinitions: Record<DisasterPhase, PhaseBoardDefinition> = {
  before: {
    phase: 'before',
    routePath: '/admin/emergency-center/before',
    tabLabel: 'Before',
    title: 'Before Disaster Board',
    subtitle: 'Preparedness, prevention, and risk reduction before disruption starts.',
    teamBoundary: 'Preparedness team owns this board and can add preventive workflows independently.',
    dataSourceStubs: [
      {
        id: 'seasonal-forecast-feed',
        title: 'Seasonal Forecast Feed',
        description: 'Ingest forecast windows and weather anomaly alerts for pre-event readiness.',
        extensionHint: 'Connector hook: add parser + polling in a dedicated preparedness data module.',
      },
      {
        id: 'asset-vulnerability-index',
        title: 'Asset Vulnerability Index',
        description: 'Track infrastructure risk scores by district and criticality tiers.',
        extensionHint: 'Extension point: map new scoring algorithm versions without touching other phases.',
      },
      {
        id: 'maintenance-readiness-backlog',
        title: 'Maintenance Readiness Backlog',
        description: 'Monitor pending preventive maintenance items for critical assets.',
        extensionHint: 'Data contract: keep backlog item shape local to before-phase services.',
      },
    ],
    kpiStubs: [
      {
        id: 'kpi-risk-coverage',
        title: 'Risk Coverage Ratio',
        description: 'Percent of high-risk assets with active mitigation plans.',
        extensionHint: 'KPI owner: preparedness analytics team.',
      },
      {
        id: 'kpi-drill-completion',
        title: 'Drill Completion Rate',
        description: 'Training and simulation completion for command + field units.',
        extensionHint: 'Add drill data source adapters without coupling to response board.',
      },
      {
        id: 'kpi-inspection-sla',
        title: 'Critical Inspection SLA',
        description: 'SLA adherence for mandatory pre-disaster inspections.',
        extensionHint: 'Add SLA thresholds per district via before-phase config only.',
      },
    ],
    actionQueueStubs: [
      {
        id: 'queue-preposition-resources',
        title: 'Pre-position Resource Orders',
        description: 'Queue strategic resource positioning before severe weather windows.',
        extensionHint: 'Workflow can be implemented by preparedness team without dispatch runtime changes.',
      },
      {
        id: 'queue-drill-followups',
        title: 'Drill Follow-up Tasks',
        description: 'Assign corrective actions from simulation exercises.',
        extensionHint: 'Action schema can evolve in before-phase repository only.',
      },
      {
        id: 'queue-communication-checks',
        title: 'Communication Readiness Checks',
        description: 'Validate alert channels and fallback communication trees.',
        extensionHint: 'Integrate channel health checks independently from during/after queues.',
      },
    ],
  },
  during: {
    phase: 'during',
    routePath: '/admin/emergency-center/during',
    tabLabel: 'During',
    title: 'During Disaster Board',
    subtitle: 'Live response orchestration, hazard tracking, and execution coordination.',
    teamBoundary: 'Response operations team owns this board and can ship live-ops enhancements independently.',
    dataSourceStubs: [
      {
        id: 'live-hazard-stream',
        title: 'Live Hazard Stream',
        description: 'Consume SSE/WebSocket hazard updates and deduplicate active alerts.',
        extensionHint: 'Realtime ingestion hook isolated for response team iteration speed.',
      },
      {
        id: 'sos-incident-timeline',
        title: 'SOS Incident Timeline',
        description: 'Merge SOS intake and incident lifecycle events into one chronological stream.',
        extensionHint: 'Timeline enrichers can be added without changing before/after data models.',
      },
      {
        id: 'resource-telemetry',
        title: 'Resource Telemetry',
        description: 'Track unit status, location heartbeat, and dispatch acknowledgments.',
        extensionHint: 'Telemetry adapters remain contained in during-phase modules.',
      },
    ],
    kpiStubs: [
      {
        id: 'kpi-response-sla',
        title: 'Response SLA Breach Rate',
        description: 'Share of active incidents crossing escalation thresholds.',
        extensionHint: 'KPI formula tuning can ship by response analytics team only.',
      },
      {
        id: 'kpi-critical-active-hazards',
        title: 'Active Critical Hazards',
        description: 'Count and trend of unresolved critical hazards in realtime.',
        extensionHint: 'Use board-local cache strategy for high-frequency updates.',
      },
      {
        id: 'kpi-resource-utilization',
        title: 'Resource Utilization',
        description: 'Percent of units currently deployed versus available capacity.',
        extensionHint: 'Capacity model versioning is isolated to this board.',
      },
    ],
    actionQueueStubs: [
      {
        id: 'queue-triage',
        title: 'Triage Queue',
        description: 'Prioritize incoming incidents by severity, confidence, and impact radius.',
        extensionHint: 'Triage policy engine can evolve without touching preparedness/postmortem code.',
      },
      {
        id: 'queue-dispatch-reroute',
        title: 'Dispatch and Reroute',
        description: 'Queue route changes and fallback dispatch plans under field constraints.',
        extensionHint: 'Dispatch optimization experiments remain local to during-phase team.',
      },
      {
        id: 'queue-public-alerts',
        title: 'Public Alert Pushes',
        description: 'Issue coordinated public advisories with audit trail.',
        extensionHint: 'Channel-specific plugins can be added independently.',
      },
    ],
  },
  after: {
    phase: 'after',
    routePath: '/admin/emergency-center/after',
    tabLabel: 'After',
    title: 'After Disaster Board',
    subtitle: 'Recovery execution, learning loops, and long-tail closure management.',
    teamBoundary: 'Recovery and governance team owns this board and can iterate post-incident workflows independently.',
    dataSourceStubs: [
      {
        id: 'after-action-reports',
        title: 'After-Action Report Feed',
        description: 'Consolidate AI-assisted and manual after-action reports per event.',
        extensionHint: 'Recovery team can expand narrative schema without response board coupling.',
      },
      {
        id: 'damage-assessment-surveys',
        title: 'Damage Assessment Surveys',
        description: 'Collect field assessments for infrastructure, utilities, and social impact.',
        extensionHint: 'Survey collectors remain encapsulated in after-phase domain.',
      },
      {
        id: 'recovery-budget-claims',
        title: 'Recovery Budget Claims',
        description: 'Track recovery funding requests and disbursement status.',
        extensionHint: 'Finance-specific enrichment can be added by recovery squad only.',
      },
    ],
    kpiStubs: [
      {
        id: 'kpi-restoration-time',
        title: 'Mean Restoration Time',
        description: 'Average duration from incident resolution to service normalization.',
        extensionHint: 'KPI windows can be versioned independently per recovery policy.',
      },
      {
        id: 'kpi-recovery-budget-burn',
        title: 'Recovery Budget Burn',
        description: 'Budget consumed versus approved recovery envelope.',
        extensionHint: 'Finance formulas and audit fields remain after-phase local.',
      },
      {
        id: 'kpi-capa-closure',
        title: 'CAPA Closure Rate',
        description: 'Closure progress for corrective and preventive actions from postmortems.',
        extensionHint: 'CAPA taxonomy changes do not impact live incident handling.',
      },
    ],
    actionQueueStubs: [
      {
        id: 'queue-postmortem',
        title: 'Postmortem Workflow',
        description: 'Track owner assignments and due dates for post-incident reviews.',
        extensionHint: 'Recovery team can add board-specific templates and checklists.',
      },
      {
        id: 'queue-restoration-milestones',
        title: 'Restoration Milestones',
        description: 'Monitor utility restoration milestones with district-level targets.',
        extensionHint: 'Milestone scoring rules are isolated to after-phase code.',
      },
      {
        id: 'queue-policy-updates',
        title: 'Policy and SOP Updates',
        description: 'Queue required SOP updates and training tasks after findings are confirmed.',
        extensionHint: 'Governance automation can be built independently of response tooling.',
      },
    ],
  },
};

export const orderedPhaseBoards: PhaseBoardDefinition[] = [
  phaseBoardDefinitions.before,
  phaseBoardDefinitions.during,
  phaseBoardDefinitions.after,
];
