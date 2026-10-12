import json
from datetime import datetime
from pathlib import Path


# Project root / data / assignments.json
ASSIGNMENTS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "assignments.json"
)


def get_assignments():
    """Read assignments and calculate accurate remaining work."""

    with open(ASSIGNMENTS_FILE, "r", encoding="utf-8") as file:
        assignments = json.load(file)

    for assignment in assignments:
        assignment["remaining_minutes"] = max(
            0,
            assignment["estimated_minutes"]
            - assignment["completed_minutes"],
        )

    return assignments


def get_assignment(assignment_id):
    """Return the facts for one assignment."""

    assignments = get_assignments()

    for assignment in assignments:
        if assignment["id"] == assignment_id:
            return assignment

    return {"error": f"Assignment {assignment_id} not found"}


def save_assignments(assignments):
    """Save assignment records to JSON."""

    with open(ASSIGNMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(assignments, file, indent=2)


def get_current_time():
    """Return the current local date and time with timezone."""

    return datetime.now().astimezone().isoformat()


def update_progress(assignment_id, minutes):
    """Record study time and update completion status."""

    if not isinstance(minutes, int) or isinstance(minutes, bool):
        raise ValueError("Minutes must be a whole number.")

    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")

    assignments = get_assignments()

    for assignment in assignments:
        if assignment["id"] == assignment_id:
            assignment["completed_minutes"] = min(
                assignment["estimated_minutes"],
                assignment["completed_minutes"] + minutes,
            )

            if (
                assignment["completed_minutes"]
                >= assignment["estimated_minutes"]
            ):
                assignment["status"] = "completed"
            elif assignment["completed_minutes"] > 0:
                assignment["status"] = "in progress"
            else:
                assignment["status"] = "not started"

            assignment["remaining_minutes"] = max(
                0,
                assignment["estimated_minutes"]
                - assignment["completed_minutes"],
            )

            save_assignments(assignments)
            return assignment

    raise ValueError(f"Assignment {assignment_id} not found.")


def reset_assignment(assignment_id):
    """Reset an assignment's progress."""

    assignments = get_assignments()

    for assignment in assignments:
        if assignment["id"] == assignment_id:
            assignment["completed_minutes"] = 0
            assignment["remaining_minutes"] = (
                assignment["estimated_minutes"]
            )
            assignment["status"] = "not started"

            save_assignments(assignments)
            return assignment

    raise ValueError(f"Assignment {assignment_id} not found.")