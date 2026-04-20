import React from 'react';

import type { SectionStubItem } from '@/types/emergency-phase-board';

interface SectionStubPanelProps {
  title: string;
  description: string;
  items: SectionStubItem[];
}

const SectionStubPanel: React.FC<SectionStubPanelProps> = ({ title, description, items }) => {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <p className="mt-1 text-sm text-slate-600">{description}</p>

      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-sm font-semibold text-slate-900">{item.title}</p>
            <p className="mt-1 text-sm text-slate-700">{item.description}</p>
            <p className="mt-2 rounded-md border border-dashed border-slate-300 bg-white px-2 py-1 text-xs text-slate-600">
              Extension point: {item.extensionHint}
            </p>
          </div>
        ))}
      </div>
    </article>
  );
};

export default SectionStubPanel;
