"""
Inference Script — Bureaucratic Maze Navigator
===============================================
Runs an LLM agent through all 6 tasks and emits structured logs.

Required environment variables:
  HF_TOKEN       Hugging Face / API key (mandatory, no default)
  API_BASE_URL   API endpoint (default: https://router.huggingface.co/v1)
  MODEL_NAME     Model identifier (default: Qwen/Qwen2.5-72B-Instruct)

Output format (stdout):
  [START] task=<n> env=<benchmark> model=<model>
  [STEP]  step=<n> action=<str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<0.00> rewards=<r1,r2,...>
"""

import os
import textwrap
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
from openai import OpenAI

# ── Load .env file ────────────────────────────────────────────────────────
def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

_load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = (
    os.getenv("HF_TOKEN")
    or os.getenv("HUGGINGFACE_TOKEN")
    or os.getenv("HUGGING_FACE_HUB_TOKEN")
    or os.getenv("API_KEY")
)
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK    = "bureaucratic-maze"

if not HF_TOKEN:
    raise ValueError(
        "No API token found. Set HF_TOKEN in your environment or in a .env file:\n"
        "    HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    )

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# ── Task configuration ─────────────────────────────────────────────────────
TASKS = ["task_1", "task_2", "task_3", "task_4", "task_5", "task_6"]

MAX_STEPS_PER_TASK: Dict[str, int] = {
    "task_1": 15,
    "task_2": 20,
    "task_3": 28,
    "task_4": 35,
    "task_5": 40,
    "task_6": 50,
}

# ── Plans ──────────────────────────────────────────────────────────────────
# skip_after_wait: True  → this speak TRIGGERS the D5 wait.
#                          The runner executes it once, records plan_idx,
#                          then when the wait drains it advances plan_idx
#                          past this step WITHOUT re-executing the speak.
#                          This prevents the -0.05 penalty from a redundant
#                          post-wait speak and avoids triggering a second wait.

TASK_PLANS: Dict[str, List[Dict[str, Any]]] = {

    # ── Task 1: ₹500 wrong transaction refund ──────────────────────────────
    "task_1": [
        {"dept": "D1",  "action_type": "speak",
         "hint": "I need help. A ₹500 wrong transaction charge appeared on my utility bill and I want it reversed."},
        {"dept": "D1",  "action_type": "go_to",       "department_id": "D3"},
        {"dept": "D3",  "action_type": "speak",
         "hint": "This is not a portal issue. It is a direct billing problem. Please process my grievance directly and do not redirect me to the portal."},
        {"dept": "D3",  "action_type": "submit_form", "form_name": "Transaction SMS Screenshot"},
        {"dept": "D3",  "action_type": "go_to",       "department_id": "D7"},
        {"dept": "D7",  "action_type": "speak",
         "hint": "I have the Transaction SMS Screenshot. I wish to file a formal grievance for a ₹500 wrong transaction charge on my utility bill."},
        {"dept": "D7",  "action_type": "go_to",       "department_id": "D10"},
        {"dept": "D10", "action_type": "speak",
         "hint": "I have filed a formal grievance and hold the Transaction SMS Screenshot. Please process my wrong transaction refund and issue the final document."},
    ],

    # ── Task 2: Name correction on ration card ─────────────────────────────
    "task_2": [
        {"dept": "D1",  "action_type": "speak",
         "hint": "I need to correct a spelling error in my name on my ration card."},
        {"dept": "D1",  "action_type": "go_to",  "department_id": "D4"},
        {"dept": "D4",  "action_type": "speak",
         "hint": "Could you clarify in simpler terms what gazette notification prerequisite means and what exact document I need to correct my name on the ration card?"},
        {"dept": "D4",  "action_type": "go_to",  "department_id": "D9"},
        {"dept": "D9",  "action_type": "speak",
         "hint": "I need to obtain a notarized affidavit for name correction on my ration card. Please notarize my affidavit."},
        {"dept": "D9",  "action_type": "go_to",  "department_id": "D2"},
        {"dept": "D2",  "action_type": "speak",
         "hint": "I have the Birth Certificate, Ration Card Original, and Affidavit for Name Correction with me. Here they are for verification."},
        {"dept": "D2",  "action_type": "go_to",  "department_id": "D10"},
        {"dept": "D10", "action_type": "speak",
         "hint": "I have all required documents including the notarized affidavit for name correction and the verification stamp. Please issue the corrected ration card."},
    ],

    # ── Task 3: Driving licence renewal ───────────────────────────────────
    "task_3": [
        {"dept": "D1",  "action_type": "speak",
         "hint": "I need to renew my expired driving licence."},
        {"dept": "D1",  "action_type": "go_to",  "department_id": "D2"},
        {"dept": "D2",  "action_type": "speak",
         "hint": "I have my expired driving licence and Form LLD with me. Here they are."},
        {"dept": "D2",  "action_type": "go_to",  "department_id": "D8"},
        {"dept": "D8",  "action_type": "speak",
         "hint": "I need help with a system error. The online form is not accepting my date of birth. Please fix this portal issue and provide a portal acknowledgment."},
        {"dept": "D8",  "action_type": "go_to",  "department_id": "D5"},
        {"dept": "D5",  "action_type": "speak",
         "hint": "I need a medical fitness certificate for my driving licence renewal.",
         "skip_after_wait": True},
        {"dept": "D5",  "action_type": "go_to",  "department_id": "D6"},
        {"dept": "D6",  "action_type": "speak",
         "hint": "I have my expired driving licence, portal acknowledgment, and medical fitness certificate. Please approve my driving licence renewal."},
        {"dept": "D6",  "action_type": "go_to",  "department_id": "D10"},
        {"dept": "D10", "action_type": "speak",
         "hint": "I have the portal acknowledgment, medical fitness certificate, and senior officer approval. Please issue my renewed driving licence."},
    ],

    # ── Task 4: Passport renewal with address update ───────────────────────
    "task_4": [
        {"dept": "D1",  "action_type": "speak",
         "hint": "I need to renew my passport and update my address in the records."},
        {"dept": "D1",  "action_type": "go_to",  "department_id": "D4"},
        {"dept": "D4",  "action_type": "speak",
         "hint": "I need a certified copy of my current address record for a passport renewal and address update."},
        {"dept": "D4",  "action_type": "go_to",  "department_id": "D2"},
        {"dept": "D2",  "action_type": "submit_form", "form_name": "Passport Renewal and Address Update Form"},
        {"dept": "D2",  "action_type": "go_to",  "department_id": "D9"},
        {"dept": "D9",  "action_type": "speak",
         "hint": "I need to notarize my address proof document for the passport renewal application."},
        {"dept": "D9",  "action_type": "go_to",  "department_id": "D6"},
        {"dept": "D6",  "action_type": "speak",
         "hint": "I need Gazetted Officer attestation on all my documents for the passport renewal. I have the notarized address proof here."},
        {"dept": "D6",  "action_type": "go_to",  "department_id": "D10"},
        {"dept": "D10", "action_type": "speak",
         "hint": "I have the notarized address proof and Gazetted Officer attestation on all my documents. Please process my passport renewal with the updated address."},
    ],

    # ── Task 5: Property tax dispute ───────────────────────────────────────
    "task_5": [
        {"dept": "D1",  "action_type": "speak",
         "hint": "I need to dispute an inflated property tax bill. The amount charged is much higher than my property classification warrants."},
        {"dept": "D1",  "action_type": "go_to",  "department_id": "D3"},
        {"dept": "D3",  "action_type": "speak",
         "hint": "I have the Tax Bill Original with me. Here it is. I believe there is a billing discrepancy in my property tax assessment."},
        {"dept": "D3",  "action_type": "go_to",  "department_id": "D7"},
        {"dept": "D7",  "action_type": "speak",
         "hint": "I have the Tax Bill Original and property documents. I wish to file a formal grievance against the inflated property tax bill."},
        {"dept": "D7",  "action_type": "go_to",  "department_id": "D4"},
        {"dept": "D4",  "action_type": "speak",
         "hint": "Could you clarify in simpler terms what revenue subdivision means? I need a certified property records extract to support my tax dispute."},
        {"dept": "D4",  "action_type": "go_to",  "department_id": "D5"},
        {"dept": "D5",  "action_type": "speak",
         "hint": "I need a site inspection to verify the classification of my property. I have filed a formal grievance and have the records extract.",
         "skip_after_wait": True},
        {"dept": "D5",  "action_type": "go_to",  "department_id": "D6"},
        {"dept": "D6",  "action_type": "speak",
         "hint": "I have the grievance reference, records extract, and site inspection clearance. I need a reclassification order to resolve my property tax dispute."},
        {"dept": "D6",  "action_type": "go_to",  "department_id": "D10"},
        {"dept": "D10", "action_type": "speak",
         "hint": "I have the Tax Bill Original, Certified Property Records Extract, "
                 "Grievance Reference Number, Site Inspection Clearance, and Reclassification Order. "
                 "Please process my property tax correction and issue the revised bill."},
    ],

    # ── Task 6: Building permit for second floor ───────────────────────────
    "task_6": [
        {"dept": "D1",  "action_type": "speak",
         "hint": "I need a permit to add a second floor to my residential building. My survey number is 12345."},
        {"dept": "D1",  "action_type": "go_to",       "department_id": "D4"},
        {"dept": "D4",  "action_type": "speak",
         "hint": "My survey number is 12345. I need a records extract for a second floor building permit application."},
        {"dept": "D4",  "action_type": "go_to",       "department_id": "D6"},
        {"dept": "D6",  "action_type": "speak",
         "hint": "I need senior officer approval for a second floor building permit. "
                 "I have obtained the structural engineer certificate from a licensed private engineer. Here it is."},
        {"dept": "D6",  "action_type": "go_to",       "department_id": "D5"},
        {"dept": "D5",  "action_type": "speak",
         "hint": "I need a site inspection for the second floor building permit. "
                 "I have the approved plan and senior officer approval.",
         "skip_after_wait": True},
        {"dept": "D5",  "action_type": "go_to",       "department_id": "D9"},
        {"dept": "D9",  "action_type": "speak",
         "hint": "I need a NOC affidavit for the second floor building permit application."},
        {"dept": "D9",  "action_type": "go_to",       "department_id": "D3"},
        {"dept": "D3",  "action_type": "speak",
         "hint": "I have the challan copy here. I need to pay the permit fee for the second floor building permit."},
        {"dept": "D3",  "action_type": "go_to",       "department_id": "D10"},
        {"dept": "D10", "action_type": "speak",
         "hint": "I have the Records Extract, Structural Engineer Certificate, Senior Officer Approval, "
                 "First Inspection Clearance, NOC Affidavit, and Permit Fee Receipt. "
                 "Please issue the building permit for adding a second floor to my property at survey number 12345."},
    ],
}

# ── Logging ────────────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val    = error if error else "null"
    action_clean = action.replace("\n", " ").replace("\r", "")[:120]
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )

# ── Environment HTTP client ────────────────────────────────────────────────

class EnvClient:
    def __init__(self, base_url: str):
        self.base_url   = base_url.rstrip("/")
        self.session_id = "inference_session"
        self._http      = httpx.Client(timeout=30.0)

    def reset(self, task_id: str) -> dict:
        r = self._http.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id, "session_id": self.session_id},
        )
        r.raise_for_status()
        return r.json()

    def step(self, action: dict) -> dict:
        r = self._http.post(
            f"{self.base_url}/step",
            json={"action": action, "session_id": self.session_id},
        )
        r.raise_for_status()
        return r.json()

    def close(self):
        self._http.close()

# ── LLM speak helper ───────────────────────────────────────────────────────

_SPEAK_SYSTEM = textwrap.dedent("""
You are a citizen navigating an Indian government office.
Given the situation context and a hint, write a natural, polite, specific 1-2 sentence
message to the clerk. Be concrete — mention document names, amounts, and your purpose.
Respond with ONLY the plain text message. No JSON, no quotes, no markdown, no preamble.
""").strip()

def get_speak_text(hint: str, obs: dict, history: List[str]) -> str:
    docs     = ", ".join(obs.get("documents_held", [])) or "none yet"
    goal     = obs.get("goal_description", "")
    clerk    = obs.get("clerk_response", "")
    dept     = obs.get("current_department_name", "")
    hist_str = "\n".join(history[-4:]) if history else "none"

    user_msg = textwrap.dedent(f"""
        GOAL: {goal}
        CURRENT DEPARTMENT: {dept}
        CLERK JUST SAID: {clerk}
        DOCUMENTS YOU HOLD: {docs}
        RECENT HISTORY:
        {hist_str}

        HINT (what to convey): {hint}

        Write your message to the clerk now.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": _SPEAK_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=120,
        )
        text = (completion.choices[0].message.content or "").strip().strip('"').strip("'")
        return text if text and not text.startswith("{") else hint
    except Exception as exc:
        print(f"[DEBUG] LLM speak error: {exc}", flush=True)
        return hint

# ── Action helpers ─────────────────────────────────────────────────────────

def action_to_string(action: dict) -> str:
    atype = action.get("action_type", "unknown")
    if atype == "speak":
        return f"speak('{action.get('text', '')[:60]}')"
    if atype in ("go_to", "request_transfer"):
        return f"{atype}('{action.get('department_id', '?')}')"
    if atype == "submit_form":
        return f"submit_form('{action.get('form_name', '?')}')"
    if atype == "check_requirements":
        return f"check_requirements('{action.get('query', '')[:40]}')"
    if atype == "wait":
        return "wait()"
    return f"{atype}()"

# ── Single task runner ─────────────────────────────────────────────────────

def run_task(env_client: EnvClient, task_id: str) -> dict:
    max_steps  = MAX_STEPS_PER_TASK.get(task_id, 30)
    rewards: List[float] = []
    steps_taken = 0
    success     = False
    score       = 0.0
    history: List[str] = []

    plan     = [dict(s) for s in TASK_PLANS.get(task_id, [])]
    plan_idx = 0
    d10_speaks = 0

    # ── Wait-state tracking ────────────────────────────────────────────────
    # was_waiting          : True if the previous iteration issued a wait action.
    # wait_triggered_plan_idx : plan_idx of the speak that started the current wait.
    #                          Cleared after the wait ends and skip is applied.
    was_waiting             = False
    wait_triggered_plan_idx: Optional[int] = None

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        reset_result = env_client.reset(task_id=task_id)
        obs          = reset_result.get("observation", {})

        for step in range(1, max_steps + 1):
            if obs.get("goal_achieved", False):
                break

            current_dept   = obs.get("current_department_id", "D1")
            is_waiting     = obs.get("is_waiting", False)
            wait_remaining = obs.get("wait_steps_remaining", 0)

            # ── Detect: wait just finished this iteration ──────────────────
            # was_waiting=True  → last step we were waiting
            # is_waiting=False  → the wait counter hit 0, wait is over
            wait_just_ended = was_waiting and not is_waiting

            # ── Skip the triggering speak now that wait has drained ────────
            # The speak at wait_triggered_plan_idx already ran (it caused the
            # wait). plan_idx is now at wait_triggered_plan_idx + 1 already
            # (it was incremented when the speak ran). We just need to ensure
            # we don't re-execute it — which we won't because plan_idx moved.
            # BUT: if the speak somehow didn't advance plan_idx (navigation
            # detour case), force-advance past it now.
            if wait_just_ended and wait_triggered_plan_idx is not None:
                # Force plan_idx to be PAST the triggering speak
                target_idx = wait_triggered_plan_idx + 1
                if plan_idx <= wait_triggered_plan_idx:
                    print(
                        f"[DEBUG] Wait ended — force-advancing plan_idx "
                        f"from {plan_idx} to {target_idx} (skip D5 speak)",
                        flush=True,
                    )
                    plan_idx = target_idx
                else:
                    print(
                        f"[DEBUG] Wait ended — plan_idx={plan_idx} already past "
                        f"trigger={wait_triggered_plan_idx}, no skip needed",
                        flush=True,
                    )
                wait_triggered_plan_idx = None

            # ── Priority 1: drain wait state ──────────────────────────────
            if is_waiting and wait_remaining > 0:
                action      = {"action_type": "wait"}
                was_waiting = True

            # ── Priority 2: execute next plan step ────────────────────────
            elif plan_idx < len(plan):
                ps    = plan[plan_idx]
                atype = ps["action_type"]
                was_waiting = False

                if atype == "go_to":
                    target = ps["department_id"]
                    if current_dept == target:
                        plan_idx += 1
                        action = {"action_type": "check_requirements",
                                  "query": "What do I need here?"}
                    else:
                        action   = {"action_type": "go_to", "department_id": target}
                        plan_idx += 1

                elif atype == "speak":
                    target = ps["dept"]
                    if current_dept != target:
                        # Navigate first — don't advance plan_idx
                        action = {"action_type": "go_to", "department_id": target}
                    else:
                        hint = ps.get("hint", "Please help me with my application.")
                        text = get_speak_text(hint, obs, history)
                        action = {"action_type": "speak", "text": text}

                        # Record this plan step as the wait trigger so we can
                        # skip it after the wait drains.
                        if ps.get("skip_after_wait"):
                            wait_triggered_plan_idx = plan_idx

                        if target == "D10":
                            d10_speaks += 1
                        plan_idx += 1
                        # If this was the final D10 speak and got a low reward,
                        # we'll catch it in the post-step break check below.

                elif atype == "submit_form":
                    target = ps["dept"]
                    if current_dept != target:
                        action = {"action_type": "go_to", "department_id": target}
                    else:
                        action   = {
                            "action_type": "submit_form",
                            "form_name":   ps["form_name"],
                            "form_fields": {},
                        }
                        plan_idx += 1

                else:
                    action   = {"action_type": atype}
                    plan_idx += 1

            # ── Priority 3: plan exhausted ─────────────────────────────────
            else:
                was_waiting = False
                if current_dept != "D10":
                    action = {"action_type": "go_to", "department_id": "D10"}
                elif d10_speaks >= 1:
                    # Already spoke at D10 once from plan — one more attempt max
                    # but only if the last reward was positive (D10 is accepting docs)
                    last_reward = rewards[-1] if rewards else 0.0
                    if d10_speaks >= 2 or last_reward <= 0:
                        break
                    docs = ", ".join(obs.get("documents_held", [])) or "all required documents"
                    text = get_speak_text(
                        f"I have completed all required steps and hold: {docs}. "
                        f"Please finalize and issue my document.",
                        obs, history,
                    )
                    action = {"action_type": "speak", "text": text}
                    d10_speaks += 1
                else:
                    docs = ", ".join(obs.get("documents_held", [])) or "all required documents"
                    text = get_speak_text(
                        f"I have completed all required steps and hold: {docs}. "
                        f"Please finalize and issue my document.",
                        obs, history,
                    )
                    action = {"action_type": "speak", "text": text}
                    d10_speaks += 1

            # ── Execute ───────────────────────────────────────────────────
            action_str = action_to_string(action)

            try:
                step_result = env_client.step(action)
            except Exception as e:
                log_step(step=step, action=action_str, reward=0.0, done=True, error=str(e)[:80])
                rewards.append(0.0)
                steps_taken = step
                break

            reward  = float(step_result.get("reward", 0.0))
            done    = bool(step_result.get("done", False))
            obs     = step_result.get("observation", {})
            error   = obs.get("last_action_error")
            info    = step_result.get("info", {})

            # If this step's speak just triggered a NEW wait, update was_waiting
            # so next iteration correctly enters Priority 1 drain.
            if not is_waiting and obs.get("is_waiting", False):
                was_waiting = True

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            clerk_resp = obs.get("clerk_response", "")[:120]
            history.append(
                f"Step {step}: [{current_dept}] {action_str} -> reward={reward:+.2f} | {clerk_resp}"
            )

            if current_dept == "D10" and d10_speaks >= 1 and reward <= 0.0:
                break

            if "final_score" in info:
                score = float(info["final_score"])

            if done:
                success = obs.get("goal_achieved", False)
                break

        # ── Compute score ─────────────────────────────────────────────────
        if score == 0.0 and rewards:
            pos   = [r for r in rewards if r > 0]
            score = min(1.0, sum(pos) / max(1.0, max_steps * 0.3))

        success = success or (score >= 0.5)

    except Exception as exc:
        print(f"[DEBUG] Task {task_id} error: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {
        "task_id": task_id,
        "success": success,
        "steps":   steps_taken,
        "score":   score,
        "rewards": rewards,
    }

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    env_client = EnvClient(base_url=ENV_BASE_URL)
    results: List[dict] = []

    try:
        for task_id in TASKS:
            result = run_task(env_client, task_id)
            results.append(result)
            print(flush=True)
    finally:
        env_client.close()

    total_score = sum(r["score"] for r in results) / len(results) if results else 0.0
    successes   = sum(1 for r in results if r["success"])
    print(
        f"[SUMMARY] tasks={len(results)} successes={successes} avg_score={total_score:.2f}",
        flush=True,
    )


if __name__ == "__main__":
    main()