# Campus Event Planning Agent

A hackathon-ready Agentic AI application built with:

- Python
- Streamlit
- SQLite
- Multi-agent orchestration
- A2A agent handoffs
- Short-term memory
- Long-term memory
- Guardrails
- Calculator tool
- Calendar conflict-checking tool

## Architecture

User
  ↓
Orchestrator
  ↓
Requirement Agent
  ├──→ Budget Agent
  └──→ Venue & Schedule Agent
             ↓
Budget + Venue/Schedule
             ↓
Workflow Planner Agent
             ↓
Final Event Workflow

## Memory

### Short-term memory
The current event request and current agent outputs are held in Streamlit session state.

### Long-term memory
SQLite stores previous event plans in `event_memory.db`.

## A2A

1. Requirement Agent → Budget Agent
2. Requirement Agent → Venue & Schedule Agent
3. Budget Agent + Venue & Schedule Agent → Workflow Planner Agent

## Tools

### Calculator
Calculates deterministic budget allocation:
- Venue & setup: 25%
- Food & refreshments: 25%
- Marketing: 10%
- Equipment: 15%
- Certificates & prizes: 10%
- Contingency: 15%

### Calendar
Checks whether the selected venue has an overlapping event on the selected date.

## Guardrails

The system checks:
1. Required fields
2. Positive budget
3. Positive audience
4. At least one activity
5. Maximum activity limit
6. Valid time range
7. No past date
8. Event-name length
9. Audience upper limit
10. Duplicate event
11. Venue/time conflict

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The SQLite database is created automatically.
