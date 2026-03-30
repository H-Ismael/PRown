# PRown - PR Comprehension Gate (MVP)

Quality gate for GitHub pull requests that checks whether the PR author understands the code they are proposing.

## What this MVP does

- receives GitHub PR webhook events (`opened`, `synchronize`, `reopened`)
- creates a comprehension session per PR head SHA
- fetches changed files from GitHub and normalizes diff metadata
- loads a versioned policy from YAML (`policies/generic_v1.yaml`)
- generates 1-2 comprehension questions from the diff
- provides a minimal answer UI (`/sessions/{id}/ui`)
- evaluates answers (stub evaluator by default, LiteLLM provider included)
- computes deterministic pass/fail gate decision from policy thresholds
- posts GitHub check-run + PR comment with constructive feedback and ideal answers
- stores sessions, questions, answers, evaluations, decisions in Postgres

## Architecture

```text
GitHub PR Event -> /webhooks/github -> Orchestration Service
                                       -> Diff Service
                                       -> Policy Service
                                       -> Question Service (LLM provider)
Author UI /sessions/{id}/ui ---------> /sessions/{id}/answers
                                       -> Evaluation Service (LLM provider)
                                       -> Decision Service
                                       -> Reporting Service
                                       -> GitHub check run + comment
                                       -> Postgres persistence
```

## Repository layout

```text
app/
  api/routes/               # HTTP routes
  core/                     # settings + webhook signature verification
  domain/services/          # orchestration, policy, diff, q/eval, decision, reporting
  integrations/github/      # github mapper/client/reporter
  integrations/llm/         # provider abstraction + implementations
  persistence/              # SQLAlchemy db/models
  web/templates/            # minimal author UI
policies/generic_v1.yaml    # versioned policy file
.github/workflows/          # sample GitHub Action trigger
```

## Quick start (Docker)

1. Copy environment template:

```bash
cp .env.example .env
```

2. Set required values in `.env`:

- `GITHUB_WEBHOOK_SECRET` (shared secret with GitHub Action/webhook)
- `GITHUB_TOKEN` (token with checks + PR comment permissions)
- Optional (LiteLLM): `LLM_PROVIDER=litellm`, `LLM_MODEL=<provider/model>`, `LLM_API_KEY=...`
- Example OpenAI model: `LLM_MODEL=openai/gpt-4o-mini`
- Example Mistral model: `LLM_MODEL=mistral/mistral-small-latest`

3. Start services:

```bash
docker compose up --build
```

4. Health check:

```bash
curl http://localhost:8000/health
```

## GitHub integration

Use `.github/workflows/pr_gate_trigger.yml` in your target repository and set secrets:

- `PR_GATE_WEBHOOK_URL` (e.g. `https://your-host/webhooks/github`)
- `PR_GATE_WEBHOOK_SECRET` (must match backend `.env`)

Then mark `pr-comprehension-gate` as a required status check in branch protection.

## API endpoints

- `POST /webhooks/github`
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/answers`
- `GET /sessions/{session_id}/result`
- `GET /sessions/{session_id}/ui`
- `GET /policies`
- `GET /health`

## Notes

- Default evaluator is deterministic stub logic for local development.
- LiteLLM integration expects JSON-only outputs and is intentionally isolated behind provider methods.
- Current implementation creates DB schema at app startup (`create_all`) for MVP speed.
