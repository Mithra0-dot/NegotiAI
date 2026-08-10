# NegotiationSim — AI-Powered Negotiation Training Simulator

## What this project is
A negotiation practice platform where users pick a scenario, then negotiate 
against an adaptive LLM agent. The agent tracks negotiation state, detects 
concession signals in real time, and adjusts its strategy accordingly. 
Sessions are scored against negotiation frameworks (BATNA discipline, 
anchoring, concession pacing) with a statistically rigorous simulated 
A/B testing layer comparing agent strategy versions.

## Tech stack (do not swap without asking)
- Frontend: React (dark theme), Recharts for scorecard visualizations
- Backend: FastAPI (Python)
- Database: PostgreSQL (NOT SQLite — Render's disk is ephemeral, will 
  wipe on redeploy/restart)
- LLM/Agent orchestration: LangChain (or a custom state machine if 
  LangChain adds unnecessary overhead — confirm before switching)
- NLP: small transformer for concession-signal classification 
  (hedging language, premature agreement, urgency detection)
- Stats: scipy/statsmodels for A/B test significance testing 
  (t-test / chi-squared, confidence intervals — no eyeballing results)
- Experiment tracking: MLflow (agent strategy versions, eval scores, 
  A/B test results)
- CI/CD: GitHub Actions (eval suite runs on every prompt/strategy change, 
  blocks merge on scoring-consistency regression)
- Containerization: Docker
- Deployment: Render (backend + Postgres)

## Core features (MVP — build in this order)

1. **Scenario picker (landing screen)**
   - Card grid: Salary Negotiation, Freelance Rate, Apartment Lease, 
     Cofounder Equity Split
   - Each card: scenario name, 1-2 line persona blurb, difficulty badge 
     (Easy/Medium/Hard), opponent style hint
   - Selecting a card starts a new session with that scenario's config 
     (persona, goals, constraints, target/walk-away values)
   - This is the first screen a user/reviewer sees — needs to look 
     genuinely polished, not an afterthought

2. **Persona-driven negotiation agent**
   - Configurable persona per scenario (goals, budget/constraints, 
     personality, opening tactic)
   - Chat interface, dark theme, clean message bubbles

3. **Strategy state machine**
   - Tracks negotiation phase: opening → probing → bargaining → closing
   - Tactic selection per phase: anchoring, silence, deadline pressure, 
     good-cop/bad-cop

4. **Concession-signal classifier**
   - Reads each user message for: unforced concessions, hedging, 
     urgency/anxiety language, premature agreement
   - Feeds directly into the agent's adaptive difficulty logic

5. **Live in-session tactic tagging**
   - Real-time inline tags next to each user message (e.g. "Anchoring", 
     "Unforced concession") — this needs to feel reactive, not delayed

6. **Post-session scorecard (dashboard, not plain text)**
   - Recharts radar/bar chart: anchoring effectiveness, concession 
     pacing, BATNA discipline
   - Annotated transcript with inline flags (color-coded by tactic type)
   - Outcome vs target vs walk-away point

7. **Session history + progress tracking**
   - Postgres `sessions` table: user, scenario, score, date, outcome
   - Line chart: score trend across sessions over time

## Stretch features (in scope, build after MVP is solid)

- **Simulated A/B testing of agent strategy versions**
  - Generate synthetic negotiation transcripts (LLM role-plays as 
    different user types: aggressive, passive, data-driven)
  - Run 50-100+ simulated sessions per strategy variant
  - Apply real statistical testing (t-test/chi-squared) on outcome 
    scores between variants — report p-values and confidence intervals
  - Implement as an actual traffic-splitting layer in the backend 
    (route % of new sessions to variant A vs B), even though traffic 
    is simulated — mirrors real experimentation infra
  - IMPORTANT: always frame this as "simulated A/B test" in UI/docs/
    README — never imply live production traffic
- Adjustable opponent difficulty/style presets (aggressive, 
  collaborative, data-driven) selectable at scenario start
- Downloadable session scorecard as PDF

## Explicitly out of scope for now (do not build unless asked)
- Voice mode (speech-to-text/text-to-speech)
- Any feature requiring real user traffic at scale

## Conventions
- Python 3.11, virtual environment (venv)
- Keep agent persona/strategy configs in dedicated files (e.g. 
  `personas/`, `strategies/`), not inline strings — needed for the 
  eval suite and A/B variant comparison to diff cleanly
- All eval + A/B test logic lives in `eval/`, runnable standalone 
  via pytest
- API keys go in `.env`, which must be in `.gitignore` before first 
  commit — never commit keys
- Explain the plan before writing code for any new feature; keep 
  changes scoped to one feature at a time
- Comment complex logic (strategy state machine, statistical testing 
  logic especially) — this project will be explained in interviews, 
  every design decision needs to be defensible