"""TODO: Module docstring."""

# Native
from typing import Dict, Set
from operator import attrgetter
import uuid


# Third-party
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import (
    desc
)
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

# Local

from study_config import STUDY_PROBLEMS, ELIMINATION_THRESHOLD, CONFIDENCE_THRESHOLD
from custom_types import ClassificationLabel, ClassificationType
from database import (
    db,
    User,
    ToolSession,
    CandidatePolicy,
    TextDescription,
)
from instances import is_instance_allowed


def get_user_from_uuid(cookie_uuid: str) -> User:
    """TODO: Write docstring."""
    if not cookie_uuid:
        return None

    try:
        cookie_uuid = uuid.UUID(cookie_uuid)
    except ValueError:
        return None

    return User.query.filter_by(user_uuid=cookie_uuid).first()



def mark_user_consented(user: User, consent: bool):
    """Set user's consent timestamp and flag, only if not already set."""
    if user.consent_time is None:
        user.consent_status = consent
        user.consent_time = func.now()

    db.session.commit()


def mark_user_walkthrough(user: User):
    """Set user's walkthrough timestamp, only if not already set."""
    if user.walkthrough_time is None:
        user.walkthrough_time = func.now()

    db.session.commit()


def mark_user_ack_instructions(user: User, ack: bool):
    """Set user's instruction acknowledgment time, only if not already set."""
    if user.instruction_time is None:
        user.instruction_status = ack
        user.instruction_time = func.now()

    db.session.commit()


def mark_user_screener_pass(user: User, passed: bool):
    """Set user's screener passage & timestamp, only if not already set."""
    if user.screener_passed is None:
        user.screener_time = func.now()
        user.screener_passed = passed

    db.session.commit()


def complete_session(session_id: int):
    """
    Mark the given ToolSession as completed by setting its `completed_at` field
    to the database server's current timestamp, if not already set.
    """
    session = ToolSession.query.get(session_id)
    if session and session.completed_at is None:
        session.completed_at = func.now()
        db.session.commit()




def get_latest_description(session_id: int):
    """
    Return the most recent natural language description (nl_description)
    for a given ToolSession.

    Parameters
    ----------
    session_id : int

    Returns
    -------
    str or None
        The most recent nl_description string, or None if none exist.
    """
    latest = (
        TextDescription.query.filter_by(session_id=session_id)
        .order_by(desc(TextDescription.submitted_at))
        .first()
    )
    return latest.description if latest else None
