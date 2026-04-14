"""TODO: Module docstring."""

# Native
import uuid
import json
from datetime import datetime, timezone

# Third-party
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    desc,
    ForeignKey,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.ext.hybrid import hybrid_property

# Local
from custom_types import ClassificationLabel, ClassificationType

db = SQLAlchemy()


# Type decorator to store UUIDs as CHAR(36) in MySQL.
class UUID(TypeDecorator):
    """TODO: Write Docstring."""

    impl = String(36)
    cache_ok = True

    @property
    def python_type(self):
        return uuid.UUID

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            from sqlalchemy.dialects.mysql import CHAR
            return dialect.type_descriptor(CHAR(36))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        return uuid.UUID(value) if value else None

    def process_literal_param(self, value, dialect):
        return f"'{str(value)}'" if value is not None else "NULL"


# Type decorator to store Python sets as JSON in MySQL.
class ListJSON(TypeDecorator):
    """
    Stores a Python list as a JSON column.
    Ensures list structure is preserved.
    """

    impl = JSON
    cache_ok = True

    @property
    def python_type(self):
        return list

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("ListJSON must be given a list.")
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []

    def process_literal_param(self, value, dialect):
        return f"'{json.dumps(value)}'" if value else "NULL"


class User(db.Model):
    """TODO: Write docstring."""

    user_uuid = db.Column(UUID(), primary_key=True)
    prolific_id = db.Column(String(50), unique=True, nullable=False)
    user_agent = db.Column(String(255), nullable=True)
    programmer_screener = db.Column(String(5), nullable=True)
    prop_logic_screener = db.Column(String(10), nullable=True)  # Boolean logic experience
    screener_passed = db.Column(Boolean, nullable=True)
    consent_status = db.Column(Boolean, nullable=True)
    consent_time = db.Column(DateTime, nullable=True)
    screener_time = db.Column(DateTime, nullable=True)
    instruction_status = db.Column(Boolean, nullable=True)
    instruction_time = db.Column(DateTime, nullable=True)
    walkthrough_time = db.Column(
        DateTime, nullable=True
    )  # Walkthrough completion time.
    created_at = db.Column(DateTime, default=func.now(), nullable=False)
    study_order = db.Column(ListJSON(), default=list, nullable=True)
    study_pos = db.Column(Integer, default=0, nullable=True)
    study_complete = db.Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        """TODO: Write docstring."""
        return {
            "user_uuid": str(self.user_uuid),  # Convert UUID to string for JSON
            "prolific_id": self.prolific_id,
            "user_agent": self.user_agent,
            "programmer_screener": self.programmer_screener,
            "prop_logic_screener": self.prop_logic_screener,
            "screener_passed": self.screener_passed,
            "consent_status": self.consent_status,
            "consent_time": str(self.consent_time),
            "instruction_status": self.instruction_status,
            "instruction_time": str(self.instruction_time),
            "walkthrough_time": str(self.walkthrough_time),
            "created_at": str(self.created_at),
            "study_order": list(self.study_order),
            "study_pos": self.study_pos,
            "study_complete": self.study_complete,
        }


class ToolSession(db.Model):
    """TODO: Write docstring."""

    session_id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = db.Column(UUID(), ForeignKey("user.user_uuid"), nullable=False)
    created_at = db.Column(DateTime, default=func.now(), nullable=False)
    study_problem = db.Column(Integer, nullable=True)
    completed_at = db.Column(DateTime, nullable=True)

    descriptions = db.relationship(
        "TextDescription",
        backref="tool_session",
        lazy="dynamic",  # So we can filter/sort
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def latest_description(self):
        return self.descriptions.order_by(desc(TextDescription.submitted_at)).first()

    def to_dict(self):
        """TODO: Write docstring."""
        return {
            "session_id": self.session_id,
            "user_uuid": str(self.user_uuid),
            "created_at": str(self.created_at),
            "study_problem": self.study_problem,
            "completed_at": str(self.completed_at),
            "description_versions": [d.to_dict() for d in self.descriptions.all()],
            "latest_description": (
                self.latest_description.to_dict() if self.latest_description else None
            ),
        }


class TextDescription(db.Model):
    """Stores a natural language description and the time it was recorded."""

    description_id = db.Column(Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(
        Integer, ForeignKey("tool_session.session_id"), nullable=False
    )
    submitted_at = db.Column(
        DateTime, default=func.now(), nullable=False, index=True
    )
    description = db.Column(Text, default=None, nullable=True)

    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {
            "description_id": self.description_id,
            "session_id": self.session_id,
            "submitted_at": self.submitted_at.isoformat(),
            "description": self.description,
        }


class CandidatePolicy(db.Model):
    """TODO: Write docstring."""

    policy_id = db.Column(Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(
        Integer, ForeignKey("tool_session.session_id"), nullable=False
    )
    generated_at = db.Column(DateTime, default=func.now(), nullable=False)
    policy_abac = db.Column(
        Text, nullable=False
    )  # TODO: Rename to formula_str in future DB migration
    confidence = db.Column(Integer, default=0, nullable=False)

    def to_dict(self):
        """TODO: Write docstring."""
        return {
            "policy_id": self.policy_id,
            "session_id": self.session_id,
            "generated_at": str(self.generated_at),
            "policy_abac": self.policy_abac,  # TODO: Change to formula_str
            "confidence": self.confidence,
        }


class FollowUpResponse(db.Model):
    """Store post-study follow-up answers (one row per user)."""

    user_uuid = db.Column(UUID(), ForeignKey("user.user_uuid"), primary_key=True)

    # Q1 – Helpfulness of candidate formula list
    q1_response = db.Column(String(20), nullable=True)
    q2_response = db.Column(Text, nullable=True)
    q3_response = db.Column(Text, nullable=True)
    q4_response = db.Column(Text, nullable=True)

    submitted_at = db.Column(DateTime, default=func.now(), nullable=False)

    user = db.relationship("User", backref="followup", lazy="joined")

    def to_dict(self):
        return {
            "user_uuid": str(self.user_uuid),
            "q1_response": self.q1_response,
            "q2_response": self.q2_response,
            "q3_response": self.q3_response,
            "q4_response": self.q4_response,
            "submitted_at": self.submitted_at.isoformat(),
        }


class QuizResult(db.Model):
    """
    Store a participant's quiz attempt after the instructions.

    Fields:
        id: primary key
        user_uuid: FK to User
        submitted_at: timestamp
        score: integer (0..N)
        details: JSON payload with per-question results
    """

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = db.Column(UUID(), ForeignKey("user.user_uuid"), nullable=False)
    submitted_at = db.Column(DateTime, default=func.now(), nullable=False)
    score = db.Column(Integer, nullable=False)
    details = db.Column(JSON, nullable=True)

    user = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "user_uuid": str(self.user_uuid),
            "submitted_at": str(self.submitted_at),
            "score": self.score,
            "details": self.details,
        }
class PolicySelection(db.Model):
    """
    Store a participant's policy selection for a study problem.
    
    Fields:
        id: primary key
        session_id: FK to ToolSession
        study_problem_id: which problem this selection is for
        selected_policy: the policy selected (e.g., 'correct', 'alt1', 'alt2', 'alt3', 'none', 'unsure')
        policy_order: JSON array of the randomized order the policies were shown
        submitted_at: timestamp
    """

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(
        Integer, ForeignKey("tool_session.session_id"), nullable=False
    )
    study_problem_id = db.Column(Integer, nullable=False)
    selected_policy = db.Column(String(50), nullable=False)
    policy_order = db.Column(JSON, nullable=True)
    submitted_at = db.Column(DateTime, default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "study_problem_id": self.study_problem_id,
            "selected_policy": self.selected_policy,
            "policy_order": self.policy_order,
            "submitted_at": str(self.submitted_at),
        }
