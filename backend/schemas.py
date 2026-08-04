"""Pydantic models for code review requests and responses."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["Critical", "High", "Medium", "Low"]


class Finding(BaseModel):
    category: str
    severity: Severity
    location: str
    description: str
    impact: str


class FindingsList(BaseModel):
    findings: List[Finding] = Field(default_factory=list)


class StrategyAndFindings(BaseModel):
    """Stage 1 output — the review plan and the findings it produced."""

    strategy_plan: List[str] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    programming_language: str
    source_code: str


class SynthesizerOutput(BaseModel):
    executive_summary: str
    quality_score: int = Field(ge=0, le=100)


class ReviewResponse(BaseModel):
    id: Optional[str] = None
    programming_language: str
    source_code: str
    strategy_plan: List[str]
    findings: List[Finding]
    refactored_code: str
    quality_score: int
    executive_summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
