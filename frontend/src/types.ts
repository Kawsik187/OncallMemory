export interface IncidentInput {
  title: string;
  service: string;
  description: string;
  symptoms: string;
  error_logs: string;
}

export interface RecalledMemoryItem {
  id?: string;
  text: string;
  type?: string;
  score?: number;
  entities?: any[];
  metadata?: Record<string, any>;
  relevance_reason?: string;
  service?: string;
  is_same_service?: boolean;
  outcome?: 'WORKED' | 'FAILED';
  relevance_grade?: 'direct_match' | 'analogy' | 'low';
}

export interface StructuredRecommendation {
  likely_root_cause: string;
  confidence: 'high' | 'medium' | 'low';
  historical_evidence: string[];
  recommended_fix: string;
  citing: string;
  runbook: string[];
}

export interface IncidentResponsePayload {
  incident: IncidentInput;
  recalled_memories: RecalledMemoryItem[];
  recommendation: StructuredRecommendation;
  hindsight_available: boolean;
  hindsight_message?: string;
  model_used: string;
}

export interface ComparisonResponse {
  incident: IncidentInput;
  with_memory: StructuredRecommendation;
  without_memory: StructuredRecommendation;
  recalled_memories: RecalledMemoryItem[];
  hindsight_available: boolean;
  contrast_summary: string;
}

export interface IncidentResolution {
  title: string;
  service: string;
  root_cause: string;
  fix: string;
  outcome: 'WORKED' | 'FAILED';
  date?: string;
}

export interface HealthStatus {
  status: string;
  bank_id: string;
  llm_model: string;
  groq_configured: boolean;
  hindsight_url: string;
  hindsight_connected: boolean;
  hindsight_status: string;
}

export interface PresetItem {
  id: string;
  label: string;
  incident: IncidentInput;
  expected_recall?: string;
  demo_instruction?: string;
  incident_number?: string;
  severity?: 'critical' | 'warning' | 'info';
  source?: string;
  started_ago?: string;
  assigned_to?: string;
  affected_resources?: string[];
  impact?: string;
  status?: 'active' | 'investigating' | 'resolved';
}

export interface ReflectMemoryItem {
  id?: string;
  text: string;
  type?: string;
}

export interface ReflectionAnalysis {
  systemic_root_cause: string;
  pattern_recognition: string;
  recurrent_risk: string;
  architectural_fix: string;
  prevention_runbook: string[];
}

export interface ReflectResponsePayload {
  incident: IncidentInput;
  hindsight_reflection_text?: string;
  based_on_memories: ReflectMemoryItem[];
  reflection: ReflectionAnalysis;
  hindsight_available: boolean;
  hindsight_message?: string;
  model_used: string;
}
