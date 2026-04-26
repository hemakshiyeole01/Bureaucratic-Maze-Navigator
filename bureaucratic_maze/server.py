"""
FastAPI server for the Bureaucratic Maze Navigator environment.
Exposes the OpenEnv-compliant interface over HTTP.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bureaucratic_maze.environment import BureaucraticMazeEnv
from bureaucratic_maze.models import BureaucracyAction, TaskInfo

app = FastAPI(
    title="Bureaucratic Maze Navigator",
    description=(
        "An OpenEnv-compliant environment where an AI agent navigates Indian "
        "government bureaucracy to accomplish real civic goals."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (one env per session_id)
_sessions: Dict[str, BureaucraticMazeEnv] = {}


class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_1"
    seed: Optional[int] = None
    session_id: Optional[str] = "default"


class StepRequest(BaseModel):
    action: BureaucracyAction
    session_id: Optional[str] = "default"


class StateRequest(BaseModel):
    session_id: Optional[str] = "default"


def _get_or_create_env(session_id: str, task_id: str = "task_1", seed: Optional[int] = None) -> BureaucraticMazeEnv:
    if session_id not in _sessions:
        _sessions[session_id] = BureaucraticMazeEnv(task_id=task_id, seed=seed)
    return _sessions[session_id]


@app.get("/")
def root():
    return {
        "env": "bureaucratic-maze",
        "version": "1.0.0",
        "description": "Navigate Indian government bureaucracy to accomplish civic goals.",
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/health"],
    }


@app.get("/health")
def health():
    # openenv validate expects status == "healthy"
    return {"status": "healthy", "env": "bureaucratic-maze"}


@app.get("/metadata")
def metadata():
    """OpenEnv required metadata endpoint."""
    return {
        "name": "bureaucratic-maze",
        "description": (
            "An OpenEnv environment where an AI agent navigates Indian government "
            "bureaucracy to accomplish real civic goals. The agent must find the "
            "correct path through departments, wrong transfers, missing forms, "
            "contradictory rules, and unhelpful clerks."
        ),
        "version": "1.0.0",
        "tasks": [
            {"id": "task_1", "difficulty": "easy", "max_steps": 15},
            {"id": "task_2", "difficulty": "easy_medium", "max_steps": 20},
            {"id": "task_3", "difficulty": "medium", "max_steps": 28},
            {"id": "task_4", "difficulty": "medium_hard", "max_steps": 35},
            {"id": "task_5", "difficulty": "hard", "max_steps": 40},
            {"id": "task_6", "difficulty": "very_hard", "max_steps": 50},
        ],
        "tags": ["openenv", "real-world", "bureaucracy", "civic", "india"],
    }


@app.get("/schema")
def schema():
    """OpenEnv required schema endpoint — action, observation, state schemas."""
    return {
        "action": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["speak", "go_to", "submit_form",
                             "request_transfer", "check_requirements", "wait"],
                },
                "text": {"type": "string", "description": "Speech text"},
                "department_id": {"type": "string", "description": "Target dept ID (D1-D10)"},
                "form_name": {"type": "string", "description": "Form name to submit"},
                "form_fields": {"type": "object", "description": "Form field values"},
                "query": {"type": "string", "description": "Requirements query text"},
            },
            "required": ["action_type"],
        },
        "observation": {
            "type": "object",
            "properties": {
                "current_department_id": {"type": "string"},
                "current_department_name": {"type": "string"},
                "clerk_response": {"type": "string"},
                "available_actions": {"type": "array", "items": {"type": "string"}},
                "available_departments": {"type": "array"},
                "documents_held": {"type": "array", "items": {"type": "string"}},
                "goal_description": {"type": "string"},
                "steps_used": {"type": "integer"},
                "steps_remaining": {"type": "integer"},
                "is_waiting": {"type": "boolean"},
                "wait_steps_remaining": {"type": "integer"},
                "goal_achieved": {"type": "boolean"},
                "last_action_error": {"type": "string", "nullable": True},
            },
        },
        "state": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "task_name": {"type": "string"},
                "episode_id": {"type": "string"},
                "current_department": {"type": "string"},
                "steps_used": {"type": "integer"},
                "max_steps": {"type": "integer"},
                "steps_remaining": {"type": "integer"},
                "goal_achieved": {"type": "boolean"},
                "documents_held": {"type": "array", "items": {"type": "string"}},
                "wait_steps_remaining": {"type": "integer"},
                "score": {"type": "number"},
            },
        },
    }


@app.post("/reset")
def reset(request: ResetRequest = None):
    if request is None:
        request = ResetRequest()
    session_id = request.session_id or "default"
    task_id = request.task_id or "task_1"

    env = BureaucraticMazeEnv(task_id=task_id, seed=request.seed)
    _sessions[session_id] = env

    result = env.reset(task_id=task_id)
    return result.dict()


@app.post("/step")
def step(request: StepRequest):
    session_id = request.session_id or "default"
    if session_id not in _sessions:
        raise HTTPException(status_code=400, detail="Session not found. Call /reset first.")

    env = _sessions[session_id]
    result = env.step(request.action)
    return result.dict()


@app.post("/state")
def state(request: StateRequest = None):
    if request is None:
        request = StateRequest()
    session_id = request.session_id or "default"
    if session_id not in _sessions:
        raise HTTPException(status_code=400, detail="Session not found. Call /reset first.")

    env = _sessions[session_id]
    return env.state()


@app.get("/tasks")
def list_tasks():
    env = BureaucraticMazeEnv(task_id="task_1")
    tasks = env.list_tasks()
    return {"tasks": [t.dict() for t in tasks]}


@app.get("/tasks/{task_id}")
def get_task_info(task_id: str):
    env = BureaucraticMazeEnv(task_id="task_1")
    info = env.get_task_info(task_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return info.dict()


@app.get("/departments")
def list_departments():
    from bureaucratic_maze.departments import get_department_list
    return {"departments": get_department_list()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bureaucratic_maze.server:app", host="0.0.0.0", port=7860, reload=False)
