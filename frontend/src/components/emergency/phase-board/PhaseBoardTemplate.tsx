import React from 'react';
import { Link } from '@tanstack/react-router';

import { orderedPhaseBoards } from '@/pages/emergency/phases/phaseBoardDefinitions';
import type { PhaseBoardDefinition } from '@/types/emergency-phase-board';

import SectionStubPanel from './SectionStubPanel';

interface PhaseBoardTemplateProps {
  board: PhaseBoardDefinition;
}

const PhaseBoardTemplate: React.FC<PhaseBoardTemplateProps> = ({ board }) => {
  return (
    <div className="space-y-6 p-4 md:p-6">
      <header className="rounded-xl bg-gradient-to-r from-slate-900 via-slate-700 to-slate-600 p-5 text-white shadow-lg">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold md:text-3xl">{board.title}</h1>
            <p className="mt-2 text-sm text-white/90 md:text-base">{board.subtitle}</p>
          </div>
          <span className="rounded-md border border-white/40 bg-white/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide">
            Team Boundary
          </span>
        </div>
        <p className="mt-3 text-sm text-white/90">{board.teamBoundary}</p>
      </header>

      <nav className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <Link
            to="/admin/emergency-center"
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Board landing
          </Link>
          {orderedPhaseBoards.map((phaseBoard) => (
            <Link
              key={phaseBoard.phase}
              to={phaseBoard.routePath}
              className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
              activeProps={{
                className:
                  'rounded-md border border-blue-300 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700',
              }}
              activeOptions={{ exact: true }}
            >
              {phaseBoard.tabLabel}
            </Link>
          ))}
        </div>
      </nav>

      <section className="grid gap-6 xl:grid-cols-3">
        <SectionStubPanel
          title="Data Sources"
          description="Board-local integration stubs owned by the phase team."
          items={board.dataSourceStubs}
        />
        <SectionStubPanel
          title="KPI Cards"
          description="Metric placeholders to evolve without cross-phase coupling."
          items={board.kpiStubs}
        />
        <SectionStubPanel
          title="Action Queue"
          description="Execution queue scaffolding for this phase's workflows."
          items={board.actionQueueStubs}
        />
      </section>

      <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 shadow-sm">
        <h2 className="text-base font-semibold">Phase Extension Contract</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Keep data adapters, KPI formulas, and queue commands inside this phase module boundary.</li>
          <li>Expose only typed contracts that other phases can consume.</li>
          <li>Avoid importing implementation details from other phase boards.</li>
        </ul>
      </section>
    </div>
  );
};

export default PhaseBoardTemplate;
