export type CapabilityStatus =
  | "draft"
  | "running"
  | "awaiting_approval"
  | "approved"
  | "completed"
  | "failed";

export interface CapabilityContext {
  projectId: string;
  knowledge: Record<string, unknown>;
  constraints: Record<string, unknown>;
  history: Array<Record<string, unknown>>;
}

export interface Capability {
  id: string;
  version: string;
  discover(ctx: CapabilityContext): Promise<unknown>;
  prepare(ctx: CapabilityContext): Promise<unknown>;
  plan(ctx: CapabilityContext): Promise<unknown>;
  execute(ctx: CapabilityContext): Promise<unknown>;
  evaluate(ctx: CapabilityContext, output: unknown): Promise<unknown>;
}
