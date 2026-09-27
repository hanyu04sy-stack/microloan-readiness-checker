"""Optional live Gemini adapter.

This module is not exercised by the offline test suite. It follows Google's
official google-genai structured-output interface and is loaded only when a
live call is explicitly requested.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Mapping

from .semantic import ModelCall


class GeminiStructuredClient:
    def __init__(
        self,
        *,
        model: str = "gemini-3.8-flash",
        api_key: str | None = None,
        max_attempts: int = 3,
    ):
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "The optional google-genai package is required for a live Gemini call"
            ) from exc

        self.model = model
        self.max_attempts = max_attempts
        self._client = genai.Client(
            api_key=resolved_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            ),
        )

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: Mapping[str, Any],
    ) -> ModelCall:
        started = time.perf_counter()
        retry_errors: list[str] = []
        response = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": dict(response_schema),
                        "temperature": 0,
                    },
                )
                break
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                retryable = any(
                    marker in message
                    for marker in ("503", "UNAVAILABLE")
                )
                if not retryable or attempt == self.max_attempts:
                    raise
                retry_errors.append(message)
                time.sleep(2 ** (attempt - 1))
        if response is None:
            raise RuntimeError("Gemini returned no response")
        latency_ms = (time.perf_counter() - started) * 1000

        raw_payload = getattr(response, "parsed", None)
        if raw_payload is None:
            response_text = getattr(response, "text", None)
            if not isinstance(response_text, str):
                raise RuntimeError("Gemini returned neither parsed JSON nor response text")
            raw_payload = json.loads(response_text)
        if hasattr(raw_payload, "model_dump"):
            raw_payload = raw_payload.model_dump()
        if not isinstance(raw_payload, Mapping):
            raise RuntimeError("Gemini structured response is not a JSON object")

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)

        return ModelCall(
            payload=dict(raw_payload),
            model=self.model,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            attempt_count=1 + len(retry_errors),
            retry_errors=tuple(retry_errors),
        )
