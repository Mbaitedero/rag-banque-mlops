export type UserRole = "agent" | "conformite";

export type AccessLevel = "public" | "conformite";

export type RefusalReason =
  | "retrieval_insuffisant"
  | "refus_modele"
  | "acces_refuse"
  | "erreur";

export interface ChatReference {
  n: number;
  doc_id: string;
  title: string;
  version: string;
  page: number;
  access_level: AccessLevel;
  excerpt: string;
}

export interface ChatRequest {
  question: string;
  role: UserRole;
  conversation_id: string;
}

export interface ChatResponse {
  request_id: string;
  answer: string;
  refused: boolean;
  reason: RefusalReason | null;
  references: ChatReference[];
  latency_ms: number;
}

export interface FeedbackRequest {
  request_id: string;
  rating: "up" | "down";
  comment?: string;
}

export type ChatStreamEvent =
  | { type: "token"; token: string }
  | { type: "sources"; references: ChatReference[] }
  | { type: "done"; response: ChatResponse };

export type ChatStreamListener = (event: ChatStreamEvent) => void;
