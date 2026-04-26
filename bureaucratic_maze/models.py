"""
Pydantic models for the Bureaucratic Maze Navigator environment.
Defines Action, Observation, State, and StepResult types.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    SPEAK = "speak"
    GO_TO = "go_to"
    SUBMIT_FORM = "submit_form"
    REQUEST_TRANSFER = "request_transfer"
    CHECK_REQUIREMENTS = "check_requirements"
    WAIT = "wait"


class BureaucracyAction(BaseModel):
    """Action the agent can take in the environment."""
    action_type: ActionType = Field(..., description="Type of action to perform")
    text: Optional[str] = Field(None, description="Speech text when action_type is SPEAK")
    department_id: Optional[str] = Field(None, description="Target department for GO_TO or REQUEST_TRANSFER")
    form_name: Optional[str] = Field(None, description="Form name for SUBMIT_FORM")
    form_fields: Optional[Dict[str, str]] = Field(None, description="Form field values for SUBMIT_FORM")
    query: Optional[str] = Field(None, description="Query text for CHECK_REQUIREMENTS")

    class Config:
        use_enum_values = True


class DocumentStatus(BaseModel):
    """Tracks a document the agent has collected."""
    doc_id: str
    doc_name: str
    obtained_from: str
    is_valid: bool = True


class BureaucracyObservation(BaseModel):
    """What the agent sees after each step."""
    current_department_id: str = Field(..., description="ID of current department")
    current_department_name: str = Field(..., description="Human-readable department name")
    clerk_response: str = Field(..., description="What the clerk says in response to last action")
    available_actions: List[str] = Field(..., description="List of valid action types from this state")
    available_departments: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Departments agent can navigate to from here"
    )
    documents_held: List[str] = Field(default_factory=list, description="Document names currently held")
    forms_available: List[str] = Field(default_factory=list, description="Forms available to submit here")
    goal_description: str = Field(..., description="The citizen's goal for this episode")
    steps_used: int = Field(..., description="Steps consumed so far")
    steps_remaining: int = Field(..., description="Steps remaining before timeout")
    is_waiting: bool = Field(default=False, description="Whether agent is in a wait state")
    wait_steps_remaining: int = Field(default=0, description="Steps remaining in current wait")
    last_action_error: Optional[str] = Field(None, description="Error message if last action was invalid")
    goal_achieved: bool = Field(default=False, description="Whether the goal has been completed")
    hint: Optional[str] = Field(None, description="Occasional hint from environment (not always present)")


class DepartmentVisit(BaseModel):
    """Records a single department visit."""
    department_id: str
    department_name: str
    step_number: int
    action_taken: str
    clerk_response_summary: str


class BureaucracyState(BaseModel):
    """Full internal state of the environment (server-side only)."""
    task_id: str
    task_name: str
    episode_id: str
    current_department_id: str
    steps_used: int
    max_steps: int
    goal_achieved: bool
    documents_held: List[DocumentStatus]
    visit_history: List[DepartmentVisit]
    wait_steps_remaining: int
    solution_path: List[str]  # Hidden from agent — sequence of dept IDs
    current_path_index: int   # How far along optimal path agent currently is
    obstacles_triggered: List[str]  # Which obstacles have fired
    contradictions_active: List[str]  # Active policy contradictions
    score: float

    class Config:
        # Prevent accidental mutation
        frozen = False


class StepResult(BaseModel):
    """Result returned by env.step()."""
    observation: BureaucracyObservation
    reward: float = Field(..., description="Reward for this step")
    done: bool = Field(..., description="Whether episode is complete")
    info: Dict[str, Any] = Field(default_factory=dict, description="Extra diagnostic info")


class ResetResult(BaseModel):
    """Result returned by env.reset()."""
    observation: BureaucracyObservation
    info: Dict[str, Any] = Field(default_factory=dict)


class TaskInfo(BaseModel):
    """Public metadata about a task."""
    task_id: str
    task_name: str
    difficulty: str
    description: str
    max_steps: int
    goal: str
