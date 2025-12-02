/**
 * Mock data for Asset Lifecycle Management endpoints
 *
 * This file provides temporary mock implementations for API endpoints
 * that haven't been implemented in the backend yet.
 *
 * TODO: Remove these mocks once backend endpoints are implemented
 */

import type { Asset, AssetLifecycleData } from '../../types/asset';
import type { Maintenance } from '../../types/maintenance';
import type { PreventiveMaintenancePlan, PreventiveMaintenanceTask } from '../../types/preventive-maintenance';
import type { Incident } from '../../types/incident';

// Mock asset with lifecycle data
export const mockAssetWithLifecycle = (id: string): Asset => ({
  id,
  asset_code: `ASSET-${id.slice(-6)}`,
  name: `Sample Asset ${id.slice(-6)}`,
  feature_type: 'Bridge',
  feature_code: `BRG-${id.slice(-6)}`,
  geometry: {
    type: 'Point',
    coordinates: [105.8342, 21.0278],
  },
  category: 'Infrastructure',
  status: 'active',
  location: {
    address: '123 Main Street, Hanoi',
    coordinates: {
      longitude: 105.8342,
      latitude: 21.0278,
    },
  },
  lifecycle: {
    lifecycle_status: 'operational',
    health_score: 87,
    remaining_lifespan_years: 12,
    commissioned_date: '2010-01-15T00:00:00Z',
    designed_lifespan_years: 30,
    last_maintenance_date: '2024-01-15T00:00:00Z',
    next_maintenance_date: '2024-07-15T00:00:00Z',
    maintenance_overdue: false,
  },
  managing_unit: 'Infrastructure Department',
  manufacturer: 'ABC Construction Co.',
  created_at: '2010-01-15T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
});

// Mock health score data
export const mockHealthScore = (assetId: string) => ({
  health_score: 87,
  factors: {
    incident_frequency: 85,
    incident_severity: 90,
    maintenance_recency: 80,
    maintenance_cost_trend: 75,
    iot_sensor_alerts: 95,
  },
});

// Mock maintenance history
export const mockMaintenanceHistory = (assetId: string): Maintenance[] => [
  {
    id: 'maint-1',
    work_order_number: 'WO-2024-001',
    asset_id: assetId,
    title: 'Routine Inspection',
    description: 'Completed routine inspection of all structural components',
    priority: 'medium',
    status: 'completed',
    type: 'preventive',
    scheduled_date: '2024-01-15T00:00:00Z',
    completed_at: '2024-01-15T12:00:00Z',
    technician: 'John Doe',
    estimated_cost: 5000,
    actual_cost: 4800,
    approval_status: 'approved',
    parts_replaced: ['Bearing pad', 'Expansion joint seal'],
    notes: 'All components in good condition',
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-01-15T12:00:00Z',
  },
  {
    id: 'maint-2',
    work_order_number: 'WO-2024-002',
    asset_id: assetId,
    title: 'Paint Touch-up',
    description: 'Touch-up painting on exposed surfaces',
    priority: 'low',
    status: 'completed',
    type: 'preventive',
    scheduled_date: '2023-12-01T00:00:00Z',
    completed_at: '2023-12-01T10:00:00Z',
    technician: 'Jane Smith',
    estimated_cost: 2000,
    actual_cost: 1950,
    approval_status: 'approved',
    parts_replaced: [],
    notes: 'Completed ahead of schedule',
    created_at: '2023-11-25T00:00:00Z',
    updated_at: '2023-12-01T10:00:00Z',
  },
  {
    id: 'maint-3',
    work_order_number: 'WO-2024-003',
    asset_id: assetId,
    title: 'Emergency Repair',
    description: 'Fixed crack in support beam',
    priority: 'high',
    status: 'completed',
    type: 'corrective',
    scheduled_date: '2023-11-10T00:00:00Z',
    completed_at: '2023-11-11T15:00:00Z',
    technician: 'Bob Johnson',
    estimated_cost: 15000,
    actual_cost: 14800,
    approval_status: 'approved',
    parts_replaced: ['Support beam section'],
    notes: 'Crack repaired, structure stable',
    created_at: '2023-11-10T08:00:00Z',
    updated_at: '2023-11-11T15:00:00Z',
  },
  {
    id: 'maint-4',
    work_order_number: 'WO-2024-004',
    asset_id: assetId,
    title: 'Pending Maintenance',
    description: 'Scheduled maintenance awaiting approval',
    priority: 'medium',
    status: 'scheduled',
    type: 'preventive',
    scheduled_date: '2024-07-15T00:00:00Z',
    technician: 'John Doe',
    estimated_cost: 6000,
    approval_status: 'pending',
    created_at: '2024-01-20T00:00:00Z',
    updated_at: '2024-01-20T00:00:00Z',
  },
];

// Mock preventive maintenance plan
export const mockPreventiveMaintenancePlan = (assetId: string): PreventiveMaintenancePlan => ({
  id: 'plan-1',
  asset_id: assetId,
  cycle_days: 180,
  cycle_description: 'Every 6 months',
  last_maintenance_date: '2024-01-15T00:00:00Z',
  next_maintenance_date: '2024-07-15T00:00:00Z',
  warning_days: 7,
  responsible_team: 'Maintenance Team A',
  assigned_technician: 'John Doe',
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
});

// Mock preventive maintenance tasks
export const mockUpcomingTasks = (assetId: string): PreventiveMaintenanceTask[] => [
  {
    id: 'task-1',
    asset_id: assetId,
    plan_id: 'plan-1',
    scheduled_date: '2024-07-15T00:00:00Z',
    status: 'upcoming',
  },
  {
    id: 'task-2',
    asset_id: assetId,
    plan_id: 'plan-1',
    scheduled_date: '2025-01-15T00:00:00Z',
    status: 'upcoming',
  },
];

export const mockOverdueTasks = (assetId: string): PreventiveMaintenanceTask[] => [
  {
    id: 'task-overdue-1',
    asset_id: assetId,
    plan_id: 'plan-1',
    scheduled_date: '2024-01-01T00:00:00Z',
    status: 'overdue',
  },
];

// Mock incidents
export const mockIncidents = (assetId: string): Incident[] => [
  {
    id: 'incident-1',
    incident_code: 'INC-2024-001',
    title: 'Crack in Support Beam',
    description: 'Discovered a crack in the main support beam during inspection',
    severity: 'high',
    status: 'resolved',
    asset_id: assetId,
    location: {
      address: '123 Main Street, Hanoi',
      coordinates: {
        longitude: 105.8342,
        latitude: 21.0278,
      },
    },
    reporter_type: 'technician',
    upvotes: 3,
    comments: [
      {
        id: 'comment-1',
        comment: 'Inspected and confirmed crack location',
        user_name: 'John Doe',
        is_internal: true,
        created_at: '2024-01-10T10:00:00Z',
      },
    ],
    created_at: '2024-01-10T08:00:00Z',
    updated_at: '2024-01-11T15:00:00Z',
  },
  {
    id: 'incident-2',
    incident_code: 'INC-2024-002',
    title: 'Loose Guardrail',
    description: 'Citizen reported loose guardrail on north side',
    severity: 'medium',
    status: 'in_progress',
    asset_id: assetId,
    location: {
      address: '123 Main Street, Hanoi',
      coordinates: {
        longitude: 105.8342,
        latitude: 21.0278,
      },
    },
    reporter_type: 'citizen',
    assigned_to: 'Jane Smith',
    upvotes: 1,
    comments: [],
    created_at: '2024-01-20T14:00:00Z',
    updated_at: '2024-01-20T14:00:00Z',
  },
];

// Mock documents
export const mockDocuments = (assetId: string) => [
  {
    file_name: 'inspection-report-2024.pdf',
    file_url: 'https://example.com/documents/inspection-report-2024.pdf',
    file_type: 'application/pdf',
    uploaded_by: 'John Doe',
    uploaded_at: '2024-01-15T10:00:00Z',
    version: 1,
    is_public: false,
    document_type: 'Inspection Report',
  },
  {
    file_name: 'asset-photo.jpg',
    file_url: 'https://example.com/documents/asset-photo.jpg',
    file_type: 'image/jpeg',
    uploaded_by: 'Jane Smith',
    uploaded_at: '2024-01-10T09:00:00Z',
    version: 1,
    is_public: true,
    document_type: 'Photo',
  },
];

// Helper function to simulate API delay
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
