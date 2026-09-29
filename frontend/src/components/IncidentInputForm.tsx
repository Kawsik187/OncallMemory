import React, { useState } from 'react';
import type { IncidentInput, PresetItem } from '../types';
import { Play, Columns, Terminal, Sparkles, HelpCircle } from 'lucide-react';

interface IncidentInputFormProps {
  presets: PresetItem[];
  onSubmit: (incident: IncidentInput, mode: 'analyze' | 'compare' | 'reflect') => void;
  isLoading: boolean;
  activeMode: 'analyze' | 'compare' | 'reflect' | null;
}

export const IncidentInputForm: React.FC<IncidentInputFormProps> = ({
  presets,
  onSubmit,
  isLoading,
  activeMode,
}) => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>(presets[0]?.id || '');
  const [incident, setIncident] = useState<IncidentInput>(
    presets[0]?.incident || {
      title: 'Postgres Connection Pool Saturation',
      service: 'order-service',
      description: 'API latency jumped to 14,000ms and checkout requests are failing with HTTP 500 errors during midday flash sale.',
      symptoms: 'Database connection pool utilization at 100%, p99 latency spike to 12s, cart abandonment rate spiked 400%.',
      error_logs: 'org.springframework.dao.CannotAcquireLockException: HikariPool-1 - Connection is not available, request timed out after 30005ms.\nCaused by: java.sql.SQLTransientConnectionException: Connection pool exhausted.',
    }
  );

  const handlePresetChange = (presetId: string) => {
    setSelectedPresetId(presetId);
    const found = presets.find((p) => p.id === presetId);
    if (found) {
      setIncident({ ...found.incident });
    }
  };

  const selectedPreset = presets.find((p) => p.id === selectedPresetId);

  return (
    <div className="bg-[#0b0d13]/90 border border-zinc-800 rounded-2xl p-5 shadow-2xl backdrop-blur-sm relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-red-500" />
            Active Incident Context
          </h2>
          <p className="text-xs text-zinc-400">
            Provide the telemetry and logs. The agent will query Hindsight memory bank before generating advice.
          </p>
        </div>

        {/* Presets dropdown */}
        {presets.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-zinc-400">Demo Scenario:</span>
            <select
              value={selectedPresetId}
              onChange={(e) => handlePresetChange(e.target.value)}
              className="bg-[#121620] border border-zinc-700/80 rounded-lg px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-2 focus:ring-red-500 max-w-xs cursor-pointer"
            >
              {presets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Preset demo instructions highlight if available */}
      {selectedPreset?.demo_instruction && (
        <div className="mb-4 text-xs p-3 rounded-xl bg-gradient-to-r from-red-950/40 via-[#161118] to-[#0d0f15] border border-red-500/30 text-red-200 flex items-start gap-2.5 shadow-sm">
          <Sparkles className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-white">Live Learning Demo Guide: </span>
            <span className="text-zinc-300">{selectedPreset.demo_instruction}</span>
          </div>
        </div>
      )}

      {selectedPreset?.expected_recall && !selectedPreset.demo_instruction && (
        <div className="mb-4 text-xs p-2.5 rounded-lg bg-[#11141d] border border-zinc-800 text-zinc-300 flex items-start gap-2">
          <HelpCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="text-zinc-400">Expected Recall: </span>
            <span className="text-zinc-200">{selectedPreset.expected_recall}</span>
          </div>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(incident, 'analyze');
        }}
        className="space-y-3.5"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-zinc-300 mb-1">
              Incident / Alert Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={incident.title}
              onChange={(e) => setIncident({ ...incident, title: e.target.value })}
              className="w-full bg-[#07090e] border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 transition-all"
              placeholder="e.g. Postgres Connection Pool Saturation"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">
              Affected Service <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={incident.service}
              onChange={(e) => setIncident({ ...incident, service: e.target.value })}
              className="w-full bg-[#07090e] border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 transition-all"
              placeholder="e.g. order-service"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">
              Description
            </label>
            <input
              type="text"
              value={incident.description}
              onChange={(e) => setIncident({ ...incident, description: e.target.value })}
              className="w-full bg-[#07090e] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 transition-all"
              placeholder="Summary of ongoing issue"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">
              Observed Symptoms & Metrics
            </label>
            <input
              type="text"
              value={incident.symptoms}
              onChange={(e) => setIncident({ ...incident, symptoms: e.target.value })}
              className="w-full bg-[#07090e] border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 transition-all"
              placeholder="e.g. 500 error rate spike, p99 latency 12s"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-300 mb-1 flex items-center justify-between">
            <span>Error Logs / Stack Trace</span>
            <span className="text-[11px] text-zinc-500">Monospace</span>
          </label>
          <textarea
            rows={3}
            value={incident.error_logs}
            onChange={(e) => setIncident({ ...incident, error_logs: e.target.value })}
            className="w-full font-mono text-xs bg-[#07090e] border border-zinc-800 rounded-lg p-2.5 text-zinc-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-zinc-600 resize-y transition-all"
            placeholder="Paste logs or stack trace here..."
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
          {/* Comparison Mode Button */}
          <button
            type="button"
            onClick={() => onSubmit(incident, 'compare')}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-zinc-200 bg-[#141822] hover:bg-[#1a202e] active:bg-[#11141d] border border-zinc-700 shadow-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            <Columns className="w-3.5 h-3.5 text-red-400" />
            <span>
              {isLoading && activeMode === 'compare'
                ? 'Contrasting...'
                : 'Compare: With vs Without Memory'}
            </span>
          </button>

          {/* Primary Analyze Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-red-900 via-red-800 to-red-900 hover:from-red-800 hover:via-red-700 hover:to-red-800 active:from-red-950 shadow-lg shadow-red-950/60 border border-red-700/60 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>
              {isLoading && activeMode === 'analyze'
                ? 'Recalling Hindsight & Reasoning...'
                : 'Analyze with Memory'}
            </span>
          </button>
        </div>
      </form>
    </div>
  );
};
