import json
import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, ValidationError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import ModelProvider, ModelSelectionConfig

# Configure module logger
logger = logging.getLogger(__name__)

# Type variable for Pydantic models used in structured outputs
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    Wrapper for LLM interactions (e.g., OpenAI/Anthropic) to handle prompt engineering
    and structured output parsing.
    
    This client supports the Deep Research architecture by providing robust methods
    for generating both free-form text (for Answer Generation) and structured data
    (for Query Planning, Memory Management, and Information Acquisition).
    """

    def __init__(self, config: ModelSelectionConfig):
        """
        Initialize the LLM client with the specified configuration.

        Args:
            config (ModelSelectionConfig): Configuration object containing provider
                                           and model details.
        """
        self.config = config
        self.client = self._initialize_client()
        # Fallback to 'gpt-4o' if model_name is not explicitly defined in config
        self.model_name = getattr(config, "model_name", "gpt-4o")

    def _initialize_client(self) -> AsyncOpenAI:
        """
        Initializes the underlying API client based on the configured provider.

        Returns:
            AsyncOpenAI: An initialized OpenAI-compatible client.
        
        Raises:
            ValueError: If the provider is not supported or configuration is missing.
        """
        provider = self.config.provider

        if provider == ModelProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not set. Client may fail if not using local auth.")
            return AsyncOpenAI(api_key=api_key)

        elif provider == ModelProvider.AZURE:
            return AsyncOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            )

        elif provider == ModelProvider.LOCAL:
            # Support for local inference servers (e.g., vLLM, Ollama) compatible with OpenAI API
            return AsyncOpenAI(
                base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1"),
                api_key="mock-key",
            )

        elif provider == ModelProvider.ANTHROPIC:
            # Note: Native Anthropic client requires 'anthropic' package.
            # If not present in dependencies, this branch would need an adapter or raise error.
            raise NotImplementedError(
                "Anthropic provider requires 'anthropic' package or OpenAI-compatible proxy."
            )

        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generates a text completion from the LLM. 
        Used primarily for the 'Answer Generation' component.

        Args:
            messages: List of message dictionaries (role, content).
            temperature: Sampling temperature (default 0.7).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional arguments passed to the API.

        Returns:
            str: The generated text content.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    @retry(
        retry=retry_if_exception_type((OpenAIError, ValidationError, json.JSONDecodeError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def get_structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> T:
        """
        Generates a structured response parsed into a Pydantic model.
        Critical for 'Query Planning' (plans), 'Information Acquisition' (queries),
        and 'Memory Management' (structured summaries).

        Args:
            messages: List of message dictionaries.
            response_model: The Pydantic model class to enforce structure.
            temperature: Sampling temperature (default 0.0 for deterministic structure).
            **kwargs: Additional arguments passed to the API.

        Returns:
            T: An instance of the provided response_model.
        """
        try:
            # Uses OpenAI's beta parse method for reliable structured outputs
            response = await self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=messages,
                response_format=response_model,
                temperature=temperature,
                **kwargs,
            )

            parsed_response = response.choices[0].message.parsed
            
            if parsed_response is None:
                refusal = response.choices[0].message.refusal
                raise ValueError(f"Model refused to generate structured output: {refusal}")

            return parsed_response

        except Exception as e:
            logger.error(f"Error generating structured completion: {e}")
            raise

    async def close(self):
        """
        Closes the underlying HTTP client session.
        """
        await self.client.close()