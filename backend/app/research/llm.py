"""Google Gemini structured completion client for grounded research reports."""
import os
import time
from typing import Optional
from pydantic import ValidationError

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.research.prompts import RESEARCH_SYSTEM_PROMPT, build_user_prompt
from app.research.schemas import ResearchReport
from app.utils.logging import logger


class ResearchLLMError(Exception):
    """Base exception for research LLM failures."""
    pass


class LLMKeyMissingError(ResearchLLMError):
    """Raised when GEMINI_API_KEY is not configured."""
    pass


class LLMAPIError(ResearchLLMError):
    """Raised when Gemini API encounters network, authentication, or rate limit issues."""
    pass


class LLMResponseParsingError(ResearchLLMError):
    """Raised when the LLM response fails schema validation or is refused."""
    pass


def call_structured_research_llm(
    context_text: str,
    ticker: str,
    company_name: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> ResearchReport:
    """
    Invokes the Google Gemini API using structured outputs (response_schema=ResearchReport)
    to generate a strictly validated ResearchReport.
    Includes bounded retries with exponential backoff for transient provider failures.
    """
    effective_key = api_key or os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
    if not effective_key:
        raise LLMKeyMissingError(
            "GEMINI_API_KEY is missing. The AI Research Layer requires a Google Gemini API key "
            "set in the environment (GEMINI_API_KEY) or .env file to generate synthesis reports."
        )

    chosen_model = model or os.getenv("GEMINI_MODEL") or settings.gemini_model
    temp = temperature if temperature is not None else settings.gemini_temperature
    req_timeout = timeout or settings.gemini_timeout

    logger.info(f"Invoking Google Gemini structured research synthesis for {ticker} using {chosen_model}")

    # google.genai.types.HttpOptions.timeout expects milliseconds
    timeout_ms = int(req_timeout * 1000)
    client = genai.Client(api_key=effective_key, http_options=types.HttpOptions(timeout=timeout_ms))
    user_prompt = build_user_prompt(context_text, ticker, company_name)

    config = types.GenerateContentConfig(
        system_instruction=RESEARCH_SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=ResearchReport,
        temperature=temp,
    )

    max_retries = 2
    initial_backoff = 1.0
    backoff = initial_backoff

    for attempt in range(1, max_retries + 2):
        try:
            response = client.models.generate_content(
                model=chosen_model,
                contents=user_prompt,
                config=config,
            )

            # Check for candidate or safety block
            if not getattr(response, "candidates", None):
                raise LLMResponseParsingError("No generation candidates returned from Gemini.")

            candidate = response.candidates[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            if finish_reason and str(finish_reason).upper() in ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "RECITATION"):
                raise LLMResponseParsingError(f"Model generation blocked by safety policy: {finish_reason}")

            # Structured parsing via response.parsed or model_validate_json
            parsed_report: Optional[ResearchReport] = getattr(response, "parsed", None)
            if not parsed_report and getattr(response, "text", None):
                try:
                    parsed_report = ResearchReport.model_validate_json(response.text)
                except ValidationError as ve:
                    raise LLMResponseParsingError(f"Failed to validate Gemini JSON against ResearchReport schema: {ve}") from ve

            if not parsed_report:
                raise LLMResponseParsingError("Failed to parse structured ResearchReport from Gemini response.")

            # Ensure model identifier is attached
            parsed_report.model_name = chosen_model
            return parsed_report

        except APIError as e:
            error_code = getattr(e, "code", None)
            error_str = str(e)

            # Non-retryable authentication / permission errors
            if error_code in (400, 401, 403) or "API_KEY_INVALID" in error_str or "PERMISSION_DENIED" in error_str:
                logger.error(f"Gemini authentication failed: {e}")
                raise LLMAPIError(f"Gemini Authentication Error: Invalid or expired API key. Details: {e}") from e

            # Rate limits / Quota exhaustion
            is_rate_limit = error_code == 429 or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower()
            if attempt <= max_retries:
                logger.warning(
                    f"Transient Gemini error ({error_code or type(e).__name__}) for {ticker} on attempt {attempt}/{max_retries + 1}. "
                    f"Retrying in {backoff:.2f}s..."
                )
                time.sleep(backoff)
                backoff *= 2.0
                continue
            else:
                logger.error(f"Gemini API transient error failed after {max_retries + 1} attempts for {ticker}: {e}")
                if is_rate_limit:
                    raise LLMAPIError(f"Gemini Rate Limit Exceeded: Please check your account quota. Details: {e}") from e
                else:
                    raise LLMAPIError(f"Gemini API Error (HTTP {error_code}): {e}") from e

        except Exception as e:
            if isinstance(e, ResearchLLMError):
                raise
            err_name = type(e).__name__
            err_msg = str(e)
            if "timeout" in err_name.lower() or "timeout" in err_msg.lower():
                if attempt <= max_retries:
                    logger.warning(f"Gemini request timeout on attempt {attempt}/{max_retries + 1}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue
                else:
                    logger.error(f"Gemini request timed out after {max_retries + 1} attempts: {e}")
                    raise LLMAPIError(f"Gemini API Request Timeout after {req_timeout}s. Details: {e}") from e
            elif "connect" in err_name.lower() or "connect" in err_msg.lower():
                if attempt <= max_retries:
                    logger.warning(f"Gemini connection error on attempt {attempt}/{max_retries + 1}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue
                else:
                    logger.error(f"Gemini network connection failed after {max_retries + 1} attempts: {e}")
                    raise LLMAPIError(f"Gemini Connection Error: Unable to reach Google Gemini servers. Details: {e}") from e

            logger.error(f"Unexpected error during research synthesis: {e}")
            raise LLMAPIError(f"Unexpected error communicating with Google Gemini: {e}") from e