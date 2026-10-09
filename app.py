
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, time
from zoneinfo import ZoneInfo

from database import (
    init_db,
    save_event_plan,
    get_past_plans,
)
from orchestrator import run_orchestrator
from llm import ask_llm


# --------------------------------------------------
# INITIALIZATION AND TIMEZONE
# --------------------------------------------------

load_dotenv()

INDIA_TZ = ZoneInfo("Asia/Kolkata")


def get_india_time():
    """Return the current date and time in Indian Standard Time."""
    return datetime.now(INDIA_TZ)


st.set_page_config(
    page_title="Campus Event Planning Agent",
    layout="wide",
)

init_db()

st.title("Campus Event Planning Agent")

st.caption(
    "Multi-Agent AI • Orchestration • A2A • "
    "Short-Term + Long-Term Memory • Guardrails"
)

now = get_india_time()

st.caption(
    "Current India Time: "
    f"{now.strftime('%d-%m-%Y %I:%M:%S %p')} IST"
)


# --------------------------------------------------
# SHORT-TERM MEMORY
# --------------------------------------------------

if "short_term_memory" not in st.session_state:
    st.session_state.short_term_memory = {}

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# --------------------------------------------------
# EVENT INPUT FORM
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    event_name = st.text_input(
        "Event name",
        placeholder="AI Workshop",
    )

    today_india = get_india_time().date()

    event_date = st.date_input(
        "Event date",
        value=today_india,
        min_value=today_india,
    )

    budget = st.number_input(
        "Total budget (₹)",
        min_value=1.0,
        value=25000.0,
        step=1000.0,
    )

    venue = st.text_input(
        "Preferred venue",
        placeholder="Seminar Hall",
    )

with col2:
    audience = st.number_input(
        "Expected audience",
        min_value=1,
        value=100,
        step=10,
    )

    activities_text = st.text_area(
        "Activities",
        placeholder=(
            "Guest lecture, coding contest, "
            "refreshments, certificates"
        ),
        height=120,
    )

    start_time = st.time_input(
        "Start time",
        value=time(9, 0),
        key="start_time",
    )

    end_time = st.time_input(
        "End time",
        value=time(17, 0),
        key="end_time",
    )


activities = [
    activity.strip()
    for activity in activities_text.split(",")
    if activity.strip()
]


# --------------------------------------------------
# CREATE EVENT PLAN
# --------------------------------------------------

if st.button(
    "Create Event Plan",
    type="primary",
    use_container_width=True,
):

    # Collect all event requirements.
    # Times are sent in 24-hour HH:MM format.
    requirements = {
        "event_name": event_name.strip(),
        "event_date": event_date.isoformat(),
        "budget": float(budget),
        "venue": venue.strip(),
        "audience": int(audience),
        "activities": activities,
        "start_time": start_time.strftime("%H:%M"),
        "end_time": end_time.strftime("%H:%M"),
    }

    # Update short-term memory.
    st.session_state.short_term_memory = requirements

    # Run multi-agent orchestration.
    with st.spinner("🤖 Agents are collaborating..."):
        try:
            result = run_orchestrator(requirements)

        except Exception as e:
            st.error(
                "An error occurred while running the agents."
            )
            st.exception(e)
            st.stop()

    # Store result in session memory.
    st.session_state.last_result = result

    # --------------------------------------------------
    # GUARDRAIL RESULT
    # --------------------------------------------------

    if result.get("status") == "blocked":

        st.error("Request blocked by guardrails.")

        for error in result.get("guardrail_errors", []):
            st.warning(error)

    elif result.get("status") == "success":

        # Save successful plan to long-term memory.
        try:
            save_event_plan(requirements, result)

            st.success(
                "Event plan created and saved to long-term memory."
            )

        except Exception as e:
            st.error(
                "The event plan was created, but saving it "
                "to the database failed."
            )
            st.exception(e)

    else:
        st.error(
            "The orchestrator returned an unexpected result."
        )


# --------------------------------------------------
# DISPLAY EVENT PLAN
# --------------------------------------------------

if st.session_state.last_result:

    result = st.session_state.last_result

    if result.get("status") == "success":

        st.divider()
        st.subheader("Agent Orchestration")

        # A2A / agent trace.
        for step in result.get("trace", []):

            st.write(
                f"**{step.get('from', 'Agent')} "
                f"→ {step.get('to', 'Agent')}**"
            )

            st.caption(step.get("message", ""))

        st.divider()

        tabs = st.tabs(
            [
                "Requirements",
                "Budget",
                "Venue & Schedule",
                "Final Workflow",
                "Guardrails",
            ]
        )

        # --------------------------------------------------
        # REQUIREMENTS
        # --------------------------------------------------

        with tabs[0]:
            st.subheader("Event Requirements")
            st.json(result.get("requirements", {}))

        # --------------------------------------------------
        # BUDGET
        # --------------------------------------------------

        with tabs[1]:
            st.subheader("Budget Breakdown")

            budget_plan = result.get("budget_plan", {})

            st.table(budget_plan.get("breakdown", []))

            if "total" in budget_plan:
                st.metric(
                    "Total Budget",
                    f"₹{budget_plan['total']:,.2f}",
                )

            st.write(budget_plan.get("message", ""))

        # --------------------------------------------------
        # VENUE AND SCHEDULE
        # --------------------------------------------------

        with tabs[2]:
            st.subheader("Venue & Schedule")
            st.json(result.get("venue_schedule", {}))

        # --------------------------------------------------
        # WORKFLOW
        # --------------------------------------------------

        with tabs[3]:
            st.subheader("Step-by-Step Workflow")

            workflow = result.get("workflow", [])

            if workflow:
                for item in workflow:

                    st.markdown(
                        f"**{item.get('step', '')}. "
                        f"{item.get('task', 'Task')}**"
                    )

                    st.write(
                        f"Owner: {item.get('owner', 'Unassigned')}"
                    )

                    st.write(
                        "Timeline: "
                        f"{item.get('timeline', 'Not specified')}"
                    )

                    st.divider()
            else:
                st.info("No workflow steps are available.")

        # --------------------------------------------------
        # GUARDRAILS
        # --------------------------------------------------

        with tabs[4]:
            guardrails = result.get("guardrails", [])

            if guardrails:
                for check in guardrails:
                    st.success(check)
            else:
                st.info("No guardrail messages are available.")


# --------------------------------------------------
# LLM CHAT
# --------------------------------------------------

st.divider()
st.subheader("Chat About Your Project")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.chat_input(
    "Ask about your event, project domain, AI, or technology..."
)

# Display previous chat messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if question:

    # Display user question
    st.session_state.chat_history.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.write(question)

    # Prepare project context
    project_context = {
        "project_name": "Campus Event Planning Agent",
        "project_domain": (
            "AI-powered event management, event scheduling, "
            "budget planning, venue coordination, and automation"
        ),
        "project_features": [
            "Multi-agent AI architecture",
            "Requirement Agent",
            "Budget Agent",
            "Venue and Schedule Agent",
            "Workflow Planner Agent",
            "Agent orchestration and A2A communication",
            "Guardrails and validation",
            "Short-term memory",
            "Long-term database memory",
            "LLM-powered chat assistant",
        ],
        "current_event_requirements":
            st.session_state.get("short_term_memory", {}),
        "latest_event_plan":
            st.session_state.get("last_result"),
    }

    # Include past event plans from the database
    try:
        past_plans = get_past_plans()
        project_context["past_event_plans"] = past_plans or []
    except Exception:
        project_context["past_event_plans"] = []

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("AI is thinking..."):
            try:
                answer = ask_llm(
                    question=question,
                    context=project_context,
                )

                st.write(answer)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as e:
                st.error("Unable to get a response from the LLM.")
                st.exception(e)



# --------------------------------------------------
# LONG-TERM MEMORY
# --------------------------------------------------

st.divider()
st.subheader("Long-Term Memory: Past Event Plans")

try:
    past = get_past_plans()

    if past:
        for row in past:

            with st.expander(
                f"{row['event_name']} — {row['event_date']}"
            ):

                st.write(
                    f"**Budget:** ₹{row['budget']:,.2f}"
                )

                st.write(f"**Venue:** {row['venue']}")
                st.write(f"**Audience:** {row['audience']}")

                created_at = row.get("created_at")

                if created_at:
                    try:
                        if isinstance(created_at, datetime):
                            timestamp = created_at
                        else:
                            timestamp = datetime.fromisoformat(
                                str(created_at)
                            )

                        if timestamp.tzinfo is None:
                            # Assumes naive database timestamps are UTC.
                            timestamp = timestamp.replace(
                                tzinfo=ZoneInfo("UTC")
                            )

                        timestamp_ist = timestamp.astimezone(
                            INDIA_TZ
                        )

                        created_display = timestamp_ist.strftime(
                            "%d-%m-%Y %I:%M:%S %p IST"
                        )

                    except (ValueError, TypeError):
                        created_display = str(created_at)

                    st.write(
                        f"**Created:** {created_display}"
                    )

    else:
        st.info("No past event plans yet.")

except Exception as e:
    st.error("Unable to load past event plans.")
    st.exception(e)