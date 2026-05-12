from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class UnifiedConsultRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    gender: Optional[str] = Field(None, min_length=1, max_length=1)
    purpose: Optional[str] = Field(None, max_length=20)
    matter_type: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=80)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in ("男", "女"):
            raise ValueError("gender must be '男' or '女'")
        return value


@dataclass
class TraceStep:
    id: str
    label: str
    detail: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    rule: str = ""
    outputs: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    derivation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "detail": self.detail,
            "inputs": self.inputs,
            "rule": self.rule,
            "outputs": self.outputs,
            "evidence": self.evidence,
            "formulas": self.formulas,
            "derivation": self.derivation,
        }


@dataclass
class TraceGraph:
    steps: List[TraceStep]
    mermaid: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "mermaid": self.mermaid,
        }
