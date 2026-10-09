from tools import calculator_tool, calendar_tool
def requirement_agent(raw):
    # Requirement Agent normalizes user input.
    return {
        "event_name": raw["event_name"].strip(),
        "event_date": raw["event_date"],
        "budget": float(raw["budget"]),
        "venue": raw["venue"].strip(),
        "audience": int(raw["audience"]),
        "activities": raw["activities"],
        "start_time": raw["start_time"],
        "end_time": raw["end_time"],
    }

def budget_agent(requirements):
    # A2A receives normalized requirements from Requirement Agent.
    return calculator_tool(
        requirements["budget"],
        requirements["audience"]
    )


def venue_schedule_agent(data):
    # Support both flat and nested input dictionaries.
    requirements = data.get("requirements", data)

    # Validate required fields before accessing them.
    required_fields = [
        "event_date",
        "venue",
        "start_time",
        "end_time",
    ]

    missing = [
        field for field in required_fields
        if not requirements.get(field)
    ]

    if missing:
        return {
            "date": requirements.get("event_date"),
            "venue": requirements.get("venue"),
            "start_time": requirements.get("start_time"),
            "end_time": requirements.get("end_time"),
            "calendar_check": {
                "available": False,
                "conflicts": [
                    f"Missing required field: {field}"
                    for field in missing
                ],
            },
            "schedule": [],
        }

    calendar_result = calendar_tool(
        requirements["event_date"],
        requirements["venue"],
        requirements["start_time"],
        requirements["end_time"],
    )

    return {
        "date": requirements["event_date"],
        "venue": requirements["venue"],
        "start_time": requirements["start_time"],
        "end_time": requirements["end_time"],
        "calendar_check": calendar_result,
        "schedule": [
            f"{requirements['start_time']} - Registration / Check-in",
            "Opening and introduction",
            "Main event activities",
            "Q&A / Interaction",
            "Feedback and certificates",
            f"{requirements['end_time']} - Closing",
        ],
    }


def workflow_planner_agent(requirements, budget_plan, venue_schedule):
    # Final agent consumes outputs from other agents.
    workflow = [
        {
            "step": 1,
            "task": "Confirm event requirements and permissions",
            "owner": "Requirement Team",
            "timeline": "T-14 days",
        },
        {
            "step": 2,
            "task": f"Finalize venue: {venue_schedule['venue']}",
            "owner": "Venue Team",
            "timeline": "T-12 days",
        },
        {
            "step": 3,
            "task": "Allocate and approve event budget",
            "owner": "Finance Team",
            "timeline": "T-10 days",
        },
        {
            "step": 4,
            "task": "Arrange equipment, seating and refreshments",
            "owner": "Operations Team",
            "timeline": "T-5 days",
        },
        {
            "step": 5,
            "task": "Promote event and confirm participants",
            "owner": "Marketing Team",
            "timeline": "T-5 to T-1 days",
        },
        {
            "step": 6,
            "task": "Conduct the event according to schedule",
            "owner": "Event Team",
            "timeline": "Event day",
        },
        {
            "step": 7,
            "task": "Collect feedback and close expenses",
            "owner": "Event Team",
            "timeline": "T+1 day",
        },
    ]
    return workflow
