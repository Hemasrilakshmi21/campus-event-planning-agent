
from datetime import datetime
from zoneinfo import ZoneInfo

from agents import (
    requirement_agent,
    budget_agent,
    venue_schedule_agent,
    workflow_planner_agent,
)

from database import has_duplicate_event
from tools import is_valid_date


# --------------------------------------------------
# TIMEZONE
# --------------------------------------------------

INDIA_TZ = ZoneInfo("Asia/Kolkata")


def india_now():
    """Return the current date and time in India."""
    return datetime.now(INDIA_TZ)


# --------------------------------------------------
# 1. INPUT GUARDRAILS
# --------------------------------------------------

def guardrails(raw):
    errors = []

    if not isinstance(raw, dict):
        return ["Input must be a dictionary."]

    # Required fields
    required = ["event_name", "event_date", "venue"]

    for field in required:
        if not raw.get(field):
            errors.append(f"Missing required field: {field}")

    # Budget validation
    budget = raw.get("budget")

    if (
        not isinstance(budget, (int, float))
        or isinstance(budget, bool)
        or budget <= 0
    ):
        errors.append("Budget must be greater than ₹0.")

    # Audience validation
    audience = raw.get("audience")

    if (
        not isinstance(audience, int)
        or isinstance(audience, bool)
        or not 1 <= audience <= 5000
    ):
        errors.append(
            "Audience size must be between 1 and 5000."
        )

    # Activities validation
    activities = raw.get("activities")

    if not isinstance(activities, list):
        errors.append("Activities must be provided as a list.")
    elif not 1 <= len(activities) <= 10:
        errors.append(
            "At least one activity is required; maximum 10 allowed."
        )

    # Time validation: 24-hour HH:MM format
    start = raw.get("start_time")
    end = raw.get("end_time")

    try:
        if not start or not end:
            errors.append(
                "Start time and end time are required."
            )
        else:
            start_time = datetime.strptime(start, "%H:%M")
            end_time = datetime.strptime(end, "%H:%M")

            if end_time <= start_time:
                errors.append(
                    "End time must be after start time."
                )
    except (ValueError, TypeError):
        errors.append("Time must use HH:MM format.")

    # Event date validation
    event_date = raw.get("event_date")

    if event_date:
        try:
            if not is_valid_date(event_date):
                errors.append(
                    "Event date is invalid or in the past."
                )
        except (ValueError, TypeError):
            errors.append("Invalid event date.")

    # Event name validation
    event_name = raw.get("event_name")

    if not isinstance(event_name, str) or not event_name.strip():
        errors.append("Event name must be a non-empty string.")
    elif len(event_name) > 100:
        errors.append("Event name is too long.")

    # Venue validation
    venue = raw.get("venue")

    if not isinstance(venue, str) or not venue.strip():
        errors.append("Venue must be a non-empty string.")

    # Activities content validation
    if isinstance(activities, list):
        if any(
            not isinstance(activity, str) or not activity.strip()
            for activity in activities
        ):
            errors.append(
                "Each activity must be a non-empty string."
            )

    # Duplicate event validation
    if (
        isinstance(event_name, str)
        and event_name.strip()
        and event_date
    ):
        try:
            if has_duplicate_event(
                event_name.strip(),
                event_date,
            ):
                errors.append(
                    "A plan with the same event name and date "
                    "already exists."
                )
        except Exception as exc:
            errors.append(
                f"Could not verify duplicate events: {exc}"
            )

    return errors


# --------------------------------------------------
# 2. AGENT OUTPUT GUARDRAILS
# --------------------------------------------------

def validate_agent_outputs(
    requirements,
    budget_plan,
    venue_schedule,
    workflow,
):
    errors = []

    # Requirement Agent output
    if not isinstance(requirements, dict) or not requirements:
        return [
            "Requirement Agent output is missing or invalid."
        ]

    # Budget Agent output
    if not isinstance(budget_plan, dict) or not budget_plan:
        errors.append(
            "Budget Agent output is missing or invalid."
        )

    # Venue Agent output
    if not isinstance(venue_schedule, dict) or not venue_schedule:
        errors.append(
            "Venue & Schedule Agent output is missing or invalid."
        )

    # Workflow Agent returns a list in the supplied agents.py.
    if not isinstance(workflow, list) or not workflow:
        errors.append(
            "Workflow Planner output must be a non-empty list."
        )

    if errors:
        return errors

    # Required normalized fields
    for field in ["event_name", "event_date", "venue"]:
        if not requirements.get(field):
            errors.append(
                f"Requirement Agent output is missing {field}."
            )

    # Budget validation
    total_budget = requirements.get("budget")

    if (
        not isinstance(total_budget, (int, float))
        or isinstance(total_budget, bool)
        or total_budget <= 0
    ):
        errors.append("Invalid total event budget.")

    # Audience validation
    audience = requirements.get("audience")

    if (
        not isinstance(audience, int)
        or isinstance(audience, bool)
        or not 1 <= audience <= 5000
    ):
        errors.append("Invalid audience size.")

    # Activities validation
    activities = requirements.get("activities")

    if (
        not isinstance(activities, list)
        or not 1 <= len(activities) <= 10
    ):
        errors.append("Invalid activities count.")

    # Event date validation
    event_date = requirements.get("event_date")

    if event_date:
        try:
            if not is_valid_date(event_date):
                errors.append(
                    "Invalid event date in agent output."
                )
        except (ValueError, TypeError):
            errors.append(
                "Malformed event date in agent output."
            )

    # Event time validation
    start = requirements.get("start_time")
    end = requirements.get("end_time")

    try:
        if not start or not end:
            errors.append("Event time range is missing.")
        else:
            start_time = datetime.strptime(start, "%H:%M")
            end_time = datetime.strptime(end, "%H:%M")

            if end_time <= start_time:
                errors.append("Invalid event time range.")
    except (ValueError, TypeError):
        errors.append("Invalid time format in agent output.")

    # Venue calendar validation
    calendar_check = venue_schedule.get("calendar_check")

    if not isinstance(calendar_check, dict):
        errors.append("Venue calendar check is missing.")
    elif calendar_check.get("available") is not True:
        conflicts = calendar_check.get("conflicts", [])

        errors.extend(
            conflicts
            if isinstance(conflicts, list) and conflicts
            else ["Venue availability is not confirmed."]
        )

    # Budget allocation validation
    allocations = budget_plan.get("allocations")

    if allocations is not None:
        if not isinstance(allocations, dict) or not allocations:
            errors.append("Budget allocations are invalid.")
        else:
            valid_amounts = all(
                isinstance(amount, (int, float))
                and not isinstance(amount, bool)
                and amount >= 0
                for amount in allocations.values()
            )

            if not valid_amounts:
                errors.append(
                    "Budget allocations contain invalid amounts."
                )
            elif sum(allocations.values()) > total_budget:
                errors.append(
                    "Budget allocations exceed the total budget."
                )

    # Workflow step validation
    if isinstance(workflow, list):
        for index, step in enumerate(workflow):
            if not isinstance(step, dict):
                errors.append(
                    f"Workflow step {index + 1} is invalid."
                )
                continue

            for field in ["step", "task", "owner", "timeline"]:
                if field not in step:
                    errors.append(
                        f"Workflow step {index + 1} "
                        f"is missing '{field}'."
                    )

    return errors


# --------------------------------------------------
# 3. MULTI-AGENT ORCHESTRATOR
# --------------------------------------------------

def run_orchestrator(raw):
    trace = []

    # Step 1: Validate original user input
    errors = guardrails(raw)

    if errors:
        return {
            "status": "blocked",
            "guardrail_errors": errors,
            "trace": trace,
        }

    # Step 2: Requirement Agent
    try:
        requirements_output = requirement_agent(raw)

        if (
            not isinstance(requirements_output, dict)
            or not requirements_output
        ):
            return {
                "status": "blocked",
                "guardrail_errors": [
                    "Requirement Agent output is missing or invalid."
                ],
                "trace": trace,
            }

        # Preserve input fields if the agent omits any.
        # Agent-normalized values take precedence.
        requirements = {
            **raw,
            **requirements_output,
        }

    except Exception as exc:
        return {
            "status": "blocked",
            "guardrail_errors": [
                f"Requirement Agent failed: {exc}"
            ],
            "trace": trace,
        }

    trace.append({
        "from": "User",
        "to": "Requirement Agent",
        "message": "Processed event requirements.",
        "output": requirements,
    })

    # Step 3: Budget Agent
    try:
        budget_plan = budget_agent(requirements)

    except Exception as exc:
        return {
            "status": "blocked",
            "guardrail_errors": [
                f"Budget Agent failed: {exc}"
            ],
            "trace": trace,
        }

    trace.append({
        "from": "Requirement Agent",
        "to": "Budget Agent",
        "message": "Passed normalized event requirements.",
        "output": budget_plan,
    })

    if not isinstance(budget_plan, dict) or not budget_plan:
        return {
            "status": "blocked",
            "guardrail_errors": [
                "Budget Agent output is missing or invalid."
            ],
            "trace": trace,
        }

    # Step 4: Venue & Schedule Agent
    # Pass both flat fields and nested requirements for compatibility.
    venue_input = {
        **requirements,
        "requirements": requirements,
        "budget_plan": budget_plan,
    }

    try:
        venue_schedule = venue_schedule_agent(venue_input)

    except Exception as exc:
        return {
            "status": "blocked",
            "guardrail_errors": [
                f"Venue & Schedule Agent failed: {exc}"
            ],
            "trace": trace,
        }

    trace.append({
        "from": "Budget Agent",
        "to": "Venue & Schedule Agent",
        "message": "Passed event requirements and budget plan.",
        "output": venue_schedule,
    })

    if not isinstance(venue_schedule, dict) or not venue_schedule:
        return {
            "status": "blocked",
            "guardrail_errors": [
                "Venue & Schedule Agent output is missing or invalid."
            ],
            "trace": trace,
        }

    # Step 5: Check venue availability
    calendar_check = venue_schedule.get("calendar_check")

    if not isinstance(calendar_check, dict):
        return {
            "status": "blocked",
            "guardrail_errors": [
                "Venue calendar check is missing or invalid."
            ],
            "trace": trace,
        }

    if calendar_check.get("available") is not True:
        conflicts = calendar_check.get("conflicts", [])

        return {
            "status": "blocked",
            "guardrail_errors": (
                conflicts
                if isinstance(conflicts, list) and conflicts
                else ["Venue is unavailable or unconfirmed."]
            ),
            "trace": trace,
        }

    # Step 6: Workflow Planner Agent
    # IMPORTANT: agents.py defines this function with three arguments.
    try:
        workflow = workflow_planner_agent(
            requirements,
            budget_plan,
            venue_schedule,
        )

    except Exception as exc:
        return {
            "status": "blocked",
            "guardrail_errors": [
                f"Workflow Planner Agent failed: {exc}"
            ],
            "trace": trace,
        }

    trace.append({
        "from": "Venue & Schedule Agent",
        "to": "Workflow Planner Agent",
        "message": (
            "Passed requirements, budget plan, "
            "and venue schedule."
        ),
        "output": workflow,
    })

    # Step 7: Validate all agent outputs
    validation_errors = validate_agent_outputs(
        requirements,
        budget_plan,
        venue_schedule,
        workflow,
    )

    if validation_errors:
        return {
            "status": "blocked",
            "guardrail_errors": validation_errors,
            "trace": trace,
        }

    # Step 8: Record successful guardrail checks
    guardrail_checks = [
        "Required fields checked",
        "Budget validated",
        "Audience size validated",
        "Activities count validated",
        "Event date validated",
        "Event time range validated",
        "Duplicate event check performed",
        "Venue calendar availability checked",
        "Budget allocations checked when provided",
        "Agent outputs checked",
        "Workflow generated after prerequisite agents completed",
    ]

    trace.append({
        "from": "Workflow Planner Agent",
        "to": "User",
        "message": "Generated final event workflow.",
        "output": workflow,
    })

    # Step 9: Return successful result
    return {
        "status": "success",
        "requirements": requirements,
        "budget_plan": budget_plan,
        "venue_schedule": venue_schedule,
        "workflow": workflow,
        "trace": trace,
        "guardrails": guardrail_checks,
        "generated_at": india_now().isoformat(
            timespec="seconds"
        ),
    }
