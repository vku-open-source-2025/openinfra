import React from 'react';
import { Link } from '@tanstack/react-router';

import { orderedPhaseBoards } from './phaseBoardDefinitions';

const EmergencyBoardsLandingPage: React.FC = () => {
  return (
    <div className="space-y-6 p-4 md:p-6">
      <header className="rounded-xl bg-gradient-to-r from-red-800 via-orange-700 to-amber-600 p-5 text-white shadow-lg">
        <h1 className="text-2xl font-bold md:text-3xl">Disaster Phase Boards</h1>
        <p className="mt-2 text-sm text-white/90 md:text-base">
          Dedicated board surfaces for before, during, and after disaster phases. Each phase is isolated so
          separate teams can implement data, KPI, and action workflows independently.
        </p>
      </header>

      <section className="grid gap-4 lg:grid-cols-3">
        {orderedPhaseBoards.map((board) => (
          <article key={board.phase} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{board.tabLabel} phase</p>
            <h2 className="mt-2 text-xl font-bold text-slate-900">{board.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{board.subtitle}</p>
            <p className="mt-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
              {board.teamBoundary}
            </p>

            <ul className="mt-4 space-y-1 text-sm text-slate-700">
              <li>Data source stubs: {board.dataSourceStubs.length}</li>
              <li>KPI card stubs: {board.kpiStubs.length}</li>
              <li>Action queue stubs: {board.actionQueueStubs.length}</li>
            </ul>

            <Link
              to={board.routePath}
              className="mt-4 inline-flex rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-100"
            >
              Open {board.tabLabel} board
            </Link>
          </article>
        ))}
      </section>

      <section className="rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900 shadow-sm">
        <h2 className="text-base font-semibold">Modular handoff note for parallel teams</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Each phase board lives in an independent page file and route file.</li>
          <li>Shared schema and rendering primitives are centralized in small reusable files.</li>
          <li>Cross-phase dependencies should happen through typed interfaces, not direct implementation imports.</li>
        </ul>
      </section>
    </div>
  );
};

export default EmergencyBoardsLandingPage;
