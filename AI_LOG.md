# AI_LOG — Kestrel Motor Group: Data & AI Challenge

A record of every material use of AI in this project: what was asked, what it produced, how it was checked, and the verdict. Entries are added by the orchestrator after each agent run or conversation; the **Verified by** and **Verdict** fields are completed by the owner.

## Tools in use

| Tool | Role |
|---|---|
| Claude (Opus 5.5, claude.ai project) | Planning, orchestration, coding assistant, agent runs in the cloud workspace |
| Open-source sentiment model (Hugging Face) | Comment sentiment |
| sentence-transformers / BERTopic | Theme discovery and assignment |
| Ollama + 3B open-source LLM (optional) | Richer theme reasoning on negative/mixed comments |

## Summary of AI errors caught

Fill this in as you go. It becomes the "where AI got it wrong" section of the technical report.

| # | Entry | What the AI got wrong | How it was caught | Fix |
|---|---|---|---|---|
| | | | | |

---

## Entry template

```
### AI-NNN · <wave/phase> · <agent or conversation> · <date>
- **Tool / model:**
- **Task / key prompt:** <brief link or one-paragraph summary>
- **Output:** <files / commit>
- **Checks performed:** <what you looked at, sample sizes, reconciliations>
- **Issues found:**
- **Verdict:** Accepted / Corrected / Rejected — <why>
- **Verified by:** <owner, date>
```

---

## Entries

### AI-001 · Planning · Planning conversation (Claude) · 28–29 Oct 2026
- **Tool / model:** Claude Opus 5.5 (claude.ai, project "PS Take Home – Kestral Motor Group Analysis").
- **Task / key prompts:**
  - "Read the brief, then help me create a plan for how to address the problems listed."
  - "Visualise the plan as a flow chart and suggest alternative ways to organise it, given under 36 hours."
  - "Detail the setup and PII guardrails step."
  - "How much will I need to do manually vs defer to AI?" · "Suggest a tech stack per phase; everything must be reproducible." · "Ask me at least 7 questions so the plan is defensible." · "Where can agents be used, and how should a master agent orchestrate?" · "Add more human-in-the-loop approval."
- **Output:** phased plan, flow chart, PII policy, tech stack, decision questions, agent map and waves, HITL control loop and gates; written up as `PLAN.md`, `DECISIONS.md`, and this file.
- **What the owner decided (not the AI):** unit of analysis; definition of negative; per-site joining; dropping customer identifiers; including the closed site; two reports; non-negotiables; zero budget / open source; no Colab; Docker for the LLM; extra HITL gates G7 and G9; separate conversations per phase.
- **Where the AI's suggestions were changed by the owner:**
  - AI initially proposed hashing customer identifiers → owner chose to drop them (identity is inconsistent and not needed).
  - AI initially assumed a paid LLM API → owner set zero budget; plan switched to open-source models.
  - AI suggested Google Colab for inference → owner rejected based on past usage-limit problems; switched to Docker on laptop.
  - AI's first plan was a waterfall over 36 hours → reorganised into waves with checkpoints after the deadline moved to Friday 3pm.
- **Where the owner pushed back and the AI held its position:** owner initially considered skipping duplicate checks; AI recommended a cheap verification step instead of an assumption (adopted as D-002).
- **Checks performed:** owner reviewed each plan section and question in conversation.
  
Verdict: Plan established. Start Wave 1 so that further information can be discovered for other decisions.
Verified by: S Gyaw
