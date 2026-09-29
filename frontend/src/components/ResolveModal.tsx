import React, { useState } from 'react';
import type { IncidentInput, IncidentResolution } from '../types';
import { X, CheckCircle2, AlertCircle, Database, Sparkles, Send } from 'lucide-react';

interface ResolveModalProps {
  isOpen: boolean;
  onClose: () => void;
  incident: IncidentInput | null;
  onResolve: (resolution: IncidentResolution) => Promise<void>;
  isSubmitting: boolean;
  onLoadStep2Preset?: () => void;
}

export const ResolveModal: React.FC<ResolveModalProps> = ({
  isOpen,
  onClose,
  incident,
  onResolve,
  isSubmitting,
  onLoadStep2Preset,
}) => {
  if (!isOpen || !incident) return null;

  const [rootCause, setRootCause] = useState<string>('');
  const [fix, setFix] = useState<string>('');
  const [outcome, setOutcome] = useState<'WORKED' | 'FAILED'>('WORKED');
  const [retainSuccess, setRetainSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rootCause.trim() || !fix.trim()) return;

    try {
      await onResolve({
        title: incident.title,
        service: incident.service,
        root_cause: rootCause.trim(),
        fix: fix.trim(),
        outcome,
      });
      setRetainSuccess(`Experience successfully retained into Hindsight bank 'oncall-memory' with outcome ${outcome}!`);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="bg-[#0e1118] border border-zinc-700/80 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/5 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-600/15 border border-red-500/30 flex items-center justify-center">
            <Database className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Resolve Incident & Retain Memory</h3>
            <p className="text-xs text-zinc-400">
              Stores learnings into Hindsight (<span className="font-mono text-red-400">oncall-memory</span>)
            </p>
          </div>
        </div>

        {retainSuccess ? (
          <div className="space-y-4 py-3">
            {/* Green for successfully retained outcome as requested by user */}
            <div className="p-4 rounded-xl bg-emerald-950/60 border-2 border-emerald-500/50 text-emerald-200 text-xs flex items-start gap-3 shadow-lg shadow-emerald-950/40">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-emerald-100 text-sm mb-1">Knowledge Persisted in Hindsight!</p>
                <p className="text-emerald-200 leading-relaxed mb-2">{retainSuccess}</p>
                <div className="p-2.5 rounded-lg bg-[#070e0a] border border-emerald-500/30 font-mono text-[11px] text-emerald-300 break-words">
                  INCIDENT: {incident.title} | SERVICE: {incident.service} | ROOT CAUSE: {rootCause} | FIX ({outcome}): {fix}
                </div>
              </div>
            </div>

            {onLoadStep2Preset && (
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-red-950/30 to-[#121620] border border-red-500/30 flex items-center justify-between gap-3">
                <div className="text-xs text-zinc-200">
                  <span className="font-bold text-white block">Test Stage 2 Demo:</span>
                  Simulate a future similar alert to verify the agent recalls this newly retained fix.
                </div>
                <button
                  onClick={() => {
                    onLoadStep2Preset();
                    onClose();
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-semibold text-xs flex-shrink-0 flex items-center gap-1.5 cursor-pointer shadow-md shadow-red-600/20"
                >
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                  <span>Load Stage 2</span>
                </button>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-300 bg-[#141822] hover:bg-[#1c2230] border border-zinc-700 cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {/* Target incident summary */}
            <div className="p-2.5 rounded-lg bg-[#07090e] border border-zinc-800 text-xs">
              <div className="text-zinc-400">Incident:</div>
              <div className="text-white font-semibold">{incident.title}</div>
              <div className="text-[11px] text-red-400 font-mono mt-0.5">service: {incident.service}</div>
            </div>

            {/* Root cause input */}
            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-1">
                Verified Root Cause <span className="text-red-500">*</span>
              </label>
              <textarea
                required
                rows={2}
                value={rootCause}
                onChange={(e) => setRootCause(e.target.value)}
                placeholder="What actually caused this issue?"
                className="w-full bg-[#07090e] border border-zinc-800 rounded-lg p-2.5 text-xs text-zinc-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 resize-none transition-all"
              />
            </div>

            {/* Fix input */}
            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-1">
                Fix Description <span className="text-red-500">*</span>
              </label>
              <textarea
                required
                rows={2}
                value={fix}
                onChange={(e) => setFix(e.target.value)}
                placeholder="What exact fix was applied (or failed)?"
                className="w-full bg-[#07090e] border border-zinc-800 rounded-lg p-2.5 text-xs text-zinc-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 resize-none transition-all"
              />
            </div>

            {/* Outcome Toggle (WORKED = Green, FAILED = Red) */}
            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                Outcome <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setOutcome('WORKED')}
                  className={`py-2 px-3 rounded-lg border text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                    outcome === 'WORKED'
                      ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/30'
                      : 'bg-[#07090e] border-zinc-800 text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>WORKED (Recommended)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setOutcome('FAILED')}
                  className={`py-2 px-3 rounded-lg border text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                    outcome === 'FAILED'
                      ? 'bg-red-600 text-white border-red-500 shadow-md shadow-red-600/30'
                      : 'bg-[#07090e] border-zinc-800 text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>FAILED (Warn Against)</span>
                </button>
              </div>
            </div>

            {/* Submit Action */}
            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-zinc-800">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-300 bg-[#141822] hover:bg-[#1c2230] border border-zinc-700 cursor-pointer"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-red-900 via-red-800 to-red-900 hover:from-red-800 hover:via-red-700 hover:to-red-800 active:from-red-950 shadow-lg shadow-red-950/60 border border-red-700/60 flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isSubmitting ? 'Retaining in Hindsight...' : 'Retain in Hindsight'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
