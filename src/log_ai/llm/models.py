from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator
import re 


class MaskingInstruction(BaseModel):
    """
    Uma instrução de masking aceita pelo Drain3
    
    Exemplo:
       {
           "regex_pattern":"((?<=[^A-Za-z0-9])|^)([\\-\\+]?\\d+)((?=[^A-Za-z0-9])|$)", 
           "mask_with": "NUM"
        },
    
    """
    
    modelconfig = ConfigDict(extra="forbid")
    
    regex_pattern: str = Field(
        min_length=1, 
        description="Expressao regular python usada para localizar valores variáveis"
    )
    
    mask_with: str = Field(
        min_length=1,
        description="Nome atribuído ao valor mascarado, por exemplo, IP UUID OU NUM"
    )
    
    @field_validator("regex_pattern")
    @classmethod
    def validate_regex_pattern(cls, value:str) -> str:
        try:
            re.compile(value)
        except re.error as e:
            raise ValueError(f"Invalid python regular expression {e}") from e 
        return value 
        
class DrainConfig(BaseModel):
    """
    Configuração sobre o Masking Seção do Drain 3
    
    """
    
    model_config = ConfigDict(extra="forbid")
    
    masking: list[MaskingInstruction]
    mask_prefix: str = Field(default="<", min_length=1)
    mask_suffix: str = Field(default=">", min_length=1)