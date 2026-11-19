import os
from typing import Literal, Protocol

import anthropic
from pydantic import BaseModel


class ModelAnswer(BaseModel):
    answer: Literal["yes", "partial", "no", "silent"]
    doc_id: str | None
    page: int | None
    quote: str
    reason: str


class Reply(BaseModel):
    answer: ModelAnswer
    model: str
    cache_read_tokens: int


class ModelClient(Protocol):
    def ask(self, system: str, contract: str, question: str) -> Reply: ...


class ModelOutputError(Exception):
    """The model returned no usable answer. `check` retries once, then records it."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def ask_with_retry(
    client: ModelClient, system: str, contract: str, question: str, attempts: int = 2
) -> Reply | ModelOutputError:
    """Ask once, retry on unusable output, and return the last error if every try fails."""
    error = ModelOutputError("no attempts made")
    for _ in range(attempts):
        try:
            return client.ask(system, contract, question)
        except ModelOutputError as e:
            error = e
    return error


class AnthropicClient:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.model = os.environ["PTLITE_MODEL"]

    def ask(self, system: str, contract: str, question: str) -> Reply:
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": [
                        # same bytes for all five questions, so 2-5 read it from cache
                        {"type": "text", "text": contract, "cache_control": {"type": "ephemeral"}},
                        {"type": "text", "text": question},
                    ],
                }
            ],
            output_format=ModelAnswer,
            output_config={"effort": "high"},
        )
        parsed = response.parsed_output
        if parsed is None:
            raise ModelOutputError(f"no parsed answer (stop_reason={response.stop_reason})")
        return Reply(
            answer=parsed,
            model=response.model,
            cache_read_tokens=response.usage.cache_read_input_tokens or 0,
        )
