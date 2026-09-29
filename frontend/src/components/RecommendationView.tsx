import React from 'react';
import type { StructuredRecommendation, IncidentInput } from '../types';
import { ShieldCheck, BookmarkCheck, ListOrdered, Wrench, CheckSquare, Sparkles } from 'lucide-react';

interface RecommendationViewProps {
  recommendation: StructuredRecommendation;
  incident: IncidentInput;
  onOpenResolve: () => void;
}

export const RecommendationView: React.FC<RecommendationViewProps> = ({
  recommendation,
  incident,
  onOpenResolve,
}) => {
  const confidenceColor = {
    high: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    medium: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    low: 'bg-zinc-800 text-zinc-400 border-zinc-700',
  }[recommendation.confidence];

  return (
    <div className="bg-[#0c0e14]/90 border-2 border-emerald-500/40 rounded-2xl p-5 shadow-2xl shadow-emerald-950/30 backdrop-blur-sm flex flex-col h-full space-y-4 relative overflow-hidden">
      {/* Subtle emerald top glow to emphasize successful recommendation generation */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500" />
      <div className="absolute top-0 right-0 w-36 h-36 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-zinc-800/80">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                Agent Recommendation
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Generated Successfully
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                {incident.service}
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Synthesized from historical evidence using Groq gpt-oss-120b
            </p>
          </div>
        </div>

        {/* Confidence Badge */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className="text-xs text-zinc-400 font-medium">Confidence:</span>
          <span
            className={`text-xs uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full border ${confidenceColor}`}
          >
            {recommendation.confidence}
          </span>
        </div>
      </div>

      {/* Likely Root Cause Card */}
      <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800">
        <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
          Likely Root Cause
        </span>
        <p className="text-sm font-medium text-zinc-100 leading-snug">
          {recommendation.likely_root_cause}
        </p>
      </div>

      {/* Recommended Fix Card (Hero - Green glow for success fix) */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-950/40 via-[#0e1713] to-[#0c0e14] border border-emerald-500/40 shadow-lg shadow-emerald-950/40">
        <div className="flex items-center gap-2 mb-2">
          <Wrench className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-emerald-300 uppercase tracking-wide flex items-center gap-1.5">
            Recommended Action & Fix
            <Sparkles className="w-3 h-3 text-emerald-400" />
          </span>
        </div>
        <p className="text-xs sm:text-sm text-emerald-100 font-medium leading-relaxed">
          {recommendation.recommended_fix}
        </p>
      </div>

      {/* Citing Historical Evidence */}
      <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800">
        <div className="flex items-center gap-2 mb-1.5">
          <BookmarkCheck className="w-4 h-4 text-red-400" />
          <span className="text-xs font-semibold text-red-200">
            Citing Historical Evidence
          </span>
        </div>
        <p className="text-xs text-zinc-300 italic leading-relaxed">
          "{recommendation.citing}"
        </p>

        {recommendation.historical_evidence.length > 0 && (
          <ul className="mt-2.5 space-y-1.5 border-t border-zinc-800/80 pt-2 text-[11px] text-zinc-400">
            {recommendation.historical_evidence.map((ev, i) => (
              <li key={i} className="flex items-start gap-1.5 font-mono">
                <span className="text-red-400">•</span>
                <span className="break-words text-zinc-300">{ev}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Actionable Runbook */}
      {recommendation.runbook && recommendation.runbook.length > 0 && (
        <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800">
          <div className="flex items-center gap-2 mb-2">
            <ListOrdered className="w-4 h-4 text-red-400" />
            <span className="text-xs font-semibold text-zinc-200">
              Oncall Action Runbook
            </span>
          </div>
          <ol className="space-y-1.5 text-xs text-zinc-300">
            {recommendation.runbook.map((step, i) => (
              <li key={i} className="flex items-start gap-2 bg-[#080a0e] p-2 rounded-lg border border-zinc-800/80">
                <span className="w-4 h-4 rounded-full bg-red-600/20 text-red-300 text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5 border border-red-500/30">
                  {i + 1}
                </span>
                <span className="leading-snug text-zinc-200">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Resolve Incident Trigger */}
      <div className="pt-2 mt-auto">
        <button
          onClick={onOpenResolve}
          className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-red-900 via-red-800 to-red-900 hover:from-red-800 hover:via-red-700 hover:to-red-800 active:from-red-950 shadow-lg shadow-red-950/50 border border-red-700/60 transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <CheckSquare className="w-4 h-4" />
          <span>Mark Incident Resolved & Retain in Hindsight</span>
        </button>
      </div>
    </div>
  );
};
