---
title: Bureaucratic Maze Navigator
sdk: docker
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

---

## 🔗 Quick Links

| Resource | Link |
|---------|------|
| 🤗 HuggingFace Space | **[LINK](https://huggingface.co/spaces/Hemakshiy/bureaucratic-maze)** |
| 📝 Blog Post | **[LINK](https://huggingface.co/spaces/Hemakshiy/bureaucratic-maze/blob/main/bureaucratic_maze_blog.md)** |
| 📓 Training Notebook (Colab) | **[LINK](https://huggingface.co/spaces/Hemakshiy/bureaucratic-maze/blob/main/unsloth_training_script.ipynb)** |

---

## 🧠 The Research Problem

Large Language Models (LLMs) are highly capable in **single-step reasoning tasks** — question answering, summarization, and code generation.

However, they struggle in a more realistic and critical setting:

> **Sequential decision-making in environments with incomplete, delayed, ambiguous, and contradictory information.**

These conditions are common in:
- Government workflows  
- Banking dispute systems  
- Insurance claims  
- Healthcare processes  

Such environments require:
- Long-horizon memory  
- Iterative reasoning  
- Error recovery  
- Adaptive strategy formation  

**Current LLMs are not trained for this.**  
They are optimized to generate *answers*, not to *navigate processes*.

---

## 🎯 Motivation

Indian government offices represent a naturally occurring **adversarial multi-step system**:
- Correct paths are hidden  
- Information is fragmented  
- Rules are inconsistently applied  
- Progress often requires trial-and-error  

This project formalizes that system into a **reinforcement learning environment** where agents must:

> Persist, adapt, and reason through bureaucratic complexity to achieve real-world goals.

---

## 🗺️ Environment Overview

### Core Setup

- Agent plays a **citizen**
- Goal: Complete a civic task (refund, correction, permit, etc.)
- Environment: **10-department government building**
- Visibility: **Partial** (only current department + clerk response)
- Solution path: **Hidden (server-side only)**

---

### 🏢 Departments

| ID  | Department                          | Location                     |
|-----|------------------------------------|------------------------------|
| D1  | Reception & Enquiry                | Ground Floor, Counter 1     |
| D2  | Documents Verification             | First Floor, Room 104       |
| D3  | Revenue & Accounts                 | Ground Floor, Room 12       |
| D4  | Records & Registry                 | Second Floor, Room 201      |
| D5  | Field Inspection                   | Ground Floor, Room 8        |
| D6  | Senior Officer Desk                | Third Floor, Room 301       |
| D7  | Grievance Redressal                | First Floor, Room 110       |
| D8  | State Portal Help Desk             | Ground Floor, Kiosk Area    |
| D9  | Notary & Affidavit                 | Ground Floor, Room 3        |
| D10 | Final Issuance                     | First Floor, Counter 7      |

---

### ⚠️ Bureaucratic Obstacles

| Obstacle Type | Description |
|--------------|------------|
| Wrong Redirects | Sent to incorrect departments |
| Missing Documents | Requirements revealed late |
| Wait States | Forced delays across steps |
| Jargon Deflection | Ambiguous bureaucratic language |
| Contradictory Rules | Conflicting instructions |
| External Requirements | Dependencies outside system |
| Circular Loops | Repeated department visits |

---

## 🧠 What the Agent Learns

- **Long-horizon planning** across 20–50 steps  
- **Context retention** over extended interactions  
- **Jargon interpretation** in ambiguous responses  
- **Error recovery** from failed paths  
- **Adaptive decision-making** under uncertainty  

---

## ⚙️ Interaction Model

### Action Space

| Action Type | Parameters | Description |
|------------|-----------|------------|
| `speak` | `text` | Communicate with clerk |
| `go_to` | `department_id` | Move to another department |
| `request_transfer` | `department_id` | Ask clerk for redirection |
| `submit_form` | `form_name`, `form_fields` | Submit required form |
| `check_requirements` | `query` | Ask for required documents |
| `wait` | — | Advance wait state |

---

### Observation Space

| Field | Description |
|------|------------|
| `current_department` | ID + name of current department |
| `clerk_response` | Natural language reply |
| `available_actions` | Valid actions for current step |
| `available_departments` | Reachable departments |
| `documents_held` | Current inventory |
| `goal_description` | Task objective |
| `steps_used / remaining` | Episode progress |
| `wait_state` | Whether agent is waiting |
| `goal_status` | Completion flag |

---

## 🎮 Tasks (Curriculum)

| Task | Difficulty | Max Steps | Key Challenge |
|------|-----------|-----------|--------------|
| Refund | Easy | 15 | Wrong routing |
| Ration Correction | Easy-Medium | 20 | Hidden affidavit |
| License Renewal | Medium | 28 | System error + wait |
| Passport Update | Medium-Hard | 35 | Contradictions |
| Tax Dispute | Hard | 40 | Denial + escalation |
| Renovation Permit | Very Hard | 50 | Multi-stage + external |

---

## 💰 Reward Design

### Dense Multi-Signal Reward

| Signal | Reward |
|--------|--------|
| Correct department | +0.10 |
| Correct action | +0.05 |
| Document obtained | +0.15 |
| Obstacle resolved | +0.08 |
| Goal completed | +0.50 |
| Wrong department | −0.02 |
| Loop penalty | −0.10 |
| Step inefficiency | −0.01 |
| Invalid action | −0.03 |

**Design principle:**  
> Reward cannot be maximized without solving the task correctly.

---

## 🏆 Evaluation

Final score ∈ [0,1]:

| Component | Weight |
|----------|--------|
| Completion | 50% |
| Path correctness | 20% |
| Documents | 15% |
| Obstacles | 10% |
| Efficiency | 5% |

---

## 📊 Baseline Performance

| Task | Score |
|------|------|
| Task 1 | ~0.60 |
| Task 2 | ~0.40 |
| Task 3 | ~0.25 |
| Task 4 | ~0.15 |
| Task 5 | ~0.10 |
| Task 6 | ~0.05 |
| **Average** | **~0.26** |

---

## 📊 Results

### 📈 Training Curve
**Reward vs Training Step (Baseline vs Trained)**  
➡️ 
<img width="1667" height="617" alt="Beaurocracy_plot" src="https://github.com/user-attachments/assets/12a01642-8c04-4825-8c0e-6c4b2d1c03aa" />

---

### 🔁 Behavior Comparison

| Task | Before Training | After Training |
|------|---------------|---------------|
| Easy | Random success | Direct navigation |
| Medium | Loops & confusion | Structured recovery |
| Hard | Fails early | Multi-step reasoning |
| Very Hard | No completion | Handles waits & dependencies |

---

### 📊 Final Metrics

| Metric | Value |
|--------|------|
| Baseline Avg | 0.26 |
| Trained Avg | 0.62 |
| Improvement | +138% |

📈 W&B Run:
<img width="1907" height="711" alt="Beaurocracy_plot2" src="https://github.com/user-attachments/assets/33de85f8-d468-4b33-9f0c-a69df6896c82" />


---

## 🚀 Setup

```bash
### Run locally
bash
# Clone and install
git clone https://github.com/hemakshiyeole01/Bureaucratic-Maze-Navigator
cd bureaucratic-maze
pip install -r requirements.txt

# Start the server
python -m uvicorn bureaucratic_maze.server:app --host 0.0.0.0 --port 7860

# In another terminal — run inference
export HF_TOKEN=your_token_here
export ENV_BASE_URL=http://localhost:7860
python inference.py
### Run with Docker
bash
docker build -t bureaucratic-maze .
docker run -p 7860:7860 bureaucratic-maze
### API Quick Reference
bash
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
--- ## 🧪 Validation
bash
# Validate OpenEnv spec
openenv validate

# Run pre-submission check
./validate-submission.sh https://Hemakshiy-bureaucratic-maze.hf.space
---
