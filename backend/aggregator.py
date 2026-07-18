"""
Response Aggregator, per the M0 decision doc.

Single agent -> pass through unchanged.
Multiple agents -> concatenate with a lightweight header per agent, no
extra LLM summarization call (avoids compounding hallucination risk and
extra token cost).
"""
from agents.base_agent import AgentResponse

AGENT_DISPLAY_NAMES = {
    "billing": "On billing",
    "technical": "On the technical issue",
    "product": "On the product",
    "complaint": "Regarding your complaint",
    "faq": "Here's what I found",
}


def aggregate(responses: list[AgentResponse]) -> str:
    if not responses:
        return "I wasn't able to find an agent to handle that — please rephrase your question."

    if len(responses) == 1:
        return responses[0].text

    parts = []
    for r in responses:
        header = AGENT_DISPLAY_NAMES.get(r.agent_name, r.agent_name.title())
        parts.append(f"**{header}:**\n{r.text}")
    return "\n\n".join(parts)
