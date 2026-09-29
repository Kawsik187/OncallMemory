import React from 'react';
import type { ComparisonResponse } from '../types';
import { Zap, AlertCircle, CheckCircle2, XCircle, Sparkles } from 'lucide-react';

interface ComparisonViewProps {
  comparison: ComparisonResponse;
  onOpenResolve: () => void;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ comparison, onOpenResolve }) => {
  const { with_memory, without_memory, contrast_summary, recalled_memories } = comparison;

  return (
    <div className="space-y-4">
      {/* Value Proposition Hero Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-red-950/60 via-[#10131b] to-emerald-950/50 border border-zinc-800 shadow-xl">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-600/20 text-red-400 flex items-center justify-center flex-shrink-0 mt-0.5 border border-red-500/30">
            <Sparkles className="w-4 h-4 text-red-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white">
                Before / After Comparison: The Power of Agent Memory
              </h3>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                1-Glance Proof
              </span>
            </div>
            <p className="text-xs text-zinc-300 mt-1 leading-relaxed">
              {contrast_summary}
            </p>
          </div>
        </div>
      </div>

      {/* Side-by-Side Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Column 1: Without Memory (Cold Start - Risk Red) */}
        <div className="bg-[#0c0e14]/90 border border-red-500/30 rounded-2xl p-5 shadow-lg backdrop-blur-sm flex flex-col space-y-3.5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-28 h-28 bg-red-600/5 rounded-full blur-2xl pointer-events-none" />

          {/* Column Header */}
          <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-red-600/15 border border-red-500/30 flex items-center justify-center">
                <AlertCircle className="w-3.5 h-3.5 text-red-400" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-zinc-200">Without Memory</h4>
                <p className="text-[10px] text-zinc-400">Cold Start (Starts from Zero)</p>
              </div>
            </div>

            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700">
              Confidence: {without_memory.confidence}
            </span>
          </div>

          {/* Likely Root Cause */}
          <div className="p-3 rounded-xl bg-[#11141d] border border-zinc-800">
            <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">
              Guessed Root Cause
            </span>
            <p className="text-xs text-zinc-300">
              {without_memory.likely_root_cause}
            </p>
          </div>

          {/* Recommended Fix */}
          <div className="p-3 rounded-xl bg-[#11141d] border border-zinc-800">
            <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">
              Generic Advice / Triage
            </span>
            <p className="text-xs text-zinc-300">
              {without_memory.recommended_fix}
            </p>
          </div>

          {/* Historical Evidence */}
          <div className="p-3 rounded-xl bg-[#11141d] border border-zinc-800 flex-1">
            <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">
              Historical Precedent
            </span>
            <p className="text-xs text-zinc-400 italic">
              "No prior memories available. Engineer must manually search Slack and tickets."
            </p>
          </div>

          <div className="text-[11px] text-red-300/90 bg-red-950/30 p-2.5 rounded-lg border border-red-500/30 flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>High risk: Engineer may repeat previously failed fixes (e.g. restarts or pod bumping).</span>
          </div>
        </div>

        {/* Column 2: With Hindsight Memory (Green for Successful Fix!) */}
        <div className="bg-[#0b120f]/90 border-2 border-emerald-500/40 rounded-2xl p-5 shadow-xl backdrop-blur-sm flex flex-col space-y-3.5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-28 h-28 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

          {/* Column Header */}
          <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
                <Zap className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  With Hindsight Memory
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    oncall-memory
                  </span>
                </h4>
                <p className="text-[10px] text-emerald-300/90">Recalled {recalled_memories.length} relevant past experiences</p>
              </div>
            </div>

            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Confidence: {with_memory.confidence}
            </span>
          </div>

          {/* Likely Root Cause */}
          <div className="p-3 rounded-xl bg-[#081510] border border-emerald-500/25">
            <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
              Historically Verified Root Cause
            </span>
            <p className="text-xs text-white font-medium">
              {with_memory.likely_root_cause}
            </p>
          </div>

          {/* Recommended Fix */}
          <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-950/40 to-[#081510] border border-emerald-500/30">
            <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
              Targeted Fix (Warns Against Failed Attempts)
            </span>
            <p className="text-xs text-emerald-100 font-medium leading-relaxed">
              {with_memory.recommended_fix}
            </p>
          </div>

          {/* Citing Historical Evidence */}
          <div className="p-3 rounded-xl bg-[#081510] border border-zinc-800 flex-1">
            <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
              Historical Citation & Evidence
            </span>
            <p className="text-xs text-zinc-300 italic">
              "{with_memory.citing}"
            </p>
          </div>

          <div className="text-[11px] text-emerald-300 bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Zero guesswork: Applies verified fix that worked previously.</span>
            </div>
            <button
              onClick={onOpenResolve}
              className="text-[10px] font-semibold px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white ml-2 flex-shrink-0 cursor-pointer transition-all"
            >
              Resolve
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
