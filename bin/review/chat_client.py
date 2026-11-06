"""Minimal client for OpenAI-compatible chat-completion APIs (stdlib only)."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

# 529 is IONOS's "overloaded" answer, to be retried like a 429.
RETRY_STATUSES = {429, 500, 502, 503, 504, 529}
MAX_ATTEMPTS = 5
TIMEOUT_SECONDS = 300


class ChatClientError(RuntimeError):
    pass


class ChatClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        prompt_caching: bool = False,
    ) -> None:
        if not base_url.startswith("https://"):
            raise ChatClientError("The API base URL must use https.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        # Every request of one client shares the key: a review only ever
        # appends to its messages, so each request extends the previous
        # one's prefix. Random, so it carries no repository or user data.
        self.prompt_cache_key = (
            f"ai-review-{uuid.uuid4().hex}" if prompt_caching else None
        )
        self.prompt_tokens = 0
        self.cached_tokens = 0
        self.completion_tokens = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send one completion request and return the assistant message."""
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if self.prompt_cache_key:
            body["prompt_cache_key"] = self.prompt_cache_key
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice
        response = self._request("POST", "/chat/completions", body)
        usage = response.get("usage") or {}
        self.prompt_tokens += usage.get("prompt_tokens", 0)
        details = usage.get("prompt_tokens_details") or {}
        self.cached_tokens += details.get("cached_tokens") or 0
        self.completion_tokens += usage.get("completion_tokens", 0)
        message = response["choices"][0]["message"]
        message["content"] = self.text_of(message.get("content"))
        return message

    @staticmethod
    def text_of(content: str | list[Any] | None) -> str:
        """The answer text; reasoning models return a list of typed parts.

        Their ``thinking`` parts are dropped, so they are neither shown in the
        review nor sent back with the conversation.
        """
        if isinstance(content, list):
            return "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        return content or ""

    def list_models(self) -> list[str]:
        response = self._request("GET", "/models")
        return sorted(model["id"] for model in response.get("data", []))

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            request = urllib.request.Request(  # noqa: S310 - https enforced in __init__
                self.base_url + path,
                data=data,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(  # noqa: S310  # nosec B310 - https only
                    request, timeout=TIMEOUT_SECONDS
                ) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as error:
                detail = error.read().decode(errors="replace")[:500]
                limits = {
                    name: value
                    for name, value in error.headers.items()
                    if "ratelimit" in name.lower() or name.lower() == "retry-after"
                }
                if limits:
                    detail += f"\nRate-limit headers: {limits}"
                if error.code not in RETRY_STATUSES or attempt == MAX_ATTEMPTS:
                    raise ChatClientError(
                        f"API {method} {path} returned HTTP {error.code}: " f"{detail}"
                    ) from error
                wait = float(error.headers.get("Retry-After") or 2**attempt)
            except (urllib.error.URLError, TimeoutError) as error:
                if attempt == MAX_ATTEMPTS:
                    raise ChatClientError(f"API unreachable: {error}") from error
                wait = 2**attempt
            print(f"  API busy, retrying in {wait:.0f}s ...", file=sys.stderr)
            time.sleep(wait)
        raise ChatClientError("unreachable")
