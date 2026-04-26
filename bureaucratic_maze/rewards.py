"""
Reward functions for the Bureaucratic Maze Navigator.
Multiple independent reward signals — anti-hacking by design.
"""

from typing import Dict, List, Optional, Tuple
from bureaucratic_maze.tasks import TaskDefinition, ObstacleType


class RewardCalculator:
    """
    Computes step-level rewards using multiple independent signals.
    Each signal is capped and independent — gaming one doesn't unlock others.
    """

    # Reward constants
    CORRECT_DEPT_REWARD = 0.10        # Visiting a department on the solution path
    CORRECT_ACTION_REWARD = 0.05      # Taking an action that advances the solution
    DOCUMENT_OBTAINED_REWARD = 0.15   # Obtaining a required document
    OBSTACLE_RESOLVED_REWARD = 0.08   # Resolving an obstacle
    GOAL_COMPLETE_REWARD = 0.50       # Completing the task

    WRONG_DEPT_PENALTY = -0.02        # Visiting a department not on solution path
    CIRCULAR_LOOP_PENALTY = -0.10     # Revisiting same dept more than 2x
    STEP_TIMEOUT_PENALTY = -0.01      # Each step over optimal count
    INVALID_ACTION_PENALTY = -0.03    # Taking an invalid action
    REWARD_HACK_PENALTY = -0.20       # Detected reward hacking attempt

    def __init__(self, task: TaskDefinition):
        self.task = task
        self.visit_counts: Dict[str, int] = {}
        self.rewarded_depts: set = set()
        self.rewarded_docs: set = set()
        self.rewarded_obstacles: set = set()
        self.total_reward: float = 0.0
        self.reward_history: List[float] = []

    def compute_step_reward(
        self,
        current_dept: str,
        action_type: str,
        action_result: str,          # "success", "error", "redirect", "wait"
        document_obtained: Optional[str],
        obstacle_resolved: Optional[str],
        steps_used: int,
        goal_achieved: bool,
        is_loop: bool = False,
        is_invalid_action: bool = False,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute reward for a single step.
        Returns (total_step_reward, breakdown).
        """
        breakdown: Dict[str, float] = {}
        step_reward = 0.0

        # Track visit counts for loop detection
        self.visit_counts[current_dept] = self.visit_counts.get(current_dept, 0) + 1

        # ── Signal 1: Correct department visited ──────────────────────────
        if (current_dept in self.task.solution_path
                and current_dept not in self.rewarded_depts):
            r = self.CORRECT_DEPT_REWARD
            breakdown["correct_dept"] = r
            step_reward += r
            self.rewarded_depts.add(current_dept)

        # ── Signal 2: Wrong department penalty ───────────────────────────
        elif current_dept not in self.task.solution_path:
            r = self.WRONG_DEPT_PENALTY
            breakdown["wrong_dept"] = r
            step_reward += r

        # ── Signal 3: Correct action reward ──────────────────────────────
        if action_result == "success" and action_type in ["speak", "submit_form"]:
            r = self.CORRECT_ACTION_REWARD
            breakdown["correct_action"] = r
            step_reward += r

        # ── Signal 4: Document obtained reward ───────────────────────────
        if (document_obtained
                and document_obtained in self.task.required_documents
                and document_obtained not in self.rewarded_docs):
            r = self.DOCUMENT_OBTAINED_REWARD
            breakdown["document_obtained"] = r
            step_reward += r
            self.rewarded_docs.add(document_obtained)

        # ── Signal 5: Obstacle resolved reward ───────────────────────────
        if (obstacle_resolved
                and obstacle_resolved not in self.rewarded_obstacles):
            r = self.OBSTACLE_RESOLVED_REWARD
            breakdown["obstacle_resolved"] = r
            step_reward += r
            self.rewarded_obstacles.add(obstacle_resolved)

        # ── Signal 6: Goal completion reward ─────────────────────────────
        if goal_achieved:
            r = self.GOAL_COMPLETE_REWARD
            breakdown["goal_complete"] = r
            step_reward += r

        # ── Signal 7: Circular loop penalty ──────────────────────────────
        if self.visit_counts.get(current_dept, 0) > 2 or is_loop:
            r = self.CIRCULAR_LOOP_PENALTY
            breakdown["circular_loop"] = r
            step_reward += r

        # ── Signal 8: Step efficiency penalty ────────────────────────────
        if steps_used > self.task.optimal_step_count:
            r = self.STEP_TIMEOUT_PENALTY
            breakdown["step_penalty"] = r
            step_reward += r

        # ── Signal 9: Invalid action penalty ─────────────────────────────
        if is_invalid_action:
            r = self.INVALID_ACTION_PENALTY
            breakdown["invalid_action"] = r
            step_reward += r

        # Clamp step reward to prevent extreme values
        step_reward = max(-0.5, min(0.8, step_reward))

        self.total_reward += step_reward
        self.reward_history.append(round(step_reward, 4))
        breakdown["step_total"] = round(step_reward, 4)

        return round(step_reward, 4), breakdown

    def detect_reward_hack(
        self,
        action_text: Optional[str],
        dept_visit_sequence: List[str],
        step_count: int,
    ) -> Tuple[bool, str]:
        """
        Detect common reward hacking patterns.
        Returns (is_hacking, reason).
        """
        # Check for suspiciously fast completion
        if step_count < 3 and len(self.rewarded_depts) >= 3:
            return True, "too_fast_completion"

        # Check for repeated identical actions (action spam)
        if action_text:
            if action_text.strip().lower() in [
                "goal achieved", "task complete", "i have completed",
                "done", "finished", "success"
            ]:
                return True, "explicit_goal_claim"

        # Check for visiting all departments rapidly (fishing for dept rewards)
        unique_depts = set(dept_visit_sequence[-5:]) if len(dept_visit_sequence) >= 5 else set()
        if len(unique_depts) >= 5 and step_count <= 6:
            return True, "rapid_dept_scanning"

        return False, ""

    def get_summary(self) -> Dict:
        return {
            "total_reward": round(self.total_reward, 4),
            "reward_history": self.reward_history,
            "depts_rewarded": list(self.rewarded_depts),
            "docs_rewarded": list(self.rewarded_docs),
            "obstacles_rewarded": list(self.rewarded_obstacles),
            "visit_counts": self.visit_counts,
        }
