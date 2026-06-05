# plan.md — WealthTrack / Aurelius Agent (Local-First, UI-Aligned, Multi-Agent)

> **Read this first, Haiku.** This file is the source of truth. Build in tier order: 0 → 1 → 2 → 3 → 4.
> **Tiers 0–2 run entirely locally — no Google Cloud billing.** Cloud is Tier 3+. Tier 4 is the
> personalization/bonus layer — build it ONLY after Tiers 0–3 are green.
> This is a **migration**, not a greenfield rebuild. Swap the backend agent layer to ADK + Gemini 3.1.
> The frontend is the **Aurelius Omni-Asset Ledger**; the agents surface in its **Agent Insights** column.

---

## 0. Pinned facts — DO NOT "correct" these

- **Framework:** Google **ADK** (`google-adk`, Python ≥3.10). Real ADK `LlmAgent`s. NO hand-rolled
  `Thought:/Action:` loop. NO `@google/generative-ai` (JS). NO Gemma / open-weights surrogate.
- **Models (current-gen "Gemini 3"):** dev = `gemini-3.1-flash-lite`; demo = `gemini-3.1-pro-preview`.
  Never `gemini-2.0-flash`, `gemini-pro`, or any `gemma-*`.
- **Access:** Vertex AI. `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_LOCATION=global`.
- **Tools:** typed Python functions, native function calling.
- **Partner = Arize.** `openinference-instrumentation-google-adk` + `arize-phoenix-otel`, plus the
  Phoenix **MCP** server so the coordinator can read its own traces.
- **Memory (Tier 4):** Vertex AI **Memory Bank** via `VertexAiMemoryBankService`. Per-user, GCP-managed.
- **Hosting (Tier 3 only):** Cloud Run (scales to zero). NOT Agent Engine for serving.
- **Style:** one tool/agent/file per change; ask before adding a dependency.

---

## 1. Agent architecture — HOW MANY AGENTS (4 base, + dynamic goal agents in Tier 4)

A **coordinator + 3 specialists**, mapped 1:1 to the UI. Each is an ADK `LlmAgent`; the coordinator
delegates via `sub_agents=[...]`. The coordinator owns the seals (confirmation gating), memory, and
the Phoenix MCP self-reflection.

| Agent | Maps to (UI) | Tools | Produces |
|-------|--------------|-------|----------|
| **Aurelius** (coordinator / `root_agent`) | the whole Agent Insights column + the net-worth header | `remember`, `recall`, `calculate`, Phoenix MCP `query_traces` | routing, synthesis, the **Seal** gate |
| **Markets Steward** (sub-agent) | Portfolio + Liquid Assets | `get_net_worth`, `get_stock_quotes`, `search_web`, `fetch_url`, **`propose_rebalance`** | the **"Portfolio Strategy"** card + its *Review Proposal* seal |
| **Estate Steward** (sub-agent) | Tangible Wealth + Liabilities | `get_accounts` (asset class), `get_credit_cards`, `get_income` | the **"Liability Management"** counsel |
| **Concierge Steward** (sub-agent) | Concierge | **`propose_engagement`**, `send_alert` (Tier 3) | the **"Concierge Alert"** card + its approval seal |

**Tier 4 adds dynamic per-user goal sub-agents** (the Goal-Agent Factory, §9) instantiated at onboarding
from the person's goals — same templates, per-user config. Not codegen per user.

**Delegation:** coordinator uses LLM-driven transfer to sub-agents (ADK auto-flow). *Verify the exact
sub-agent/AgentTool API for your installed `google-adk` version before wiring.*
**Safe fallback:** if delegation misbehaves, collapse all sub-agent tools onto the coordinator.
**Keep specialists lean:** no specialist calls another specialist.

---

## 2. Where the agents surface in the Omni-Asset Ledger

- **Agent Insights cards** = the render of completed `/run_sse` runs; each is a tool-grounded finding.
- **"Review Proposal" (gold card)** = the **Seal** for `propose_rebalance` (Markets). Expanding it reveals
  the reasoning (the Notation) and offers **Approve / Decline**. No funds move until approved.
- **"Concierge Alert"** = the Seal for `propose_engagement` (Concierge).
- **"Liability Management"** = standing counsel from the Estate Steward.
- **Provenance footer** (ADD) = one discreet line: *steps · latency · faithfulness · view Arize trace*.
- **Reasoning (Notation)** lives INSIDE the expanded Review Proposal — calm by default, accountable on inspection.

---

## 3. Feature migration map (existing repo → this build)

12 existing tools → ADK FunctionTools, distributed across the 4 agents per §1. Label `get_stock_quotes`
`source: live|mock`; `calculate` uses a real parser; `remember`/`recall` scoped per user; `query_traces`
via Phoenix MCP. **New:** `propose_rebalance` (Markets) + `propose_engagement` (Concierge), both return
`requires_confirmation: true` and never execute. Frontend = the Aurelius Omni-Asset Ledger (keep, repoint).
**Tier 2:** evals. **Tier 3:** statements PDF, Sheets, notifications/cron. **Tier 4:** onboarding goal
extraction + Memory Bank. **Drop:** Perplexity, **Dynatrace, Elastic** (other tracks).

---

## 4. Repo layout

```
wealth-agent/
├─ .github/copilot-instructions.md       # paste §0
├─ wealth_agent/
│  ├─ __init__.py                         # from .agent import root_agent
│  ├─ agent.py                            # Aurelius coordinator, sub_agents=[markets, estate, concierge]
│  ├─ onboarding.py                       # Tier 4: extract goals → Firestore + Memory Bank
│  ├─ sub_agents/
│  │  ├─ markets.py                       # markets_agent + market/portfolio tools + propose_rebalance
│  │  ├─ estate.py                        # estate_agent + tangible/liability/income tools
│  │  ├─ concierge.py                     # concierge_agent + propose_engagement (+ send_alert Tier 3)
│  │  └─ goal_factory.py                  # Tier 4: make_goal_agent(goal, profile) -> LlmAgent
│  ├─ tools/
│  │  ├─ finance.py                       # get_net_worth, get_accounts, get_credit_cards, get_income, get_profile
│  │  ├─ market.py                        # get_stock_quotes, search_web, fetch_url
│  │  ├─ actions.py                       # propose_rebalance, propose_engagement, send_alert
│  │  ├─ memory.py                        # remember, recall (per-user)
│  │  └─ utils.py                         # calculate
│  ├─ instrumentation.py                  # Arize/Phoenix tracing
│  └─ data/ ...                           # existing JSON, single source of truth
├─ frontend/                              # Aurelius Omni-Asset Ledger, repointed
├─ tests/test_tools.py
├─ eval/golden.jsonl
├─ requirements.txt
├─ .env.example
├─ Dockerfile                             # Tier 3
├─ terraform/{main,variables,outputs}.tf  # Tier 3
├─ LICENSE                                # MIT, 2026
└─ README.md
```

`requirements.txt`: `google-adk`, `google-cloud-aiplatform[adk,agent_engines]` (the `agent_engines`
extra also covers Memory Bank), `arize-phoenix-otel`, `openinference-instrumentation-google-adk`,
your stock provider, `pdfplumber` (Tier 3), `python-dotenv`, `pytest`.

---

## 5. TIER 0 — Coordinator works alone, locally (no cloud)

- **0.1** Scaffold repo + `.env` (`MODEL=gemini-3.1-flash-lite`). `pip install -r requirements.txt`.
- **0.2** Move existing data JSON into `wealth_agent/data/` (single source of truth).
- **0.3** `instrumentation.py` (snippet below).
- **0.4** Port the 5 read tools in `tools/finance.py`.
- **0.5** `agent.py`: `root_agent = Aurelius` as a single `LlmAgent` with the 5 read tools (NO sub-agents yet).
- **0.6** `docker run -p 6006:6006 arizephoenix/phoenix:latest`, then `adk web`.
- **Acceptance:** "what's my net worth?" → calls `get_net_worth`; **nested** `agent→llm→tool` trace in Phoenix.

```python
# instrumentation.py
from phoenix.otel import register
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
def init_tracing():
    tp = register(project_name="aurelius-agent", auto_instrument=True)
    GoogleADKInstrumentor().instrument(tracer_provider=tp)
```

---

## 6. TIER 1 — Split into 4 agents + oversight (no cloud)

- **1.1** Add the remaining tools: `market.py`, `utils.py` (safe `calculate`), `memory.py` (per-user).
- **1.2** Create `sub_agents/markets.py`, `estate.py`, `concierge.py` — each an `LlmAgent` with its tools (§1).
- **1.3** Add the two seals in `actions.py`: `propose_rebalance` + `propose_engagement` — return
  `requires_confirmation: true`, never execute.
- **1.4** `agent.py`: give Aurelius `sub_agents=[markets, estate, concierge]`; delegate by domain, require
  the owner's confirmation before any seal resolves.
- **1.5** `pytest -q` green on pure-logic tools.
- **Acceptance:** "rebalance toward 60/40" → routes to Markets → proposal + halt. "book chalet maintenance"
  → routes to Concierge → proposal + halt. All 12 tools reachable.

---

## 7. TIER 2 — Arize differentiator + evals + UI wiring (no cloud)

- **2.1** Phoenix **MCP** toolset on the coordinator (`npx -y @arizeai/phoenix-mcp@latest`) for `query_traces`.
  *Verify the exact ADK MCP class/import for your installed version first.*
- **2.2** Port the golden dataset → `eval/golden.jsonl`; add an Arize LLM-as-judge eval.
- **2.3** **Wire the UI:** repoint the Ledger at the ADK API server. Agent Insights render from `/run_sse`;
  *Review Proposal* drives the seal; add the **Provenance footer**.
- **Acceptance:** a repeat question is answered after consulting past traces; eval scores; the Ledger talks
  to the agents end-to-end locally and renders all three rites.

---

## 8. TIER 3 — Cloud validation + richer features (LAST of the core, cheap)

- **3.1** Flip `MODEL=gemini-3.1-pro-preview`; re-run Tier 2 once.
- **3.2** Dockerfile (ADK FastAPI entry, port 8000); `docker build` + local curl passes.
- **3.3** Terraform: APIs (`run`,`aiplatform`,`artifactregistry`,`secretmanager`,`firestore`),
  Artifact Registry, service account (`roles/aiplatform.user`), Secret for `PHOENIX_API_KEY`,
  `google_cloud_run_v2_service` (image + env + secret), public `roles/run.invoker`.
  **Terraform owns the service — do NOT also `adk deploy cloud_run`.** `gcloud builds submit` → `terraform apply`.
- **3.4** Phoenix Cloud key via Secret Manager so the hosted demo keeps tracing.
- **Optional:** `read_statement(pdf)`, `import_from_sheet`, `send_alert` + scheduled weekly review.
- **Acceptance:** public Cloud Run URL responds; traces land in Phoenix Cloud.

---

## 9. TIER 4 — Personalization: per-user goal agents + Memory Bank (BONUS; after 0–3 are green)

> Goal: the moment a person onboards, build a personalized roster of goal sub-agents tied to their
> current and future goals, and have those agents improve for that person over time via GCP-native
> long-term memory. This is the documented "personalized multi-agent + Memory Bank" pattern.
> Do NOT generate new agent *code* per user — instantiate from templates and personalize via memory.

**Prereqs:** Tiers 0–3 green; a GCP project with the Agent Platform/Agent Engine API enabled; create an
**Agent Runtime** (required to use Memory Bank — note: you do NOT need to deploy your serving agent there).

- **4.1 Onboarding goal-extraction (`onboarding.py`).** The Onboarding agent reads `get_profile` + a short
  intake, derives a structured goal list (e.g. `[{id, name:"retirement", horizon, target}, ...]`), and
  writes it to Firestore (source of truth) AND seeds Memory Bank for that `user_id`. **Validate/sanitise
  extracted goals** before storing (poisoning guard).
- **4.2 Wire Memory Bank.** Use `VertexAiMemoryBankService`; start the server with
  `--memory_service_uri agentengine://<agent_engine_id>`. Add **`PreloadMemoryTool`** to the coordinator
  (proactively briefs every session with this person's goals/context) and **`LoadMemoryTool`** to the
  specialists (on-demand deeper recall). *Verify the exact ADK memory class/tool names for your installed
  version before writing.*
- **4.3 Goal-Agent Factory (`sub_agents/goal_factory.py`).** Write `make_goal_agent(goal, profile) -> LlmAgent`
  — one template, parameterised by goal name + instruction + the relevant existing tools (e.g. a "retirement"
  goal agent gets `get_net_worth`, `get_income`, `calculate`, `propose_rebalance`). At session start, the
  coordinator reads the user's active goals and instantiates one goal-agent per goal, attached as
  `sub_agents` (cap at ~3 to bound latency/cost). Same code, per-user config — never codegen.
- **4.4 The adaptive loop.** At session end, persist new facts to Memory Bank (ADK callback). When goals
  change, the coordinator re-derives the roster next session. Combine Memory Bank (who the person is) with
  Phoenix `query_traces` (how well it served them) so the coordinator improves per person — the Arize
  bonus-points behaviour.
- **4.5 Guardrail.** The **seals still gate every action** — even a poisoned memory cannot move funds or
  book anything without the owner's Approve. Keep memory advisory, not authoritative for actions.
- **Acceptance:** a returning user is greeted with their goals preloaded (PreloadMemoryTool); a new goal
  stated in one session appears in the next; a per-goal sub-agent answers a goal-specific question; all
  actions still require a seal.

---

## 10. Cost guardrails
$100 hackathon credit / free trial. Iterate on `gemini-3.1-flash-lite`. Phoenix free. Cloud Run scales to
zero. Avoid Agent Engine for *serving*. **Tier 4 note:** Memory Bank needs an Agent Runtime (a standing
resource) and incurs storage + Gemini-extraction cost — use the credit, set a TTL on memories, keep intake
short, and a $10 budget alert. 4 agents (+ goal agents) = more model hops, so dev on flash-lite.

## 11. Compliance checklist
- [ ] Public Cloud Run URL works (Stage-One gate)
- [ ] Public repo, detectable MIT LICENSE
- [ ] ADK + Gemini 3.1 on Vertex (no Gemma)
- [ ] Arize: auto-tracing + Phoenix MCP self-reflection + Provenance footer
- [ ] Beyond chat: coordinator + 3 specialists, two human-confirmed seals
- [ ] All 12 tools + the Omni-Asset Ledger working
- [ ] Dynatrace/Elastic/Perplexity removed; no committed logs; real hosted URL in README
- [ ] ≤3-min video: a request → routing → Review Proposal seal → live Arize trace
- [ ] **BONUS (Tier 4):** onboarding → personalized goal agents + Memory Bank that improves over time
- [ ] Devpost: track = Arize, description, repo URL, hosted URL, video

## 12. Driving Haiku
One task at a time, in tier order. Build the coordinator alone (Tier 0) before sub-agents (Tier 1); build
the base four agents before Tier 4. Paste current Google/Arize/Memory-Bank doc snippets for any API call.
**Reject** output that uses `@google/generative-ai`, `gemini-2.0-flash`/`gemma-*`, text-parsed Thought/Action,
makes a `propose_*` tool execute, has a specialist call another specialist, or **generates new agent code per
user** (Tier 4 must instantiate from `make_goal_agent`, not write classes). Run each Acceptance check first.

## 13. Definition of Done
Aurelius routes to Markets, Estate, and Concierge specialists; all 12 tools work; the two seals
propose-and-wait; the agent consults its own Phoenix traces; runs on `gemini-3.1-pro-preview` via Vertex;
the Omni-Asset Ledger renders Agent Insights + Review Proposal + Provenance from `/run_sse`; deployed to a
public Cloud Run URL via Terraform; clean nested traces in Arize; Dynatrace/Elastic removed; all §11 boxes
ticked. **Bonus complete when** onboarding spins up per-user goal agents from the Goal-Agent Factory, Memory
Bank preloads each returning owner's goals, and the system improves per person while every action stays sealed.