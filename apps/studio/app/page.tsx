"use client";

import { FormEvent, useEffect, useState } from "react";

type DiscoveryStatus = "collecting" | "awaiting_approval" | "approved";

type KnowledgeField = {
  value: string | null;
  confidence: number;
};

type DiscoveryContext = {
  project_id: string;
  session_id: string;
  version: number;
  status: DiscoveryStatus;
  knowledge: {
    business_name: KnowledgeField;
    industry: KnowledgeField;
    goals: KnowledgeField[];
    audience: KnowledgeField[];
    value_proposition: KnowledgeField;
  };
  source_messages: string[];
  completeness_score: number;
  open_questions: string[];
  approved_at: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export default function Home() {
  const [projectName, setProjectName] = useState("Demo website project");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [context, setContext] = useState<DiscoveryContext | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedProjectId = window.localStorage.getItem("awe.projectId");
    if (!savedProjectId) return;

    setProjectId(savedProjectId);
    api<DiscoveryContext>(`/api/v1/business-discovery/context/${savedProjectId}`)
      .then(setContext)
      .catch(() => window.localStorage.removeItem("awe.projectId"));
  }, []);

  async function createProject(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const project = await api<{ id: string }>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({ name: projectName }),
      });
      const discovery = await api<DiscoveryContext>(
        `/api/v1/business-discovery/start?project_id=${project.id}`,
        { method: "POST" },
      );
      window.localStorage.setItem("awe.projectId", project.id);
      setProjectId(project.id);
      setContext(discovery);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!projectId || !message.trim() || context?.status === "approved") return;

    setBusy(true);
    setError(null);
    try {
      const next = await api<DiscoveryContext>("/api/v1/business-discovery/message", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, message: message.trim() }),
      });
      setContext(next);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send message");
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    if (!projectId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api<{ context: DiscoveryContext }>(
        `/api/v1/business-discovery/approve/${projectId}`,
        { method: "POST" },
      );
      setContext(result.context);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve discovery");
    } finally {
      setBusy(false);
    }
  }

  if (!projectId || !context) {
    return (
      <main className="shell">
        <div className="eyebrow">AWE Studio · Genesis 0.1.0</div>
        <h1>Understand the business before building the website.</h1>
        <p className="lede">
          Start a project and let AWE progressively structure the business knowledge
          that will drive every downstream website capability.
        </p>
        <form className="card" onSubmit={createProject}>
          <label htmlFor="project-name">Project name</label>
          <input
            id="project-name"
            value={projectName}
            onChange={(event) => setProjectName(event.target.value)}
            maxLength={120}
            required
          />
          <button disabled={busy}>{busy ? "Starting…" : "Start Business Discovery"}</button>
          {error && <p className="error">{error}</p>}
        </form>
        <style>{styles}</style>
      </main>
    );
  }

  const knowledge = context.knowledge;
  const completeness = Math.round(context.completeness_score * 100);
  const locked = context.status === "approved";

  return (
    <main className="shell">
      <header className="header">
        <div>
          <div className="eyebrow">AWE Studio · Business Discovery</div>
          <h1>Build understanding first.</h1>
        </div>
        <div className={`status status-${context.status}`}>
          {context.status.replace("_", " ")}
        </div>
      </header>

      <section className="grid">
        <div className="card conversation">
          <div className="card-title">
            <div>
              <h2>Discovery conversation</h2>
              <p>AWE captures structured knowledge from what you tell it.</p>
            </div>
            <span>{completeness}% complete</span>
          </div>

          <div className="messages">
            {context.source_messages.length === 0 ? (
              <p className="muted">Tell AWE about the business, what it does and what the website needs to achieve.</p>
            ) : (
              context.source_messages.map((item, index) => (
                <div className="message" key={`${item}-${index}`}>{item}</div>
              ))
            )}
          </div>

          {!locked && context.status !== "awaiting_approval" && (
            <form className="composer" onSubmit={sendMessage}>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="e.g. We are a marketing agency called Northstar. Our main goal is to generate qualified leads."
                rows={4}
                maxLength={10000}
              />
              <button disabled={busy || !message.trim()}>{busy ? "Processing…" : "Add to discovery"}</button>
            </form>
          )}

          {context.status === "awaiting_approval" && (
            <div className="approval">
              <div>
                <strong>Discovery is ready for review.</strong>
                <p>Review the structured knowledge on the right before approving it for downstream capabilities.</p>
              </div>
              <button onClick={approve} disabled={busy}>{busy ? "Approving…" : "Approve Discovery"}</button>
            </div>
          )}

          {locked && <div className="approved">Approved context is immutable. Downstream capabilities can now consume it.</div>}
          {error && <p className="error">{error}</p>}
        </div>

        <aside className="card knowledge">
          <div className="card-title">
            <div>
              <h2>Business knowledge</h2>
              <p>Structured context extracted from the conversation.</p>
            </div>
          </div>

          <Field label="Business name" value={knowledge.business_name.value} />
          <Field label="Industry" value={knowledge.industry.value} />
          <Field label="Goals" value={knowledge.goals.map((goal) => goal.value).filter(Boolean).join(", ")} />
          <Field label="Audience" value={knowledge.audience.map((item) => item.value).filter(Boolean).join(", ")} />
          <Field label="Value proposition" value={knowledge.value_proposition.value} />

          {context.open_questions.length > 0 && (
            <div className="questions">
              <span>Open question</span>
              {context.open_questions.map((question) => <p key={question}>{question}</p>)}
            </div>
          )}
        </aside>
      </section>
      <style>{styles}</style>
    </main>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="field">
      <span>{label}</span>
      <strong className={value ? "filled" : "empty"}>{value || "Not captured yet"}</strong>
    </div>
  );
}

const styles = `
  * { box-sizing: border-box; }
  body { margin: 0; background: #f7f7f4; color: #161616; font-family: Arial, Helvetica, sans-serif; }
  button, input, textarea { font: inherit; }
  .shell { max-width: 1180px; margin: 0 auto; padding: 56px 24px 80px; }
  .eyebrow { font-size: 11px; letter-spacing: .16em; text-transform: uppercase; color: #666; }
  h1 { max-width: 820px; margin: 18px 0 12px; font-size: clamp(38px, 6vw, 68px); line-height: .98; letter-spacing: -.045em; }
  .lede { max-width: 720px; margin: 0 0 36px; color: #555; font-size: 19px; line-height: 1.55; }
  .header { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 36px; }
  .header h1 { margin-bottom: 0; font-size: clamp(34px, 5vw, 56px); }
  .status { padding: 9px 12px; border-radius: 999px; background: #e7e7e2; font-size: 12px; text-transform: capitalize; white-space: nowrap; }
  .status-awaiting_approval { background: #eee7cf; }
  .status-approved { background: #dce9df; }
  .grid { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(300px, .8fr); gap: 20px; }
  .card { background: white; border: 1px solid #deded8; border-radius: 18px; padding: 24px; box-shadow: 0 8px 30px rgba(0,0,0,.035); }
  .card-title { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 22px; }
  h2 { margin: 0 0 5px; font-size: 18px; }
  .card-title p { margin: 0; color: #777; font-size: 13px; line-height: 1.45; }
  .card-title > span { color: #666; font-size: 12px; white-space: nowrap; }
  .messages { min-height: 180px; display: flex; flex-direction: column; gap: 10px; padding: 4px 0 20px; }
  .message { align-self: flex-end; max-width: 86%; padding: 12px 14px; border-radius: 14px 14px 4px 14px; background: #161616; color: white; line-height: 1.5; font-size: 14px; }
  .muted { color: #888; line-height: 1.6; font-size: 14px; }
  .composer textarea { width: 100%; resize: vertical; min-height: 110px; padding: 13px; border: 1px solid #d4d4ce; border-radius: 12px; outline: none; }
  .composer textarea:focus, input:focus { border-color: #555; }
  button { border: 0; border-radius: 10px; background: #161616; color: white; padding: 12px 16px; cursor: pointer; }
  button:disabled { opacity: .45; cursor: not-allowed; }
  .composer button { margin-top: 10px; }
  .approval { display: flex; justify-content: space-between; gap: 18px; align-items: center; padding-top: 18px; border-top: 1px solid #eee; }
  .approval p { margin: 5px 0 0; color: #777; font-size: 13px; line-height: 1.5; }
  .approved { margin-top: 16px; padding: 12px; border-radius: 10px; background: #edf4ee; color: #35563d; font-size: 13px; }
  .field { padding: 15px 0; border-top: 1px solid #eee; }
  .field span { display: block; color: #777; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
  .field strong { font-size: 14px; line-height: 1.45; }
  .empty { color: #aaa; font-weight: 400; }
  .questions { margin-top: 18px; padding: 14px; background: #f7f4e9; border-radius: 12px; }
  .questions span { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: #806f35; }
  .questions p { margin: 7px 0 0; font-size: 13px; line-height: 1.45; }
  .error { color: #a52b2b; font-size: 13px; margin-bottom: 0; }
  label { display: block; margin-bottom: 8px; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: #666; }
  input { width: 100%; padding: 13px; border: 1px solid #d4d4ce; border-radius: 10px; margin-bottom: 12px; outline: none; }
  @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } .header { align-items: flex-start; flex-direction: column; } .approval { align-items: flex-start; flex-direction: column; } }
`;
