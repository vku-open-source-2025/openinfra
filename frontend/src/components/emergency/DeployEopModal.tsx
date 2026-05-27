import React, { useState, useCallback } from 'react';
import { X, Loader2, Save, Send } from 'lucide-react';
import { eopApi } from '@/api/eop';
import type { DeployHazardResponse } from '@/api/hazards';

interface Props {
  deployData: DeployHazardResponse;
  onClose: () => void;
  onSubmitted: () => void;
}

const DeployEopModal: React.FC<Props> = ({ deployData, onClose, onSubmitted }) => {
  const [markdown, setMarkdown] = useState(deployData.markdown_body ?? '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const handleSaveDraft = useCallback(async () => {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      await eopApi.updateMarkdown(deployData.eop_plan_id, {
        markdown_body: markdown,
        review_notes: 'Saved from deploy modal',
      });
      setInfo('Đã lưu nháp EOP.');
    } catch (err) {
      console.error(err);
      setError('Không thể lưu nháp. Vui lòng thử lại.');
    } finally {
      setBusy(false);
    }
  }, [deployData.eop_plan_id, markdown]);

  const handleSubmit = useCallback(async () => {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      // Save markdown first, then submit to generate tasks
      await eopApi.updateMarkdown(deployData.eop_plan_id, {
        markdown_body: markdown,
        review_notes: 'Submitted for task generation',
      });
      const result = await eopApi.submit(deployData.eop_plan_id);
      setInfo(`Đã tạo ${result.orders.length} task từ EOP. Nguồn: ${result.task_source}`);
      // Brief delay so user sees the success message before close
      setTimeout(() => {
        onSubmitted();
        onClose();
      }, 1500);
    } catch (err) {
      console.error(err);
      setError('Không thể submit EOP. Vui lòng thử lại.');
      setBusy(false);
    }
  }, [deployData.eop_plan_id, markdown, onClose, onSubmitted]);

  return (
    <div
      className="fixed inset-0 z-[2000] bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-200 flex items-start justify-between bg-gradient-to-r from-amber-50 to-orange-50">
          <div>
            <h2 className="font-bold text-slate-900 text-lg">Kế hoạch ứng phó (EOP)</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Sửa markdown bên dưới → Lưu nháp hoặc Submit để sinh task tự động
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Event: {deployData.event_id} · EOP: {deployData.eop_plan_id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Feedback banners */}
        {error && (
          <div className="px-5 py-2 bg-red-50 border-b border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}
        {info && (
          <div className="px-5 py-2 bg-emerald-50 border-b border-emerald-200 text-sm text-emerald-700">
            {info}
          </div>
        )}

        {/* Markdown editor */}
        <div className="flex-1 overflow-y-auto p-5">
          <label className="block text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">
            Nội dung kế hoạch (Markdown)
          </label>
          <textarea
            value={markdown}
            onChange={(e) => setMarkdown(e.target.value)}
            rows={20}
            className="w-full resize-y rounded-lg border border-slate-300 bg-slate-50 px-3 py-2.5 font-mono text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent"
            placeholder="# Kế hoạch ứng phó..."
            disabled={busy}
          />
        </div>

        {/* Footer actions */}
        <div className="px-5 py-4 border-t border-slate-200 flex justify-end gap-3 bg-slate-50">
          <button
            onClick={onClose}
            disabled={busy}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-60"
          >
            Huỷ
          </button>
          <button
            onClick={handleSaveDraft}
            disabled={busy || !markdown.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-300 rounded-lg hover:bg-amber-100 transition-colors disabled:opacity-60"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Lưu nháp
          </button>
          <button
            onClick={handleSubmit}
            disabled={busy || !markdown.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-60 shadow"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Submit & Sinh task
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeployEopModal;
