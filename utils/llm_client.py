"""
LLM client utilities for the Kayako ticket analysis pipeline.

Provides OpenAI client factory and retry-enabled call wrapper.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

from dotenv import load_dotenv
import openai

from config import LLM_CONFIG

load_dotenv()

# Configure logger for this module
logger = logging.getLogger(__name__)


def get_openai_client() -> openai.OpenAI:
    """
    Create and return an OpenAI client.

    Raises RuntimeError if OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")
    return openai.OpenAI(api_key=api_key)


def _is_retryable_error(error: Exception) -> bool:
    """
    Determine if an OpenAI API error is retryable.

    Non-retryable errors (fail immediately):
    - AuthenticationError (401): Wrong API key
    - BadRequestError (400): Malformed request
    - NotFoundError (404): Invalid model/endpoint
    - PermissionDeniedError (403): No access

    Retryable errors (worth retrying):
    - RateLimitError (429): Rate limit hit
    - APIConnectionError: Network issues
    - InternalServerError (500): Server issues
    - APIStatusError (502, 503, 504): Server issues
    """
    # Non-retryable client errors
    if isinstance(error, openai.AuthenticationError):
        return False
    if isinstance(error, openai.BadRequestError):
        return False
    if isinstance(error, openai.NotFoundError):
        return False
    if isinstance(error, openai.PermissionDeniedError):
        return False

    # Retryable errors
    if isinstance(error, openai.RateLimitError):
        return True
    if isinstance(error, openai.APIConnectionError):
        return True
    if isinstance(error, openai.InternalServerError):
        return True
    if isinstance(error, openai.APIStatusError):
        # 5xx errors are retryable
        return error.status_code >= 500

    # Default: don't retry unknown errors
    return False


def _get_retry_delay(error: Exception, base_delay: float, attempt: int) -> float:
    """
    Calculate retry delay based on error type and attempt number.

    Rate limit errors get longer delays (5x base).
    Other errors use exponential backoff.
    """
    multiplier = attempt + 1

    if isinstance(error, openai.RateLimitError):
        # Rate limits need longer waits
        return base_delay * 5 * multiplier

    # Standard exponential backoff for other errors
    return base_delay * 1.5 * multiplier


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    reasoning_effort: Optional[str] = None,
    max_retries: Optional[int] = None,
    retry_delay_base: Optional[float] = None,
    response_format: Optional[dict] = None,
) -> Optional[dict]:
    """
    Call the LLM with smart retry logic and return parsed JSON response.

    Retry behavior:
    - Non-retryable errors (auth, bad request): Fail immediately
    - Rate limit errors: Retry with longer delays (5x)
    - Server errors: Retry with exponential backoff
    - Empty responses: Do NOT retry (likely model refusal)
    - JSON parse errors: Retry (might be transient)

    Args:
        system_prompt: The system message content
        user_prompt: The user message content
        model: Model name (defaults to LLM_CONFIG["model"])
        max_completion_tokens: Max tokens (defaults to LLM_CONFIG["max_completion_tokens"])
        reasoning_effort: Reasoning effort level (defaults to LLM_CONFIG["reasoning_effort"])
        max_retries: Number of retries (defaults to LLM_CONFIG["max_retries"])
        retry_delay_base: Base delay between retries (defaults to LLM_CONFIG["retry_delay_base"])
        response_format: Response format dict (defaults to {"type": "json_object"})

    Returns:
        Parsed JSON dict from the response, or None if failed.
    """
    config = LLM_CONFIG
    _model = model or config["model"]
    _max_tokens = max_completion_tokens or config["max_completion_tokens"]
    _reasoning = reasoning_effort or config["reasoning_effort"]
    _retries = max_retries if max_retries is not None else config["max_retries"]
    _retry_delay = retry_delay_base or config["retry_delay_base"]
    _format = response_format or {"type": "json_object"}

    client = get_openai_client()
    last_err: Optional[Exception] = None

    for attempt in range(_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=_max_tokens,
                reasoning_effort=_reasoning,
                response_format=_format,
            )
            content = resp.choices[0].message.content

            # Empty response - don't retry, this is likely a refusal or content filter
            if not content or not content.strip():
                logger.warning("LLM returned empty content (possible refusal)")
                return None

            # Try to parse JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # JSON parse error - worth retrying (might be transient)
                last_err = e
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < _retries:
                    time.sleep(_retry_delay * (attempt + 1))
                continue

        except Exception as e:
            last_err = e

            # Check if this error is retryable
            if not _is_retryable_error(e):
                logger.error(f"Non-retryable error: {type(e).__name__}: {e}")
                return None

            # Retryable error - wait and try again
            if attempt < _retries:
                delay = _get_retry_delay(e, _retry_delay, attempt)
                logger.warning(f"Retryable error (attempt {attempt + 1}), waiting {delay:.1f}s: {type(e).__name__}")
                time.sleep(delay)
            continue

    # All retries exhausted
    if last_err:
        logger.error(f"All retries exhausted. Last error: {type(last_err).__name__}: {last_err}")
    return None


def call_llm_raw(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    max_completion_tokens: Optional[int] = None,
    reasoning_effort: Optional[str] = None,
    response_format: Optional[dict] = None,
) -> Optional[str]:
    """
    Call the LLM and return raw string response (no retries, no JSON parsing).

    Useful for non-JSON responses or when you want to handle parsing yourself.
    """
    config = LLM_CONFIG
    _model = model or config["model"]
    _max_tokens = max_completion_tokens or config["max_completion_tokens"]
    _reasoning = reasoning_effort or config["reasoning_effort"]
    _format = response_format or {"type": "json_object"}

    client = get_openai_client()

    try:
        resp = client.chat.completions.create(
            model=_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=_max_tokens,
            reasoning_effort=_reasoning,
            response_format=_format,
        )
        return resp.choices[0].message.content
    except Exception:
        return None
