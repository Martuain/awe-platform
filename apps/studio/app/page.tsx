"use client";

import { FormEvent, SyntheticEvent, useEffect, useMemo, useState } from "react";
import { safeArtifactPreviewHtml } from "./lib/safe-artifact-preview";

type Deployment = {
  project_id: string;
  deployment_id: string;
  generation_version: number;
  version: number;
  status: "queued" | "deploying" | "deployed" | "failed" | "stopped";
  lifecycle_role?: "current" | "previous" | "historical";
  snapshot_ref?: string | null;
  provider: string;
  url?: string | null;
  runtime_id?: string | null;
  diagnostics: string[];
  created_at: string;
  deployed_at?: string | null;
  stopped_at?: string | null;
};

type Stage = "discovery" | "strategy" | "design" | "specification" | "generation" | "mock" | "build" | "preview" | "deployment";
type PerformanceReport = {
  generation_version: number;
  status: "passed" | "warning";
  total_bytes: number;
  javascript_bytes: number;
  css_bytes: number;
  checks: { name: string; status: string; detail: string }[];
};
type BrowserPerformanceReport = {
  generation_version: number;
  status: "passed" | "warning" | "failed" | "unavailable";
  browser: string;
  url?: string | null;
  http_status?: number | null;
  diagnostics: string[];
  metrics: {
    fcp_ms?: number | null;
    lcp_ms?: number | null;
    inp_ms?: number | null;
    cls?: number | null;
    ttfb_ms?: number | null;
    dom_content_loaded_ms?: number | null;
    load_ms?: number | null;
  };
  checks: { name: string; status: string; detail: string }[];
};
type MonitoringReport = { status: string; service: string; projects: number; deployments: number; deployed: number; failed: number };

type Project = { id: string; name: string; status?: string; created_at?: string };
type Workspace = {
  project: Project;
  current_stage: Stage | "archived";
  discovery_version?: number | null;
  strategy_version?: number | null;
  design_version?: number | null;
  specification_version?: number | null;
  generation_version?: number | null;
  deployment_count: number;
  latest_deployment_status?: string | null;
  completed_capabilities: string[];
  next_capability?: string | null;
  last_activity_at?: string | null;
  execution_state?: {
    generation_version?: number | null;
    build_status?: string | null;
    build_result?: Record<string, unknown>;
    validation_status?: string | null;
    validation?: WebsiteValidation | null;
    preview_status?: string | null;
    preview?: WebsitePreview | null;
  } | null;
};
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

type WebsitePreview = {
  status: "started" | "stopped" | "failed" | "unavailable";
  url?: string | null;
  container_id?: string | null;
  diagnostics: string[];
};

type WebsiteBuildPlan = {
  project_id: string;
  generation_version: number;
  status: "planned" | "rejected";
  diagnostics: string[];
  files: string[];
  isolation: string;
  network_access: string;
  allowed_commands: string[];
};

type WebsiteMock = {
  version: number;
  generation_version: number;
  status: "ready_for_review" | "changes_requested" | "approved";
  title: string;
  html: string;
  feedback: string[];
};

type WebsiteContent = {
  content_id: string; project_id: string; page: string; key: string; content_type: string; value: string; version: number; status: "draft" | "published"; created_at: string; updated_at: string; published_at?: string | null;
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

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      body.detail || `Request failed (${response.status})`,
      response.status,
    );
  }
  return response.json();
}

function Score({ value }: { value: number }) {
  return <strong>{Math.round(value * 100)}%</strong>;
}

export default function Home() {
  const [project, setProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [stage, setStage] = useState<Stage>("discovery");
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [context, setContext] = useState<DiscoveryContext | null>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [design, setDesign] = useState<DesignDirection | null>(null);
  const [specification, setSpecification] = useState<WebsiteSpecification | null>(null);
  const [generation, setGeneration] = useState<WebsiteGeneration | null>(null);
  const [content, setContent] = useState<WebsiteContent[]>([]);
  const [contentDrafts, setContentDrafts] = useState<Record<string, string>>({});
  const [mock, setMock] = useState<WebsiteMock | null>(null);
  const [mockFeedback, setMockFeedback] = useState("");
  const [buildPlan, setBuildPlan] = useState<WebsiteBuildPlan | null>(null);
  const [buildResult, setBuildResult] = useState<Record<string, unknown> | null>(null);
  const [validation, setValidation] = useState<WebsiteValidation | null>(null);
  const [previewRuntime, setPreviewRuntime] = useState<WebsitePreview | null>(null);
  const [previewRefreshKey, setPreviewRefreshKey] = useState(0);
  const [previewFrameVisible, setPreviewFrameVisible] = useState(false);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [performance, setPerformance] = useState<PerformanceReport | null>(null);
  const [browserPerformance, setBrowserPerformance] = useState<BrowserPerformanceReport | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringReport | null>(null);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const deployedDeployment =
    deployments.find((item) => item.lifecycle_role === "current") ||
    deployments.find((item) => item.status === "deployed") ||
    null;
  const previousDeployment =
    deployments.find((item) => item.lifecycle_role === "previous") ||
    (deployedDeployment
      ? deployments.find((item) => item.version === deployedDeployment.version - 1 && item.status === "stopped") || null
      : null);

  async function ensureDiscovery(projectId: string): Promise<DiscoveryContext> {
    try {
      return await api<DiscoveryContext>(
        `/api/v1/business-discovery/context/${projectId}`,
      );
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) {
        throw error;
      }
      return await api<DiscoveryContext>(
        `/api/v1/business-discovery/start?project_id=${projectId}`,
        { method: "POST" },
      );
    }
  }

  useEffect(() => {
    api<Project[]>("/api/v1/projects")
      .then(setProjects)
      .catch(() => undefined);

    const saved = window.localStorage.getItem("awe-project-id");
    if (!saved) return;
    api<Project>(`/api/v1/projects/${saved}`)
      .then(async (p) => {
        setProject(p);
        let w: Workspace | null = null;
        let deploymentHistory: Deployment[] = [];
        try {
          w = await api<Workspace>(`/api/v1/projects/${p.id}/workspace`);
          setWorkspace(w);
          const persisted = w.execution_state;
          if (persisted) {
            if (persisted.build_result && Object.keys(persisted.build_result).length) setBuildResult(persisted.build_result);
            if (persisted.validation) setValidation(persisted.validation);
            if (persisted.preview) setPreviewRuntime(persisted.preview);
          }
        } catch { setWorkspace(null); }
        try {
          deploymentHistory = await api<Deployment[]>(`/api/v1/deployments?project_id=${p.id}`);
          setDeployments(deploymentHistory);
        } catch { setDeployments([]); }

        // Hydrate persisted artifacts independently, but use the workspace's
        // authoritative next stage to decide which future artifacts are safe
        // to request. A missing future artifact (404) is expected and must not
        // move the wizard backwards.
        try { setContext(await ensureDiscovery(p.id)); } catch { setContext(null); }

        const current = w?.current_stage;
        const latestDeployment = deploymentHistory.length
          ? deploymentHistory.reduce((latest, item) => item.created_at > latest.created_at ? item : latest)
          : null;
        const rank: Record<string, number> = {
          discovery: 0, strategy: 1, design: 2, specification: 3,
          generation: 4, mock: 5, build: 6, preview: 7, deployment: 8,
        };
        const hasReachedArtifact = (target: Stage) => current === "archived" || (current ? rank[current] > rank[target] : false);

        if (hasReachedArtifact("strategy")) {
          try { setStrategy(await api<Strategy>(`/api/v1/website-strategy/${p.id}`)); } catch { setStrategy(null); }
        }
        if (hasReachedArtifact("design")) {
          try { setDesign(await api<DesignDirection>(`/api/v1/brand-design/${p.id}`)); } catch { setDesign(null); }
        }
        if (hasReachedArtifact("specification")) {
          try { setSpecification(await api<WebsiteSpecification>(`/api/v1/website-specification/${p.id}`)); } catch { setSpecification(null); }
        }
        if (hasReachedArtifact("generation")) {
          try { setGeneration(await api<WebsiteGeneration>(`/api/v1/website-generation/${p.id}`)); } catch { setGeneration(null); }
        }
        if (hasReachedArtifact("generation")) {
          try {
            const items = await api<WebsiteContent[]>(`/api/v1/website-content/${p.id}`);
            setContent(items);
            setContentDrafts(Object.fromEntries(items.map((item) => [`${item.page}:${item.key}`, item.value])));
          } catch { setContent([]); setContentDrafts({}); }
        }
        if (hasReachedArtifact("mock")) {
          try { setMock(await api<WebsiteMock>(`/api/v1/website-mock/${p.id}`)); } catch { setMock(null); }
        }

        // Resume from durable workspace state. A successful deployment is the
        // strongest durable completion signal: transient build/validation
        // artifacts from the previous browser session are not required to
        // reopen the project at the live/deployment boundary.
        if (current === "archived") setStage("discovery");
        else if (current === "deployment" || latestDeployment?.status === "deployed") setStage("deployment");
        else if (current === "preview") {
          try {
            const m = await api<WebsiteMock>(`/api/v1/website-mock/${p.id}`);
            setMock(m);
            setStage(m.status === "approved" ? "build" : "mock");
          } catch { setStage("generation"); }
        } else if (current === "generation") setStage("generation");
        else if (current === "specification") setStage("specification");
        else if (current === "design") setStage("design");
        else if (current === "strategy") setStage("strategy");
        else setStage("discovery");
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
      const c = await ensureDiscovery(p.id);
      setProject(p); setProjects((current) => [p, ...current.filter((item) => item.id !== p.id)]); setContext(c); setName("");
      setWorkspace(await api<Workspace>(`/api/v1/projects/${p.id}/workspace`));
      window.localStorage.setItem("awe-project-id", p.id);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to create project"); }
    finally { setBusy(false); }
  }

  function startNewProject() {
    window.localStorage.removeItem("awe-project-id");
    setProject(null);
    setWorkspace(null);
    setContext(null);
    setStrategy(null);
    setDesign(null);
    setSpecification(null);
    setGeneration(null);
    setMock(null);
    setMockFeedback("");
    setBuildPlan(null);
    setBuildResult(null);
    setValidation(null);
    setPreviewRuntime(null);
    setDeployments([]);
    setStage("discovery");
    setMessage("");
    setError("");
    setName("");
  }

  async function duplicateProject() {
    if (!project) return;
    const requestedName = window.prompt("Name for the duplicate project", `${project.name} Copy`);
    if (requestedName === null) return;
    const duplicateName = requestedName.trim();
    if (!duplicateName) {
      setError("Project name cannot be empty.");
      return;
    }

    setBusy(true);
    setError("");
    try {
      const duplicate = await api<Project>(`/api/v1/projects/${project.id}/duplicate`, {
        method: "POST",
        body: JSON.stringify({ name: duplicateName }),
      });
      const context = await ensureDiscovery(duplicate.id);
      setProjects((current) => [duplicate, ...current.filter((item) => item.id !== duplicate.id)]);
      setProject(duplicate);
      setContext(context);
      setWorkspace(await api<Workspace>(`/api/v1/projects/${duplicate.id}/workspace`));
      setStrategy(null);
      setDesign(null);
      setSpecification(null);
      setGeneration(null);
      setBuildPlan(null);
      setBuildResult(null);
      setValidation(null);
      setPreviewRuntime(null);
      setDeployments([]);
      setStage("discovery");
      window.localStorage.setItem("awe-project-id", duplicate.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to duplicate project");
    } finally {
      setBusy(false);
    }
  }

  async function setProjectStatus(status: "active" | "archived") {
    if (!project) return;
    setBusy(true);
    setError("");
    try {
      const updated = await api<Project>(`/api/v1/projects/${project.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setProject(updated);
      setProjects((current) => current.map((item) => item.id === updated.id ? updated : item));
      const nextWorkspace = await api<Workspace>(`/api/v1/projects/${updated.id}/workspace`);
      setWorkspace(nextWorkspace);
      if (status === "archived") setStage("discovery");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to update project");
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!project || !message.trim()) return;
    setBusy(true); setError("");
    try {
      // Recover the persisted Discovery lifecycle before mutating it. This is
      // intentionally defensive: the API remains strict and never creates a
      // session implicitly, while Studio can recover from stale UI state.
      const current = await ensureDiscovery(project.id);
      setContext(current);
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
      setGeneration(g);
      if (specification?.pages?.length) {
        const seed = specification.pages.flatMap((page) => [
          { page: page.path, key: "headline", content_type: "text", value: page.name },
          { page: page.path, key: "positioning", content_type: "text", value: strategy?.content.positioning || "" },
          { page: page.path, key: "cta", content_type: "text", value: page.primary_cta || "Get started" },
        ]);
        const seeded: WebsiteContent[] = [];
        for (const item of seed) {
          seeded.push(await api<WebsiteContent>(`/api/v1/website-content/${project.id}`, { method: "PUT", body: JSON.stringify(item) }));
        }
        setContent(seeded);
        setContentDrafts(Object.fromEntries(seeded.map((item) => [`${item.page}:${item.key}`, item.value])));
      }
      const m = await api<WebsiteMock>(`/api/v1/website-mock/create?project_id=${project.id}`, { method: "POST" });
      setMock(m); setStage("mock");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to generate website"); }
    finally { setBusy(false); }
  }

  async function submitMockFeedback() {
    if (!project || !mockFeedback.trim()) return;
    setBusy(true); setError("");
    try {
      const m = await api<WebsiteMock>(`/api/v1/website-mock/${project.id}/feedback`, { method: "POST", body: JSON.stringify({ feedback: mockFeedback.trim() }) });
      setMock(m); setMockFeedback("");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to save mock feedback"); }
    finally { setBusy(false); }
  }

  async function reviseMock() {
    if (!project || !mockFeedback.trim()) return;
    setBusy(true); setError("");
    try {
      const m = await api<WebsiteMock>(`/api/v1/website-mock/${project.id}/revise`, { method: "POST", body: JSON.stringify({ feedback: mockFeedback.trim() }) });
      const g = await api<WebsiteGeneration>(`/api/v1/website-generation/${project.id}`);
      setGeneration(g); setMock(m); setMockFeedback("");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to revise website mock"); }
    finally { setBusy(false); }
  }

  function handleMockFrameLoad(event: SyntheticEvent<HTMLIFrameElement>) {
    const frame = event.currentTarget;
    const document = frame.contentDocument;
    if (!document) return;

    const handleClick = (click: MouseEvent) => {
      const target = click.target instanceof Element ? click.target.closest("a") : null;
      if (!target) return;
      const href = target.getAttribute("href") || "";
      if (!href.startsWith("#")) return;

      const targetId = href.slice(1);
      if (!targetId) return;
      const destination = document.getElementById(targetId);
      if (!destination) return;

      click.preventDefault();
      click.stopPropagation();

      const pages = Array.from(document.querySelectorAll<HTMLElement>(".awe-mock-page"));
      if (destination.classList.contains("awe-mock-page")) {
        pages.forEach((page) => {
          page.style.display = page === destination ? "block" : "none";
        });
      }
      destination.scrollIntoView({ block: "start", behavior: "auto" });
    };

    document.addEventListener("click", handleClick, true);
  }

 async function approveMock() {
  if (!project) return;
  setBusy(true);
  setError("");

  try {
    const m = await api<WebsiteMock>(
      `/api/v1/website-mock/${project.id}/approve`,
      { method: "POST" },
    );

    setMock(m);

    const plan = await api<WebsiteBuildPlan>(
      `/api/v1/website-build/plan?project_id=${project.id}`,
      { method: "POST" },
    );

    setBuildPlan(plan);
    setStage("build");

    if (plan.status !== "planned") {
      setError(plan.diagnostics.join(" ") || "Build plan rejected");
    }
  } catch (e) {
    setError(
      e instanceof Error ? e.message : "Unable to approve website mock",
    );
  } finally {
    setBusy(false);
  }
}

  async function planBuild() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const plan = await api<WebsiteBuildPlan>(`/api/v1/website-build/plan?project_id=${project.id}`, { method: "POST" });
      setBuildPlan(plan);
      if (plan.status !== "planned") setError(plan.diagnostics.join(" ") || "Build plan rejected");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to plan website build"); }
    finally { setBusy(false); }
  }

  async function executeBuild() {
    if (!project) return;
    setBusy(true);
    setError("");

    try {
      const result = await api<Record<string, unknown>>(
        `/api/v1/website-build/execute?project_id=${project.id}`,
        { method: "POST" }
      );

      setBuildResult(result);

      if (result.status !== "succeeded") {
        setError(String(result.reason || result.stderr || "Build did not succeed."));
        return;
      }

      // Refresh authoritative build-plan state after execution.
      const plan = await api<WebsiteBuildPlan>(
        `/api/v1/website-build/plan?project_id=${project.id}`,
        { method: "POST" }
      );
      setBuildPlan(plan);

      setStage("build");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to execute website build");
    } finally {
      setBusy(false);
    }
  }

  async function runToPreview() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const plan = await api<WebsiteBuildPlan>(`/api/v1/website-build/plan?project_id=${project.id}`, { method: "POST" });
      setBuildPlan(plan);
      if (plan.status !== "planned") throw new Error(plan.diagnostics.join(" ") || "Build plan rejected");
      const result = await api<Record<string, unknown>>(`/api/v1/website-build/execute?project_id=${project.id}`, { method: "POST" });
      setBuildResult(result);
      if (result.status !== "succeeded") throw new Error(String(result.reason || result.stderr || "Build did not succeed."));
      const validationResult = await api<WebsiteValidation>(`/api/v1/website-validation/validate?project_id=${project.id}`, { method: "POST" });
      setValidation(validationResult);
      if (validationResult.status !== "passed") throw new Error(validationResult.diagnostics.join(" ") || "Generated website validation failed.");
      setStage("preview");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to complete the executable website flow"); }
    finally { setBusy(false); }
  }

  async function saveContent(item: WebsiteContent) {
    if (!project) return;
    const value = contentDrafts[`${item.page}:${item.key}`] ?? item.value;
    setBusy(true); setError("");
    try {
      const saved = await api<WebsiteContent>(`/api/v1/website-content/${project.id}`, { method: "PUT", body: JSON.stringify({ page: item.page, key: item.key, content_type: item.content_type, value }) });
      setContent((current) => current.map((entry) => entry.content_id === saved.content_id ? saved : entry));
      setContentDrafts((current) => ({ ...current, [`${saved.page}:${saved.key}`]: saved.value }));
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to save website content"); }
    finally { setBusy(false); }
  }

  const hasUnsavedContentChanges = content.some((item) => {
    const draft = contentDrafts[`${item.page}:${item.key}`];
    return draft !== undefined && draft !== item.value;
  });

  async function publishContent() {
    if (!project) return;
    setBusy(true); setError("");
    // Never leave the previous Preview document visible while the published
    // content is being reconciled into the Preview runtime.
    setPreviewFrameVisible(false);
    try {
      // The editor keeps unsaved textarea changes locally. Publish must first
      // persist those values as drafts; otherwise the API would publish the
      // previous database values while the user expects the visible edits.
      const changed = content.filter((item) => {
        const draft = contentDrafts[`${item.page}:${item.key}`];
        return draft !== undefined && draft !== item.value;
      });
      for (const item of changed) {
        await api<WebsiteContent>(`/api/v1/website-content/${project.id}`, {
          method: "PUT",
          body: JSON.stringify({ page: item.page, key: item.key, content_type: item.content_type, value: contentDrafts[`${item.page}:${item.key}`] }),
        });
      }
      const published = await api<WebsiteContent[]>(`/api/v1/website-content/${project.id}/publish`, { method: "POST" });
      setContent(published);
      setContentDrafts(Object.fromEntries(published.map((item) => [`${item.page}:${item.key}`, item.value])));
      // Publication is a hard consistency boundary: rebuild the disposable
      // Preview runtime from the just-published content before the UI reports
      // success. This prevents Validate Website from reopening an older
      // runtime/snapshot. Deployment runtimes are deliberately preserved.
      const refreshed = await api<WebsitePreview>(`/api/v1/website-preview/refresh?project_id=${project.id}`, { method: "POST" });
      setPreviewRuntime(refreshed);
      if (refreshed.status !== "started") {
        throw new Error(refreshed.diagnostics.join(" ") || "Unable to refresh live preview");
      }
      setPreviewRefreshKey((key) => key + 1);
      setPreviewFrameVisible(true);
    } catch (e) {
      setPreviewFrameVisible(false);
      setError(e instanceof Error ? e.message : "Unable to publish website content");
    }
    finally { setBusy(false); }
  }

  function liveDeploymentUrl(url: string, projectId?: string, deploymentId?: string) {
    try {
      const parsed = new URL(url);
      if ((parsed.hostname === "127.0.0.1" || parsed.hostname === "localhost") && projectId) {
        return deploymentId
          ? `/api/live/${projectId}/deployment/${encodeURIComponent(deploymentId)}/`
          : `/api/live/${projectId}/`;
      }
      return url;
    } catch {
      return url;
    }
  }

  function livePreviewRuntimeUrl(url: string, projectId?: string) {
    try {
      const parsed = new URL(url);
      if ((parsed.hostname === "127.0.0.1" || parsed.hostname === "localhost") && projectId) {
        return `/api/live-preview/preview/${projectId}/`;
      }
      return url;
    } catch {
      return url;
    }
  }

  async function refreshLivePreview() {
    if (!project || !previewRuntime?.url) return;
    setBusy(true); setError("");
    // Refresh must reconcile the disposable runtime, not merely remount the
    // existing iframe. A runtime can be alive but stale/unreachable, so the
    // API refresh endpoint is the authoritative recovery path.
    setPreviewFrameVisible(false);
    try {
      const refreshed = await api<WebsitePreview>(
        `/api/v1/website-preview/refresh?project_id=${project.id}`,
        { method: "POST" },
      );
      setPreviewRuntime(refreshed);
      if (refreshed.status !== "started") {
        throw new Error(
          refreshed.diagnostics.join(" ") || "Unable to refresh live preview",
        );
      }
      // Force a new iframe instance and a cache-distinct proxy request only
      // after the API confirms that the runtime is ready.
      setPreviewRefreshKey((key) => key + 1);
      setPreviewFrameVisible(true);
    } catch (e) {
      setPreviewFrameVisible(false);
      setError(e instanceof Error ? e.message : "Unable to refresh live preview");
    } finally {
      setBusy(false);
    }
  }

  async function startLivePreview() {
    if (!project) return;
    if (validation?.status !== "passed") {
      setError("A passed validation is required before starting the live preview.");
      return;
    }
    setBusy(true); setError("");
    try {
      const preview = await api<WebsitePreview>(`/api/v1/website-preview/start?project_id=${project.id}`, { method: "POST" });
      setPreviewRuntime(preview);
      if (preview.status === "started") setPreviewRefreshKey((key) => key + 1);
      if (preview.status !== "started") setError(preview.diagnostics.join(" ") || "Unable to start live preview");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to start live preview"); }
    finally { setBusy(false); }
  }

  async function stopLivePreview() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const preview = await api<WebsitePreview | null>(`/api/v1/website-preview/stop?project_id=${project.id}`, { method: "POST" });
      setPreviewRuntime(preview);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to stop live preview"); }
    finally { setBusy(false); }
  }

  async function loadDeployments(projectId = project?.id) {
    if (!projectId) return;
    try {
      const result = await api<Deployment[]>(`/api/v1/deployments?project_id=${projectId}`);
      setDeployments(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load deployments.");
    }
  }

  async function runPerformanceCheck() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      setPerformance(await api<PerformanceReport>(`/api/v1/website-performance/check?project_id=${project.id}`, { method: "POST" }));
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to run performance check."); }
    finally { setBusy(false); }
  }

  async function runBrowserPerformanceCheck() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const report = await api<BrowserPerformanceReport>(`/api/v1/website-performance/browser-check?project_id=${project.id}`, { method: "POST" });
      setBrowserPerformance(report);
      if (report.status === "failed" || report.status === "unavailable") {
        setError(report.diagnostics.join(" ") || "Unable to run browser performance validation.");
      }
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to run browser performance validation."); }
    finally { setBusy(false); }
  }

  async function loadMonitoring() {
    try {
      setMonitoring(await api<MonitoringReport>("/api/v1/monitoring"));
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load monitoring status."); }
  }

  async function deployWebsite() {
    if (!project) return;
    setBusy(true); setError("");
    try {
      const deployment = await api<Deployment>(`/api/v1/deployments?project_id=${project.id}`, { method: "POST" });
      setDeployments((current) => [deployment, ...current.filter((item) => item.deployment_id !== deployment.deployment_id)]);
      setStage("deployment");
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to deploy website."); }
    finally { setBusy(false); }
  }

  async function stopDeployment(deploymentId: string) {
    setBusy(true); setError("");
    try {
      const deployment = await api<Deployment>(`/api/v1/deployments/${deploymentId}/stop`, { method: "POST" });
      setDeployments((current) => current.map((item) => item.deployment_id === deployment.deployment_id ? deployment : item));
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to stop deployment."); }
    finally { setBusy(false); }
  }

  async function validateWebsite() {
    if (!project) return;
    setBusy(true); setError("");
    // Unmount the old interactive document before validation/Preview refresh.
    // Otherwise React can keep the previous runtime visible until the new
    // runtime request completes, creating a misleading stale first render.
    setPreviewFrameVisible(false);
    setError("");
    try {
      const v = await api<WebsiteValidation>(`/api/v1/website-validation/validate?project_id=${project.id}`, { method: "POST" });
      setValidation(v);
      setStage("preview");

      // Validation is the entry point to the interactive preview. Always
      // start/reconcile the runtime here so the iframe is backed by the
      // latest generated artifact + currently published CAP-035 content,
      // rather than the static HTML captured by the validation response.
      if (v.status === "passed") {
        const preview = await api<WebsitePreview>(`/api/v1/website-preview/refresh?project_id=${project.id}`, { method: "POST" });
        setPreviewRuntime(preview);
        if (preview.status === "started") {
          setPreviewRefreshKey((key) => key + 1);
          setPreviewFrameVisible(true);
        } else {
          setPreviewFrameVisible(false);
          setError(preview.diagnostics.join(" ") || "Unable to start live preview");
        }
      }
    } catch (e) {
      setPreviewFrameVisible(false);
      setError(e instanceof Error ? e.message : "Unable to validate generated website");
    }
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
        <div className="project-controls">
          {projects.length > 0 ? (
            <label className="project-switcher">
              <span className="sr-only">Active project</span>
              <select
                value={project?.id ?? ""}
                onChange={async (event) => {
                  const projectId = event.target.value;
                  if (!projectId) return;

                  setBusy(true);
                  setError("");
                  try {
                    await ensureDiscovery(projectId);
                    window.localStorage.setItem("awe-project-id", projectId);
                    window.location.reload();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Unable to switch project");
                  } finally {
                    setBusy(false);
                  }
                }}
                aria-label="Select project"
              >
                {!project && <option value="">Select a project…</option>}
                {projects.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}{item.status === "archived" ? " · Archived" : ""}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <button className="secondary header-action" onClick={startNewProject} disabled={busy}>New project</button>
        </div>
      </header>

      <section className="hero">
        <span className="eyebrow">AI-native website engineering</span>
        <h1>Turn business knowledge into an engineered digital experience.</h1>
        <p>AWE moves from understanding to strategy, design and eventually implementation — with evaluation and human approval at every important boundary.</p>
      </section>

      {project && workspace ? (
        <section className="workspace-bar card">
          <div>
            <span className="eyebrow">Project workspace</span>
            <h2>{project.name}</h2>
            <p>{workspace.completed_capabilities.length} capabilities completed · {workspace.deployment_count} deployment{workspace.deployment_count === 1 ? "" : "s"}</p>
          </div>
          <div>
            <div className="workspace-meta">
              <div><small>Status</small><strong className={`status ${project.status}`}>{project.status}</strong></div>
              <div><small>Current stage</small><strong>{workspace.current_stage.replaceAll("_", " ")}</strong></div>
              <div><small>Next</small><strong>{workspace.next_capability ? workspace.next_capability.replaceAll("_", " ") : "Complete"}</strong></div>
              <div><small>Last activity</small><strong>{workspace.last_activity_at ? new Date(workspace.last_activity_at).toLocaleString() : "—"}</strong></div>
            </div>
            <div className="project-actions">
              <button className="secondary" onClick={duplicateProject} disabled={busy}>Duplicate</button>
              <button className="secondary" onClick={() => setProjectStatus(project.status === "archived" ? "active" : "archived")} disabled={busy}>
                {project.status === "archived" ? "Restore project" : "Archive project"}
              </button>
            </div>
          </div>
        </section>
      ) : null}

      <nav className="pipeline" aria-label="AWE capability pipeline">
        {[["discovery", "01", "Discovery"], ["strategy", "02", "Strategy"], ["design", "03", "Design"], ["specification", "04", "Website Spec"], ["generation", "05", "Generate"], ["mock", "06", "Customer Mock"], ["build", "07", "Build"], ["preview", "08", "Preview"], ["deployment", "09", "Deploy"]].map(([key, number, label]) => (
          <button key={key} className={stage === key ? "active" : ""} onClick={() => setStage(key as Stage)} disabled={!project || project.status === "archived" || (key === "strategy" && context?.status !== "approved") || (key === "design" && strategy?.status !== "approved") || (key === "specification" && design?.status !== "approved") || (key === "generation" && specification?.status !== "approved") || (key === "mock" && !generation) || (key === "build" && (!generation || mock?.status !== "approved")) || (key === "preview" && (!deployedDeployment && (!buildResult || validation?.status !== "passed"))) || (key === "deployment" && (!buildResult || validation?.status !== "passed"))}>
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
            {context && context.status !== "approved" && project.status !== "archived" && <form onSubmit={sendMessage} className="composer"><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Tell AWE what matters about the business…" rows={4} /><button className="primary" disabled={busy || !message.trim()}>{busy ? "Thinking…" : "Continue discovery"}</button></form>}
            {context?.status === "awaiting_approval" && project.status !== "archived" && <button className="approve" onClick={approveDiscovery} disabled={busy}>{busy ? "Approving…" : "Approve Business Discovery"}</button>}
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
            <div className="actions"><button className="secondary" onClick={() => setStage("specification")}>Back to Website Spec</button><button className="approve" onClick={() => setStage("mock")} disabled={busy}>Review Customer Mock</button></div>
          </>}
        </section>
      ) : stage === "mock" ? (
        <section className="card mock">
          <div className="section-heading"><div><span className="eyebrow">CAP-026 · CAP-027 · CAP-028</span><h2>Customer Website Mock</h2><p>Review the generated website before any executable build. Feedback creates an explicit revision boundary; approval is the gate into isolated build and preview.</p></div>{mock && <span className={`status ${mock.status}`}>{mock.status.replaceAll("_", " ")}</span>}</div>
          {!mock ? <div className="empty large"><p>Generate the website artifact to create the first customer-facing mock.</p><button className="primary" onClick={generateWebsite} disabled={busy}>{busy ? "Generating…" : "Generate Customer Mock"}</button></div> : <>
            <div className="design-summary"><div><small>Mock</small><strong>v{mock.version}</strong></div><div><small>Generation</small><strong>v{mock.generation_version}</strong></div><div><small>Feedback</small><strong>{mock.feedback.length}</strong></div><div><small>Gate</small><strong>{mock.status === "approved" ? "Build ready" : "Customer review"}</strong></div></div>
            <div className="preview-pane"><div className="preview-toolbar"><div><h3>{mock.title}</h3><small>Safe customer-facing artifact mock · no generated application code executes here</small></div></div><iframe title="AWE customer website mock" srcDoc={safeArtifactPreviewHtml(mock.html)} className="preview-frame" sandbox="allow-same-origin" onLoad={handleMockFrameLoad} /></div>
            {mock.feedback.length > 0 && <div className="finding"><strong>Review history</strong><ul>{mock.feedback.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul></div>}
            {mock.status !== "approved" && <div className="actions"><div className="inline-form"><input value={mockFeedback} onChange={(event) => setMockFeedback(event.target.value)} placeholder="Feedback, e.g. headline: Welcome to Acme" /></div><button className="secondary" onClick={submitMockFeedback} disabled={busy || !mockFeedback.trim()}>Save feedback</button><button className="secondary" onClick={reviseMock} disabled={busy || !mockFeedback.trim()}>Revise mock</button><button className="approve" onClick={approveMock} disabled={busy}>Approve mock → Build</button></div>}
          </>}
        </section>
      ) : stage === "build" ? (
        <section className="card build">
          <div className="section-heading"><div><span className="eyebrow">CAP-008</span><h2>Build & Validation</h2><p>Execute the generated website inside the isolated build boundary, then validate the resulting artifact before preview or deployment.</p></div>{buildResult && <span className={`status ${buildResult.status === "succeeded" ? "passed" : "failed"}`}>{String(buildResult.status)}</span>}</div>
          {!generation ? (
            <div className="empty large"><p>Generate the website artifact before starting an isolated build.</p><button className="primary" onClick={() => setStage("generation")} disabled={busy}>Back to Generation</button></div>
          ) : (
            <>
              <div className="design-summary">
                <div><small>Generation</small><strong>v{generation.version}</strong></div>
                <div><small>Build plan</small><strong>{buildPlan?.status || "Pending"}</strong></div>
                <div><small>Isolation</small><strong>{buildPlan?.isolation || "Docker"}</strong></div>
                <div><small>Validation</small><strong>{validation?.status || "Pending"}</strong></div>
              </div>
              {buildPlan?.diagnostics?.length ? <div className="finding"><strong>Build plan diagnostics</strong><ul>{buildPlan.diagnostics.map((x) => <li key={x}>{x}</li>)}</ul></div> : null}
              {buildResult?.stderr || buildResult?.stdout ? <div className="finding"><strong>Build diagnostics</strong><pre>{String(buildResult.stderr || buildResult.stdout)}</pre></div> : null}
              <div className="actions">
                <button className="secondary" onClick={() => setStage("generation")} disabled={busy}>Back to Generation</button>
                <button className="secondary" onClick={planBuild} disabled={busy}>{busy ? "Planning…" : "Refresh Build Plan"}</button>
                {!buildResult || buildResult.status !== "succeeded" ? <button className="primary" onClick={executeBuild} disabled={busy || buildPlan?.status === "rejected"}>{busy ? "Building…" : "Run Isolated Build"}</button> : <button className="primary" onClick={validateWebsite} disabled={busy}>{busy ? "Validating…" : "Validate Build"}</button>}
              </div>
              {validation?.status === "passed" && <div className="actions"><button className="approve" onClick={() => setStage("preview")}>Continue to Preview</button></div>}
            </>
          )}
        </section>
      ) : stage === "preview" ? (
        <>
        <section className="card content-manager">
          <div className="section-heading"><div><span className="eyebrow">CAP-035</span><h2>Website Content</h2><p>Edit persistent website copy without regenerating the website. Save changes as draft, then publish them into the live preview.</p></div><span className="status">{content.filter((item) => item.status === "draft").length} draft</span></div>
          {content.length === 0 ? <div className="empty">No editable content exists yet. Add content through the API or continue with the generated website.</div> : <div className="content-editor">{content.map((item) => <article className="spec-page" key={item.content_id}><div><strong>{item.page} · {item.key}</strong><code>v{item.version} · {item.status}</code></div><textarea value={contentDrafts[`${item.page}:${item.key}`] ?? item.value} onChange={(event) => setContentDrafts((current) => ({ ...current, [`${item.page}:${item.key}`]: event.target.value }))} rows={3} /><div className="actions"><button className="secondary" onClick={() => saveContent(item)} disabled={busy}>Save draft</button></div></article>)}</div>}
          {content.length > 0 && <div className="actions"><button className="approve" onClick={publishContent} disabled={busy || (!content.some((item) => item.status === "draft") && !hasUnsavedContentChanges)}>{busy ? "Publishing…" : "Publish content → Live Preview"}</button></div>}
        </section>
        <section className="card preview">
          <div className="section-heading"><div><span className="eyebrow">CAP-006</span><h2>Preview & Validation</h2><p>Validate the generated project artifact and inspect a safe browser preview before moving toward deployable execution.</p></div>{validation && <span className={`status ${validation.status}`}>{validation.status}</span>}</div>
          {!validation ? <div className="empty large"><p>Run validation to produce the CAP-006 preview.</p><button className="primary" onClick={validateWebsite} disabled={busy}>{busy ? "Validating…" : "Validate Website"}</button></div> : <>
            <div className="design-summary"><div><small>Generation</small><strong>v{validation.generation_version}</strong></div><div><small>Validation</small><strong>{validation.status}</strong></div><div><small>Checks</small><strong>{Object.values(validation.checks).filter(Boolean).length}/{Object.keys(validation.checks).length}</strong></div><div><small>Preview</small><strong>{validation.preview.format.toUpperCase()}</strong></div></div>
            <div className="strategy-grid"><div><h3>Validation checks</h3><ul>{Object.entries(validation.checks).map(([key, value]) => <li key={key}>{key}: <strong>{value ? "PASS" : "FAIL"}</strong></li>)}</ul>{validation.diagnostics.length > 0 && <><h3>Diagnostics</h3><ul>{validation.diagnostics.map((x) => <li key={x}>{x}</li>)}</ul></>}</div><div className="preview-pane">
                <div className="preview-toolbar">
                  <div><h3>Browser preview</h3><small>{previewRuntime?.status === "started" ? "Live isolated runtime" : "Safe artifact preview"}</small></div>
                  <div className="preview-toolbar-actions">
                    {previewRuntime?.status === "started" && previewRuntime.url ? (
                      <>
                        <button className="secondary" onClick={refreshLivePreview} disabled={busy}>{busy ? "Refreshing…" : "Refresh"}</button><button className="secondary" onClick={runBrowserPerformanceCheck} disabled={busy || validation?.status !== "passed" || previewRuntime?.status !== "started"}>Browser / Web Vitals</button>
                        <a className="secondary preview-link" href={livePreviewRuntimeUrl(previewRuntime.url, project?.id)} target="_blank" rel="noreferrer">Open in new tab ↗</a>
                      </>
                    ) : null}
                  </div>
                </div>
                {previewRuntime?.status === "started" && previewRuntime.url && previewFrameVisible ? (
                  <iframe
                    key={previewRefreshKey}
                    title="AWE generated website live preview"
                    src={`${livePreviewRuntimeUrl(previewRuntime.url, project?.id)}?preview_refresh=${previewRefreshKey}`}
                    className="preview-frame"
                    referrerPolicy="no-referrer"
                    onLoad={(event) => {
                      const frame = event.currentTarget;
                      frame.setAttribute("data-preview-loaded", "true");
                    }}
                  />
                ) : previewRuntime?.status === "started" && previewRuntime.url ? (
                  <div className="preview-frame" role="status" aria-live="polite">
                    {busy ? "Refreshing live preview…" : "Live preview is ready to refresh."}
                  </div>
                ) : busy ? (
                  <div className="preview-frame" role="status" aria-live="polite">
                    Refreshing live preview…
                  </div>
                ) : (
                  <iframe
                    title="AWE generated website artifact preview"
                    srcDoc={validation.preview.html}
                    className="preview-frame"
                  />
                )}
              </div></div>
            {browserPerformance && <div className="finding"><strong>Browser / Core Web Vitals · {browserPerformance.status === "passed" ? "Passed" : browserPerformance.status === "warning" ? "Warning" : browserPerformance.status}</strong><p>Chromium · HTTP {browserPerformance.http_status ?? "n/a"} · {browserPerformance.checks.filter((check) => check.status === "passed").length} passed · {browserPerformance.checks.filter((check) => check.status === "warning").length} warning</p><div className="metrics">{([
  ["FCP", "First Contentful Paint", "How quickly the first visible content appears on the page.", browserPerformance.metrics.fcp_ms == null ? "n/a" : `${Math.round(browserPerformance.metrics.fcp_ms)} ms`],
  ["LCP", "Largest Contentful Paint", "How quickly the main or largest visible content finishes loading.", browserPerformance.metrics.lcp_ms == null ? "n/a" : `${Math.round(browserPerformance.metrics.lcp_ms)} ms`],
  ["INP", "Interaction to Next Paint", "How quickly the page responds after a user interaction such as a click or tap.", browserPerformance.metrics.inp_ms == null ? "n/a" : `${Math.round(browserPerformance.metrics.inp_ms)} ms`],
  ["CLS", "Cumulative Layout Shift", "How much the page unexpectedly moves around while loading.", browserPerformance.metrics.cls == null ? "n/a" : browserPerformance.metrics.cls.toFixed(3)],
  ["TTFB", "Time to First Byte", "How quickly the server starts responding to the browser.", browserPerformance.metrics.ttfb_ms == null ? "n/a" : `${Math.round(browserPerformance.metrics.ttfb_ms)} ms`],
] as const).map(([shortName, fullName, meaning, value]) => <div key={shortName} title={meaning}><small>{shortName} · {fullName}</small><strong>{value}</strong><span>{meaning}</span></div>)}</div>{browserPerformance.diagnostics.length > 0 && <div><small>Diagnostics</small><ul>{browserPerformance.diagnostics.map((diagnostic) => <li key={diagnostic}>{diagnostic}</li>)}</ul></div>}<details><summary>Technical details</summary><ul>{browserPerformance.checks.map((check) => <li key={check.name}>{check.name}: {check.detail}</li>)}</ul><small>Generation version {browserPerformance.generation_version}{browserPerformance.url ? ` · ${browserPerformance.url}` : ""}</small></details></div>}
            <div className="finding"><strong>CAP-016 / CAP-017 MVP outcome</strong><p>The executable path now moves from approved generation through isolated build and validation into preview. Generated output also carries approved strategy and design decisions into a responsive, SEO-aware Next.js baseline.</p></div>
            <div className="finding"><strong>CAP-006 boundary</strong><p>This preview is rendered from the generated artifact and validation metadata. It does not execute arbitrary generated code inside Studio.</p></div>
            <div className="finding"><strong>CAP-009 disposable runtime</strong><p>Start an isolated Docker runtime for the validated generated site. The runtime is disposable and never runs inside the AWE Studio or API process.</p>{previewRuntime?.status === "started" && previewRuntime.url ? <p className="preview-runtime-status"><span className="status passed">Live preview running</span><button className="secondary" onClick={stopLivePreview} disabled={busy}>Stop runtime</button></p> : <><p>Validation has passed. Starting the disposable runtime may take a few minutes on a cold Docker/npm cache; Studio remains responsive while it runs.</p><button className="primary" onClick={startLivePreview} disabled={busy || validation?.status !== "passed"}>{busy ? "Starting live preview…" : "Start live preview"}</button></>}{previewRuntime?.diagnostics?.length ? <ul>{previewRuntime.diagnostics.map((x) => <li key={x}>{x}</li>)}</ul> : null}</div>
            <div className="actions"><button className="secondary" onClick={() => setStage("generation")}>Back to Generation</button><button className="approve" onClick={deployWebsite} disabled={busy || validation?.status !== "passed"}>{busy ? "Deploying…" : "Deploy Website"}</button></div>
          </>}
        </section>
        </>

      ) : stage === "deployment" ? (
        <section className="card deployment">
          <div className="section-heading"><div><span className="eyebrow">CAP-011</span><h2>Deployment</h2><p>Promote the validated website into a versioned deployment lifecycle without coupling Studio to infrastructure.</p></div></div>
          <div className="actions"><button className="primary" onClick={deployWebsite} disabled={busy || validation?.status !== "passed"}>{busy ? "Working…" : "Deploy Website"}</button><button className="secondary" onClick={() => loadDeployments()} disabled={busy}>Refresh history</button><button className="secondary" onClick={runPerformanceCheck} disabled={busy || !generation}>Performance check</button><button className="secondary" onClick={loadMonitoring} disabled={busy}>Monitoring</button>{deployedDeployment && <button className="secondary" onClick={() => setStage("preview")}>Edit website content</button>}</div>
          {deployedDeployment && <div className="finding"><strong>Website is live · deployment v{deployedDeployment.version}</strong><p>Your validated website is deployed and can be reopened from this workspace. Published content remains editable without regenerating the website.</p><div className="actions"><a className="secondary preview-link" href={deployedDeployment.url ? liveDeploymentUrl(deployedDeployment.url, project?.id) : "#"} target="_blank" rel="noreferrer">Open live website ↗</a>{previousDeployment && <a className="secondary preview-link" href={liveDeploymentUrl(previousDeployment.url || "http://127.0.0.1", project?.id, previousDeployment.deployment_id)} target="_blank" rel="noreferrer">Open previous version ↗</a>}<button className="secondary" onClick={() => setStage("preview")}>Return to website editing</button></div></div>}
          {(performance || monitoring) && <div className="metrics">{performance && <div><small>Artifact</small><strong>{Math.round(performance.total_bytes / 1024)} KB</strong></div>}{performance && <div><small>JavaScript</small><strong>{Math.round(performance.javascript_bytes / 1024)} KB</strong></div>}{performance && <div><small>CSS</small><strong>{Math.round(performance.css_bytes / 1024)} KB</strong></div>}{monitoring && <div><small>Deployments</small><strong>{monitoring.deployments}</strong></div>}{monitoring && <div><small>Failed</small><strong>{monitoring.failed}</strong></div>}</div>}
          {performance && <div className="finding"><strong>Performance · {performance.status}</strong><ul>{performance.checks.map((check) => <li key={check.name}>{check.name}: {check.detail}</li>)}</ul></div>}
          <div className="spec-pages">
            {deployments.length === 0 ? <div className="empty">No deployments yet.</div> : deployments.map((deployment) => (
              <article className="spec-page" key={deployment.deployment_id}>
                <div><strong>v{deployment.version} · {deployment.status}</strong><code>{deployment.provider}</code></div>
                <p>Generation v{deployment.generation_version} · {new Date(deployment.created_at).toLocaleString()}</p>
                {deployment.status === "deployed" && <p><a href={liveDeploymentUrl(deployment.url || "http://127.0.0.1", project?.id, deployment.deployment_id)} target="_blank" rel="noreferrer">Open live deployment ↗</a></p>}
                {previousDeployment?.deployment_id === deployment.deployment_id && <p><a href={liveDeploymentUrl(deployment.url || "http://127.0.0.1", project?.id, deployment.deployment_id)} target="_blank" rel="noreferrer">Open previous version ↗</a></p>}
                {deployment.diagnostics.length > 0 && <ul>{deployment.diagnostics.map((item) => <li key={item}>{item}</li>)}</ul>}
                {deployment.status === "deployed" && <button className="secondary" onClick={() => stopDeployment(deployment.deployment_id)} disabled={busy}>Stop deployment</button>}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <footer>AWE · Capability-driven · API-first · Human approval by design</footer>
      <style jsx global>{`
        :root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f7f7f4;color:#151515;font-family:Arial,Helvetica,sans-serif}.shell{max-width:1180px;margin:0 auto;padding:28px 28px 64px}.topbar{display:flex;justify-content:space-between;align-items:center;padding-bottom:28px;border-bottom:1px solid #ddd}.topbar>div{display:flex;gap:10px;align-items:center}.project-controls{display:flex;align-items:center;gap:8px}.project-switcher{display:flex;align-items:center}.project-switcher select{min-width:220px;border:1px solid #d7d7d2;border-radius:999px;padding:10px 36px 10px 14px;font:inherit;font-size:13px;background:#fff;color:#151515;cursor:pointer}.project-switcher select:focus{outline:2px solid #151515;outline-offset:2px}.header-action{white-space:nowrap}.project-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:10px}.project-chip,.status,.tags span{border:1px solid #d7d7d2;border-radius:999px;padding:7px 12px;font-size:12px;background:#fff}.hero{padding:70px 0 45px;max-width:850px}.eyebrow{font-size:11px;letter-spacing:1.8px;text-transform:uppercase;color:#6a6a64}.hero h1{font-size:clamp(42px,7vw,76px);line-height:.98;letter-spacing:-3px;margin:18px 0}.hero p{font-size:18px;line-height:1.65;color:#555;max-width:720px}.pipeline{display:grid;grid-template-columns:repeat(9,1fr);gap:8px;margin:10px 0 24px}.pipeline button{border:1px solid #ddd;background:#fff;padding:16px;text-align:left;border-radius:12px;cursor:pointer}.pipeline button span{display:block;font-size:11px;color:#888;margin-bottom:8px}.pipeline button.active{border-color:#111;background:#111;color:#fff}.pipeline button:disabled{opacity:.4;cursor:not-allowed}.card{background:#fff;border:1px solid #ddd;border-radius:18px;padding:28px}.create-card{display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:center}.card h2{font-size:30px;margin:8px 0}.card p{color:#666;line-height:1.6}.grid{display:grid;grid-template-columns:1.6fr .8fr;gap:18px}.section-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;margin-bottom:20px}.status{color:#555;text-transform:capitalize}.status.approved{background:#e8f4e8;border-color:#b7d8b7}.status.awaiting_approval,.status.ready_for_review,.status.changes_requested{background:#f5f0df}.messages{min-height:260px;border:1px solid #e4e4df;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:10px;margin-bottom:16px}.message{padding:13px 15px;border-radius:12px;max-width:80%;line-height:1.5}.message.user{align-self:flex-end;background:#111;color:#fff}.message.awe{align-self:flex-start;background:#f0f0ec}.empty{color:#777;padding:30px;text-align:center}.large{min-height:320px;display:flex;flex-direction:column;align-items:center;justify-content:center}.composer textarea,input{width:100%;border:1px solid #ccc;border-radius:10px;padding:13px;font:inherit;background:#fff}.composer{display:grid;gap:10px}.inline-form{display:flex;gap:10px}.inline-form input{flex:1}.button,button{font:inherit}.primary,.approve,.actions button{border:0;border-radius:10px;padding:12px 16px;cursor:pointer;background:#111;color:#fff}.primary:disabled,.approve:disabled,button:disabled{opacity:.45;cursor:not-allowed}.approve{margin-top:12px;width:100%}.side-panel .score{padding:18px 0;border-bottom:1px solid #eee}.score strong{font-size:40px;display:block}.score span{font-size:12px;color:#777}.fact{padding:12px 0;border-bottom:1px solid #eee}.fact small{color:#888}.fact p{margin:5px 0;color:#222}.finding{margin-top:18px;padding:16px;border-radius:12px;background:#f5f3eb}.finding ul{margin:10px 0 0;padding-left:20px;line-height:1.7}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:20px 0}.metrics>div{padding:15px;background:#f6f6f2;border-radius:12px}.metrics strong{font-size:24px;display:block;margin-top:7px}.metrics span{display:block;color:#666;font-size:11px;line-height:1.45;margin-top:8px}.strategy-grid{display:grid;grid-template-columns:.8fr 1.2fr;gap:35px;margin-top:25px}.strategy-grid h3{font-size:13px;text-transform:uppercase;letter-spacing:1px;margin-top:22px}.pages{display:grid;gap:10px}.pages>div{border:1px solid #e3e3df;border-radius:10px;padding:15px}.pages code{float:right;color:#888}.pages p{margin-bottom:0}.tags{display:flex;gap:6px;flex-wrap:wrap}.actions{display:flex;gap:10px;align-items:center;margin-top:22px}.actions .inline-form{flex:1}.actions .approve{width:auto;margin:0}.build pre{white-space:pre-wrap;max-height:220px;overflow:auto;background:#f6f6f2;padding:12px;border-radius:10px;font-size:11px}.error{margin:14px 0;padding:13px 15px;background:#f8e8e8;border:1px solid #e3bcbc;border-radius:10px;color:#7d2929}footer{padding:40px 0 0;color:#888;font-size:12px}.design-summary{display:grid;grid-template-columns:.7fr 1.5fr .8fr .8fr;gap:8px;margin:20px 0}.design-summary>div{padding:16px;background:#f6f6f2;border-radius:12px}.design-summary small{display:block;color:#888;margin-bottom:7px}.design-summary strong{font-size:18px}.design-grid{display:grid;grid-template-columns:1fr 1fr;gap:35px;margin-top:25px}.design-grid h3{font-size:13px;text-transform:uppercase;letter-spacing:1px;margin:24px 0 10px}.design-grid ul{margin:0;padding-left:20px;line-height:1.7;color:#444}.palette{display:grid;gap:8px}.palette>div{display:grid;grid-template-columns:18px 100px 1fr;gap:10px;align-items:center;padding:10px;border:1px solid #e3e3df;border-radius:10px}.palette span{width:18px;height:18px;border-radius:50%;background:#d8d8d2;border:1px solid #bbb}.palette small{color:#777;text-transform:capitalize}.palette strong{font-size:13px;font-weight:500}.secondary{border:1px solid #ccc;border-radius:10px;padding:12px 16px;cursor:pointer;background:#fff;color:#222}.actions .secondary{margin:0}.actions .approve{width:auto;margin:0}.design .finding{margin-top:24px}.spec-pages{display:grid;gap:12px;margin-top:22px}.spec-page{border:1px solid #e3e3df;border-radius:12px;padding:18px}.spec-page>div:first-child{display:flex;justify-content:space-between}.spec-page code{color:#888}.spec-page p{margin:10px 0 16px}.preview-pane{min-width:0}.preview-toolbar{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:10px}.preview-toolbar h3{margin:0 0 4px}.preview-toolbar small{color:#777}.preview-toolbar-actions{display:flex;gap:8px;align-items:center}.preview-link{display:inline-flex;align-items:center;text-decoration:none}.content-editor{display:grid;gap:12px}.content-editor textarea{width:100%;margin-top:14px;border:1px solid #ccc;border-radius:10px;padding:13px;font:inherit;background:#fff;resize:vertical}.preview-frame{width:100%;height:560px;border:1px solid #ddd;border-radius:12px;background:#fff}.preview-runtime-status{display:flex;align-items:center;gap:10px}.preview-runtime-status .status{display:inline-flex}.preview-runtime-status .secondary{margin:0}@media(max-width:800px){.preview-toolbar{align-items:stretch;flex-direction:column}.preview-toolbar-actions{width:100%}.preview-toolbar-actions>*{flex:1}.preview-frame{height:480px}}.deployment .actions{margin-bottom:22px}.deployment a{color:#111;text-decoration:underline}.spec-columns{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.spec-columns small{color:#888;text-transform:uppercase;letter-spacing:1px;font-size:10px}.spec-columns ul{margin:8px 0 0;padding-left:18px;line-height:1.6;color:#444}.workspace-bar{display:grid;grid-template-columns:1fr 1.8fr;gap:24px;align-items:center;margin:0 0 20px}.workspace-bar h2{margin:6px 0;font-size:22px}.workspace-bar p{margin:0;color:#666}.workspace-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.workspace-meta>div{padding:12px;background:#f6f6f2;border-radius:10px}.workspace-meta small{display:block;color:#888;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}.workspace-meta strong{font-size:13px;text-transform:capitalize}.status.archived{background:#eee;border-color:#ccc}@media(max-width:800px){.workspace-bar{grid-template-columns:1fr}.workspace-meta{grid-template-columns:repeat(2,1fr)}.project-controls{align-items:stretch;flex-direction:column}.project-switcher select{min-width:0;width:100%}.project-actions{justify-content:stretch}.project-actions button{flex:1}}@media(max-width:800px){.create-card,.grid,.strategy-grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.pipeline{grid-template-columns:1fr}.inline-form,.actions{flex-direction:column}.hero h1{letter-spacing:-2px}.actions .approve{width:100%}}
      `}</style>
    </main>
  );
}
