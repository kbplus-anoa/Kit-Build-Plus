/** 由后端 openapi.json 手工对应生成；改后端 schemas 时须同步本文件。 */

export type TextSource = "TEXT_LAYER" | "EPUB" | "OCR_CLOUD";
export type Mode = "test" | "study";
export type TimePoint = "pre" | "post" | "delayed";
export type Decision = "accepted" | "rejected";
export type ErrorKind = "lacking" | "excessive" | "leaving" | "reversed";
export type LockState = "locked" | "mutable";

export interface VocabIn {
  vocab_id: string;
  version: string;
  connections: string[];
}

export interface IngestIn {
  path: string;
}

export interface IngestOut {
  file_name: string;
  source: TextSource;
  has_ocr: boolean;
  page_count: number;
  chars: number;
}

export interface ExtractIn {
  text: string;
  vocab: VocabIn;
}

export interface TripleOut {
  head: string;
  connection: string;
  tail: string;
  confidence: number;
}

export interface ExtractOut {
  vocab_id: string;
  vocab_version: string;
  count: number;
  triples: TripleOut[];
}

export interface AdjudicationIn {
  head: string;
  connection: string;
  tail: string;
  confidence: number;
  decision: Decision;
  reason?: string;
}

export interface BatchIn {
  batch_id: string;
  vocab: VocabIn;
  items: AdjudicationIn[];
}

export interface BatchOut {
  batch_id: string;
  saved: number;
}

export interface BuildKitIn {
  batch_id: string;
  map_version: string;
}

export interface ConceptOut {
  concept_id: string;
  label: string;
}

export interface KitOut {
  map_version: string;
  concepts: ConceptOut[];
  connections: string[];
  total_propositions: number;
}

export interface ReadyOut {
  map_version: string;
  locked: LockState;
}

export interface Vec2In {
  head_id: string;
  connection: string;
  tail_id: string;
}

export interface SubmitIn {
  batch_id: string;
  map_version: string;
  mode: Mode;
  participant_id: number;
  material_id: number;
  session: number;
  propositions: Vec2In[];
}

export interface ErrorOut {
  kind: ErrorKind;
  head_id: string;
  connection: string;
  tail_id: string;
}

export interface ScoreOut {
  total_propositions: number;
  correct_propositions: number;
  score: number;
  lacking: number;
  excessive: number;
  leaving: number;
  reversed: number;
  errors: ErrorOut[];
}

export interface AnswerIn {
  question_id: string;
  choice_index: number;
}

export interface QuestionIn {
  question_id: string;
  stem: string;
  choices: string[];
  answer_index: number;
  qtype: string;
  content_dimension?: string;
}

export interface QuizIn {
  quiz_id: string;
  participant_id: number;
  material_id: number;
  session: number;
  time_point: TimePoint;
  questions: QuestionIn[];
  answers: AnswerIn[];
}

export interface QuizOut {
  quiz_id: string;
  time_point: TimePoint;
  percent: number;
  answered: number;
}

export interface SubjectRowIn {
  participant_id: number;
  material_id: number;
  target_map_version: string;
  session: number;
  mode: Mode;
  condition: "exp" | "con";
  is_practice: 0 | 1;
  correct_propositions: number;
  total_propositions: number;
  n_lacking: number;
  n_excessive: number;
  n_leaving: number;
  n_reversed: number;
  possibly_inaccurate: 0 | 1;
  map_size: number;
  map_node_count: number;
  signal_isolated?: number | null;
  signal_coverage?: number | null;
  signal_concentration?: number | null;
  signal_baseline?: number | null;
}

export interface QuestionRowIn {
  participant_id: number;
  material_id: number;
  target_map_version: string;
  session: number;
  question_id: string;
  time_point: TimePoint;
  correct: 0 | 1;
  score?: number | null;
  qtype: string;
  content_dimension?: string;
}

export interface HealthOut {
  ok: boolean;
  tables: number;
}
