"""
Standalone data analysis script.

Uses dotenv (.env) to read DB connection values, reflects the existing
database schema (no Flask app context), computes per-user accuracy
(excluding 'unsure'), and writes `user_accuracy.csv`.

Run: python3 data_analysis.py
"""

# Native Libraries
from datetime import datetime, timezone
import csv
import os
import sys

# Third-party Libraries
from dotenv import dotenv_values
from sqlalchemy import (
    create_engine,
    MetaData,
    select,
    func,
    text,
    literal_column,
    desc,
    and_,
    column,
    String,
    literal,
    case,
)
from sqlalchemy.sql import over


# Local Libraries
from database import *
from study_config import (
    STUDY_PROBLEMS,
    ELIMINATION_THRESHOLD,
    UNSURE_THRESHOLD,
    CONFIDENCE_THRESHOLD,
)

# Read .env (falls back to environment variables).
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
env = dotenv_values(env_path)


def get_env(key):
    return os.environ.get(key) or env.get(key)


# Define variables for DB connection setup.
DB_USER = get_env("DB_USER")
DB_PASSWORD = get_env("DB_PASSWORD")
DB_HOST = get_env("DB_HOST")
DB_PORT = get_env("DB_PORT")
DB_NAME = get_env("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise SystemExit("Database configuration missing in environment or .env")

DB_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{int(DB_PORT)}/{DB_NAME}"
)

engine = create_engine(DB_URL)
metadata = MetaData()

problem_id_to_name = {
    0: "Acct",
    1: "Grade",
    2: "Tech",
}

# Use the ORM model tables.
user_table = User.__table__
tool_session_table = ToolSession.__table__
candidate_policy_table = CandidatePolicy.__table__
text_description_table = TextDescription.__table__
policy_selection_table = PolicySelection.__table__
followup_table = FollowUpResponse.__table__
quiz_result_table = QuizResult.__table__

PROLIFIC_DATA_AGG_FILE = "prolific_data_aggregated.csv"


def to_dt(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        s = val
        # Normalize trailing Z to +00:00 for fromisoformat
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(s)
        except Exception:
            # Fallback: try common formats
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    continue
        return None


class UserData:
    def __init__(self, user_uuid, prolific_id):
        # Identifiers
        self.user_uuid = user_uuid
        self.prolific_id = prolific_id

        # Prolific Status
        self.prolific_status = None

        # Prolific demographic data
        self.country_of_birth = None
        self.country_of_residence = None
        self.nationality = None
        self.language = None

        # User information
        self.user_agent = None

        # Screener data
        self.programmer_screener = None
        self.bool_logic_screener = None

        # Quiz score data
        self.quiz_score = None
        self.quiz_problem_accuracy = {}

        # Completion checkpoints
        self.consent_status = None
        self.screener_passed = None
        self.instruction_status = None
        self.study_complete = None

        # Study data
        self.study_order = None
        self.study_pos = None

        # Pre-study event completion timestamps
        self.created_time = None
        self.consent_comp_time = None
        self.screener_comp_time = None
        self.instruction_comp_time = None
        self.quiz_comp_time = None

        # Note: All per-problem data is stored in dictionaries keyed by problem ID.

        # Problem start timestamps
        self.problem_creation_times = {
            0: None,
            1: None,
            2: None,
        }

        # Policy selection timestamps
        self.policy_selection_times = {
            0: None,
            1: None,
            2: None,
        }

        # Problem completion timestamps
        self.problem_comp_times = {
            0: None,
            1: None,
            2: None,
        }

        self.problem_result = {
            0: None,
            1: None,
            2: None,
        }

        # Reflection responses
        self.reflection_responses = {}

        # Followup responses
        self.abac_familiarity = None
        self.acp_firewall_exp = None
        self.technical_issues = None
        self.confusion_feedback = None

    def compute_consent_duration(self) -> str:
        """Return the number of seconds between created_time and consent_comp_time."""
        t1 = to_dt(self.created_time)
        t2 = to_dt(self.consent_comp_time)
        if t1 is None or t2 is None:
            return ""

        # Compute delta in seconds (integer).
        try:
            delta = t2 - t1
            return str(int(delta.total_seconds()))
        except Exception:
            return ""

    def compute_screener_duration(self) -> str:
        """Return the number of seconds between consent_comp_time and screener_comp_time."""
        t1 = to_dt(self.consent_comp_time)
        t2 = to_dt(self.screener_comp_time)
        if t1 is None or t2 is None:
            return ""

        # Compute delta in seconds (integer).
        try:
            delta = t2 - t1
            return str(int(delta.total_seconds()))
        except Exception:
            return ""

    def compute_instruction_duration(self) -> str:
        """Return the number of seconds between screener_comp_time and instruction_comp_time."""
        t1 = to_dt(self.screener_comp_time)
        t2 = to_dt(self.instruction_comp_time)
        if t1 is None or t2 is None:
            return ""

        # Compute delta in seconds (integer).
        try:
            delta = t2 - t1
            return str(int(delta.total_seconds()))
        except Exception:
            return ""

    def compute_quiz_duration(self) -> str:
        """Return the number of seconds between instruction_comp_time and quiz_comp_time."""
        t1 = to_dt(self.instruction_comp_time)
        t2 = to_dt(self.quiz_comp_time)
        if t1 is None or t2 is None:
            return ""

        # Compute delta in seconds (integer).
        try:
            delta = t2 - t1
            return str(int(delta.total_seconds()))
        except Exception:
            return ""

    def _get_walkthrough_timedelta(self):
        """Return the timedelta between quiz_comp_time and walkthrough_comp_time, or None."""
        t1 = to_dt(self.quiz_comp_time)
        t2 = to_dt(self.quiz_comp_time)
        if t1 is None or t2 is None:
            return None
        try:
            return t2 - t1
        except Exception:
            return None

    def compute_problem_duration(self, pid) -> str:
        """Return the number of seconds between problem_creation_times and problem_comp_times."""
        t1 = to_dt(self.problem_creation_times[pid])
        t2 = to_dt(self.problem_comp_times[pid])
        if t1 is None or t2 is None:
            return ""

        # Compute delta in seconds (integer).
        try:
            delta = t2 - t1
            return str(int(delta.total_seconds()))
        except Exception:
            return ""


def generate_user_objects(conn) -> list[UserData]:
    """Fetch all users from the database and return a list of UserData objects."""
    # Load Prolific CSV (if present) to map Participant id -> Status
    prolific_map = {}
    try:
        with open(PROLIFIC_DATA_AGG_FILE, newline="", encoding="utf-8") as pf:
            reader = csv.DictReader(pf)
            for r in reader:
                pid = r.get("Participant id") or r.get("Participant id")
                if pid:
                    prolific_map[pid] = {
                        "status": r.get("Status"),
                        "country_of_birth": r.get("Country of birth"),
                        "country_of_residence": r.get("Country of residence"),
                        "nationality": r.get("Nationality"),
                        "language": r.get("Language"),
                    }
    except FileNotFoundError:
        # File not present; proceed without prolific mapping
        prolific_map = {}

    res = conn.execute(select(user_table))

    # Return object with user_uuid and prolific_id.
    users = []
    for row in res.mappings().all():
        user_object = UserData(row["user_uuid"], row["prolific_id"])
        prolific_data = prolific_map.get(user_object.prolific_id, {})
        user_object.prolific_status = prolific_data.get("status")
        user_object.country_of_birth = prolific_data.get("country_of_birth")
        user_object.country_of_residence = prolific_data.get("country_of_residence")
        user_object.nationality = prolific_data.get("nationality")
        user_object.user_agent = row.get("user_agent", None)
        user_object.programmer_screener = row.get("programmer_screener", None)
        user_object.bool_logic_screener = row.get("prop_logic_screener", None)
        user_object.consent_status = row.get("consent_status", None)
        user_object.screener_passed = row.get("screener_passed", None)
        user_object.instruction_status = row.get("instruction_status", None)
        user_object.study_complete = row.get("study_complete", None)
        user_object.study_order = row.get("study_order", None)
        user_object.study_pos = row.get("study_pos", None)
        user_object.created_time = row.get("created_time", None)
        user_object.consent_comp_time = row.get("consent_time", None)
        user_object.screener_comp_time = row.get("screener_time", None)
        user_object.instruction_comp_time = row.get("instruction_time", None)

        # Fetch quiz data.
        user_object = fetch_quiz_data(conn, user_object)

        # Fetch followup data.
        user_object = fetch_followups(conn, user_object)

        # Fetch study data.
        user_object = fetch_study_data(conn, user_object)
        if user_object.study_complete:
            print(user_object.prolific_id, user_object.problem_result)

        # Append user object to return list.
        users.append(user_object)

    return users


def fetch_study_data(conn, user: UserData) -> UserData:
    """Fetch and calculate study data for a given user."""
    # Fetch all problem (tool) sessions for the user.
    sessions_query = select(tool_session_table).where(
        tool_session_table.c.user_uuid == user.user_uuid
    )
    sessions_res = conn.execute(sessions_query)
    sessions = sessions_res.mappings().all()
    for sess in sessions:
        pid = sess.get("study_problem")

        # Retrieve the creation and completion times for each problem.
        user.problem_creation_times[pid] = sess.get("created_at", None)
        user.problem_comp_times[pid] = sess.get("completed_at", None)

        policy_selection_query = select(policy_selection_table).where(
            policy_selection_table.c.session_id == sess.session_id
        )

        policy_selection_res = conn.execute(policy_selection_query)
        selections = policy_selection_res.mappings().all()
        for sel in selections:
            user.policy_selection_times[pid] = sel.get("submitted_at", None)
            selected_policy = sel.get("selected_policy", None)

            if selected_policy == "c":
                result = "correct"
            elif selected_policy in ("a", "b", "d"):
                lookup = {
                    "a": "alt1",
                    "b": "alt2",
                    "d": "alt3",
                }
                result = f"wrong ({lookup[selected_policy]})"
            elif selected_policy in ("unsure", "none"):
                result = selected_policy
            else:
                result = "error"

            user.problem_result[pid] = result

    return user


def fetch_quiz_data(conn, user: UserData) -> UserData:
    """Fetch quiz answers for a given user uuid."""
    query = select(quiz_result_table).where(
        quiz_result_table.c.user_uuid == user.user_uuid
    )
    res = conn.execute(query)
    row = res.mappings().first()
    if row:
        score_details = row.get("details", {})
        if score_details:
            score_details = dict(score_details)
            # Map between question number and OK status:
            user.quiz_problem_accuracy = {
                int(k): v["ok"] for k, v in score_details.items() if k.isdigit()
            }
        user.quiz_score = row.get("score", None)
        user.quiz_comp_time = row.get("submitted_at", None)

    return user


def fetch_followups(conn, user: UserData) -> UserData:
    """Fetch screener answers for a given user uuid."""
    query = select(followup_table).where(followup_table.c.user_uuid == user.user_uuid)
    res = conn.execute(query)
    row = res.mappings().first()
    if row:
        user.abac_familiarity = row.get("q1_response")
        user.acp_firewall_exp = row.get("q2_response")
        user.technical_issues = row.get("q3_response")
        user.confusion_feedback = row.get("q4_response")

    return user


def write_simple_completed_csv(users):
    """Write user data to CSV file."""

    output_csv = "simple_completed_users.csv"

    fieldnames = [
        "Prolific ID",
        "Prolific Status",
        "Country of birth",
        "Country of residence",
        "Nationality",
        "Language",
        "Programmer Screener",
        "Bool Logic Screener",
        "Overall Quiz Score",
        "Instruction Duration",
        "Quiz Duration",
        "Acct Result",
        "Acct Duration",
        "Grade Result",
        "Grade Duration",
        "Tech Result",
        "Tech Duration",
        "ABAC Familiarity",
        "ACP/Firewall Experience",
        "Technical Issues",
        "Study Confusions",
    ]

    rows = []
    for u in users:
        if not u.study_complete:
            continue

        def safe(val, default=""):
            return default if val is None else val

        row = {
            "Prolific ID": safe(u.prolific_id),
            "Prolific Status": safe(u.prolific_status),
            "Country of birth": safe(u.country_of_birth),
            "Country of residence": safe(u.country_of_residence),
            "Nationality": safe(u.nationality),
            "Language": safe(u.language),
            "Programmer Screener": safe(u.programmer_screener),
            "Bool Logic Screener": safe(u.bool_logic_screener),
            "Overall Quiz Score": safe(u.quiz_score),
            "Instruction Duration": safe(u.compute_instruction_duration()),
            "Quiz Duration": safe(u.compute_quiz_duration()),
        }

        # Per-problem fields
        for pid in range(3):
            name = problem_id_to_name.get(pid, f"Problem {pid}")
            row[f"{name} Result"] = safe(u.problem_result.get(pid))
            row[f"{name} Duration"] = safe(u.compute_problem_duration(pid))

        row["ABAC Familiarity"] = safe(u.abac_familiarity)
        row["ACP/Firewall Experience"] = safe(u.acp_firewall_exp)
        row["Technical Issues"] = safe(u.technical_issues)
        row["Study Confusions"] = safe(u.confusion_feedback)

        rows.append(row)

    # Write CSV
    if rows:
        with open(output_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    print(f"Wrote {len(rows)} completed users to {output_csv}")


def write_reflections_csv(users):
    """Write user data to CSV file."""

    output_csv = "reflections.csv"

    # Compose rows: one row per reflection entry
    rows = []
    for u in users:
        pid = u.prolific_id
        uid = u.user_uuid
        # reflection_responses is a dict: problem_id -> list[dict]
        rr = getattr(u, "reflection_responses", {}) or {}
        for spid, entries in rr.items():
            if not entries:
                continue
            for e in entries:
                rows.append(
                    {
                        "prolific_id": pid,
                        "user_uuid": str(uid),
                        "study_problem": spid,
                        "word": e.get("word"),
                        "user_answer": e.get("user_answer"),
                        "expected": e.get("expected"),
                        "explanation": e.get("explanation"),
                    }
                )

    # Write CSV with explicit fieldnames for reflections
    out_fields = [
        "prolific_id",
        "user_uuid",
        "study_problem",
        "word",
        "user_answer",
        "expected",
        "explanation",
    ]
    if rows:
        with open(output_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=out_fields)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    print(f"Wrote {len(rows)} reflection rows to {output_csv}")


def collect_data(conn):
    """
    Collect data from the database and write it to a CSV file.
    """
    users = generate_user_objects(conn)
    write_simple_completed_csv(users)
    write_reflections_csv(users)


if __name__ == "__main__":
    with engine.connect() as conn:
        collect_data(conn)
