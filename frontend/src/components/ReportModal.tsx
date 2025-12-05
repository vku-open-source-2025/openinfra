import React, { useState } from 'react';
import { X, Send, AlertTriangle } from 'lucide-react';
import { createIncident, IncidentCategory, IncidentSeverity, type Asset } from '../api';

interface ReportModalProps {
    isOpen: boolean;
    onClose: () => void;
    asset: Asset | null;
}

const ReportModal: React.FC<ReportModalProps> = ({ isOpen, onClose, asset }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState<IncidentCategory>(IncidentCategory.MALFUNCTION);
    const [severity, setSeverity] = useState<IncidentSeverity>(IncidentSeverity.LOW);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    if (!isOpen || !asset) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);

        try {
            await createIncident({
                asset_id: asset._id,
                title,
                description,
                category,
                severity,
                reported_via: 'web',
                public_visible: true
            });
            setSuccess(true);
            setTimeout(() => {
                onClose();
                setSuccess(false);
                setTitle('');
                setDescription('');
                setCategory(IncidentCategory.MALFUNCTION);
                setSeverity(IncidentSeverity.LOW);
            }, 2000);
        } catch (err) {
            console.error("Failed to submit report:", err);
            setError("Failed to submit report. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (success) {
        return (
            <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden p-8 text-center animate-in fade-in zoom-in duration-200">
                    <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Send size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-800 mb-2">Report Submitted</h3>
                    <p className="text-slate-500">Thank you for your report. We will investigate the issue.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
                <div className="flex justify-between items-center p-4 border-b border-slate-100 shrink-0">
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="text-amber-500" size={20} />
                        <h3 className="font-bold text-lg text-slate-800">Report Issue</h3>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto">
                    <div className="mb-6 bg-slate-50 p-3 rounded-lg border border-slate-100 text-sm">
                        <p className="font-medium text-slate-700">Reporting for: {asset.feature_type}</p>
                        <p className="text-slate-500 font-mono text-xs mt-1">ID: {asset._id}</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Issue Title
                            </label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                placeholder="e.g., Broken Equipment"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Category
                            </label>
                            <select
                                value={category}
                                onChange={(e) => setCategory(e.target.value as IncidentCategory)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
                            >
                                {Object.values(IncidentCategory).map((cat) => (
                                    <option key={cat} value={cat}>
                                        {cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' ')}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Severity
                            </label>
                            <select
                                value={severity}
                                onChange={(e) => setSeverity(e.target.value as IncidentSeverity)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all bg-white"
                            >
                                {Object.values(IncidentSeverity).map((sev) => (
                                    <option key={sev} value={sev}>
                                        {sev.charAt(0).toUpperCase() + sev.slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Description
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                required
                                rows={4}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
                                placeholder="Please describe the issue in detail..."
                            />
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">
                                {error}
                            </div>
                        )}

                        <div className="pt-2">
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors shadow-sm"
                            >
                                {isSubmitting ? (
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <Send size={18} />
                                        Submit Report
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ReportModal;
