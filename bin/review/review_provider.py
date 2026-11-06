"""Which API the review runs against, chosen with AI_REVIEW_PROVIDER."""

from __future__ import annotations

import os
from dataclasses import dataclass

from chat_client import ChatClient, ChatClientError


@dataclass(frozen=True)
class ReviewProvider:
    name: str
    base_url: str
    key_variable: str
    default_model: str
    prompt_caching: bool = False
    # Share of the input price billed for a cached prompt token.
    cached_price_factor: float = 1.0
    # List prices of default_model per million tokens, for the cost estimate.
    default_price_input: float | None = None
    default_price_output: float | None = None
    currency: str = "$"

    @classmethod
    def from_environment(cls) -> ReviewProvider:
        name = os.environ.get("AI_REVIEW_PROVIDER", "mistral").lower()
        if name not in PROVIDERS:
            raise ChatClientError(
                f"Unknown AI_REVIEW_PROVIDER '{name}', use one of: "
                f"{', '.join(PROVIDERS)}."
            )
        return PROVIDERS[name]

    @property
    def model(self) -> str:
        """AI_REVIEW_MODEL, MISTRAL_MODEL for Mistral, else the default model."""
        legacy = os.environ.get("MISTRAL_MODEL") if self.name == "mistral" else None
        return os.environ.get("AI_REVIEW_MODEL") or legacy or self.default_model

    def client(self, model: str | None = None) -> ChatClient:
        api_key = os.environ.get(self.key_variable, "")
        if not api_key:
            raise ChatClientError(f"{self.key_variable} is not set.")
        return ChatClient(
            api_key,
            model or self.model,
            base_url=os.environ.get("AI_REVIEW_BASE_URL", self.base_url),
            prompt_caching=self.prompt_caching,
        )

    def prices(self, model: str) -> tuple[float, float] | None:
        """Input and output price per million tokens, if known for the model."""
        price_in = os.environ.get("AI_REVIEW_PRICE_INPUT")
        price_out = os.environ.get("AI_REVIEW_PRICE_OUTPUT")
        if price_in and price_out:
            return float(price_in), float(price_out)
        if (
            model == self.default_model
            and self.default_price_input is not None
            and self.default_price_output is not None
        ):
            return self.default_price_input, self.default_price_output
        return None


PROVIDERS = {
    "mistral": ReviewProvider(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        key_variable="MISTRAL_API_KEY",
        default_model="mistral-large-4",
        prompt_caching=True,
        cached_price_factor=0.1,
    ),
    # Hosted in Germany; no prompt caching documented, no list price known for
    # the default model, so the cost estimate needs AI_REVIEW_PRICE_*.
    "ionos": ReviewProvider(
        name="ionos",
        base_url="https://openai.inference.de-txl.ionos.com/v1",
        key_variable="IONOS_API_TOKEN",
        default_model="Qwen/Qwen3-Coder-Next",
        currency="€",
    ),
}
