"""OpenAI structured completion client for grounded research reports."""
import os
from typing import Optional
import openai
from openai import OpenAI

from app.config import settings
from app.research.prompts import RESEARCH_SYSTEM_PROMPT, build_user_prompt
from app.research.schemas import ResearchReport
from app.utils.logging import logger


class ResearchLLMError(Exception):
    """Base exception for research LLM failures."""
    pass


class LLMKeyMissingError(ResearchLLMError):
    """Raised when OPENAI_API_KEY is not configured."""
    pass


class LLMAPIError(ResearchLLMError):
    """Raised when OpenAI API encounters network, authentication, or rate limit issues."""
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
    Invokes the OpenAI API using structured outputs (beta.chat.completions.parse)
    to generate a strictly validated ResearchReport.
    """
    effective_key = api_key or os.getenv("OPENAI_API_KEY") or settings.openai_api_key
    if not effective_key:
        raise LLMKeyMissingError(
            "OPENAI_API_KEY is missing. The AI Research Layer requires an OpenAI API key "
            "set in the environment (OPENAI_API_KEY) or .env file to generate synthesis reports."
        )

    chosen_model = model or os.getenv("OPENAI_MODEL") or settings.openai_model
    temp = temperature if temperature is not None else settings.openai_temperature
    req_timeout = timeout or settings.openai_timeout

    logger.info(f"Invoking OpenAI structured research synthesis for {ticker} using {chosen_model}")

    try:
        client = OpenAI(api_key=effective_key, timeout=req_timeout)
        user_prompt = build_user_prompt(context_text, ticker, company_name)

        completion = client.beta.chat.completions.parse(
            model=chosen_model,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=ResearchReport,
            temperature=temp,
        )

        message = completion.choices[0].message
        if message.refusal:
            raise LLMResponseParsingError(f"Model refused to generate research report: {message.refusal}")

        parsed_report: Optional[ResearchReport] = message.parsed
        if not parsed_report:
            raise LLMResponseParsingError("Failed to parse structured ResearchReport from model response.")

        # Ensure model identifier is attached
        parsed_report.model_name = chosen_model
        return parsed_report

    except openai.AuthenticationError as e:
        logger.error(f"OpenAI authentication failed: {e}")
        raise LLMAPIError(f"OpenAI Authentication Error: Invalid or expired API key. Details: {e}") from e
    except openai.RateLimitError as e:
        logger.error(f"OpenAI rate limit reached: {e}")
        raise LLMAPIError(f"OpenAI Rate Limit Exceeded: Please check your account quota. Details: {e}") from e
    except openai.APITimeoutError as e:
        logger.error(f"OpenAI request timed out: {e}")
        raise LLMAPIError(f"OpenAI API Request Timeout after {req_timeout}s. Details: {e}") from e
    except openai.APIConnectionError as e:
        logger.error(f"OpenAI network connection failed: {e}")
        raise LLMAPIError(f"OpenAI Connection Error: Unable to reach OpenAI servers. Details: {e}") from e
    except openai.LengthFinishReasonError as e:
        logger.error(f"OpenAI token limit exceeded during report generation: {e}")
        raise LLMResponseParsingError(f"Report generation exceeded context token length. Details: {e}") from e
    except Exception as e:
        if isinstance(e, ResearchLLMError):
            raise
        logger.error(f"Unexpected error during research synthesis: {e}")
        raise LLMAPIError(f"Unexpected error communicating with OpenAI: {e}") from e