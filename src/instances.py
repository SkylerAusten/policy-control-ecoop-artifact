from build_accounting_db import build_database as build_a_database
from build_grading_db import build_database as build_g_database
from build_tech_db import build_database as build_t_database
from instance_types import AccountingRequest, GradingRequest, TechRequest
from study_config import STUDY_PROBLEMS
import ast
import random

accounting_db = build_a_database()
grading_db = build_g_database()
tech_db = build_t_database()

POLICY_SHORTHANDS = ["correct", "alt1", "alt2", "alt3"]

def get_full_policy(problem_id: int, policy_short_name: str) -> str:
    problem = next((p for p in STUDY_PROBLEMS if p["id"] == problem_id), None)
    if not problem:
        raise ValueError(f"Problem ID {problem_id} not found.")

    if policy_short_name not in problem["candidates"]:
        raise ValueError(f"Policy '{policy_short_name}' not found in problem ID {problem_id}.")

    full_policy = problem["full_policies"].get(policy_short_name, None)

    if not full_policy:
        raise ValueError(
            f"Policy '{policy_short_name}' not found in problem {problem_id}'s full policy list."
        )

    else:
        return full_policy

def parse_accounting_request_string(request_str: str) -> AccountingRequest:
    """Parse a string representation of AccountingRequest back to an AccountingRequest object."""
    lines = request_str.strip().split('\n')

    # Initialize with defaults
    person_no = None
    roles = []
    is_in_training = None
    action_type = None
    resource_type = None
    is_under_audit = None
    is_archived = None

    for line in lines:
        line = line.strip()
        if line.startswith('Subject:'):
            person_no = line.split("Subject: Person", 1)[1].strip()
        elif line.startswith('Roles:'):
            roles_str = line.split(':', 1)[1].strip()
            # Parse the list format, e.g., "['Admin', 'Accountant']"
            try:
                roles_str = roles_str.strip("{}")  # remove the curly braces
                roles = [r.strip() for r in roles_str.split(",") if r.strip()]

            except:
                roles = []
        elif line.startswith('In Training:'):
            is_in_training = line.split(':', 1)[1].strip() == 'True'
        elif line.startswith('Action:'):
            action_type = line.split(':', 1)[1].strip()
        elif line.startswith('Resource:'):
            resource_type = line.split(':', 1)[1].strip()
        elif line.startswith('Under Audit:'):
            is_under_audit = line.split(':', 1)[1].strip() == 'True'
        elif line.startswith('Archived:'):
            is_archived = line.split(':', 1)[1].strip() == 'True'

    return AccountingRequest(
        roles=set(roles),
        is_in_training=is_in_training,
        action_type=action_type,
        resource_type=resource_type,
        is_under_audit=is_under_audit,
        is_archived=is_archived,
        person_no = person_no
    )


def parse_grading_request_string(request_str: str) -> GradingRequest:
    """Parse a string representation of GradingRequest back to an GradingRequest object."""
    lines = request_str.strip().split("\n")

    # Initialize with defaults
    person_no = None
    roles = []
    is_submitted = None
    action_type = None
    resource_type = None

    for line in lines:
        line = line.strip()
        if line.startswith("Subject:"):
            person_no = line.split("Subject: Person", 1)[1].strip()
        elif line.startswith("Roles:"):
            roles_str = line.split(":", 1)[1].strip()
            # Parse the list format, e.g., "['Admin', 'Accountant']"
            try:
                roles_str = roles_str.strip("{}")  # remove the curly braces
                roles = [r.strip() for r in roles_str.split(",") if r.strip()]

            except:
                roles = []
        elif line.startswith("Action:"):
            action_type = line.split(":", 1)[1].strip()
        elif line.startswith("Resource:"):
            resource_type = line.split(":", 1)[1].strip()
        elif line.startswith("Submitted:"):
            is_submitted = line.split(":", 1)[1].strip() == "True"

    return GradingRequest(
        roles=set(roles),
        action_type=action_type,
        resource_type=resource_type,
        is_submitted=is_submitted,
        person_no=person_no,
    )


def parse_tech_request_string(request_str: str) -> TechRequest:
    """Parse a string representation of TechRequest back to an TechRequest object."""
    lines = request_str.strip().split("\n")

    # Initialize with defaults
    person_no = None
    roles = []
    is_on_call = None
    action_type = None
    is_privileged = None
    resource_type = None
    is_after_hours = None

    for line in lines:
        line = line.strip()
        if line.startswith("Subject:"):
            person_no = line.split("Subject: Person", 1)[1].strip()
        elif line.startswith("Roles:"):
            roles_str = line.split(":", 1)[1].strip()
            # Parse the list format, e.g., "['Admin', 'Accountant']"
            try:
                roles_str = roles_str.strip("{}")  # remove the curly braces
                roles = [r.strip() for r in roles_str.split(",") if r.strip()]

            except:
                roles = []
        elif line.startswith("On Call:"):
            is_on_call = line.split(":", 1)[1].strip() == "True"
        elif line.startswith("Action:"):
            action_type = line.split(":", 1)[1].strip()
        elif line.startswith("Privileged:"):
            is_privileged = line.split(":", 1)[1].strip() == "True"
        elif line.startswith("Resource:"):
            resource_type = line.split(":", 1)[1].strip()
        elif line.startswith("After Hours:"):
            is_after_hours = line.split(":", 1)[1].strip() == "True"

    return TechRequest(
        roles=set(roles),
        is_on_call=is_on_call,
        action_type=action_type,
        resource_type=resource_type,
        is_privileged=is_privileged,
        is_after_hours=is_after_hours,
        person_no=person_no,
    )


def is_instance_allowed(problem_id: int, instance: str, policy: str) -> bool:
    if problem_id == 0:
        parsed_instance = parse_accounting_request_string(instance)
        return accounting_db.is_instance_allowed_by_individual_policy(parsed_instance, policy)
    elif problem_id == 1:
        parsed_instance = parse_grading_request_string(instance)
        return grading_db.is_instance_allowed_by_individual_policy(parsed_instance, policy)
    elif problem_id == 2:
        parsed_instance = parse_tech_request_string(instance)
        return tech_db.is_instance_allowed_by_individual_policy(parsed_instance, policy)
    else:
        raise ValueError(f"Unknown problem ID: {problem_id}")


def generate_two_distinguishing_instances(problem_id: int,
    candidates_in_play=[], excluded_words=[]
):
    # Parse excluded_words (which are strings) back to AccountingRequest objects
    excluded_instances = set()
    for word_str in excluded_words:
        try:
            parsed_instance = None
            if problem_id == 0:
                parsed_instance = parse_accounting_request_string(word_str)
            elif problem_id == 1:
                parsed_instance = parse_grading_request_string(word_str)
            elif problem_id == 2:
                parsed_instance = parse_tech_request_string(word_str)
            else:
                raise ValueError(f"Unknown problem ID: {problem_id}")
            excluded_instances.add(parsed_instance)
        except Exception as e:
            print(f"Warning: Failed to parse excluded word: {word_str}, error: {e}")

    db = None

    if problem_id == 0:
        db = accounting_db
    elif problem_id == 1:
        db = grading_db
    elif problem_id == 2:
        db = tech_db

    word0, word1 = db.generate_instances(
        candidates_in_play,
        list(set(POLICY_SHORTHANDS) - set(candidates_in_play)),
        excluded_instances,
    )

    # Convert to strings
    result = [str(word0), str(word1)]

    # Shuffle with consistent seed based on problem_id
    random.seed(problem_id)
    random.shuffle(result)

    return result[0], result[1]
