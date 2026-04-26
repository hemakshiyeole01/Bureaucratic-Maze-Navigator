"""
Bureaucratic Maze Navigator — Core Environment
Implements OpenEnv-compliant reset() / step() / state() interface.
"""

import uuid
import random
from typing import Any, Dict, List, Optional, Tuple

from bureaucratic_maze.models import (
    ActionType,
    BureaucracyAction,
    BureaucracyObservation,
    BureaucracyState,
    DocumentStatus,
    DepartmentVisit,
    ResetResult,
    StepResult,
    TaskInfo,
)
from bureaucratic_maze.departments import (
    DEPARTMENTS,
    get_clerk_response,
    get_department,
    get_department_list,
)
from bureaucratic_maze.tasks import (
    ALL_TASKS,
    ObstacleType,
    TaskDefinition,
    get_task,
    grade_episode,
)
from bureaucratic_maze.rewards import RewardCalculator


class BureaucraticMazeEnv:
    """
    Bureaucratic Maze Navigator Environment.

    An OpenEnv-compliant environment where an AI agent plays a citizen
    trying to accomplish real government/civic goals by navigating
    a maze of departments, wrong transfers, missing forms, and unhelpful clerks.
    """

    ENV_NAME = "bureaucratic-maze"
    ENV_VERSION = "1.0.0"

    def __init__(self, task_id: str = "task_1", seed: Optional[int] = None):
        if task_id not in ALL_TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Valid: {list(ALL_TASKS.keys())}")

        self.task_id = task_id
        self.seed = seed
        if seed is not None:
            random.seed(seed)

        # Internal state — initialized on reset()
        self._state: Optional[BureaucracyState] = None
        self._task: Optional[TaskDefinition] = None
        self._reward_calc: Optional[RewardCalculator] = None
        self._obstacles_resolved: List[str] = []
        self._obstacles_triggered: List[str] = []
        self._active_contradictions: List[str] = []

    # ─────────────────────────────────────────────
    # OpenEnv Core Interface
    # ─────────────────────────────────────────────

    def reset(self, task_id: Optional[str] = None) -> ResetResult:
        """Start a fresh episode. Returns initial observation."""
        if task_id:
            if task_id not in ALL_TASKS:
                raise ValueError(f"Unknown task_id: {task_id}")
            self.task_id = task_id

        self._task = get_task(self.task_id)
        self._reward_calc = RewardCalculator(self._task)
        self._obstacles_resolved = []
        self._obstacles_triggered = []
        self._active_contradictions = []

        episode_id = str(uuid.uuid4())[:8]

        # Initialize state
        self._state = BureaucracyState(
            task_id=self._task.task_id,
            task_name=self._task.task_name,
            episode_id=episode_id,
            current_department_id="D1",
            steps_used=0,
            max_steps=self._task.max_steps,
            goal_achieved=False,
            documents_held=[
                DocumentStatus(
                    doc_id=doc,
                    doc_name=doc.replace("_", " ").title(),
                    obtained_from="initial",
                )
                for doc in self._task.initial_documents
            ],
            visit_history=[],
            wait_steps_remaining=0,
            solution_path=self._task.solution_path,  # Server-side only
            current_path_index=0,
            obstacles_triggered=[],
            contradictions_active=[],
            score=0.0,
        )

        obs = self._build_observation(
            clerk_response=get_clerk_response("D1", "greeting"),
            error=None,
        )

        return ResetResult(observation=obs, info={"episode_id": episode_id, "task": self._task.task_name})

    def step(self, action: BureaucracyAction) -> StepResult:
        """Apply an action and return (observation, reward, done, info)."""
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        if self._state.goal_achieved:
            obs = self._build_observation("Task already completed. Episode is done.", None)
            return StepResult(observation=obs, reward=0.0, done=True, info={"message": "already_done"})

        self._state.steps_used += 1
        done = False
        reward = 0.0
        info: Dict[str, Any] = {}
        error_msg: Optional[str] = None
        document_obtained: Optional[str] = None
        obstacle_resolved: Optional[str] = None

        # ── Handle wait state ──────────────────────────────────────────
        if self._state.wait_steps_remaining > 0:
            if action.action_type == ActionType.WAIT:
                self._state.wait_steps_remaining -= 1
                if self._state.wait_steps_remaining == 0:
                    # Resolve the wait-state obstacle and grant any gated document
                    dept_id = self._state.current_department_id
                    for obs in self._task.obstacles:
                        if (obs.obstacle_type == ObstacleType.WAIT_STATE
                                and obs.triggered_at_dept == dept_id
                                and obs.obstacle_id not in self._obstacles_resolved):
                            obstacle_resolved = obs.obstacle_id
                            self._obstacles_resolved.append(obs.obstacle_id)
                            if obs.obstacle_id in self._obstacles_triggered:
                                self._obstacles_triggered.remove(obs.obstacle_id)
                            break
                    document_obtained = self._check_document_grant(dept_id)
                    next_name = self._get_next_dept_name()
                    next_id = self._get_next_dept_id()
                    granted_msg = ""
                    if document_obtained:
                        pretty = document_obtained.replace("_", " ").title()
                        granted_msg = f" Here is your {pretty}."
                    clerk_response = (
                        f"Your waiting period is over. The report is ready.{granted_msg} "
                        f"Please proceed to {next_name} ({next_id})."
                    )
                else:
                    clerk_response = (
                        f"Please wait. {self._state.wait_steps_remaining} more working "
                        f"day(s) remaining. Come back then."
                    )
            else:
                clerk_response = (
                    f"You are currently in a wait state. "
                    f"{self._state.wait_steps_remaining} working day(s) remaining. "
                    f"Please use the WAIT action or come back later."
                )
                error_msg = "must_wait"
        else:
            # ── Process action ─────────────────────────────────────────
            clerk_response, document_obtained, obstacle_resolved, error_msg = (
                self._process_action(action)
            )

        # ── Check for reward hacking ───────────────────────────────────
        dept_sequence = [v.department_id for v in self._state.visit_history]
        is_hack, hack_reason = self._reward_calc.detect_reward_hack(
            action_text=action.text,
            dept_visit_sequence=dept_sequence,
            step_count=self._state.steps_used,
        )
        if is_hack:
            reward = self._reward_calc.REWARD_HACK_PENALTY
            clerk_response = "Invalid interaction detected. Please interact naturally."
            info["hack_detected"] = hack_reason
        else:
            # ── Compute reward ─────────────────────────────────────────
            is_loop = (
                self._state.visit_history.count(
                    self._state.current_department_id
                ) > 2
                if self._state.visit_history else False
            )
            reward, reward_breakdown = self._reward_calc.compute_step_reward(
                current_dept=self._state.current_department_id,
                action_type=action.action_type,
                action_result="error" if error_msg else "success",
                document_obtained=document_obtained,
                obstacle_resolved=obstacle_resolved,
                steps_used=self._state.steps_used,
                goal_achieved=self._state.goal_achieved,
                is_loop=is_loop,
                is_invalid_action=error_msg is not None,
            )
            info["reward_breakdown"] = reward_breakdown

        # ── Record visit ───────────────────────────────────────────────
        dept = get_department(self._state.current_department_id)
        self._state.visit_history.append(DepartmentVisit(
            department_id=self._state.current_department_id,
            department_name=dept.name if dept else "Unknown",
            step_number=self._state.steps_used,
            action_taken=f"{action.action_type}: {action.text or action.department_id or ''}",
            clerk_response_summary=clerk_response[:100],
        ))

        # ── Check done conditions ──────────────────────────────────────
        if self._state.goal_achieved:
            done = True
            final_score, score_breakdown = grade_episode(
                task_id=self._task.task_id,
                departments_visited=[v.department_id for v in self._state.visit_history],
                actions_taken=[v.action_taken for v in self._state.visit_history],
                documents_collected=[d.doc_id for d in self._state.documents_held],
                goal_achieved=True,
                steps_used=self._state.steps_used,
                obstacles_resolved=self._obstacles_resolved,
            )
            self._state.score = final_score
            info["final_score"] = final_score
            info["score_breakdown"] = score_breakdown

        elif self._state.steps_used >= self._state.max_steps:
            done = True
            final_score, score_breakdown = grade_episode(
                task_id=self._task.task_id,
                departments_visited=[v.department_id for v in self._state.visit_history],
                actions_taken=[v.action_taken for v in self._state.visit_history],
                documents_collected=[d.doc_id for d in self._state.documents_held],
                goal_achieved=False,
                steps_used=self._state.steps_used,
                obstacles_resolved=self._obstacles_resolved,
            )
            self._state.score = final_score
            info["timeout"] = True
            info["final_score"] = final_score
            info["score_breakdown"] = score_breakdown
            clerk_response += " [TIMEOUT: Maximum steps reached]"

        obs = self._build_observation(clerk_response, error_msg)
        return StepResult(observation=obs, reward=reward, done=done, info=info)

    def state(self) -> Dict[str, Any]:
        """Return current environment state metadata (public-safe subset)."""
        if self._state is None:
            return {"status": "not_initialized"}

        return {
            "task_id": self._state.task_id,
            "task_name": self._state.task_name,
            "episode_id": self._state.episode_id,
            "current_department": self._state.current_department_id,
            "steps_used": self._state.steps_used,
            "max_steps": self._state.max_steps,
            "steps_remaining": self._state.max_steps - self._state.steps_used,
            "goal_achieved": self._state.goal_achieved,
            "documents_held": [d.doc_name for d in self._state.documents_held],
            "wait_steps_remaining": self._state.wait_steps_remaining,
            "score": self._state.score,
            # NOTE: solution_path is intentionally NOT included here
        }

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Return public metadata about a task."""
        task = get_task(task_id)
        if not task:
            return None
        return TaskInfo(
            task_id=task.task_id,
            task_name=task.task_name,
            difficulty=task.difficulty,
            description=task.description,
            max_steps=task.max_steps,
            goal=task.goal,
        )

    def list_tasks(self) -> List[TaskInfo]:
        return [self.get_task_info(tid) for tid in ALL_TASKS.keys()]

    # ─────────────────────────────────────────────
    # Internal Logic
    # ─────────────────────────────────────────────

    def _process_action(
        self, action: BureaucracyAction
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """
        Process a non-wait action.
        Returns (clerk_response, document_obtained, obstacle_resolved, error_msg).
        """
        dept_id = self._state.current_department_id
        task = self._task

        if action.action_type == ActionType.GO_TO:
            return self._handle_go_to(action)

        elif action.action_type == ActionType.REQUEST_TRANSFER:
            return self._handle_transfer(action)

        elif action.action_type == ActionType.SPEAK:
            return self._handle_speak(action)

        elif action.action_type == ActionType.SUBMIT_FORM:
            return self._handle_submit_form(action)

        elif action.action_type == ActionType.CHECK_REQUIREMENTS:
            return self._handle_check_requirements(action)

        else:
            return (
                "I don't understand that action. Please speak, go to a department, or submit a form.",
                None, None, "unknown_action"
            )

    def _handle_go_to(self, action: BureaucracyAction) -> Tuple:
        """Handle navigation to a department."""
        target_id = action.department_id
        if not target_id or target_id not in DEPARTMENTS:
            return ("I don't know that department. Please check the department list.", None, None, "invalid_dept")

        # Compute expected next dept BEFORE moving so the comparison is meaningful
        expected = self._get_expected_next_dept()

        self._state.current_department_id = target_id
        dept = get_department(target_id)

        if target_id == expected:
            self._state.current_path_index += 1
            obstacle_resolved = self._check_obstacle_resolution(target_id, "arrival")
            response = get_clerk_response(target_id, "greeting")
        elif target_id in self._task.solution_path:
            # On the solution path but out of order — still helpful, just no path advance.
            obstacle_resolved = self._check_obstacle_resolution(target_id, "arrival")
            response = get_clerk_response(target_id, "greeting")
        else:
            correct_dept_name = get_department(expected).name if expected and get_department(expected) else "another department"
            response = get_clerk_response(
                target_id, "wrong_dept",
                correct_dept=correct_dept_name,
                floor=get_department(expected).floor if expected and get_department(expected) else "unknown floor"
            )
            obstacle_resolved = None

        # Trigger any wait-state obstacle that fires on arrival at this dept
        self._maybe_trigger_wait_state(target_id)

        return response, None, obstacle_resolved, None

    def _handle_transfer(self, action: BureaucracyAction) -> Tuple:
        """Handle requesting a transfer to another department."""
        target_id = action.department_id
        if not target_id or target_id not in DEPARTMENTS:
            return ("Transfer request unclear. Please specify a valid department.", None, None, "invalid_dept")

        expected = self._get_expected_next_dept()

        self._state.current_department_id = target_id
        dept = get_department(target_id)

        if target_id == expected:
            self._state.current_path_index += 1

        response = f"Okay, I am transferring your file to {dept.name}. Please proceed to {dept.floor}."
        obstacle_resolved = self._check_obstacle_resolution(target_id, "transfer")
        self._maybe_trigger_wait_state(target_id)
        return response, None, obstacle_resolved, None

    def _handle_speak(self, action: BureaucracyAction) -> Tuple:
        """Handle speaking to the current clerk."""
        if not action.text:
            return ("Please state your purpose.", None, None, "empty_speech")

        dept_id = self._state.current_department_id
        text_lower = action.text.lower()
        document_obtained = None
        obstacle_resolved = None

        # Check for active obstacles and how agent responds
        active_obstacle = self._get_active_obstacle_at(dept_id)

        if active_obstacle:
            # Check if agent's speech resolves the obstacle
            resolved = self._check_speech_resolves_obstacle(text_lower, active_obstacle)
            if resolved:
                obstacle_resolved = active_obstacle.obstacle_id
                self._obstacles_resolved.append(active_obstacle.obstacle_id)
                # Remove from triggered
                if active_obstacle.obstacle_id in self._obstacles_triggered:
                    self._obstacles_triggered.remove(active_obstacle.obstacle_id)

                # Give appropriate response after resolution
                response = self._get_resolution_response(dept_id, active_obstacle)
                document_obtained = self._check_document_grant(dept_id)
            else:
                # Obstacle still active — clerk gives obstacle response
                response = self._get_obstacle_response(dept_id, active_obstacle)
        else:
            # No active obstacle — normal interaction
            response = self._get_normal_speak_response(dept_id, text_lower)
            document_obtained = self._check_document_grant(dept_id)

            # Check if this interaction achieves goal
            if dept_id == "D10" and self._check_goal_conditions():
                self._state.goal_achieved = True
                dept = get_department("D10")
                response = get_clerk_response(
                    "D10", "goal_achieved",
                    document_name=self._task.success_document
                )

        return response, document_obtained, obstacle_resolved, None

    def _handle_submit_form(self, action: BureaucracyAction) -> Tuple:
        """Handle form submission."""
        if not action.form_name:
            return ("Which form do you want to submit?", None, None, "no_form_specified")

        dept_id = self._state.current_department_id
        doc_id = action.form_name.lower().replace(" ", "_").replace("-", "_")

        # Submitting a relevant form often satisfies a missing-doc obstacle here.
        active_obstacle = self._get_active_obstacle_at(dept_id)
        obstacle_resolved = None
        if (active_obstacle is not None
                and active_obstacle.obstacle_type == ObstacleType.MISSING_DOC):
            obstacle_resolved = active_obstacle.obstacle_id
            self._obstacles_resolved.append(active_obstacle.obstacle_id)
            if active_obstacle.obstacle_id in self._obstacles_triggered:
                self._obstacles_triggered.remove(active_obstacle.obstacle_id)

        if doc_id in self._task.required_documents:
            doc = DocumentStatus(
                doc_id=doc_id,
                doc_name=action.form_name,
                obtained_from=dept_id,
            )
            if doc_id not in [d.doc_id for d in self._state.documents_held]:
                self._state.documents_held.append(doc)
            next_dept_name = self._get_next_dept_name()
            response = (
                f"Form {action.form_name} submitted and accepted. "
                f"I will process this. Please proceed to {next_dept_name} for the next step."
            )
            return response, doc_id, obstacle_resolved, None
        else:
            # Even if the form isn't on the required list, if it resolved an obstacle,
            # treat as soft-success.
            if obstacle_resolved:
                next_dept_name = self._get_next_dept_name()
                return (
                    f"Okay, I have noted your {action.form_name}. Please proceed to {next_dept_name}.",
                    None, obstacle_resolved, None,
                )
            return (
                f"Form {action.form_name} is not required at this stage. Please check requirements.",
                None, None, "wrong_form",
            )

    def _handle_check_requirements(self, action: BureaucracyAction) -> Tuple:
        """Handle the agent asking what is needed."""
        dept_id = self._state.current_department_id
        task = self._task
        docs_held = [d.doc_id for d in self._state.documents_held]
        missing = [d for d in task.required_documents if d not in docs_held]

        if not missing:
            response = "You appear to have all required documents. Proceed with your application."
        else:
            missing_names = ", ".join(d.replace("_", " ").title() for d in missing[:3])
            response = f"For this process, you still need: {missing_names}. Please arrange these documents."

        return response, None, None, None

    def _get_expected_next_dept(self) -> Optional[str]:
        """Get the next expected department on the solution path.

        The agent is always 'at' some position on the path; this returns the
        department they should move to next.
        """
        path = self._task.solution_path
        cur = self._state.current_department_id
        # Find the latest occurrence of the current dept on the path
        idx = -1
        for i, d in enumerate(path):
            if d == cur:
                idx = i
        if idx >= 0 and idx + 1 < len(path):
            return path[idx + 1]
        # If current dept not on path at all, fall back to the next unreached one
        idx2 = self._state.current_path_index
        if idx2 < len(path):
            return path[idx2]
        return None

    # Map of obstacle_id -> set of department IDs whose visit/action resolves it.
    # Derived from the human-readable required_resolution text in tasks.py.
    _OBSTACLE_RESOLVING_DEPTS: Dict[str, set] = {
        "T1_O1": {"D3", "D7"},          # not portal — go to billing/grievance
        "T2_O2": {"D9"},                 # need notarized affidavit from notary
        "T3_O1": {"D8"},                 # fix portal error
        "T3_O2": {"D5"},                 # medical fitness from D5
        "T4_O1": {"D9"},                 # notarize address proof
        "T4_O2": {"D6"},                 # gazetted attestation
        "T5_O1": {"D7"},                 # file formal grievance
        "T5_O2": {"D5"},                 # site inspection first
        "T6_O1": {"D6"},                 # get D6 approval before D5
        "T6_O2": {"D6"},                 # external structural cert presented at D6
        "T6_O3": {"D9"},                 # NOC affidavit at D9
    }

    def _check_obstacle_resolution(self, dept_id: str, trigger: str) -> Optional[str]:
        """Check if arriving at a dept resolves any pending obstacle."""
        for obs in self._task.obstacles:
            if obs.obstacle_id in self._obstacles_resolved:
                continue
            if obs.obstacle_id not in self._obstacles_triggered:
                continue
            resolving_depts = self._OBSTACLE_RESOLVING_DEPTS.get(obs.obstacle_id, set())
            if dept_id in resolving_depts:
                self._obstacles_resolved.append(obs.obstacle_id)
                if obs.obstacle_id in self._obstacles_triggered:
                    self._obstacles_triggered.remove(obs.obstacle_id)
                return obs.obstacle_id
        return None

    def _maybe_trigger_wait_state(self, dept_id: str) -> None:
        """If arriving at this dept fires a WAIT_STATE obstacle, set up the wait."""
        if self._state.wait_steps_remaining > 0:
            return
        for obs in self._task.obstacles:
            if (obs.obstacle_type == ObstacleType.WAIT_STATE
                    and obs.triggered_at_dept == dept_id
                    and obs.obstacle_id not in self._obstacles_resolved
                    and obs.obstacle_id not in self._obstacles_triggered):
                # Number of wait steps = obstacle.step_cost (or fall back to 3)
                wait_steps = max(1, obs.step_cost or 3)
                self._state.wait_steps_remaining = wait_steps
                self._obstacles_triggered.append(obs.obstacle_id)
                return

    def _get_active_obstacle_at(self, dept_id: str):
        """Get the currently active speak/form obstacle at a department, if any.

        Wait-state obstacles are handled separately by _maybe_trigger_wait_state
        and are not surfaced here.
        """
        for obs in self._task.obstacles:
            if obs.obstacle_type == ObstacleType.WAIT_STATE:
                continue
            if (obs.triggered_at_dept == dept_id
                    and obs.obstacle_id not in self._obstacles_resolved):
                if obs.obstacle_id not in self._obstacles_triggered:
                    self._obstacles_triggered.append(obs.obstacle_id)
                return obs
        return None

    def _check_speech_resolves_obstacle(self, text: str, obstacle) -> bool:
        """Check if agent's speech text resolves the given obstacle."""
        obstacle_type = obstacle.obstacle_type

        # Resolution keywords by obstacle type. Wait states are handled separately
        # and never resolved by speaking.
        resolution_keywords = {
            "wrong_redirect": [
                "not portal", "not a portal", "direct charge", "direct billing",
                "billing", "account issue", "transaction issue", "not online",
            ],
            "missing_doc": [
                "have the", "bring the", "here is", "i have", "screenshot",
                "document", "attached", "submit", "providing",
            ],
            "jargon_deflection": [
                "clarify", "what does", "explain", "mean", "what is required",
                "simpler", "in simple", "could you explain", "what is",
            ],
            "contradictory_rule": [
                "you said", "earlier", "different", "trust", "noc", "certificate",
                "follow", "okay i will", "understood", "i will obtain",
            ],
            "external_requirement": [
                "engineer", "certificate", "obtained", "here it is", "have it",
                "private", "doctor", "external",
            ],
            "system_error": [
                "portal", "error", "fix", "technical", "help desk", "it support", "d8",
            ],
        }

        keywords = resolution_keywords.get(obstacle.obstacle_type.value, [])
        return any(kw in text for kw in keywords)

    def _get_obstacle_response(self, dept_id: str, obstacle) -> str:
        """Get clerk response when obstacle is active."""
        responses = {
            "T1_O1": "For transaction issues, have you tried the portal? Go to D8 first.",
            "T1_O2": "I need to see the transaction SMS screenshot. Do you have it?",
            "T2_O1": "As per gazette notification prerequisite under Section 12(3), mutation entry requires prior documentation.",
            "T2_O2": "Name correction requires a notarized affidavit. Have you obtained that from the Notary Counter?",
            "T3_O1": "Your online application has an error. The system is not accepting your date. Go to Portal Help Desk.",
            "T3_O2": "Medical fitness certificate is also required. Have you done your medical verification?",
            "T3_O3": "Inspection report is not ready yet. Please wait the required working days.",
            "T4_O1": "Address proof must be notarized. Have you got it notarized from the Notary Counter?",
            "T4_O2": "In addition, Gazetted Officer attestation is also required on all documents.",
            "T4_O3": "Police verification is in progress. Please wait for the report.",
            "T5_O1": "Our records show no discrepancy. If you disagree, file a formal grievance.",
            "T5_O2": "For revenue disputes, site inspection is mandatory. Please go to Field Inspection Unit first.",
            "T5_O3": "The record shows legacy classification — revenue subdivision required before modification.",
            "T5_O4": "Inspection report will be ready in a few more working days. Please wait.",
            "T6_O1": "Building plan has not been approved yet. Get Senior Officer approval first.",
            "T6_O2": "You need a structural engineer certificate. That is from a licensed private engineer, not from us.",
            "T6_O3": "Actually, NOC affidavit is also required. New circular. Please go to Notary Counter.",
            "T6_O4": "First inspection report is not ready. Please wait.",
            "T6_O5": "Second inspection report is not ready. Please wait.",
        }
        return responses.get(obstacle.obstacle_id, "Please provide the required documents before proceeding.")

    def _get_resolution_response(self, dept_id: str, obstacle) -> str:
        """Get clerk response after obstacle is resolved."""
        next_name = self._get_next_dept_name()
        next_id = self._get_next_dept_id()
        return (
            f"Okay, that is acceptable. Your matter at this counter is settled. "
            f"Please now proceed to {next_name} ({next_id}) for the next step."
        )

    def _get_normal_speak_response(self, dept_id: str, text: str) -> str:
        """Get normal clerk response when no obstacle is active."""
        # If agent is on the solution path, push them clearly to the next stop.
        if dept_id in self._task.solution_path:
            idx = self._task.solution_path.index(dept_id)
            if idx + 1 < len(self._task.solution_path):
                next_dept = self._task.solution_path[idx + 1]
                next_dept_obj = get_department(next_dept)
                next_dept_name = next_dept_obj.name if next_dept_obj else "next department"
                if idx + 1 == len(self._task.solution_path) - 1:
                    return (
                        f"Your file is in order. Please proceed to {next_dept_name} ({next_dept}) "
                        f"for final issuance."
                    )
                return (
                    f"Understood. I have noted your request. You should now proceed to "
                    f"{next_dept_name} ({next_dept}) for the next step."
                )
        return get_clerk_response(dept_id, "greeting")

    def _check_document_grant(self, dept_id: str) -> Optional[str]:
        """Check if current interaction should grant a document."""
        doc_grants = {
            "D9": "notarized_document",
            "D7": "grievance_reference",
            "D5": "inspection_clearance",
            "D6": "approval_order",
            "D3": "fee_receipt",
            "D8": "portal_acknowledgment",
            "D4": "records_extract",
            "D2": "verification_stamp",
        }
        doc_id = doc_grants.get(dept_id)
        if doc_id and doc_id not in [d.doc_id for d in self._state.documents_held]:
            task_docs = self._task.required_documents
            # Only grant if this doc is relevant to current task
            relevant_grants = {
                "D9": ["notarized_address_proof", "noc_affidavit", "affidavit_name_correction"],
                "D7": ["grievance_reference"],
                "D5": ["inspection_clearance", "first_inspection_clearance",
                       "second_inspection_clearance", "police_verification_clearance",
                       "medical_fitness_certificate"],
                "D6": ["gazetted_officer_attestation", "reclassification_order", "approved_plan"],
                "D3": ["permit_fee_receipt"],
                "D8": ["portal_acknowledgment"],
                "D4": ["records_extract"],
            }
            dept_grants = relevant_grants.get(dept_id, [])
            for task_doc in task_docs:
                if task_doc in dept_grants:
                    doc = DocumentStatus(
                        doc_id=task_doc,
                        doc_name=task_doc.replace("_", " ").title(),
                        obtained_from=dept_id,
                    )
                    self._state.documents_held.append(doc)
                    return task_doc
        return None

    def _check_goal_conditions(self) -> bool:
        """Check if all conditions are met to achieve the goal."""
        required = set(self._task.required_documents)
        held = set(d.doc_id for d in self._state.documents_held)
        # Goal achieved if at D10 with most required documents
        docs_met = len(required & held) >= len(required) * 0.8
        return docs_met

    def _get_post_wait_response(self) -> str:
        """Response after wait state ends."""
        dept_id = self._state.current_department_id
        # Mark any wait_state obstacle at this dept as resolved.
        for obs in self._task.obstacles:
            if (obs.obstacle_type == ObstacleType.WAIT_STATE
                    and obs.triggered_at_dept == dept_id
                    and obs.obstacle_id not in self._obstacles_resolved):
                self._obstacles_resolved.append(obs.obstacle_id)
                if obs.obstacle_id in self._obstacles_triggered:
                    self._obstacles_triggered.remove(obs.obstacle_id)
                break
        # Try to grant the inspection/clearance document this dept is gated on.
        granted = self._check_document_grant(dept_id)
        next_name = self._get_next_dept_name()
        next_id = self._get_next_dept_id()
        granted_msg = ""
        if granted:
            pretty = granted.replace("_", " ").title()
            granted_msg = f" Here is your {pretty}."
        return (
            f"Your waiting period is over. The report is ready.{granted_msg} "
            f"Please proceed to {next_name} ({next_id})."
        )

    def _get_next_dept_name(self) -> str:
        """Get name of next department on solution path."""
        next_id = self._get_next_dept_id()
        if next_id:
            dept = get_department(next_id)
            return dept.name if dept else "next department"
        return "Final Issuance Window"

    def _get_next_dept_id(self) -> str:
        """Get ID of next department on solution path."""
        path = self._task.solution_path
        cur = self._state.current_department_id
        # Find the last occurrence of current dept in path so revisits behave correctly
        idx = -1
        for i, d in enumerate(path):
            if d == cur:
                idx = i
        if idx >= 0 and idx + 1 < len(path):
            return path[idx + 1]
        return "D10"

    def _build_observation(
        self, clerk_response: str, error: Optional[str]
    ) -> BureaucracyObservation:
        """Build the observation object from current state."""
        dept = get_department(self._state.current_department_id)
        docs_held = [d.doc_name for d in self._state.documents_held]

        # Available departments to navigate to
        available_depts = [
            {"id": d_id, "name": d.name, "floor": d.floor}
            for d_id, d in DEPARTMENTS.items()
            if d_id != self._state.current_department_id
        ]

        return BureaucracyObservation(
            current_department_id=self._state.current_department_id,
            current_department_name=dept.name if dept else "Unknown",
            clerk_response=clerk_response,
            available_actions=[a.value for a in ActionType],
            available_departments=available_depts,
            documents_held=docs_held,
            forms_available=[],
            goal_description=self._task.goal,
            steps_used=self._state.steps_used,
            steps_remaining=self._state.max_steps - self._state.steps_used,
            is_waiting=self._state.wait_steps_remaining > 0,
            wait_steps_remaining=self._state.wait_steps_remaining,
            last_action_error=error,
            goal_achieved=self._state.goal_achieved,
        )
