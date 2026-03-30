# MVP Spec v0 — PR/MR Comprehension Gate

## 1. Purpose

Build a **GitHub pull request comprehension gate** that verifies whether the author understands the submitted code diff before merge.

The system should:

- generate targeted questions from the PR diff using LLM calls,
- evaluate the author’s answers using LLM calls,
- block merge when understanding is insufficient,
- always provide the constructive and adequate answer afterward,
- remain extensible so later versions can support:
  - GitLab,
  - richer policy engines,
  - admin/customization UI,
  - analytics,
  - multi-team policy management.

---

## 2. Product Objective

### Core Objective

Prevent **unowned code** from entering the codebase by requiring a minimum demonstration of understanding at PR time.

### Secondary Objectives

- improve PR quality,
- reduce reviewer cognitive burden,
- preserve engineering ownership in AI-assisted development,
- introduce constructive friction,
- create a foundation for policy-driven governance across teams.

---

## 3. Scope of MVP

### In Scope

- GitHub PR trigger
- generic first policy
- Dockerized backend
- FastAPI-based API/service
- Postgres persistence
- LLM-based question generation
- LLM-based answer evaluation
- pass/fail merge gate
- constructive feedback with ideal answer
- minimal answer submission UI or structured submission path

### Out of Scope for MVP

- policy customization UI
- GitLab integration
- SSO/RBAC sophistication
- advanced analytics dashboard
- multi-tenant enterprise packaging
- fine-grained team admin workflows
- human reviewer moderation panel
- advanced cheating detection

---

## 4. High-Level Architecture

```text
GitHub Pull Request Event
        |
        v
GitHub Action / GitHub App Integration
        |
        v
Backend API (FastAPI)
        |
        +--> Diff Ingestion Module
        +--> Policy Resolution Engine
        +--> Question Generation Service (LLM)
        +--> Answer Collection API
        +--> Answer Evaluation Service (LLM)
        +--> Decision Engine
        +--> Feedback / Reporting Service
        +--> Policy Registry
        +--> Audit / Persistence Layer
        |
        v
Postgres
        |
        v
GitHub Status Check / PR Comment / Check Summary
```

---

## 5. Architectural Principles

### 5.1 Extensibility First

The MVP should not be a hardcoded script around GitHub Actions.

It should already separate:

- integration layer,
- policy layer,
- orchestration layer,
- evaluation layer,
- storage layer.

That way, later versions can add:

- policy editing UI,
- GitLab adapters,
- team-level configs,
- domain-specific rule packs,
- analytics and calibration tools.

### 5.2 Policy-Driven Behavior

Question generation and grading should be governed by external policy files, preferably YAML or JSON.

This matters because later:

- different teams will need different strictness,
- different file categories will need different prompts/rubrics,
- an admin UI can become a frontend over persisted policy definitions.

### 5.3 Clear Service Boundaries

Even if initially deployed as one service, internals should already be modular enough to split later if needed.

### 5.4 Constructive Failure

A failed answer must still produce:

- what was missing,
- why it failed,
- the ideal or adequate answer.

### 5.5 Risk-Weighted Friction

The architecture should assume later support for different levels of scrutiny depending on:

- changed paths,
- language,
- inferred risk,
- domain.

---

## 6. Deployment Shape

### Recommended MVP Deployment

```text
docker-compose
  - api            (FastAPI backend)
  - postgres       (persistence)
  - worker         (optional later, can be same service first)
```

### Why This Shape

- fast local development,
- simple deployment,
- easy portability,
- clear path to future scaling.

### Later Extensibility

This can later evolve into:

```text
- api
- background worker
- postgres
- redis / queue
- frontend-admin
- frontend-author
```

But the MVP should not start there.

---

## 7. Main Components

### 7.1 Integration Adapter Layer

#### Responsibility

Translate SCM platform events into internal workflow jobs.

#### MVP Adapter

- `github_adapter`

#### Later Adapters

- `gitlab_adapter`
- potentially `bitbucket_adapter`

#### Responsibilities

- receive PR metadata,
- fetch diff / changed files,
- map repo/branch/PR identifiers,
- publish result back as:
  - status check,
  - PR comment,
  - check summary.

#### Design Note

This layer should be isolated from policy logic and LLM logic.

GitHub/GitLab differences belong here, not everywhere.

---

### 7.2 Orchestrator

#### Responsibility

Run the end-to-end comprehension gate workflow.

#### Workflow Responsibilities

- start assessment on PR event,
- select applicable policy,
- request questions,
- persist session,
- receive answers,
- request evaluation,
- compute final decision,
- publish result.

#### Why Explicit Orchestration Matters

Without this layer, logic becomes scattered between webhooks, API handlers, and prompt code.

A dedicated orchestrator keeps the flow stable as the system grows.

---

### 7.3 Diff Ingestion and Preprocessing

#### Responsibility

Normalize incoming PR change data into a form suitable for policy selection and LLM prompting.

#### Input

- repo
- PR number
- base branch
- head branch / head SHA
- PR title/description
- changed files
- patch/diff text

#### Output

Internal normalized diff object.

#### Internal Tasks

- filter irrelevant files,
- ignore binaries,
- ignore generated artifacts,
- identify file extensions/languages,
- compute stats:
  - files changed,
  - additions/deletions,
  - touched paths,
- optionally chunk large diffs.

#### Future Extensibility

Later this module can enrich diffs with:

- code owners,
- critical path tagging,
- dependency change detection,
- risk heuristics,
- semantic file classification.

---

### 7.4 Policy Engine

#### Responsibility

Resolve which policy should govern the PR.

#### MVP Behavior

Use a single generic policy file.

#### Future Behavior

Resolve policy based on:

- repo,
- team,
- path,
- language,
- risk class,
- project metadata.

#### Policy Engine Responsibilities

- load policy from file/database,
- validate schema,
- select active policy,
- merge policy inheritance later if needed.

#### Important Design Choice

Even if the first version has only one generic policy, build the engine as if multiple policies will exist.

---

### 7.5 Policy Registry

#### Responsibility

Store and serve policy definitions.

#### MVP Storage

Filesystem-based YAML/JSON files.

Example:

```text
/policies
  generic_v1.yaml
```

#### Later Extension

Policies can be stored in DB and edited from a UI.

That future UI should not require rewriting policy logic; it should only change the source of policy definitions.

---

### 7.6 Question Generation Service

#### Responsibility

Generate comprehension questions from:

- diff,
- policy,
- metadata.

#### Input

- normalized diff,
- policy,
- repository metadata,
- optional risk tags.

#### Output

Structured question set.

#### Constraints

Questions should be:

- short,
- diff-grounded,
- high-information,
- non-trivial,
- focused on understanding rather than memorization.

#### MVP Output Shape

- 1 or 2 questions,
- each with:
  - id,
  - text,
  - type,
  - expected focus.

#### Note

This service uses LLM calls but should expose a stable internal contract, so the rest of the app is not coupled to one model provider.

---

### 7.7 Answer Collection Layer

#### Responsibility

Receive and persist author responses.

#### MVP Options

##### Option A

Structured PR comment command

##### Option B

Minimal web UI

#### Recommended

A **small web UI** backed by FastAPI.

Why:

- cleaner UX,
- easier validation,
- better future extensibility,
- straightforward transition to richer author/reviewer/admin UIs later.

#### Future Extensibility

This subsystem can later support:

- retry flow,
- timer UX if ever needed,
- reviewer overrides,
- hints,
- answer history,
- analytics.

---

### 7.8 Answer Evaluation Service

#### Responsibility

Evaluate author answers using LLM calls under policy-defined rubric.

#### Input

- diff,
- policy,
- question,
- author answer.

#### Output

Structured evaluation result:

- score,
- pass/fail,
- missing points,
- rationale summary,
- ideal answer.

#### Critical Design Principle

The service should evaluate with a **rubric**, not vague judging.

That rubric should be policy-driven.

#### Why This Matters

It is the main place where trust can fail if behavior is inconsistent.

---

### 7.9 Decision Engine

#### Responsibility

Combine per-question results into a final merge decision.

#### MVP Logic

Configurable thresholds, for example:

- average score threshold,
- per-question minimum,
- all-questions-pass mode.

#### Output

- final pass/fail,
- summary reason,
- constructive feedback bundle,
- reviewer summary.

#### Why Separate This

Question generation and answer grading are probabilistic; merge gating must remain deterministic after those outputs are received.

---

### 7.10 Feedback and Reporting Service

#### Responsibility

Generate human-readable feedback for:

- author,
- reviewer,
- GitHub check summary.

#### Must Include

- result,
- short explanation,
- ideal answer(s),
- constructive feedback.

#### Optional Reviewer Artifact

A short summary such as:

- claimed behavior change,
- acknowledged risk,
- missing understanding area,
- final gate result.

#### Later Extensibility

This service can later feed:

- dashboards,
- audit logs,
- trend analysis,
- policy calibration tooling.

---

### 7.11 Persistence Layer

#### Responsibility

Store durable workflow state and audit artifacts.

#### MVP DB

Postgres.

#### Why

- simple,
- robust,
- easy with FastAPI ecosystem,
- future-safe enough.

---

## 8. Suggested Internal Modules

A clean monorepo or service layout could look like this:

```text
app/
  api/
    routes/
      github_webhooks.py
      sessions.py
      answers.py
      policies.py
  core/
    config.py
    logging.py
    security.py
  domain/
    models/
    schemas/
    services/
      orchestration_service.py
      policy_service.py
      diff_service.py
      question_service.py
      evaluation_service.py
      decision_service.py
      reporting_service.py
  integrations/
    github/
      client.py
      mapper.py
      reporter.py
    llm/
      provider.py
      prompt_builder.py
      response_parser.py
  persistence/
    db.py
    models.py
    repositories/
  policies/
    generic_v1.yaml
  web/
    templates/ or static/
tests/
docker-compose.yml
Dockerfile
README.md
```

This keeps internal boundaries clean while still shipping as one deployable service initially.

---

## 9. Data Model

### Core Entities

#### Repository

Represents repo-specific configuration and future policy binding.

Fields:

- id
- provider
- external_repo_id
- name
- default_branch
- created_at

#### PullRequestSession

Represents one comprehension-gate session for one PR SHA.

Fields:

- id
- repository_id
- provider
- pr_number
- head_sha
- base_sha
- status
- policy_id
- created_at
- updated_at

#### DiffArtifact

Stores normalized diff and metadata.

Fields:

- id
- session_id
- raw_diff
- normalized_diff
- file_count
- additions
- deletions
- languages_detected

#### QuestionSet

Represents generated questions for a session.

Fields:

- id
- session_id
- generator_model
- policy_version
- generated_at

#### Question

Fields:

- id
- question_set_id
- question_key
- type
- text
- expected_focus
- order_index

#### AnswerSubmission

Fields:

- id
- session_id
- submitted_by
- submitted_at
- raw_payload

#### Answer

Fields:

- id
- submission_id
- question_id
- answer_text

#### EvaluationResult

Fields:

- id
- answer_id
- evaluator_model
- score
- passed
- rationale_summary
- missing_points
- ideal_answer
- created_at

#### GateDecision

Fields:

- id
- session_id
- final_score
- passed
- decision_reason
- reviewer_summary
- decided_at

#### PolicyRecord

Optional in DB for MVP, but useful later.

Fields:

- id
- policy_id
- version
- source_type
- source_path
- checksum
- active

---

## 10. API Surface

### MVP API Endpoints

#### `POST /webhooks/github`

Receives GitHub webhook or Action callback.

#### `GET /sessions/{session_id}`

Returns session status and questions.

#### `POST /sessions/{session_id}/answers`

Submits answers.

#### `GET /sessions/{session_id}/result`

Returns evaluation result.

#### `GET /policies`

Initially read-only list or metadata.

#### `GET /health`

Health check.

### Later Endpoints

- policy CRUD,
- team-policy assignments,
- analytics,
- calibration review,
- override actions,
- admin auth.

---

## 11. Workflow Sequence

### Step 1 — PR Event Received

GitHub integration triggers on:

- PR opened,
- PR synchronized,
- PR reopened.

### Step 2 — Session Created

Backend creates a `PullRequestSession` for the head SHA.

### Step 3 — Diff Fetched and Normalized

Diff ingestion module processes the change set.

### Step 4 — Policy Resolved

For MVP: `generic_v1`.

### Step 5 — Questions Generated

Question service calls LLM and persists 1–2 questions.

### Step 6 — Author Answers

Through minimal web UI or structured comment flow.

### Step 7 — Answers Evaluated

Evaluation service calls LLM with rubric and returns structured output.

### Step 8 — Decision Made

Decision engine computes pass/fail.

### Step 9 — Feedback Published

GitHub check/comment updated with result and constructive answer.

### Step 10 — Merge Gate Enforced

GitHub required status check blocks or allows merge.

---

## 12. Policy Schema Direction

Start with YAML because it is more editable for humans.

### Policy Responsibilities

A policy should define:

- scope,
- triggers,
- questioning rules,
- grading rules,
- feedback behavior,
- future metadata hooks.

### Example Policy Shape

```yaml
metadata:
  policy_id: generic_v1
  version: 1
  name: Generic Comprehension Policy

selection:
  include_paths:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude_paths:
    - "**/*.md"
    - "**/docs/**"
  min_changed_lines: 10

questioning:
  max_questions: 2
  types:
    - behavior_change
    - risk_identification
    - invariant_preservation
  constraints:
    - avoid trivial wording
    - avoid style-only questions
    - anchor in concrete diff behavior

grading:
  pass_threshold: 0.75
  min_question_score: 0.50
  allow_partial_credit: true
  require_behavioral_grounding: true

feedback:
  reveal_ideal_answer: true
  constructive_mode: true
  generate_reviewer_summary: true
```

---

## 13. LLM Abstraction Layer

This is important for extensibility.

### Do Not Hardwire Business Logic to One Provider

Create an internal interface such as:

- `generate_questions(...)`
- `evaluate_answer(...)`

with provider implementations underneath.

### Why

Later you may want:

- OpenAI,
- Anthropic,
- local model,
- hybrid model routing,

without rewriting orchestration.

### Also Useful Later

You may route:

- cheap model for question generation,
- stronger model for evaluation,
- domain-specific model for some teams.

---

## 14. Minimal Frontend Strategy

### MVP Recommendation

A tiny server-rendered or lightweight SPA answer page.

It only needs:

- PR/session identification,
- rendered questions,
- text areas for answers,
- submit button,
- result view.

### Why This Matters for Extensibility

That same UI layer can later evolve into:

- author portal,
- policy testing sandbox,
- admin policy editor,
- reviewer audit panel.

So even though the customization UI is not in scope now, the answer UI should not be designed as a dead end.

---

## 15. Extensibility Plan for Future Policy UI

Even now, the architecture should assume that policies will later be editable through a UI.

To support that later without refactoring, do this now:

### 15.1 Separate Policy Storage from Policy Execution

The engine should consume a validated internal policy object, regardless of whether it came from:

- a file,
- a database,
- an API.

### 15.2 Introduce Policy Schema Validation Now

Use a schema model so later UI-submitted policies are validated the same way as file-based ones.

### 15.3 Keep Policy IDs and Versions Explicit

This will matter later for:

- auditability,
- rollback,
- A/B testing,
- policy evolution.

### 15.4 Store Policy Version With Every Gate Session

Otherwise later it will be hard to explain why a session passed or failed.

---

## 16. Non-Functional Requirements

### Reliability

- no duplicated sessions for same PR SHA unless intended,
- safe webhook handling,
- idempotent reporting when possible.

### Auditability

Store:

- policy version,
- questions,
- answers,
- evaluator outputs,
- final decision,
- timestamps.

### Performance

MVP can tolerate moderate latency, but should avoid feeling broken.

Targets:

- question generation: fast enough for PR workflow,
- answer evaluation: near-interactive.

### Security

- verify GitHub webhook signatures,
- protect answer submission routes,
- do not expose secrets in logs,
- sanitize stored artifacts.

### Maintainability

- modular service boundaries,
- clear schemas,
- provider abstraction for LLM layer.

---

## 17. Risks to Design Against

### 17.1 Tight GitHub Coupling

**Mitigation:** isolate SCM integration in adapter layer.

### 17.2 Policy Sprawl Later

**Mitigation:** formal policy schema now and versioning now.

### 17.3 LLM Output Inconsistency

**Mitigation:**

- structured outputs,
- schema validation,
- rubric-based grading,
- explicit parsing/retry logic.

### 17.4 UI Dead End

**Mitigation:** answer UI as standalone module, not embedded ad hoc in comments logic.

### 17.5 Monolith Turning Messy

**Mitigation:** modular internals even if one deployable container initially.

---

## 18. Suggested MVP Milestone Breakdown

### Milestone 1 — Skeleton

- FastAPI app
- Postgres
- Docker/docker-compose
- GitHub webhook endpoint
- session creation
- health check

### Milestone 2 — Diff + Policy

- GitHub diff retrieval
- normalized diff storage
- generic policy loader
- schema validation

### Milestone 3 — Question Generation

- LLM integration for question generation
- question persistence
- basic session UI/API

### Milestone 4 — Answer Submission

- minimal answer UI
- answer persistence

### Milestone 5 — Evaluation + Decision

- LLM evaluation
- threshold logic
- ideal answer generation
- final decision persistence

### Milestone 6 — Reporting + Gate

- GitHub status/check updates
- merge-blocking integration
- constructive PR feedback

### Milestone 7 — Hardening

- logging
- retries
- failure modes
- policy version auditing

---

## 19. Recommended First Tech Choices

### Backend

- FastAPI

### Database

- Postgres

### ORM / DB Layer

- SQLAlchemy or SQLModel

### Validation

- Pydantic

### Config

- environment variables + typed settings

### Containerization

- Docker + docker-compose

### Background Processing

- can wait initially,
- later: Celery / RQ / Dramatiq / async worker.

### Frontend

- minimal server-rendered templates or small frontend,
- keep simple for MVP.

---

## 20. Final Architectural Recommendation

For the MVP, build this as:

**one Dockerized FastAPI service with modular internals, backed by Postgres, integrated with GitHub Actions/checks, and driven by external versioned policy files.**

That gives:

- speed now,
- enough structure for future scaling,
- a clean path toward:
  - policy customization UI,
  - GitLab support,
  - richer governance features.

---

## 21. Short Executive Summary

This MVP should not be built as a brittle script around GitHub hooks. It should be built as a small but properly layered platform:

- **SCM adapter** for GitHub now, GitLab later,
- **policy engine** backed by versioned YAML/JSON definitions,
- **LLM services** for question generation and answer evaluation,
- **decision engine** for deterministic merge gating,
- **FastAPI backend** and **Postgres persistence**,
- **minimal author UI** that can evolve later into richer policy/admin interfaces.

That structure is small enough to ship, but not so narrow that it collapses when you add policy customization later.
