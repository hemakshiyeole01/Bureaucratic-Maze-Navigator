---
title: Bureaucratic Maze Navigator
emoji: 🏛️
colorFrom: orange
colorTo: red
sdk: docker
pinned: true
license: mit
tags:
  - openenv
  - reinforcement-learning
  - environment
  - real-world
  - bureaucracy
  - india
  - multi-step
  - reasoning
app_port: 7860
---

# 🏛️ Bureaucratic Maze Navigator

> *Can an AI survive the Indian government office?*

An [OpenEnv](https://github.com/huggingface/openenv)-compliant reinforcement learning environment where an AI agent plays a frustrated citizen trying to accomplish real-world civic goals by navigating a maze of departments, wrong transfers, missing forms, contradictory rules, and unhelpful clerks.

---

## 🎯 Motivation

Every Indian has suffered through a government office. You go to the right counter, get sent to the wrong one, come back with the wrong form, wait three days, then find out you needed a notarized affidavit all along.

**This environment trains agents to do exactly that** — persist through bureaucracy, track context across long interactions, discover non-obvious paths, and recover from dead ends.

This tests capabilities that current LLMs genuinely struggle with:
- Long-horizon context tracking (remembering what each department said)
- Persistence under repeated rejection
- Disambiguation of jargon-heavy responses
- Recovery from contradictory instructions
- Multi-step planning without a map

---

## 🗺️ Environment Overview

### The Setup
The agent is a citizen trying to accomplish a civic goal inside a 10-department government office building. It can only see the current department and what the clerk says — it never sees the solution path.

### The 10 Departments

| ID | Department | Floor |
|----|-----------|-------|
| D1 | Reception and Enquiry Counter | Ground Floor, Counter 1 |
| D2 | Documents Verification Cell | First Floor, Room 104 |
| D3 | Revenue and Accounts Section | Ground Floor, Room 12 |
| D4 | Records and Registry Office | Second Floor, Room 201 |
| D5 | Field Inspection Unit | Ground Floor, Room 8 |
| D6 | Senior Officer / Gazetted Officer Desk | Third Floor, Room 301 |
| D7 | Grievance Redressal Cell | First Floor, Room 110 |
| D8 | State Portal Help Desk | Ground Floor, Kiosk Area |
| D9 | Notary and Affidavit Counter | Ground Floor, Room 3 |
| D10 | Final Issuance Window | First Floor, Counter 7 |

### Bureaucratic Obstacles
Each task combines multiple obstacle types:
- **Wrong redirects** — clerk sends you somewhere incorrect
- **Missing documents** — required paperwork not mentioned upfront
- **Wait states** — forced multi-step delays ("come back after 3 working days")
- **Jargon deflection** — clerk uses bureaucratic terms the agent must decode
- **Contradictory rules** — Department A says bring X; Department B says X is invalid
- **External requirements** — requirements from outside the government system
- **Circular loops** — getting sent back to a department you already visited

---

## 📋 Action Space

The agent has 6 action types:

```json
{"action_type": "speak",              "text": "your message to the clerk"}
{"action_type": "go_to",              "department_id": "D3"}
{"action_type": "request_transfer",   "department_id": "D7"}
{"action_type": "submit_form",        "form_name": "Form 7A", "form_fields": {}}
{"action_type": "check_requirements", "query": "what documents do I need?"}
{"action_type": "wait"}
```

---

## 👁️ Observation Space

Each step returns:

```json
{
  "current_department_id": "D3",
  "current_department_name": "Revenue and Accounts Section",
  "clerk_response": "Our records show no discrepancy. File a formal grievance.",
  "available_actions": ["speak", "go_to", "submit_form", ...],
  "available_departments": [{"id": "D7", "name": "Grievance Cell", "floor": "..."}],
  "documents_held": ["Tax Bill Original", "Property Documents"],
  "goal_description": "Dispute an inflated property tax bill",
  "steps_used": 4,
  "steps_remaining": 36,
  "is_waiting": false,
  "wait_steps_remaining": 0,
  "goal_achieved": false
}
```

---

## 🎮 The 6 Tasks

| # | Task | Difficulty | Max Steps | Key Obstacles |
|---|------|-----------|-----------|--------------|
| 1 | Wrong Charge Refund | Easy | 15 | Wrong redirect, missing doc |
| 2 | Ration Card Name Correction | Easy-Medium | 20 | Jargon, non-obvious affidavit requirement |
| 3 | Driving License Renewal | Medium | 28 | Portal error, wait state, multi-visit |
| 4 | Passport Renewal + Address Change | Medium-Hard | 35 | Contradictory rule, police verification wait |
| 5 | Property Tax Dispute | Hard | 40 | Denial, jargon, 5-day wait, reclassification |
| 6 | Building Renovation Permit | Very Hard | 50 | External requirement, 2 wait states, contradiction |

### Task Descriptions

**Task 1 — Wrong Charge Refund (Easy)**
You are Ramesh Kumar. ₹500 was wrongly debited from your account. Get it reversed.
Solution: D1 → D3 → D7 → D10 | Obstacle: Clerk initially redirects to D8 portal

**Task 2 — Ration Card Name Correction (Easy-Medium)**
You are Priya Lakshmi. Your name is misspelled on the ration card. Get it corrected.
Solution: D1 → D4 → D9 → D2 → D10 | Obstacle: Jargon at D4, needs notarized affidavit

**Task 3 — Driving License Renewal (Medium)**
You are Vijay Anand. Your license expired 6 months ago and the portal has a date bug.
Solution: D1 → D2 → D8 → D2 → D5 → D6 → D10 | Obstacle: System error + wait state

**Task 4 — Passport Renewal with Address Change (Medium-Hard)**
You are Kavitha Suresh. Passport expiring soon, need new address on it.
Solution: D1 → D4 → D2 → D9 → D6 → D5 → D2 → D10 | Obstacle: Contradictory requirement at D2

**Task 5 — Property Tax Dispute (Hard)**
You are Sundaram Iyer. Your residential property is taxed at commercial rates.
Solution: D1 → D3 → D7 → D4 → D5 → D6 → D3 → D10 | Obstacle: Denial + 5-day wait

**Task 6 — Building Renovation Permit (Very Hard)**
You are Mohan Krishnamurthy. Adding a second floor requires navigating 10 steps.
Solution: D1 → D4 → D5 → D6 → D2 → D9 → D5 → D6 → D3 → D10 | Obstacle: External requirement + 2 waits + contradiction

---

## 💰 Reward Function

Dense reward with **8 independent signals** — designed to be hard to game:

| Signal | Value | Description |
|--------|-------|-------------|
| Correct department visited | +0.10 | First visit to each correct dept |
| Correct action taken | +0.05 | Action that advances the solution |
| Required document obtained | +0.15 | Collecting a task-required document |
| Obstacle resolved | +0.08 | Successfully navigating an obstacle |
| Goal completed | +0.50 | Reaching D10 with all documents |
| Wrong department penalty | −0.02 | Visiting a dept not on solution path |
| Circular loop penalty | −0.10 | Revisiting same dept >2 times |
| Step efficiency penalty | −0.01 | Each step over optimal count |
| Invalid action penalty | −0.03 | Taking an action that doesn't parse |

**Anti-hacking protections:**
- Solution path is server-side only, never sent to client
- Department graph is frozen — no mutation possible
- Graders run server-side
- Reward hacking detector checks for explicit goal claims and rapid dept scanning
- Score requires both goal achievement AND correct document sequence

---

## 🏆 Grading (per task)

Each task grader returns a score in `[0.0, 1.0]`:

```
score = completion_bonus (0.50)
      + path_progress    (0.20) × fraction of solution path visited in order
      + document_score   (0.15) × fraction of required documents collected
      + obstacle_score   (0.10) × fraction of obstacles resolved
      + efficiency_score (0.05) × step efficiency (if goal achieved)
```

- Perfect run → **1.0**
- Partial progress without completion → **0.05–0.45**
- Reward hacking attempt → **≤0.0**

---

## 📊 Baseline Performance

Baseline scores from a `Qwen2.5-72B-Instruct` agent with no training:

| Task | Difficulty | Baseline Score |
|------|-----------|---------------|
| task_1 | Easy | ~0.60 |
| task_2 | Easy-Medium | ~0.40 |
| task_3 | Medium | ~0.25 |
| task_4 | Medium-Hard | ~0.15 |
| task_5 | Hard | ~0.10 |
| task_6 | Very Hard | ~0.05 |
| **Average** | | **~0.26** |

Training target: **>0.60 average** across all tasks.

---

## 🚀 Setup and Usage

### Run locally

```bash
# Clone and install
git clone <your-repo-url>
cd bureaucratic-maze
pip install -r requirements.txt

# Start the server
python -m uvicorn bureaucratic_maze.server:app --host 0.0.0.0 --port 7860

# In another terminal — run inference
export HF_TOKEN=your_token_here
export ENV_BASE_URL=http://localhost:7860
python inference.py
```

### Run with Docker

```bash
docker build -t bureaucratic-maze .
docker run -p 7860:7860 bureaucratic-maze
```

### API Quick Reference

```bash
# Health check
curl http://localhost:7860/health

# List tasks
curl http://localhost:7860/tasks

# Start episode
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_1"}'

# Take a step
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "speak", "text": "I need help with a wrong charge"}}'

# Get state
curl -X POST http://localhost:7860/state
```

---

## 🧪 Validation

```bash
# Validate OpenEnv spec
openenv validate

# Run pre-submission check
./validate-submission.sh https://your-space.hf.space
```

---

## 📁 Project Structure

```
bureaucratic-maze/
├── inference.py                    # Baseline inference script (root, mandatory)
├── openenv.yaml                    # OpenEnv manifest
├── Dockerfile                      # Container definition
├── requirements.txt
├── setup.py
├── README.md
└── bureaucratic_maze/
    ├── __init__.py
    ├── models.py                   # Pydantic models (Action, Observation, State)
    ├── departments.py              # 10 departments + clerk response templates
    ├── tasks.py                    # 6 task definitions + graders
    ├── rewards.py                  # Multi-signal reward calculator
    ├── environment.py              # Core env (reset/step/state)
    └── server.py                   # FastAPI HTTP wrapper
```

---

## 📚 Additional Resources

- 🎥 Demo Video: [YouTube link]
- 📝 HuggingFace Blog Post: [HF link]
- 🤗 HuggingFace Space: [Space](https://huggingface.co/spaces/Hemakshiy/bureaucratic-maze)
- 📓 Training Colab (TRL + Unsloth): [Colab link]
- 📈 Training Curves (W&B): [W&B link]

---

## 👥 Team

Built for the **Meta OpenEnv Hackathon — India, April 2026**

*"Can AI survive the DMV? We found out."*
