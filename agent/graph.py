from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools.escalation import escalate_to_human
from tools.knowledge_base import search_knowledge_base
from tools.ticketing import create_ticket

SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"


def build_agent():
    llm = ChatOpenAI(
        model="gpt-5.4-mini",
        temperature=0.7,
        max_tokens=2048,
    )

    tools = [search_knowledge_base, create_ticket, escalate_to_human]

    with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        system_prompt = f.read()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent
