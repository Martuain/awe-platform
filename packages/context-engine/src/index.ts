export interface AWEContext {
  project: { id: string; name?: string };
  business: Record<string, unknown>;
  brand: Record<string, unknown>;
  goals: string[];
  audience: string[];
  knowledge: Record<string, unknown>;
  constraints: Record<string, unknown>;
  history: Array<Record<string, unknown>>;
  currentCapability?: string;
}

export function createContext(projectId: string): AWEContext {
  return {
    project: { id: projectId },
    business: {},
    brand: {},
    goals: [],
    audience: [],
    knowledge: {},
    constraints: {},
    history: []
  };
}
