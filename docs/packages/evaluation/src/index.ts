export interface EvaluationResult {
  evaluatorId: string;
  passed: boolean;
  score: number;
  findings: string[];
}

export function passesApprovalGate(results: EvaluationResult[]): boolean {
  return results.length > 0 && results.every((r) => r.passed);
}
