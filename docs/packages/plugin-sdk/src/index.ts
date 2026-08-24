export interface AWEPlugin {
  id: string;
  version: string;
  capabilities: string[];
  initialize(): Promise<void>;
}
