"""
Task definitions for the Bureaucratic Maze Navigator.
Defines all 6 tasks with solution paths, obstacles, and graders.
SERVER-SIDE ONLY — solution paths never exposed to agent.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ObstacleType(str, Enum):
    WRONG_REDIRECT = "wrong_redirect"
    MISSING_DOC = "missing_doc"
    WAIT_STATE = "wait_state"
    JARGON_DEFLECTION = "jargon_deflection"
    CONTRADICTORY_RULE = "contradictory_rule"
    EXTERNAL_REQUIREMENT = "external_requirement"
    RUDE_CLERK = "rude_clerk"
    SYSTEM_ERROR = "system_error"


@dataclass
class Obstacle:
    obstacle_id: str
    obstacle_type: ObstacleType
    triggered_at_dept: str
    trigger_condition: str          # When this fires
    description: str
    step_cost: int = 0              # Extra steps this obstacle costs
    required_resolution: Optional[str] = None  # What resolves this obstacle


@dataclass
class TaskDefinition:
    task_id: str
    task_name: str
    difficulty: str
    goal: str
    description: str
    citizen_persona: str            # Who the agent is playing
    solution_path: List[str]        # Ordered dept IDs — NEVER sent to agent
    required_documents: List[str]   # Documents needed to complete task
    max_steps: int
    obstacles: List[Obstacle]
    success_document: str           # Name of document issued on success
    optimal_step_count: int         # Steps for a perfect run
    initial_documents: List[str] = field(default_factory=list)  # Docs agent starts with


# ─────────────────────────────────────────────
# TASK 1 — Wrong Charge Refund (EASY)
# ─────────────────────────────────────────────
TASK_1 = TaskDefinition(
    task_id="task_1",
    task_name="wrong_charge_refund",
    difficulty="easy",
    goal="Get a ₹500 wrong transaction reversed by the bank's grievance cell",
    description=(
        "You are Ramesh Kumar, a salaried employee who noticed ₹500 was wrongly "
        "debited from your account for a service you never used. You need to get "
        "this charge reversed and obtain an acknowledgment letter."
    ),
    citizen_persona="Ramesh Kumar, 35, software engineer, polite but firm",
    solution_path=["D1", "D3", "D7", "D10"],
    required_documents=["transaction_sms_screenshot", "account_statement", "grievance_reference"],
    max_steps=15,
    obstacles=[
        Obstacle(
            obstacle_id="T1_O1",
            obstacle_type=ObstacleType.WRONG_REDIRECT,
            triggered_at_dept="D1",
            trigger_condition="first_visit",
            description="Clerk at D1 initially redirects to D8 (portal) instead of D3",
            step_cost=2,
            required_resolution="Agent must clarify it's not a portal issue but a direct charge"
        ),
        Obstacle(
            obstacle_id="T1_O2",
            obstacle_type=ObstacleType.MISSING_DOC,
            triggered_at_dept="D3",
            trigger_condition="first_visit",
            description="D3 requires transaction SMS screenshot before processing",
            step_cost=1,
            required_resolution="Agent must mention having the SMS screenshot"
        ),
    ],
    success_document="Refund Acknowledgment Letter",
    optimal_step_count=7,
    initial_documents=["transaction_sms_screenshot", "account_statement"],
)


# ─────────────────────────────────────────────
# TASK 2 — Ration Card Name Correction (EASY-MEDIUM)
# ─────────────────────────────────────────────
TASK_2 = TaskDefinition(
    task_id="task_2",
    task_name="ration_card_name_correction",
    difficulty="easy_medium",
    goal="Fix a spelling error in applicant's name on the ration card",
    description=(
        "You are Priya Lakshmi, whose name is misspelled as 'Priya Laxmi' on the "
        "family ration card. This is causing issues with other documents. You need "
        "the correct spelling officially recorded and a new ration card issued."
    ),
    citizen_persona="Priya Lakshmi, 28, homemaker, first time dealing with government offices",
    solution_path=["D1", "D4", "D9", "D2", "D10"],
    required_documents=["birth_certificate", "affidavit_name_correction", "ration_card_original"],
    max_steps=20,
    obstacles=[
        Obstacle(
            obstacle_id="T2_O1",
            obstacle_type=ObstacleType.JARGON_DEFLECTION,
            triggered_at_dept="D4",
            trigger_condition="first_visit",
            description="D4 clerk uses jargon: 'gazette notification prerequisite' — agent must ask for clarification",
            step_cost=2,
            required_resolution="Agent must ask what 'gazette notification prerequisite' means concretely"
        ),
        Obstacle(
            obstacle_id="T2_O2",
            obstacle_type=ObstacleType.MISSING_DOC,
            triggered_at_dept="D4",
            trigger_condition="after_jargon_cleared",
            description="D4 requires notarized affidavit from D9 before accepting documents",
            step_cost=3,
            required_resolution="Agent must go to D9 first and get affidavit, then return to D4"
        ),
    ],
    success_document="Corrected Ration Card",
    optimal_step_count=10,
    initial_documents=["birth_certificate", "ration_card_original"],
)


# ─────────────────────────────────────────────
# TASK 3 — Driving License Renewal (MEDIUM)
# ─────────────────────────────────────────────
TASK_3 = TaskDefinition(
    task_id="task_3",
    task_name="driving_license_renewal",
    difficulty="medium",
    goal="Renew an expired driving license (expired 6 months ago)",
    description=(
        "You are Vijay Anand, whose driving license expired 6 months ago. You have "
        "been driving with an expired license and need to renew it urgently. The "
        "online portal has a date validation error that is blocking your application."
    ),
    citizen_persona="Vijay Anand, 42, small business owner, somewhat impatient",
    solution_path=["D1", "D2", "D8", "D2", "D5", "D6", "D10"],
    required_documents=[
        "expired_driving_license", "form_lld", "medical_fitness_certificate",
        "portal_acknowledgment", "inspection_clearance"
    ],
    max_steps=28,
    obstacles=[
        Obstacle(
            obstacle_id="T3_O1",
            obstacle_type=ObstacleType.SYSTEM_ERROR,
            triggered_at_dept="D2",
            trigger_condition="first_visit",
            description="D2 cannot process because portal application has date validation error",
            step_cost=3,
            required_resolution="Agent must go to D8 to fix the portal error"
        ),
        Obstacle(
            obstacle_id="T3_O2",
            obstacle_type=ObstacleType.MISSING_DOC,
            triggered_at_dept="D2",
            trigger_condition="second_visit",
            description="After portal fix, D2 requires medical fitness certificate from D5",
            step_cost=2,
            required_resolution="Agent must get medical/fitness verification from D5"
        ),
        Obstacle(
            obstacle_id="T3_O3",
            obstacle_type=ObstacleType.WAIT_STATE,
            triggered_at_dept="D5",
            trigger_condition="inspection_scheduled",
            description="D5 inspection requires 2 working days before report is ready",
            step_cost=4,
            required_resolution="Agent must wait (use WAIT action) or come back after wait period"
        ),
    ],
    success_document="Renewed Driving License",
    optimal_step_count=14,
    initial_documents=["expired_driving_license", "form_lld"],
)


# ─────────────────────────────────────────────
# TASK 4 — Passport Renewal with Address Change (MEDIUM-HARD)
# ─────────────────────────────────────────────
TASK_4 = TaskDefinition(
    task_id="task_4",
    task_name="passport_renewal_address_change",
    difficulty="medium_hard",
    goal="Renew passport and update address simultaneously",
    description=(
        "You are Kavitha Suresh, who needs to renew her passport which expires in "
        "3 months. She also recently moved houses and needs the new address reflected. "
        "She has her address proof but is unaware of the full requirements."
    ),
    citizen_persona="Kavitha Suresh, 31, IT professional, organized but new to passport process",
    solution_path=["D1", "D4", "D2", "D9", "D6", "D5", "D2", "D10"],
    required_documents=[
        "passport_original", "address_proof", "notarized_address_proof",
        "gazetted_officer_attestation", "police_verification_clearance"
    ],
    max_steps=35,
    obstacles=[
        Obstacle(
            obstacle_id="T4_O1",
            obstacle_type=ObstacleType.MISSING_DOC,
            triggered_at_dept="D2",
            trigger_condition="first_visit",
            description="D2 requires address proof to be notarized before acceptance",
            step_cost=3,
            required_resolution="Agent must go to D9 for notarization"
        ),
        Obstacle(
            obstacle_id="T4_O2",
            obstacle_type=ObstacleType.CONTRADICTORY_RULE,
            triggered_at_dept="D2",
            trigger_condition="second_visit_with_notarized_doc",
            description="D2 now says Gazetted Officer attestation ALSO needed — wasn't mentioned first visit",
            step_cost=3,
            required_resolution="Agent must go to D6 for attestation despite not being told initially"
        ),
        Obstacle(
            obstacle_id="T4_O3",
            obstacle_type=ObstacleType.WAIT_STATE,
            triggered_at_dept="D5",
            trigger_condition="police_verification_triggered",
            description="Police verification (D5) takes 3 working days",
            step_cost=5,
            required_resolution="Agent must wait for police verification to complete"
        ),
    ],
    success_document="Renewed Passport with Updated Address",
    optimal_step_count=18,
    initial_documents=["passport_original", "address_proof"],
)


# ─────────────────────────────────────────────
# TASK 5 — Property Tax Dispute (HARD)
# ─────────────────────────────────────────────
TASK_5 = TaskDefinition(
    task_id="task_5",
    task_name="property_tax_dispute",
    difficulty="hard",
    goal="Dispute an inflated property tax bill — charged commercial rate on residential property",
    description=(
        "You are Sundaram Iyer, a retired teacher who received a property tax bill "
        "at commercial rates for his residential house. The bill is 3x the expected "
        "amount. He needs the property reclassified and a revised bill issued."
    ),
    citizen_persona="Sundaram Iyer, 62, retired teacher, persistent but gets confused by jargon",
    solution_path=["D1", "D3", "D7", "D4", "D5", "D6", "D3", "D10"],
    required_documents=[
        "tax_bill_original", "property_documents", "grievance_reference",
        "records_extract", "inspection_report", "reclassification_order"
    ],
    max_steps=40,
    obstacles=[
        Obstacle(
            obstacle_id="T5_O1",
            obstacle_type=ObstacleType.WRONG_REDIRECT,
            triggered_at_dept="D3",
            trigger_condition="first_visit",
            description="D3 denies error and redirects to Grievance Cell without acknowledging the problem",
            step_cost=2,
            required_resolution="Agent must file formal grievance at D7"
        ),
        Obstacle(
            obstacle_id="T5_O2",
            obstacle_type=ObstacleType.MISSING_DOC,
            triggered_at_dept="D7",
            trigger_condition="grievance_filed",
            description="D7 requires site inspection before accepting revenue dispute",
            step_cost=3,
            required_resolution="Agent must get inspection from D5 before D7 will process"
        ),
        Obstacle(
            obstacle_id="T5_O3",
            obstacle_type=ObstacleType.JARGON_DEFLECTION,
            triggered_at_dept="D4",
            trigger_condition="records_check",
            description="D4 uses jargon about 'legacy classification' and 'revenue subdivision'",
            step_cost=2,
            required_resolution="Agent must ask clarifying questions to understand reclassification needed"
        ),
        Obstacle(
            obstacle_id="T5_O4",
            obstacle_type=ObstacleType.WAIT_STATE,
            triggered_at_dept="D5",
            trigger_condition="inspection_scheduled",
            description="D5 inspection report takes 5 working days",
            step_cost=6,
            required_resolution="Agent must wait for inspection report"
        ),
    ],
    success_document="Revised Property Tax Bill (Residential Rate)",
    optimal_step_count=20,
    initial_documents=["tax_bill_original", "property_documents"],
)


# ─────────────────────────────────────────────
# TASK 6 — Building Renovation Permit (VERY HARD)
# ─────────────────────────────────────────────
TASK_6 = TaskDefinition(
    task_id="task_6",
    task_name="building_renovation_permit",
    difficulty="very_hard",
    goal="Get a permit to add a second floor to a residential property",
    description=(
        "You are Mohan Krishnamurthy, who wants to add a second floor to his "
        "ground-floor house. He has the building plan ready but has no idea how "
        "many approvals are needed. The process involves multiple departments, "
        "contradictory requirements, and two separate wait states."
    ),
    citizen_persona="Mohan Krishnamurthy, 48, businessman, determined but easily frustrated by contradictions",
    solution_path=["D1", "D4", "D5", "D6", "D2", "D9", "D5", "D6", "D3", "D10"],
    required_documents=[
        "property_documents", "building_plan", "structural_engineer_certificate",
        "noc_affidavit", "first_inspection_clearance", "second_inspection_clearance",
        "approved_plan", "permit_fee_receipt"
    ],
    max_steps=50,
    obstacles=[
        Obstacle(
            obstacle_id="T6_O1",
            obstacle_type=ObstacleType.MISSING_DOC,
            triggered_at_dept="D5",
            trigger_condition="first_inspection_attempt",
            description="D5 rejects inspection because D6 hasn't approved the plan yet",
            step_cost=3,
            required_resolution="Agent must get D6 approval before D5 inspection"
        ),
        Obstacle(
            obstacle_id="T6_O2",
            obstacle_type=ObstacleType.EXTERNAL_REQUIREMENT,
            triggered_at_dept="D6",
            trigger_condition="first_visit",
            description="D6 requires structural engineer certificate — from private engineer, not government",
            step_cost=4,
            required_resolution="Agent must obtain structural engineer certificate externally and return"
        ),
        Obstacle(
            obstacle_id="T6_O3",
            obstacle_type=ObstacleType.CONTRADICTORY_RULE,
            triggered_at_dept="D2",
            trigger_condition="after_first_d6_approval",
            description="D2 initially says NOC not needed; D9 later says it is",
            step_cost=4,
            required_resolution="Agent must trust D9's requirement and get NOC affidavit"
        ),
        Obstacle(
            obstacle_id="T6_O4",
            obstacle_type=ObstacleType.WAIT_STATE,
            triggered_at_dept="D5",
            trigger_condition="first_inspection",
            description="First inspection report takes 3 working days",
            step_cost=4,
            required_resolution="Agent must wait for first inspection report"
        ),
        Obstacle(
            obstacle_id="T6_O5",
            obstacle_type=ObstacleType.WAIT_STATE,
            triggered_at_dept="D5",
            trigger_condition="second_inspection",
            description="Second inspection report takes 4 working days",
            step_cost=5,
            required_resolution="Agent must wait for second inspection report"
        ),
    ],
    success_document="Building Renovation Permit",
    optimal_step_count=28,
    initial_documents=["property_documents", "building_plan"],
)


# Registry of all tasks
ALL_TASKS: Dict[str, TaskDefinition] = {
    "task_1": TASK_1,
    "task_2": TASK_2,
    "task_3": TASK_3,
    "task_4": TASK_4,
    "task_5": TASK_5,
    "task_6": TASK_6,
}


def get_task(task_id: str) -> Optional[TaskDefinition]:
    return ALL_TASKS.get(task_id)


def get_all_task_ids() -> List[str]:
    return list(ALL_TASKS.keys())


# ─────────────────────────────────────────────
# GRADERS — one per task, deterministic, 0.0–1.0
# ─────────────────────────────────────────────

def grade_episode(
    task_id: str,
    departments_visited: List[str],
    actions_taken: List[str],
    documents_collected: List[str],
    goal_achieved: bool,
    steps_used: int,
    obstacles_resolved: List[str],
) -> Tuple[float, Dict]:
    """
    Grade a completed episode for a given task.
    Returns (score 0.0-1.0, breakdown dict).
    All graders are deterministic and reproducible.
    """
    task = get_task(task_id)
    if not task:
        return 0.0, {"error": "unknown task"}

    breakdown = {
        "completion_bonus": 0.0,
        "path_progress_score": 0.0,
        "document_score": 0.0,
        "obstacle_score": 0.0,
        "efficiency_score": 0.0,
        "total": 0.0,
    }

    # 1. Completion bonus (50% of total score)
    if goal_achieved:
        breakdown["completion_bonus"] = 0.5

    # 2. Path progress score (20% of total)
    # How many solution path nodes did the agent visit in correct order?
    solution = task.solution_path
    correct_visits = 0
    sol_index = 0
    for dept in departments_visited:
        if sol_index < len(solution) and dept == solution[sol_index]:
            correct_visits += 1
            sol_index += 1
    path_fraction = correct_visits / len(solution) if solution else 0.0
    breakdown["path_progress_score"] = round(path_fraction * 0.20, 4)

    # 3. Document score (15% of total)
    # What fraction of required documents were collected?
    required = set(task.required_documents)
    collected = set(documents_collected)
    doc_fraction = len(required & collected) / len(required) if required else 1.0
    breakdown["document_score"] = round(doc_fraction * 0.15, 4)

    # 4. Obstacle resolution score (10% of total)
    # What fraction of obstacles did the agent resolve?
    total_obstacles = len(task.obstacles)
    resolved_count = len(obstacles_resolved)
    obstacle_fraction = resolved_count / total_obstacles if total_obstacles > 0 else 1.0
    breakdown["obstacle_score"] = round(obstacle_fraction * 0.10, 4)

    # 5. Efficiency score (5% of total)
    # Penalize for steps over the optimal count
    if goal_achieved:
        efficiency = max(0.0, 1.0 - (steps_used - task.optimal_step_count) / task.max_steps)
        breakdown["efficiency_score"] = round(efficiency * 0.05, 4)

    total = sum([
        breakdown["completion_bonus"],
        breakdown["path_progress_score"],
        breakdown["document_score"],
        breakdown["obstacle_score"],
        breakdown["efficiency_score"],
    ])
    breakdown["total"] = round(min(1.0, total), 4)

    return breakdown["total"], breakdown
