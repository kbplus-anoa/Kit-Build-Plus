/** 由后端 openapi.json 手工对应生成；改后端 schemas 时须同步本文件。 */
export interface HealthOut {
  ok: boolean;
  tables: number;
}

export interface UploadOut {
  material_id: number;
  file_name: string;
  ext: string;
  source: string;
  chars: number;
  has_ocr: boolean;
  page_count: number;
  text: string;
}

export interface MaterialOut {
  material_id: number;
  file_name: string;
  ext: string;
  chars: number;
  created_at: string;
}

export interface MaterialsOut {
  items: MaterialOut[];
}

export interface MaterialTextOut {
  material_id: number;
  file_name: string;
  ext: string;
  chars: number;
  text: string;
}

export interface ConfigIn {
  provider: string;
  model: string;
  base_url: string;
  timeout_s: number;
  max_chars: number;
  enabled: boolean;
}

export interface ConfigOut extends ConfigIn {
  has_key: boolean;
  key_env: string;
  error: string;
}

export interface VocabIn {
  vocab_id: string;
  version: string;
  connections: string[];
}

export interface KitAutoIn {
  material_id: number;
  text: string;
  vocab: VocabIn;
  map_version?: string;
  retry?: boolean;
}

export interface ConceptOut {
  concept_id: string;
  label: string;
}

export interface SignalOut {
  name: string;
  label: string;
  value: number | null;
  threshold: number | null;
  triggered: boolean;
}

export interface KitAutoOut {
  map_version: string;
  concepts: ConceptOut[];
  connections: string[];
  total_propositions: number;
  fingerprint: string;
  from_bank: boolean;
  possibly_inaccurate: boolean;
  message: string;
  signals: SignalOut[];
  calibrated: boolean;
  baseline_n: number;
  baseline_source: string;
}

export interface PropositionIn {
  head_id: string;
  connection: string;
  tail_id: string;
}

export interface SubmitIn {
  batch_id?: string;
  map_version: string;
  mode: "study" | "test";
  condition: "exp" | "con";
  is_practice?: number;
  possibly_inaccurate?: number;
  participant_id: number;
  material_id: number;
  time_point: string;
  propositions: PropositionIn[];
}

export interface ErrorChain {
  kind: string;
  head_id: string;
  connection: string;
  tail_id: string;
}

export interface SubmitOut {
  submit_seq: number;
  fingerprint: string;
  fms: number;
  total_propositions: number;
  correct_propositions: number;
  lacking: number;
  excessive: number;
  leaving: number;
  reversed: number;
  errors: ErrorChain[];
  target_propositions: PropositionIn[];
}
