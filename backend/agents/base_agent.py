"""
Shared agent interface. Every specialized agent (FAQ, Billing, Technical,
Product, Complaint) implements this so the aggregator can treat them
uniformly (Instruction 16 — isolated, not tightly coupled).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResponse:
    agent_name: str
    text: str
    grounded: bool  # False when the confidence-threshold fallback fired


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def respond(self, query: str) -> AgentResponse:
        raise NotImplementedError
