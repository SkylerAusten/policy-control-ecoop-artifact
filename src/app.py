"""
This module defines the Flask application endpoints for the Text-to-LTL tool.

It provides the following routes:
    - TODO

To run the application, execute: python app.py
"""

# Native
import random
import uuid
import hashlib
import logging
import re
import secrets
from functools import wraps
from collections import defaultdict
from typing import NoReturn

def get_prolific_redirect(code_type: str):
    ct_map_prolific = {
        "question_screenout": "C1I0FSLH",  # Screener fail
        "mobile_screenout": "C8Z294SH",  # Mobile disqualification
        "no_consent": "CFN2Z4FW",  # No consent
        "no_instructions_ack": "CXJY2BLY",  # No instructions ack
        "complete": "C1GXEDZT",  # Study complete
    }

    ct_map_local = {
        "question_screenout": "Screener fail",  # Screener fail
        "mobile_screenout": "Mobile screenout",  # Mobile disqualification
        "no_consent": "No consent",  # No consent
        "no_instructions_ack": "No instructions ack/consent",  # No instructions ack
        "complete": "Completed study",  # Study complete
    }

    if TESTING:
        message = ct_map_local.get(code_type, "Unknown end reason")
        return redirect(url_for("end_page", message=message))

    else:
        cc = ct_map_prolific.get(code_type, "Unknown")
        return redirect(
                f"https://app.prolific.com/submissions/complete?cc={cc}", code=302
            )

# Third-party
from flask import (
    Flask,
    request,
    redirect,
    jsonify,
    url_for,
    make_response,
    render_template,
    g,
)
from flask.logging import default_handler
from sqlalchemy import select
from sqlalchemy.sql import func
import user_agents

# Local
from app_config import Config
from custom_types import ClassificationType, ClassificationLabel
from study_config import (
    STUDY_PROBLEMS,
    CONFIDENCE_THRESHOLD,
    UNSURE_THRESHOLD,
    SHOW_CANDIDATES,
    SHOW_LABELS,
    ELIMINATION_THRESHOLD,
    TESTING,
)
from instances import (
    is_instance_allowed,
    generate_two_distinguishing_instances,
    get_full_policy,
)
from policy_image_generator import generate_policy_images_dict

from database import (
    db,
    User,
    ToolSession,
    CandidatePolicy,
    TextDescription,
    FollowUpResponse,
    QuizResult,
    PolicySelection,
)
from db_functions import (
    mark_user_consented,
    mark_user_ack_instructions,
    mark_user_screener_pass,
    mark_user_walkthrough,
    get_latest_description,
    get_user_from_uuid,
    complete_session,
)

import os
static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static"))
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
    static_folder=static_path
)


app.config.from_object(Config)
db.init_app(app)

# Add enumerate filter for Jinja templates
app.jinja_env.filters['enumerate'] = enumerate

root_logger = app.logger
root_logger.addHandler(default_handler)
root_logger.addHandler((logging.getLogger("sqlalchemy")))

# When the app starts, drop and create all DB tables.
with app.app_context():
    # db.drop_all()
    db.create_all()


def user_study_complete(user: User) -> bool:
    """Return whether or not a given user has completed the study.
    Args:
        user: the User object.

    Returns:
        True if the user has completed the study, false otherwise.
    """

    complete = bool(user.study_complete)

    if complete:
        assert (
            user.study_pos >= len(STUDY_PROBLEMS)
        ) is True, "User hasn't completed all study problem blocks."

    return complete

def require_user(consent_required: bool = False, session_required: bool = False):
    """Create a decorator function for the Flask endpoints which checks that
    the user exists, and if specified, whether they've consented and/or
    have an active session.

    Args:
        consent_required: whether participation consent is required.
        session_required: whether an active tool session is required.
    Returns:
        Decorator function for Flask app endpoints.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            cookie_uuid = request.cookies.get("user_uuid")
            user = get_user_from_uuid(cookie_uuid)

            if not user:
                return redirect(url_for("setup_user"))

            if consent_required and not user.consent_status:
                return redirect(url_for("consent"))

            g.user = user  # Save user in global 'g' object.

            if session_required:
                # Note: g.user.consent_status could be None or False.
                if not hasattr(g, "user") or not g.user.consent_status:
                    return redirect(url_for("setup_user"))

                study_order = g.user.study_order
                study_pos = g.user.study_pos

                # If the user has completed all blocks in the study:
                if study_pos >= len(study_order):
                    # Remove the session from g.
                    g.tool_session = None
                else:
                    study_prob_id = STUDY_PROBLEMS[study_order[study_pos]]["id"]
                    session = ToolSession.query.filter_by(
                        user_uuid=g.user.user_uuid, study_problem=study_prob_id
                    ).first()
                    if not session:
                        # Session for this user & problem does not exist.
                        session = setup_session(g.user)
                    else:
                        # Session for this user & problem exists.
                        g.tool_session = session

            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def setup_session(user: User) -> ToolSession | None:
    """Create a ToolSession for the current study block.

    Args:
        user: Current tool user's User object.
    """
    study_order = list(user.study_order)
    study_pos = user.study_pos

    # If the user's completed the study, don't return a session.
    if study_pos >= len(study_order):
        return None

    study_problem = STUDY_PROBLEMS[study_order[study_pos]]["id"]

    # Check if this session already exists in DB.
    existing_session = ToolSession.query.filter_by(
        user_uuid=user.user_uuid, study_problem=study_problem
    ).first()

    if existing_session:
        g.tool_session = existing_session
        return existing_session

    # Create a new session in DB.
    block = STUDY_PROBLEMS[study_order[study_pos]]
    tool_session = ToolSession(user_uuid=user.user_uuid, study_problem=study_problem)
    db.session.add(tool_session)
    db.session.commit()
    g.tool_session = tool_session

    # Add text description to DB.
    db.session.add(
        TextDescription(
            session_id=tool_session.session_id, description=block["description"]
        )
    )

    # Add candidate formulas to DB.
    rng = random.Random(1234)
    for pc in rng.sample(block["candidates"], len(block["candidates"])):
        db.session.add(
            CandidatePolicy(
                session_id=tool_session.session_id,
                policy_abac=pc,
                confidence=0,
            )
        )

    db.session.commit()
    return tool_session


def generate_study_order(seed=None) -> list[int]:
    order = list(range(len(STUDY_PROBLEMS)))
    if seed is not None:
        random.seed(seed)
    random.shuffle(order)
    return order

@app.route("/setup", methods=["GET", "POST"])
def setup_user():
    # On GET, look for a query-param; on POST, read the form
    if request.method == "POST":
        prolific_id = request.form.get("prolific_id", "").strip()
    else:
        prolific_id = request.args.get("PROLIFIC_PID", "").strip()
        if not prolific_id and TESTING:
            prolific_id = secrets.token_hex(12)  # 12 bytes = 24 hex chars

    # If still empty, render the PID entry form
    if TESTING:
        if not prolific_id:
            error = None
            if request.method == "POST" and prolific_id:
                error = "Please enter a valid 24-character Prolific ID."
            return render_template("enter_pid.html", prolific_id=prolific_id, error=error)
    else:
        if not prolific_id or not re.fullmatch(r"[0-9a-f]{24}", prolific_id):
            error = None
            if request.method == "POST" and prolific_id:
                error = "Please enter a valid 24-character Prolific ID."
            return render_template("enter_pid.html", prolific_id=prolific_id, error=error)

    # Check if the user already exists.
    user = User.query.filter_by(prolific_id=prolific_id).first()

    if not user:
        user_uuid = uuid.uuid4()

        ua_string = request.headers.get("User-Agent")
        user_agent = user_agents.parse(ua_string)

        user = User(
            user_uuid=user_uuid,
            prolific_id=prolific_id,
            study_order=generate_study_order(),
            study_pos=0,
            user_agent=str(user_agent),
        )

        db.session.add(user)
        db.session.commit()

        if user_agent.is_mobile or user_agent.is_tablet:
            return get_prolific_redirect("mobile_screenout")
    else:
        # ─── Existing user logic ───
        if not user.consent_status:
            return redirect(url_for("consent"))
        if user.screener_passed is None:
            return redirect(url_for("screener"))
        if user.screener_passed is False:
            return get_prolific_redirect("question_screenout")
        if user.instruction_status is False:
            return get_prolific_redirect("no_instructions_ack")
        if user.study_complete:
            return get_prolific_redirect("complete")

    response = make_response(redirect(url_for("consent")))
    response.set_cookie("user_uuid", str(user.user_uuid), max_age=60 * 60 * 24 * 7)
    return response

@app.route("/end_page")
def end_page():
    """Render the end page with a message."""
    message = request.args.get("message", "Thank you for your participation!")
    return render_template("end_page.html", message=message)

@app.route("/consent", methods=["POST", "GET"])
@require_user(consent_required=False, session_required=False)
def consent():
    """TODO: Write docstring."""
    if request.method == "POST":
        consent_response = request.form.get("consent")

        if consent_response not in ["true", "false"]:
            return "Invalid consent option", 400

        mark_user_consented(g.user, consent_response == "true")
        db.session.commit()

        if g.user.consent_status:
            return redirect(url_for("screener"))
        else:
            return get_prolific_redirect("no_consent")

    # GET Request:
    return render_template("consent.html")


@app.route("/screener", methods=["GET", "POST"])
@require_user(consent_required=True, session_required=False)
def screener():
    """
    Show screener questions and store responses.
    If passed, continue to /instructions. Otherwise, disqualify.
    """
    if request.method == "POST":
        prog_screener_answer = request.form.get("q1", "").strip().lower()
        prop_logic_screener = request.form.get("q2", "").strip().lower()

        # Store responses.
        g.user.programmer_screener = prog_screener_answer
        g.user.prop_logic_screener = prop_logic_screener  # Repurposing this field for boolean logic

        # Define pass condition: 
        # - Must have programming experience (yes)
        # - Must have at least basic boolean logic experience (not none)
        # - LTL experience is recorded but doesn't affect pass/fail.
        passed = (prog_screener_answer == "yes") and (prop_logic_screener in ["some", "advanced"] ) 
        mark_user_screener_pass(g.user, passed)
        db.session.commit()

        if passed:
            return redirect(url_for("instructions"))
        else:
            return get_prolific_redirect("question_screenout")

    return render_template("screener.html")


@app.route("/instructions", methods=["POST", "GET"])
@require_user(consent_required=True, session_required=False)
def instructions():
    """TODO: Write docstring."""
    if request.method == "POST":
        understand_response = request.form.get("understand")

        if understand_response not in ["true", "false"]:
            return "Invalid consent option", 400

        mark_user_ack_instructions(g.user, understand_response == "true")
        db.session.commit()

        if g.user.instruction_status:
            # After acknowledging instructions, send participant to the brief practice quiz
            return redirect(url_for("quiz"))
        else:
            return get_prolific_redirect("no_instructions_ack")

    return render_template("instructions.html")


@app.route("/study", methods=["GET"])
@require_user(consent_required=True, session_required=True)
def study():
    user = g.user

    # Case: study is over (all study blocks completed)
    if user.study_pos >= len(user.study_order):
        return redirect(url_for("followup"))

    session_id = g.tool_session.session_id
    study_problem_id = g.tool_session.study_problem

    # Check if user has already made a selection for this problem
    existing_selection = PolicySelection.query.filter_by(
        session_id=session_id, study_problem_id=study_problem_id
    ).first()
    
    if existing_selection:
        # User already completed this problem, redirect to next
        # (study_pos should already be incremented, so just redirect)
        if g.user.study_pos >= len(g.user.study_order):
            return redirect(url_for("followup"))
        else:
            return redirect(url_for("study"))

    # Get the study problem configuration
    study_block = None
    for block in STUDY_PROBLEMS:
        if block["id"] == study_problem_id:
            study_block = block
            break
    
    if not study_block:
        return "Study problem not found", 404

    text_description = get_latest_description(session_id)

    # Get all candidate policies for this problem
    candidates = study_block["candidates"]
    full_policies = study_block["full_policies"]

    # Create policy options with randomized order for the 4 policies
    policy_options = []
    for candidate_key in candidates:
        policy_options.append({
            "key": candidate_key,
            "html": full_policies[candidate_key]
        })
    
    # Randomize the order of the 4 policies
    random.shuffle(policy_options)
    
    # Store the randomized order
    policy_order = [p["key"] for p in policy_options]
    
    # Add the two fixed options at the end
    policy_options.append({
        "key": "none",
        "html": "None of these policies match the description."
    })
    policy_options.append({
        "key": "unsure",
        "html": "I'm unsure."
    })

    # Generate images for all policies
    policy_images = generate_policy_images_dict(policy_options, study_problem_id)

    return render_template(
        "study.html",
        text_description=text_description,
        session_id=session_id,
        study_problem_id=study_problem_id,
        policy_options=policy_options,
        policy_order=policy_order,
        policy_images=policy_images,
    )


@app.route("/submit_policy_selection", methods=["POST"])
@require_user(consent_required=True, session_required=True)
def submit_policy_selection():
    """
    Handle the submission of a policy selection.
    Stores the selection and advances to the next study problem.
    """
    data = request.get_json()
    selected_policy = data.get("selected_policy")
    response_session_id = int(data.get("session_id"))
    study_problem_id = int(data.get("study_problem_id"))
    policy_order = data.get("policy_order", [])

    if not selected_policy:
        return "No policy selected", 400

    if g.user.study_complete or not hasattr(g, "tool_session"):
        return get_prolific_redirect("complete")

    if response_session_id != g.tool_session.session_id:
        return "Invalid session", 400

    # Store the policy selection
    selection = PolicySelection(
        session_id=response_session_id,
        study_problem_id=study_problem_id,
        selected_policy=selected_policy,
        policy_order=policy_order,
    )
    db.session.add(selection)

    # Mark this session as complete and advance to next problem
    g.user.study_pos += 1
    complete_session(response_session_id)
    db.session.commit()
    
    # Clear the cached session
    g.pop("tool_session", None)

    # Redirect to the next study problem or reflection if all done
    if g.user.study_pos >= len(g.user.study_order):
        return jsonify({"redirect": url_for("followup")})
    else:
        return jsonify({"redirect": url_for("study")})


@app.route("/mark_walkthrough_complete", methods=["POST"])
@require_user(consent_required=True, session_required=True)
def mark_walkthrough_complete():
    mark_user_walkthrough(g.user)
    return "OK", 200


@app.route("/followup", methods=["GET", "POST"])
@require_user(consent_required=True, session_required=False)
def followup():
    if request.method == "POST":
        row = FollowUpResponse.query.get(g.user.user_uuid) or FollowUpResponse(
            user_uuid=g.user.user_uuid
        )

        row.q1_response = request.form.get("q1", "").strip() or None
        row.q2_response = request.form.get("q2", "").strip() or None
        row.q3_response = request.form.get("q3", "").strip() or None
        row.q4_response = request.form.get("q4", "").strip() or None

        db.session.merge(row)

        # Mark study complete
        g.user.study_complete = True
        db.session.commit()

        return get_prolific_redirect("complete")

    return render_template("followup_without_list.html")


@app.route("/quiz", methods=["GET", "POST"])
@require_user(consent_required=True, session_required=False)
def quiz():
    """Render the post-instructions practice quiz and accept results.

    GET: render the quiz page
    POST: accept JSON payload {score: int, details: dict}, persist QuizResult,
          and redirect to /study so the participant can continue.
    """
    if request.method == "GET":
        return render_template("quiz.html")

    # POST: expect JSON body
    data = request.get_json()
    if not data:
        return "Invalid payload", 400

    score = data.get("score")
    details = data.get("details")

    try:
        score = int(score)
    except Exception:
        return "Invalid score", 400

    qr = QuizResult(user_uuid=g.user.user_uuid, score=score, details=details, submitted_at=func.now())
    db.session.add(qr)
    db.session.commit()

    # After quiz, proceed to study
    return jsonify({"redirect": url_for("study")})


if __name__ == "__main__":
    # Respect PORT env var (App Platform / Docker) and listen on all interfaces
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
