from __future__ import annotations

from typing import Any, Literal, TypeVar, TypedDict

from litellm import completion 
from pydantic import BaseModel, ValidationError


ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)
     

class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMClientError(RuntimeError):
    """Erro base relacionado ao processamento da resposta do modelo."""


class EmptyLLMResponseError(LLMClientError):
    """O modelo não retornou conteúdo textual."""


class StructuredOutputValidationError(LLMClientError):
    """O conteúdo retornado não corresponde ao schema esperado."""

class LLMClient:
    
    
    def __init__(self, model: str, temperature: float):

        if not model.strip():
            raise ValueError("Model cannot be empty")
        
        self.model = model
        self.temperature = temperature
        
        
    @staticmethod
    def system_message(content: str) -> Message:
        return {
            "role": "system",
            "content": content,
        }

    @staticmethod
    def user_message(content: str) -> Message:
        return {
            "role": "user",
            "content": content,
        }

    @staticmethod
    def assistant_message(content: str) -> Message:
        return {
            "role": "assistant",
            "content": content,
        }
    
    def complete(self, messages, response_schema: type[ResponseModelT]) -> ResponseModelT:


        request_parameters: dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "response_format": response_schema, 
            "temperature": self.temperature

        }


        response = completion(**request_parameters)

        if not response.choices:
            raise EmptyLLMResponseError("O modelo retornou sem choices")

        content = response.choices[0].message.content

        if not isinstance(content, str) or not content.strip():
            raise EmptyLLMResponseError("Mensagem vazia")

        try: 
            return response_schema.model_validate_json(content)
        except ValidationError as e:
            content_preview =  content[:1_000]

            raise StructuredOutputValidationError("Model response does not match the expected schema." f"Response Preview: {content_preview!r}") from e
