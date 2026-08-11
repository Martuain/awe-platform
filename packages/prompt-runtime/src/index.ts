export interface PromptTemplate {
  id: string;
  version: string;
  system: string;
  userTemplate: string;
}

export interface ModelRequest {
  model: string;
  messages: Array<{ role: "system" | "user" | "assistant"; content: string }>;
  temperature?: number;
}

export interface ModelGateway {
  complete(request: ModelRequest): Promise<string>;
}
