import React from 'react';
import type { RecalledMemoryItem } from '../types';
import { Database, Clock, CheckCircle2, XCircle, Search, AlertTriangle } from 'lucide-react';

interface HindsightRecallViewProps {
  memories: RecalledMemoryItem[];
  hindsightAvailable: boolean;
  hindsightMessage?: string;
  bankId?: string;
}

export const HindsightRecallView: React.FC<HindsightRecallViewProps> = ({
  memories,
  hindsightAvailable,
  hindsightMessage,
  bankId = 'oncall-memory',
}) => {
  return (
    <div className="bg-[#0c0e14]/90 border border-zinc-800 rounded-2xl p-5 shadow-2xl backdrop-blur-sm flex flex-col h-full relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-zinc-800/80 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-red-600/15 border border-red-500/30 flex items-center justify-center">
            <Database className="w-4 h-4 text-red-500" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Hindsight Recall
              <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-red-950/70 text-red-300 border border-red-600/40">
                bank: {bankId}
              </span>
            </h3>
            <p className="text-[11px] text-zinc-400">
              Multi-strategy TEMPR retrieval (Semantic, Temporal, Entity, Keyword)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-zinc-400 font-medium">Recalled:</span>
          <span className="px-2 py-0.5 rounded-md bg-[#161a24] font-mono text-zinc-200 font-semibold border border-zinc-700">
            {memories.length} memories
          </span>
        </div>
      </div>

      {/* Graceful / Unavailability Message */}
      {!hindsightAvailable && (
        <div className="p-3.5 mb-4 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-100">Notice: </span>
            {hindsightMessage || 'Hindsight memory temporarily unavailable, continuing without historical context'}
          </div>
        </div>
      )}

      {/* Memory items list */}
      <div className="space-y-3 flex-1 overflow-y-auto max-h-[520px] pr-1">
        {memories.length === 0 ? (
          <div className="text-center py-12 px-4 rounded-xl border border-dashed border-zinc-800 bg-[#080a0e]">
            <Search className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
            <p className="text-xs font-medium text-zinc-300">No Prior Experiences Matched</p>
            <p className="text-[11px] text-zinc-500 mt-1 max-w-xs mx-auto">
              This incident appears for the first time. Once resolved, retain it into Hindsight to teach the agent!
            </p>
          </div>
        ) : (
          memories.map((mem, index) => {
            const isWorked = mem.text.includes('FIX (WORKED):');
            const isFailed = mem.text.includes('FIX (FAILED):');

            // Parse date if present: [DATE]
            const dateMatch = mem.text.match(/^\[(.*?)\]/);
            const dateStr = dateMatch ? dateMatch[1] : null;

            return (
              <div
                key={mem.id || index}
                className={`p-3.5 rounded-xl border transition-all text-xs ${
                  isFailed
                    ? 'bg-red-950/20 border-red-500/40 hover:border-red-500/60 shadow-sm shadow-red-950/20'
                    : isWorked
                    ? 'bg-emerald-950/25 border-emerald-500/40 hover:border-emerald-500/60 shadow-sm shadow-emerald-950/20'
                    : 'bg-[#10131c] border-zinc-800 hover:border-zinc-700'
                }`}
              >
                {/* Memory Badges */}
                <div className="flex flex-wrap items-center justify-between gap-1.5 mb-2">
                  <div className="flex items-center gap-1.5">
                    {isWorked && (
                      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase tracking-wide">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        Fix Worked
                      </span>
                    )}
                    {isFailed && (
                      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-red-600/20 text-red-300 border border-red-500/40 uppercase tracking-wide">
                        <XCircle className="w-3 h-3 text-red-400" />
                        Fix Failed (Avoid)
                      </span>
                    )}
                    {!isWorked && !isFailed && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700 font-mono">
                        {mem.type || 'experience'}
                      </span>
                    )}

                    {mem.is_same_service ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                        {mem.service || 'Direct Match'}
                      </span>
                    ) : mem.service ? (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                        Analogy: {mem.service}
                      </span>
                    ) : null}

                    {dateStr && (
                      <span className="flex items-center gap-1 text-[10px] text-zinc-400 font-mono">
                        <Clock className="w-2.5 h-2.5 text-zinc-500" />
                        {dateStr}
                      </span>
                    )}
                  </div>

                  {mem.score !== undefined && mem.score !== null && (
                    <span className="text-[10px] font-mono text-zinc-400" title="TEMPR Fused Relevance Score">
                      score: {mem.score.toFixed(3)}
                    </span>
                  )}
                </div>

                {/* Main Memory Text */}
                <p className="text-zinc-200 leading-relaxed font-mono text-[11px] break-words">
                  {mem.text}
                </p>

                {/* Relevance explanation / context note */}
                {mem.relevance_reason && (
                  <div className="mt-2 pt-2 border-t border-zinc-800/80 text-[10px] text-red-400/90 italic flex items-center gap-1">
                    <span>Relevance:</span>
                    <span>{mem.relevance_reason}</span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
