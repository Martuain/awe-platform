"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Stage = "discovery" | "strategy" | "design" | "specification" | "generation" | "preview";
type Project = { id: string; name: string };
type DiscoveryContext = {
  status: "collecting" | "awaiting_approval" | "approved";
  version: number;
  completeness_score: number;
  open_questions: string[];
  source_messages: string[];
  knowledge: {
    business_name: { value?: string | null };
    industry: { value?: string | null };
    goals: { value?: string | null }[];
    audience: { value?: string | null }[];
    value_proposition: { value?: string | null };
  };
};
type Strategy = {
  version: number;
  status: "draft" | "ready_for_review" | "approved";
  sitemap: { path: string; name: string; objective: string; primary_cta?: string | null }[];
  content: { positioning: string; key_messages: string[]; tone: string[]; primary_cta?: string | null };
  design: { visual_principles: string[]; layout_principles: string[]; accessibility_priority: string; responsive_priority: string };
  rationale: string[];
  evaluation: { completeness: number; business_alignment: number; traceability: number; actionability: number; overall: number; findings: string[]; ready: boolean };
};
type DesignDirection = {
  version: number;
  status: "draft" | "ready_for_review" | "approved";
  brand_attributes: string[];
  visual_principles: string[];
  color_palette: { primary: string; secondary: string; accent: string; background: string; text: string };
  typography: { heading_style: string; body_style: string; hierarchy: string };
  imagery_direction: string[];
  component_direction: string[];
  accessibility_requirements: string[];
  rationale: string[];
  source_strategy_version: number;
};

type WebsiteSpecification = {
  version: number;
  status: "draft" | "ready_for_review" | "approved";
  source_strategy_version: number;
  source_design_version: number;
  pages: { path: string; name: string; objective: string; primary_cta?: string | null; required_sections: string[]; content_requirements: string[]; components: string[] }[];
  global_components: string[];
  content_requirements: string[];
  seo_requirements: string[];
  accessibility_requirements: string[];
  responsive_requirements: string[];
  technical_requirements: string[];
  acceptance_criteria: string[];
  rationale: string[];
};

type WebsiteValidation = {
  generation_version: number;
  status: "passed" | "failed";
  checks: Record<string, boolean>;
  diagnostics: string[];
  preview: { format: string; title: string; html: string };
};

type WebsiteGeneration = {
  version: number;
  status: "generated" | "validated" | "failed";
  source_specification_version: number;
  framework: string;
  files: { path: string; content: string }[];
  pages_generated: string[];
  validation: Record<string, boolean | string>;
  rationale: string[];
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function Score({ value }: { value: number }) {
  return <strong>{Math.round(value * 100)}%</strong>;
}

export default function Home() {
  const [project, setProject] = useState<Project | null>(null);
  const [stage, setStage] = useState<Stage>("discovery");
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [context, setContext] = useState<DiscoveryContext | null>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [design, setDesign] = useState<DesignDirection | null>(null);
  const [specification, setSpecification] = useState<WebsiteSpecification | null>(null);
  const [generation, setGeneration] = useState<WebsiteGeneration | null>(null);
  const [validation, setValidation] = useState<WebsiteValidation | null>(null);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = window.localStorage.getItem("awe-project-id");
    if (!saved) return;
    api<Project>(`/api/v1/projects/${saved}`)
      .then(async (p) => {
        setProject(p);
        try {
          const c = await api<DiscoveryContext>(`/api/v1/business-discovery/context/${p.id}`);
          setContext(c);
          if (c.status === "approved") {
            try {
              const s = await api<Strategy>(`/api/v1/website-strategy/${p.id}`);
              setStrategy(s);
              if (s.status === "approved") {
                try {
                  const d = await api<DesignDirection>(`/api/v1/brand-design/${p.id}`);
                  setDesign(d);
                  if (d.status === "approved") {
                    try {
                      const w = await api<WebsiteSpecification>(`/api/v1/website-specification/${p.id}`);
                      setSpecification(w);
                      if (w.status === "approved") {
                        try {
                          const g = await api<WebsiteGeneration>(`/api/v1/website-generation/${p.id}`);
                          setGeneration(g);
                          try {
                            const v = await api<WebsiteValidation>(`/api/v1/website-validation/validate?project_id=${p.id}`, { method: "POST" });
                            setValidation(v);
                            setStage("preview");
                          } catch { setStage("generation"); }
                        } catch { setStage("specification"); }
                      } else { setStage("specification"); }
                    } catch { setStage("design"); }
                  } else { setStage("design"); }
                } catch {
                  setStage("strategy");
                }
              } else {
                setStage("strategy");
              }
            } catch {
              setStage("strategy");
            }
          }
        } catch {
          // Project exists, but discovery has not started yet.
        }
      })
      .catch(() => window.localStorage.removeItem("awe-project-id"));
  }, []);

  const knowledgeSummary = useMemo(() => {
    if (!context) return [];
    return [
      ["Industry", context.knowledge.industry.value],
      ["Goal", context.knowledge.goals.map((g) => g.value).filter(Boolean).join(", ")],
      ["Audience", context.knowledge.audience.map((g) => g.value).filter(Boolean).join(", ")],
      ["Value proposition", context.knowledge.value_proposition.value],
    ].filter(([, value]) => value);
  }, [context]);

  async function createProject(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true); setError("");
    try {
      const p = await api<Project>("/api/v1/projects", { method: "POST", body: JSON.stringify({ name: name.trim() }) });
      await api(`/api/v1/business-discovery/start?project_id=${p.id}`, { method: "POST" });
      const c = await api<DiscoveryContext>(`/api/v1/business-discovery/context/${p.id}`);
      setProject(p); setContext(c); setName("");
      window.localStorage.setItem("awe-project-id", p.id);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to create project"); }
    finally { setBusy(false); }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!project || !message.trim()) return;
    setBusy(true); setError("");
    try {
      const c = await api<DiscoveryContext>("/api/v1/business-discovery/message", {
        method: "POST", body: JSON.stringify({ project_id: project.id, message: message.trim() }),
      });
      setContext(c); setMessage("");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to update discovery"); }
    finally { setBusy(false); }
  }

  async function approveDiscovery() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const result = await api<{ context: DiscoveryContext }>(`/api/v1/business-discovery/approve/${project.id}`, { method: "POST" });
      setContext(result.context); setStage("strategy");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to approve discovery"); }
    finally { setBusy(false); }
  }

  async function generateStrategy() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const s = await api<Strategy>(`/api/v1/website-strategy/generate?project_id=${project.id}`, { method: "POST" });
      setStrategy(s);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to generate strategy"); }
    finally { setBusy(false); }
  }

  async function approveStrategy() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const s = await api<Strategy>(`/api/v1/website-strategy/${project.id}/approve`, { method: "POST" });
      setStrategy(s); setStage("design");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to approve strategy"); }
    finally { setBusy(false); }
  }

  async function generateDesign() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const d = await api<DesignDirection>(`/api/v1/brand-design/generate?project_id=${project.id}`, { method: "POST" });
      setDesign(d);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to generate design direction"); }
    finally { setBusy(false); }
  }

  async function approveDesign() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const d = await api<DesignDirection>(`/api/v1/brand-design/${project.id}/approve`, { method: "POST" });
      setDesign(d);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to approve design direction"); }
    finally { setBusy(false); }
  }

  async function generateSpecification() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const w = await api<WebsiteSpecification>(`/api/v1/website-specification/generate?project_id=${project.id}`, { method: "POST" });
      setSpecification(w); setStage("specification");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to generate Website Specification"); }
    finally { setBusy(false); }
  }

  async function approveSpecification() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const w = await api<WebsiteSpecification>(`/api/v1/website-specification/${project.id}/approve`, { method: "POST" });
      setSpecification(w); setStage("generation");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to approve Website Specification"); }
    finally { setBusy(false); }
  }

  async function generateWebsite() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const g = await api<WebsiteGeneration>(`/api/v1/website-generation/generate?project_id=${project.id}`, { method: "POST" });
      setGeneration(g); setStage("generation");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to generate website"); }
    finally { setBusy(false); }
  }

  async function validateWebsite() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const v = await api<WebsiteValidation>(`/api/v1/website-validation/validate?project_id=${project.id}`, { method: "POST" });
      setValidation(v); setStage("preview");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to validate generated website"); }
    finally { setBusy(false); }
  }

  async function reviseStrategy(event: FormEvent) {
    event.preventDefault();
    if (!project || !feedback.trim()) return;
    setBusy(true); setError("");
    try {
      const s = await api<Strategy>(`/api/v1/website-strategy/${project.id}/revise`, { method: "POST", body: JSON.stringify({ feedback: feedback.trim() }) });
      setStrategy(s); setFeedback("");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to revise strategy"); }
    finally { setBusy(false); }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div><span className="eyebrow">AWE Studio</span><strong>Genesis</strong></div>
        {project && <span className="project-chip">{project.name}</span>}
      </header>

      <section className="hero">
        <span className="eyebrow">AI-native website engineering</span>
        <h1>Turn business knowledge into an engineered digital experience.</h1>
        <p>AWE moves from understanding to strategy, design and eventually implementation — with evaluation and human approval at every important boundary.</p>
      </section>

      <nav className="pipeline" aria-label="AWE capability pipeline">
        {[ ["discovery", "01", "Discovery"], ["strategy", "02", "Strategy"], ["design", "03", "Design"], ["specification", "04", "Website Spec"], ["generation", "05", "Generate"], ["preview", "06", "Preview"] ].map(([key, number, label]) => (
          <button key={key} className={stage === key ? "active" : ""} onClick={() => setStage(key as Stage)} disabled={!project || (key === "strategy" && context?.status !== "approved") || (key === "design" && strategy?.status !== "approved") || (key === "specification" && design?.status !== "approved") || (key === "generation" && specification?.status !== "approved") || (key === "preview" && !generation)}>
            <span>{number}</span>{label}
          </button>
        ))}
      </nav>

      {error && <div className="error">{error}</div>}

      {!project ? (
        <section className="card create-card">
          <div><span className="eyebrow">Start a project</span><h2>What are we building?</h2><p>Create a project and AWE will begin with Business Discovery.</p></div>
          <form onSubmit={createProject} className="inline-form">
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Acme Architecture Studio" maxLength={120} />
            <button className="primary" disabled={busy || !name.trim()}>{busy ? "Starting…" : "Start with AWE"}</button>
          </form>
        </section>
      ) : stage === "discovery" ? (
        <section className="grid">
          <div className="card conversation">
            <div className="section-heading"><div><span className="eyebrow">CAP-001</span><h2>Business Discovery</h2></div><span className={`status ${context?.status}`}>{context?.status?.replace("_", " ")}</span></div>
            <div className="messages">
              {(context?.source_messages || []).map((item, i) => <div className="message user" key={`${item}-${i}`}>{item}</div>)}
              {context?.open_questions?.map((item, i) => <div className="message awe" key={`${item}-${i}`}>AWE needs to know: {item}</div>)}
              {!context?.source_messages.length && <div className="empty">Tell AWE about the business, its market and what the website needs to achieve.</div>}
            </div>
            {context?.status !== "approved" && <form onSubmit={sendMessage} className="composer"><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Tell AWE what matters about the business…" rows={4} /><button className="primary" disabled={busy || !message.trim()}>{busy ? "Thinking…" : "Continue discovery"}</button></form>}
            {context?.status === "awaiting_approval" && <button className="approve" onClick={approveDiscovery} disabled={busy}>{busy ? "Approving…" : "Approve Business Discovery"}</button>}
          </div>
          <aside className="card side-panel"><span className="eyebrow">Knowledge captured</span><div className="score"><Score value={context?.completeness_score || 0} /><span>completeness</span></div>{knowledgeSummary.map(([key, value]) => <div className="fact" key={key}><small>{key}</small><p>{value}</p></div>)}{context?.open_questions?.length ? <div className="finding"><strong>Still needed</strong><ul>{context.open_questions.map((q) => <li key={q}>{q}</li>)}</ul></div> : null}</aside>
        </section>
      ) : stage === "strategy" ? (
        <section className="card strategy">
          <div className="section-heading"><div><span className="eyebrow">CAP-002</span><h2>Website Strategy</h2><p>Derived from the approved Business Discovery context.</p></div>{strategy && <span className={`status ${strategy.status}`}>{strategy.status.replaceAll("_", " ")}</span>}</div>
          {!strategy ? <div className="empty large"><p>AWE is ready to turn the approved business context into a website strategy.</p><button className="primary" onClick={generateStrategy} disabled={busy}>{busy ? "Generating…" : "Generate Strategy"}</button></div> : <>
            <div className="metrics">{[["Overall", strategy.evaluation.overall], ["Completeness", strategy.evaluation.completeness], ["Alignment", strategy.evaluation.business_alignment], ["Traceability", strategy.evaluation.traceability], ["Actionability", strategy.evaluation.actionability]].map(([label, value]) => <div key={label as string}><small>{label}</small><Score value={value as number} /></div>)}</div>
            <div className="strategy-grid"><div><h3>Positioning</h3><p>{strategy.content.positioning}</p><h3>Key messages</h3><ul>{strategy.content.key_messages.map((x) => <li key={x}>{x}</li>)}</ul><h3>Tone</h3><div className="tags">{strategy.content.tone.map((x) => <span key={x}>{x}</span>)}</div></div><div><h3>Information architecture</h3><div className="pages">{strategy.sitemap.map((page) => <div key={page.path}><strong>{page.name}</strong><code>{page.path}</code><p>{page.objective}</p></div>)}</div></div></div>
            {strategy.evaluation.findings.length > 0 && <div className="finding"><strong>Evaluation findings</strong><ul>{strategy.evaluation.findings.map((x) => <li key={x}>{x}</li>)}</ul></div>}
            {strategy.status !== "approved" && <div className="actions"><form onSubmit={reviseStrategy} className="inline-form"><input value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="Request a strategic change, e.g. CTA: Book a consultation" /><button disabled={busy || !feedback.trim()}>Revise</button></form>{strategy.evaluation.ready && <button className="approve" onClick={approveStrategy} disabled={busy}>{busy ? "Approving…" : "Approve Strategy"}</button>}</div>}
          </>}
        </section>
      ) : stage === "design" ? (
        <section className="card design">
          <div className="section-heading"><div><span className="eyebrow">CAP-003</span><h2>Brand & Design Direction</h2><p>Derived from the approved Website Strategy. This is the visual and interaction brief AWE will use before composing the website.</p></div>{design && <span className={`status ${design.status}`}>{design.status.replaceAll("_", " ")}</span>}</div>
          {!design ? <div className="empty large"><p>AWE is ready to translate the approved strategy into a reviewable design direction.</p><button className="primary" onClick={generateDesign} disabled={busy}>{busy ? "Generating…" : "Generate Design Direction"}</button></div> : <>
            <div className="design-summary">
              <div><small>Source strategy</small><strong>v{design.source_strategy_version}</strong></div>
              <div><small>Brand attributes</small><div className="tags">{design.brand_attributes.map((x) => <span key={x}>{x}</span>)}</div></div>
              <div><small>Accessibility</small><strong>Required</strong></div>
              <div><small>Responsive</small><strong>First-class</strong></div>
            </div>
            <div className="design-grid">
              <div>
                <h3>Visual principles</h3><ul>{design.visual_principles.map((x) => <li key={x}>{x}</li>)}</ul>
                <h3>Color direction</h3><div className="palette">{Object.entries(design.color_palette).map(([name, value]) => <div key={name}><span></span><small>{name}</small><strong>{value}</strong></div>)}</div>
                <h3>Typography</h3><div className="fact"><small>Headings</small><p>{design.typography.heading_style}</p></div><div className="fact"><small>Body</small><p>{design.typography.body_style}</p></div><div className="fact"><small>Hierarchy</small><p>{design.typography.hierarchy}</p></div>
              </div>
              <div>
                <h3>Imagery direction</h3><ul>{design.imagery_direction.map((x) => <li key={x}>{x}</li>)}</ul>
                <h3>Component direction</h3><ul>{design.component_direction.map((x) => <li key={x}>{x}</li>)}</ul>
                <h3>Accessibility requirements</h3><ul>{design.accessibility_requirements.map((x) => <li key={x}>{x}</li>)}</ul>
              </div>
            </div>
            <div className="finding"><strong>Why AWE chose this direction</strong><ul>{design.rationale.map((x) => <li key={x}>{x}</li>)}</ul></div>
            {design.status !== "approved" && <div className="actions"><button className="secondary" onClick={() => setStage("strategy")}>Back to Strategy</button><button className="approve" onClick={approveDesign} disabled={busy}>{busy ? "Approving…" : "Approve Design Direction"}</button></div>}
          </>}
        </section>
      ) : stage === "specification" ? (
        <section className="card specification">
          <div className="section-heading"><div><span className="eyebrow">CAP-004</span><h2>Website Specification</h2><p>Implementation-ready instructions derived from the approved Strategy and Brand & Design Direction.</p></div>{specification && <span className={`status ${specification.status}`}>{specification.status.replaceAll("_", " ")}</span>}</div>
          {!specification ? <div className="empty large"><p>AWE is ready to translate the approved strategy and design into an implementation specification.</p><button className="primary" onClick={generateSpecification} disabled={busy}>{busy ? "Generating…" : "Generate Website Specification"}</button></div> : <>
            <div className="design-summary">
              <div><small>Strategy source</small><strong>v{specification.source_strategy_version}</strong></div>
              <div><small>Design source</small><strong>v{specification.source_design_version}</strong></div>
              <div><small>Pages</small><strong>{specification.pages.length}</strong></div>
              <div><small>Generation ready</small><strong>{specification.status === "approved" ? "Yes" : "Review"}</strong></div>
            </div>
            <div className="spec-pages">{specification.pages.map((page) => <article key={page.path} className="spec-page"><div><strong>{page.name}</strong><code>{page.path}</code></div><p>{page.objective}</p><div className="spec-columns"><div><small>Sections</small><ul>{page.required_sections.map((x) => <li key={x}>{x}</li>)}</ul></div><div><small>Components</small><ul>{page.components.map((x) => <li key={x}>{x}</li>)}</ul></div><div><small>Content</small><ul>{page.content_requirements.map((x) => <li key={x}>{x}</li>)}</ul></div></div></article>)}</div>
            <div className="strategy-grid"><div><h3>Global components</h3><ul>{specification.global_components.map((x) => <li key={x}>{x}</li>)}</ul><h3>SEO</h3><ul>{specification.seo_requirements.map((x) => <li key={x}>{x}</li>)}</ul><h3>Accessibility</h3><ul>{specification.accessibility_requirements.map((x) => <li key={x}>{x}</li>)}</ul></div><div><h3>Responsive requirements</h3><ul>{specification.responsive_requirements.map((x) => <li key={x}>{x}</li>)}</ul><h3>Technical requirements</h3><ul>{specification.technical_requirements.map((x) => <li key={x}>{x}</li>)}</ul><h3>Acceptance criteria</h3><ul>{specification.acceptance_criteria.map((x) => <li key={x}>{x}</li>)}</ul></div></div>
            <div className="finding"><strong>Why AWE chose this specification</strong><ul>{specification.rationale.map((x) => <li key={x}>{x}</li>)}</ul></div>
            {specification.status !== "approved" && <div className="actions"><button className="secondary" onClick={() => setStage("design")}>Back to Design</button><button className="approve" onClick={approveSpecification} disabled={busy}>{busy ? "Approving…" : "Approve Website Specification"}</button></div>}
          </>}
        </section>

      ) : stage === "generation" ? (
        <section className="card generation">
          <div className="section-heading"><div><span className="eyebrow">CAP-005</span><h2>Website Generation</h2><p>Turn the approved Website Specification into a deterministic Next.js App Router website artifact.</p></div>{generation && <span className={`status ${generation.status}`}>{generation.status}</span>}</div>
          {!generation ? <div className="empty large"><p>The Website Specification is approved. AWE can now generate the first runnable website artifact.</p><button className="primary" onClick={generateWebsite} disabled={busy}>{busy ? "Generating…" : "Generate Website"}</button></div> : <>
            <div className="design-summary"><div><small>Specification source</small><strong>v{generation.source_specification_version}</strong></div><div><small>Framework</small><strong>{generation.framework}</strong></div><div><small>Pages generated</small><strong>{generation.pages_generated.length}</strong></div><div><small>Validation</small><strong>{validation?.status || "Pending"}</strong></div></div>
            <div className="strategy-grid"><div><h3>Generated pages</h3><ul>{generation.pages_generated.map((x) => <li key={x}><code>{x}</code></li>)}</ul><h3>Generation checks</h3><ul>{Object.entries(generation.validation).map(([key, value]) => <li key={key}>{key}: <strong>{String(value)}</strong></li>)}</ul></div><div><h3>Generated files</h3><div className="spec-pages">{generation.files.map((file) => <article className="spec-page" key={file.path}><div><strong>{file.path}</strong><code>{file.content.length} chars</code></div></article>)}</div></div></div>
            <div className="finding"><strong>Generation principles</strong><ul>{generation.rationale.map((x) => <li key={x}>{x}</li>)}</ul></div>
            <div className="actions"><button className="secondary" onClick={() => setStage("specification")}>Back to Website Spec</button><button className="approve" onClick={validateWebsite} disabled={busy}>{busy ? "Validating…" : "Validate & Preview"}</button></div>
          </>}
        </section>
      ) : (
        <section className="card preview">
          <div className="section-heading"><div><span className="eyebrow">CAP-006</span><h2>Preview & Validation</h2><p>Validate the generated project artifact and inspect a safe browser preview before moving toward deployable execution.</p></div>{validation && <span className={`status ${validation.status}`}>{validation.status}</span>}</div>
          {!validation ? <div className="empty large"><p>Run validation to produce the CAP-006 preview.</p><button className="primary" onClick={validateWebsite} disabled={busy}>{busy ? "Validating…" : "Validate Website"}</button></div> : <>
            <div className="design-summary"><div><small>Generation</small><strong>v{validation.generation_version}</strong></div><div><small>Validation</small><strong>{validation.status}</strong></div><div><small>Checks</small><strong>{Object.values(validation.checks).filter(Boolean).length}/{Object.keys(validation.checks).length}</strong></div><div><small>Preview</small><strong>{validation.preview.format.toUpperCase()}</strong></div></div>
            <div className="strategy-grid"><div><h3>Validation checks</h3><ul>{Object.entries(validation.checks).map(([key, value]) => <li key={key}>{key}: <strong>{value ? "PASS" : "FAIL"}</strong></li>)}</ul>{validation.diagnostics.length > 0 && <><h3>Diagnostics</h3><ul>{validation.diagnostics.map((x) => <li key={x}>{x}</li>)}</ul></>}</div><div><h3>Browser preview</h3><iframe title="AWE generated website preview" srcDoc={validation.preview.html} style={{width:"100%",height:520,border:"1px solid #ddd",borderRadius:12,background:"white"}} /></div></div>
            <div className="finding"><strong>CAP-006 boundary</strong><p>This preview is rendered from the generated artifact and validation metadata. It does not execute arbitrary generated code inside Studio.</p></div>
            <div className="actions"><button className="secondary" onClick={() => setStage("generation")}>Back to Generation</button><button className="approve" onClick={validateWebsite} disabled={busy}>{busy ? "Revalidating…" : "Revalidate"}</button></div>
          </>}
        </section>
      )}

      <footer>AWE · Capability-driven · API-first · Human approval by design</footer>
      <style jsx global>{`
        :root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f7f7f4;color:#151515;font-family:Arial,Helvetica,sans-serif}.shell{max-width:1180px;margin:0 auto;padding:28px 28px 64px}.topbar{display:flex;justify-content:space-between;align-items:center;padding-bottom:28px;border-bottom:1px solid #ddd}.topbar>div{display:flex;gap:10px;align-items:center}.project-chip,.status,.tags span{border:1px solid #d7d7d2;border-radius:999px;padding:7px 12px;font-size:12px;background:#fff}.hero{padding:70px 0 45px;max-width:850px}.eyebrow{font-size:11px;letter-spacing:1.8px;text-transform:uppercase;color:#6a6a64}.hero h1{font-size:clamp(42px,7vw,76px);line-height:.98;letter-spacing:-3px;margin:18px 0}.hero p{font-size:18px;line-height:1.65;color:#555;max-width:720px}.pipeline{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:10px 0 24px}.pipeline button{border:1px solid #ddd;background:#fff;padding:16px;text-align:left;border-radius:12px;cursor:pointer}.pipeline button span{display:block;font-size:11px;color:#888;margin-bottom:8px}.pipeline button.active{border-color:#111;background:#111;color:#fff}.pipeline button:disabled{opacity:.4;cursor:not-allowed}.card{background:#fff;border:1px solid #ddd;border-radius:18px;padding:28px}.create-card{display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:center}.card h2{font-size:30px;margin:8px 0}.card p{color:#666;line-height:1.6}.grid{display:grid;grid-template-columns:1.6fr .8fr;gap:18px}.section-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:20px}.status{color:#555;text-transform:capitalize}.status.approved{background:#e8f4e8;border-color:#b7d8b7}.status.awaiting_approval,.status.ready_for_review{background:#f5f0df}.messages{min-height:260px;border:1px solid #e4e4df;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:10px;margin-bottom:16px}.message{padding:13px 15px;border-radius:12px;max-width:80%;line-height:1.5}.message.user{align-self:flex-end;background:#111;color:#fff}.message.awe{align-self:flex-start;background:#f0f0ec}.empty{color:#777;padding:30px;text-align:center}.large{min-height:320px;display:flex;flex-direction:column;align-items:center;justify-content:center}.composer textarea,input{width:100%;border:1px solid #ccc;border-radius:10px;padding:13px;font:inherit;background:#fff}.composer{display:grid;gap:10px}.inline-form{display:flex;gap:10px}.inline-form input{flex:1}.button,button{font:inherit}.primary,.approve,.actions button{border:0;border-radius:10px;padding:12px 16px;cursor:pointer;background:#111;color:#fff}.primary:disabled,.approve:disabled,button:disabled{opacity:.45;cursor:not-allowed}.approve{margin-top:12px;width:100%}.side-panel .score{padding:18px 0;border-bottom:1px solid #eee}.score strong{font-size:40px;display:block}.score span{font-size:12px;color:#777}.fact{padding:12px 0;border-bottom:1px solid #eee}.fact small{color:#888}.fact p{margin:5px 0;color:#222}.finding{margin-top:18px;padding:16px;border-radius:12px;background:#f5f3eb}.finding ul{margin:10px 0 0;padding-left:20px;line-height:1.7}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:20px 0}.metrics>div{padding:15px;background:#f6f6f2;border-radius:12px}.metrics strong{font-size:24px;display:block;margin-top:7px}.strategy-grid{display:grid;grid-template-columns:.8fr 1.2fr;gap:35px;margin-top:25px}.strategy-grid h3{font-size:13px;text-transform:uppercase;letter-spacing:1px;margin-top:22px}.pages{display:grid;gap:10px}.pages>div{border:1px solid #e3e3df;border-radius:10px;padding:15px}.pages code{float:right;color:#888}.pages p{margin-bottom:0}.tags{display:flex;gap:6px;flex-wrap:wrap}.actions{display:flex;gap:10px;align-items:center;margin-top:22px}.actions .inline-form{flex:1}.actions .approve{width:auto;margin:0}.error{margin:14px 0;padding:13px 15px;background:#f8e8e8;border:1px solid #e3bcbc;border-radius:10px;color:#7d2929}footer{padding:40px 0 0;color:#888;font-size:12px}.design-summary{display:grid;grid-template-columns:.7fr 1.5fr .8fr .8fr;gap:8px;margin:20px 0}.design-summary>div{padding:16px;background:#f6f6f2;border-radius:12px}.design-summary small{display:block;color:#888;margin-bottom:7px}.design-summary strong{font-size:18px}.design-grid{display:grid;grid-template-columns:1fr 1fr;gap:35px;margin-top:25px}.design-grid h3{font-size:13px;text-transform:uppercase;letter-spacing:1px;margin:24px 0 10px}.design-grid ul{margin:0;padding-left:20px;line-height:1.7;color:#444}.palette{display:grid;gap:8px}.palette>div{display:grid;grid-template-columns:18px 100px 1fr;gap:10px;align-items:center;padding:10px;border:1px solid #e3e3df;border-radius:10px}.palette span{width:18px;height:18px;border-radius:50%;background:#d8d8d2;border:1px solid #bbb}.palette small{color:#777;text-transform:capitalize}.palette strong{font-size:13px;font-weight:500}.secondary{border:1px solid #ccc;border-radius:10px;padding:12px 16px;cursor:pointer;background:#fff;color:#222}.actions .secondary{margin:0}.actions .approve{width:auto;margin:0}.design .finding{margin-top:24px}.spec-pages{display:grid;gap:12px;margin-top:22px}.spec-page{border:1px solid #e3e3df;border-radius:12px;padding:18px}.spec-page>div:first-child{display:flex;justify-content:space-between}.spec-page code{color:#888}.spec-page p{margin:10px 0 16px}.spec-columns{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.spec-columns small{color:#888;text-transform:uppercase;letter-spacing:1px;font-size:10px}.spec-columns ul{margin:8px 0 0;padding-left:18px;line-height:1.6;color:#444}@media(max-width:800px){.create-card,.grid,.strategy-grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.pipeline{grid-template-columns:1fr}.inline-form,.actions{flex-direction:column}.hero h1{letter-spacing:-2px}.actions .approve{width:100%}}
      `}</style>
    </main>
  );
}
