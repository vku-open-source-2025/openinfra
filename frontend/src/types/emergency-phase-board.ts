export type DisasterPhase = 'before' | 'during' | 'after';

export interface SectionStubItem {
  id: string;
  title: string;
  description: string;
  extensionHint: string;
}

export interface PhaseBoardDefinition {
  phase: DisasterPhase;
  routePath: string;
  tabLabel: string;
  title: string;
  subtitle: string;
  teamBoundary: string;
  dataSourceStubs: SectionStubItem[];
  kpiStubs: SectionStubItem[];
  actionQueueStubs: SectionStubItem[];
}
