import React from 'react';
import type { ReflectResponsePayload, IncidentInput } from '../types';
import { Brain, ShieldCheck, AlertTriangle, ListOrdered, Sparkles, Layers, CheckSquare } from 'lucide-react';

interface ReflectViewProps {
  reflectData: ReflectResponsePayload;
  incident: IncidentInput;
  onOpenResolve: () => void;
}

export const ReflectView: React.FC<ReflectViewProps> = ({
  reflectData,
  incident,
  onOpenResolve,
}) => {
  const { reflection, based_on_memories, hindsight_reflection_text, hindsight_available, hindsight_message } = reflectData;

  return (
    <div className="bg-[#0c0e14]/90 border-2 border-emerald-500/40 rounded-2xl p-5 shadow-2xl shadow-emerald-950/30 backdrop-blur-sm flex flex-col space-y-4 relative overflow-hidden">
      {/* Top emerald glow line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-emerald-500 to-rose-600" />
      <div className="absolute top-0 right-0 w-36 h-36 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-zinc-800/80">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
            <Brain className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                Hindsight Systemic Reflection
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Reflected Successfully
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                {incident.service}
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Formulated via Hindsight native /reflect API + Groq gpt-oss-120b
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#161a24] text-zinc-200 border border-zinc-700">
            {based_on_memories.length} facts synthesized
          </span>
        </div>
      </div>

      {/* 2-Column Grid for Deep Reflection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Systemic Root Cause */}
        <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800">
          <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
            Systemic Architectural Root Cause
          </span>
          <p className="text-xs sm:text-sm font-medium text-zinc-100 leading-snug">
            {reflection.systemic_root_cause}
          </p>
        </div>

        {/* Pattern Recognition */}
        <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800">
          <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
            Historical Pattern Recognition
          </span>
          <p className="text-xs text-zinc-300 leading-relaxed">
            {reflection.pattern_recognition}
          </p>
        </div>
      </div>

      {/* Recurrent Risk Warning Banner */}
      <div className="p-3.5 rounded-xl bg-red-950/30 border border-red-500/30 text-red-200 text-xs flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-red-100 block mb-0.5">Cascade & Recurrence Vulnerability:</span>
          <span className="text-zinc-300">{reflection.recurrent_risk}</span>
        </div>
      </div>

      {/* Architectural Fix (Hero - Green glow for success solution) */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-950/40 via-[#0e1713] to-[#0c0e14] border border-emerald-500/40 shadow-lg shadow-emerald-950/40">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-emerald-300 uppercase tracking-wide flex items-center gap-1.5">
            Long-Term Engineering Resilience Redesign
            <Sparkles className="w-3 h-3 text-emerald-400" />
          </span>
        </div>
        <p className="text-xs sm:text-sm text-emerald-100 font-medium leading-relaxed">
          {reflection.architectural_fix}
        </p>
      </div>

      {/* Prevention Runbook & Based-on Memories in side-by-side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Prevention Checklist */}
        <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800">
          <div className="flex items-center gap-2 mb-2">
            <ListOrdered className="w-4 h-4 text-red-400" />
            <span className="text-xs font-semibold text-zinc-200">
              Platform SRE Prevention Guardrails
            </span>
          </div>
          <ol className="space-y-1.5 text-xs text-zinc-300">
            {reflection.prevention_runbook.map((step, i) => (
              <li key={i} className="flex items-start gap-2 bg-[#080a0e] p-2 rounded-lg border border-zinc-800/80">
                <span className="w-4 h-4 rounded-full bg-red-600/20 text-red-300 text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5 border border-red-500/30">
                  {i + 1}
                </span>
                <span className="leading-snug text-zinc-200">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Based-on memories cited by Hindsight reflect */}
        <div className="p-3.5 rounded-xl bg-[#11141d] border border-zinc-800 flex flex-col">
          <div className="flex items-center gap-2 mb-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-semibold text-zinc-200">
              Hindsight Reflected Memory Evidence
            </span>
          </div>
          <div className="space-y-2 overflow-y-auto max-h-[160px] pr-1">
            {hindsight_reflection_text && (
              <div className="p-2 rounded bg-[#080a0e] border border-emerald-500/20 text-[11px] text-zinc-300 italic mb-1">
                <span className="text-emerald-400 font-semibold not-italic">Hindsight Reflection: </span>
                {hindsight_reflection_text}
              </div>
            )}
            {based_on_memories.length === 0 ? (
              <p className="text-xs text-zinc-400 italic">No historical memory records cited during reflection.</p>
            ) : (
              based_on_memories.map((m, idx) => (
                <div key={idx} className="p-2 rounded bg-[#080a0e] border border-zinc-800 text-[11px] font-mono text-zinc-300">
                  <span className="text-emerald-400 font-bold mr-1">•</span>
                  <span>{m.text}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {!hindsight_available && (
        <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>{hindsight_message || 'Hindsight memory temporarily offline. Local deterministic reflection active.'}</span>
        </div>
      )}

      {/* Resolve Incident Trigger */}
      <div className="pt-2 mt-auto">
        <button
          onClick={onOpenResolve}
          className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 active:from-red-700 shadow-lg shadow-red-600/20 border border-red-500/40 transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <CheckSquare className="w-4 h-4" />
          <span>Mark Incident Resolved & Retain in Hindsight</span>
        </button>
      </div>
    </div>
  );
};

