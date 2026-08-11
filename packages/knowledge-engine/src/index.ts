export type KnowledgeConfidence = "low" | "medium" | "high";

export interface KnowledgeFact {
  id: string;
  subject: string;
  predicate: string;
  object: string;
  confidence: KnowledgeConfidence;
  sources: string[];
}

export interface KnowledgeDocument {
  projectId: string;
  version: number;
  facts: KnowledgeFact[];
}
