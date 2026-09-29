import React, { useState, useEffect } from 'react';
import type {
  IncidentInput,
  IncidentResponsePayload,
  ComparisonResponse,
  ReflectResponsePayload,
  IncidentResolution,
  HealthStatus,
  PresetItem,
} from './types';
import {
  fetchHealth,
  fetchPresets,
  analyzeIncident,
  compareIncident,
  reflectIncident,
  resolveIncident,
  seedBank,
} from './api';
import { Header } from './components/Header';
import { IncidentInputForm } from './components/IncidentInputForm';
import { HindsightRecallView } from './components/HindsightRecallView';
import { RecommendationView } from './components/RecommendationView';
import { ComparisonView } from './components/ComparisonView';
import { ReflectView } from './components/ReflectView';
import { ResolveModal } from './components/ResolveModal';
import { BookOpen, ArrowRight, Brain } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [presets, setPresets] = useState<PresetItem[]>([]);
  const [activeIncident, setActiveIncident] = useState<IncidentInput | null>(null);
  const [analysisResult, setAnalysisResult] = useState<IncidentResponsePayload | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResponse | null>(null);
  const [reflectResult, setReflectResult] = useState<ReflectResponsePayload | null>(null);
  const [activeView, setActiveView] = useState<'recommendation' | 'comparison' | 'reflect'>('recommendation');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMode, setLoadingMode] = useState<'analyze' | 'compare' | 'reflect' | null>(null);
  const [isSeeding, setIsSeeding] = useState<boolean>(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);
  const [isResolveOpen, setIsResolveOpen] = useState<boolean>(false);
  const [isSubmittingResolution, setIsSubmittingResolution] = useState<boolean>(false);
  const [demoStep, setDemoStep] = useState<number>(1);

  // Initial load: health check & preset incidents
  useEffect(() => {
    loadHealth();
    loadPresets();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.warn('Backend or Hindsight health check warning:', err);
    }
  };

  const loadPresets = async () => {
    try {
      const data = await fetchPresets();
      setPresets(data);
      if (data.length > 0) {
        setActiveIncident(data[0].incident);
      }
    } catch (err) {
      console.warn('Failed to load presets:', err);
    }
  };

  const handleSeed = async () => {
    setIsSeeding(true);
    setSeedResult(null);
    try {
      const res = await seedBank();
      setSeedResult(`Successfully seeded ${res.retained}/${res.total} incidents into Hindsight bank '${res.bank_id}'!`);
      await loadHealth();
    } catch (err: any) {
      setSeedResult(`Seeding notice: ${err.message || 'Could not seed'}`);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleSubmitIncident = async (incident: IncidentInput, mode: 'analyze' | 'compare' | 'reflect') => {
    setActiveIncident(incident);
    setIsLoading(true);
    setLoadingMode(mode);

    try {
      if (mode === 'analyze') {
        const payload = await analyzeIncident(incident);
        setAnalysisResult(payload);
        setActiveView('recommendation');
      } else if (mode === 'compare') {
        const comp = await compareIncident(incident);
        setComparisonResult(comp);
        setActiveView('comparison');
      } else if (mode === 'reflect') {
        const ref = await reflectIncident(incident);
        setReflectResult(ref);
        setActiveView('reflect');
      }
    } catch (err: any) {
      alert(`Request failed: ${err.message}`);
    } finally {
      setIsLoading(false);
      setLoadingMode(null);
    }
  };

  const handleResolve = async (resolution: IncidentResolution) => {
    setIsSubmittingResolution(true);
    try {
      await resolveIncident(resolution);
      setDemoStep(2);
    } finally {
      setIsSubmittingResolution(false);
    }
  };

  const handleLoadStep2Preset = () => {
    const step2Preset = presets.find((p) => p.id === 'demo_stage2_similar_incident');
    if (step2Preset) {
      setActiveIncident(step2Preset.incident);
      handleSubmitIncident(step2Preset.incident, 'analyze');
    }
  };

  const handleReflectStep = () => {
    setDemoStep(3);
    if (activeIncident) {
      handleSubmitIncident(activeIncident, 'reflect');
    } else {
      const defaultIncident = presets[0]?.incident;
      if (defaultIncident) {
        setActiveIncident(defaultIncident);
        handleSubmitIncident(defaultIncident, 'reflect');
      }
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#060709] text-zinc-100 selection:bg-red-600 selection:text-white">
      {/* Top Header */}
      <Header
        health={health}
        onSeed={handleSeed}
        isSeeding={isSeeding}
        seedResult={seedResult}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Interactive Demo Progression Bar */}
        <div className="bg-[#0b0d13]/90 border border-zinc-800 rounded-2xl p-4 shadow-xl backdrop-blur-sm relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-red-600/15 border border-red-500/30 text-red-500 flex items-center justify-center">
                <BookOpen className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-white uppercase tracking-wider block">
                  Core Loop Progression: Resolve, Retain & Reflect
                </span>
                <span className="text-[11px] text-zinc-400">
                  1. Triage incident ➔ 2. Retain verified solution ➔ 3. Deep systemic reflection & resilience.
                </span>
              </div>
            </div>

            {/* Stepper buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  const stage1 = presets.find((p) => p.id === 'demo_stage1_new_incident');
                  if (stage1) {
                    setActiveIncident(stage1.incident);
                    setDemoStep(1);
                    handleSubmitIncident(stage1.incident, 'analyze');
                  }
                }}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all cursor-pointer ${
                  demoStep === 1
                    ? 'bg-red-900 text-white border-red-700 shadow-md shadow-red-950/50'
                    : 'bg-[#141822] text-zinc-300 border-zinc-700 hover:bg-[#1c2230]'
                }`}
              >
                1. New Incident (Cold Start)
              </button>

              <ArrowRight className="w-3.5 h-3.5 text-zinc-600 hidden sm:block" />

              <button
                onClick={() => {
                  if (analysisResult) {
                    setIsResolveOpen(true);
                  }
                }}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all cursor-pointer ${
                  demoStep === 2
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/25'
                    : 'bg-[#141822] text-zinc-300 border-zinc-700 hover:bg-[#1c2230]'
                }`}
              >
                2. Resolve & Retain
              </button>

              <ArrowRight className="w-3.5 h-3.5 text-zinc-600 hidden sm:block" />

              <button
                onClick={handleReflectStep}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                  demoStep === 3 || activeView === 'reflect'
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/25'
                    : 'bg-[#141822] text-zinc-300 border-zinc-700 hover:bg-[#1c2230]'
                }`}
              >
                <Brain className="w-3.5 h-3.5 text-white" />
                <span>3. Reflect & Prevent</span>
              </button>
            </div>
          </div>
        </div>

        {/* Incident Input Form */}
        <IncidentInputForm
          presets={presets}
          onSubmit={handleSubmitIncident}
          isLoading={isLoading}
          activeMode={loadingMode}
        />



        {/* Active View Display */}
        {activeView === 'recommendation' && analysisResult && activeIncident && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
            <RecommendationView
              recommendation={analysisResult.recommendation}
              incident={activeIncident}
              onOpenResolve={() => setIsResolveOpen(true)}
            />
            <HindsightRecallView
              memories={analysisResult.recalled_memories}
              hindsightAvailable={analysisResult.hindsight_available}
              hindsightMessage={analysisResult.hindsight_message}
              bankId={health?.bank_id || 'oncall-memory'}
            />
          </div>
        )}

        {activeView === 'comparison' && comparisonResult && (
          <ComparisonView
            comparison={comparisonResult}
            onOpenResolve={() => setIsResolveOpen(true)}
          />
        )}

        {activeView === 'reflect' && reflectResult && activeIncident && (
          <ReflectView
            reflectData={reflectResult}
            incident={activeIncident}
            onOpenResolve={() => setIsResolveOpen(true)}
          />
        )}
      </main>

      {/* Resolve Incident & Retain Modal */}
      <ResolveModal
        isOpen={isResolveOpen}
        onClose={() => setIsResolveOpen(false)}
        incident={activeIncident}
        onResolve={handleResolve}
        isSubmitting={isSubmittingResolution}
        onLoadStep2Preset={handleLoadStep2Preset}
      />
    </div>
  );
};

export default App;
