import React from 'react';
import type { HealthStatus } from '../types';
import { Database, Cpu, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';

interface HeaderProps {
  health: HealthStatus | null;
  onSeed: () => void;
  isSeeding: boolean;
  seedResult: string | null;
}

export const Header: React.FC<HeaderProps> = ({ health, onSeed, isSeeding, seedResult }) => {
  return (
    <header className="border-b border-zinc-800/80 bg-[#090b0f]/90 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          {/* Logo & Branding */}
          <div className="flex items-center gap-3">
            <img
              src="/logo.png"
              alt="OnCall Memory Logo"
              className="w-10 h-10 rounded-xl object-cover border border-zinc-800 bg-black flex-shrink-0"
            />

            <div>
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white">
                OnCall Memory
              </h1>
              <p className="text-xs text-zinc-400">
                Memory-augmented with Hindsight
              </p>
            </div>
          </div>

          {/* Status Indicators & Seed Action */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Hindsight Bank Indicator */}
            <div className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-[#11141b] border border-zinc-800 text-zinc-300">
              <Database className="w-3.5 h-3.5 text-red-400" />
              <span className="text-zinc-400">Bank:</span>
              <span className="font-mono font-medium text-zinc-200">
                {health?.bank_id || 'oncall-memory'}
              </span>
              {health?.hindsight_connected ? (
                <span className="flex items-center gap-1 text-emerald-400 font-semibold ml-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="text-[11px]">Connected</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-amber-400 ml-1" title={health?.hindsight_status}>
                  <AlertTriangle className="w-3 h-3" />
                  <span className="text-[11px] font-medium">Fallback</span>
                </span>
              )}
            </div>

            {/* LLM Model Indicator */}
            <div className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg bg-[#11141b] border border-zinc-800 text-zinc-300">
              <Cpu className="w-3.5 h-3.5 text-zinc-400" />
              <span className="text-zinc-400">LLM:</span>
              <span className="font-mono text-zinc-200 font-medium">
                {health?.llm_model || 'openai/gpt-oss-120b'}
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-950/60 text-red-300 border border-red-700/50 font-semibold">
                Groq
              </span>
            </div>

            {/* Seed Bank Action */}
            <button
              onClick={onSeed}
              disabled={isSeeding}
              className="flex items-center gap-1.5 text-xs px-3.5 py-1.5 rounded-lg bg-red-900 hover:bg-red-800 active:bg-red-950 text-white font-medium border border-red-700/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-sm shadow-red-950/40"
              title="Seeds ~12 realistic incidents into Hindsight bank oncall-memory"
            >
              {isSeeding ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />
              ) : (
                <Database className="w-3.5 h-3.5 text-white" />
              )}
              <span>{isSeeding ? 'Seeding...' : 'Seed Bank (~12)'}</span>
            </button>
          </div>
        </div>

        {/* Seed confirmation banner (Green for successful action!) */}
        {seedResult && (
          <div className="mt-2.5 text-xs py-2 px-3.5 rounded-xl bg-emerald-950/80 border border-emerald-500/60 text-emerald-200 flex items-center gap-2 animate-fadeIn shadow-lg shadow-emerald-950/50">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="font-medium">{seedResult}</span>
          </div>
        )}
      </div>
    </header>
  );
};
