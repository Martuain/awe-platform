# ADR-0006 — Disposable Isolated Execution

**Status:** Accepted for CAP-008

**Context**

CAP-007 established that generated websites must never execute inside the AWE API or Studio process. CAP-008 needs a real execution boundary to prove that generated Next.js artifacts can be built safely enough for an MVP.

**Decision**

Use Docker containers as the first execution substrate. Each build gets an ephemeral workspace and container with explicit CPU, memory and PID limits, a read-only container root filesystem, restricted mounts and network-disabled build execution. Dependency acquisition is limited to the approved runtime dependency set and runs with npm lifecycle scripts disabled.

**Why not host subprocesses?**

A subprocess shares the host kernel and filesystem permissions and therefore is not an adequate boundary for untrusted generated code.

**Why not Kubernetes?**

Kubernetes can provide stronger orchestration and operational isolation, but it would introduce cluster-level infrastructure before AWE has demonstrated the basic build/runtime lifecycle.

**Why not Firecracker now?**

Firecracker/microVMs are a strong candidate for a future higher-assurance multi-tenant execution plane. At this stage, they would add substantial platform complexity without evidence that the current capability requires it.

**Consequences**

Positive:
- reproducible local execution;
- straightforward CI integration;
- explicit network/resource controls;
- clean migration boundary to a future sandbox service.

Negative:
- Docker becomes a local prerequisite for actual execution;
- dependency installation still requires a controlled network phase;
- container isolation is not equivalent to a hardened microVM boundary.

**Revisit when:** multi-tenant untrusted execution, public preview at scale, stronger compliance requirements, or sustained sandbox escape threat modelling makes container isolation insufficient.
