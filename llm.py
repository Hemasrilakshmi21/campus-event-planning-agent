
import os
import json
from groq import Groq

from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL_NAME = "openai/gpt-oss-20b"


def ask_llm(question, context=None):
    """Answer general knowledge and event-project questions."""

    if isinstance(context, (dict, list)):
        context_text = json.dumps(
            context,
            indent=2,
            default=str
        )
    elif context is None:
        context_text = "No project or event context was provided."
    else:
        context_text = str(context)

    system_prompt = """
You are a helpful AI assistant for students and a campus
event-planning project.

You can answer BOTH general questions and project-specific questions.

GENERAL KNOWLEDGE:
- Artificial Intelligence (AI)
- Machine Learning (ML)
- Deep Learning
- Python and programming
- Data science
- LLMs and generative AI
- Computer science and technology
- Project domains and hackathon topics

PROJECT KNOWLEDGE:
- Campus event management and planning
- Event dates, venues, budgets, and schedules
- Multi-agent systems and agent orchestration
- Requirement, Budget, Venue/Schedule, and Workflow agents
- Python, Streamlit, Groq, databases, and guardrails
- Project objectives, advantages, limitations, and future scope

IMPORTANT RULES:
1. Answer general knowledge questions using your own knowledge.
   Do not require the answer to be present in event details.
2. For example, if asked "What is AI?", explain Artificial
   Intelligence. If asked "What is ML?", explain Machine Learning.
3. Use project context only when the question concerns this project
   or its actual saved event records.
4. Never invent event dates, budgets, venues, or saved information.
5. If a specific event detail is missing, say that detail is unavailable.
6. Explain concepts in simple, student-friendly language.
7. Use examples and bullet points when helpful.
8. Do not call external tools. Answer directly.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": (
                f"Project and event context:\n{context_text}\n\n"
                f"My question: {question}"
            )
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.3,
        max_completion_tokens=1200
    )

    return response.choices[0].message.content
