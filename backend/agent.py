"""LangChain LCEL orchestration for code evaluation (no LangGraph)."""
import os
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import env_loader  # noqa: F401 — loads backend/.env before reading os.environ
from prompts import (
    EVALUATOR_HUMAN,
    EVALUATOR_SYSTEM,
    PLANNER_HUMAN,
    PLANNER_SYSTEM,
    REFACTORER_HUMAN,
    REFACTORER_SYSTEM,
    SYNTHESIZER_HUMAN,
    SYNTHESIZER_SYSTEM,
)
from schemas import Finding, FindingsList, SynthesizerOutput

_PLACEHOLDER_KEY = "your_openai_api_key_here"


def _get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to backend/.env "
            f"(expected file: {env_loader.ENV_PATH})."
        )
    if key == _PLACEHOLDER_KEY:
        raise ValueError(
            "OPENAI_API_KEY is still the placeholder value. "
            "Replace it in backend/.env with a real key from "
            "https://platform.openai.com/account/api-keys"
        )
    return key


def _llm(temp: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temp,
        api_key=_get_openai_api_key(),
    )


def _parse_strategy(text: str) -> List[str]:
    lines = []
    for raw in text.strip().splitlines():
        line = raw.strip().lstrip("-•*").strip()
        if line:
            lines.append(line)
    return lines[:5] or ["Review security, performance, and clean code."]


def _fmt_findings(findings: List[Finding]) -> str:
    if not findings:
        return "No findings."
    parts = []
    for i, f in enumerate(findings, 1):
        parts.append(
            f"{i}. [{f.severity}] {f.category} @ {f.location}: "
            f"{f.description} (Impact: {f.impact})"
        )
    return "\n".join(parts)


async def run_evaluation(language: str, source_code: str) -> Dict[str, Any]:
    planner = ChatPromptTemplate.from_messages(
        [("system", PLANNER_SYSTEM), ("human", PLANNER_HUMAN)]
    ) | _llm(0.3)
    plan_msg = await planner.ainvoke(
        {"programming_language": language, "source_code": source_code}
    )
    strategy_plan = _parse_strategy(plan_msg.content)

    evaluator = ChatPromptTemplate.from_messages(
        [("system", EVALUATOR_SYSTEM), ("human", EVALUATOR_HUMAN)]
    ) | _llm(0.1).with_structured_output(FindingsList)
    eval_out: FindingsList = await evaluator.ainvoke(
        {
            "programming_language": language,
            "strategy_plan": "\n".join(f"- {s}" for s in strategy_plan),
            "source_code": source_code,
        }
    )
    findings = eval_out.findings

    refactorer = ChatPromptTemplate.from_messages(
        [("system", REFACTORER_SYSTEM), ("human", REFACTORER_HUMAN)]
    ) | _llm(0.2)
    ref_msg = await refactorer.ainvoke(
        {
            "programming_language": language,
            "findings": _fmt_findings(findings),
            "source_code": source_code,
        }
    )
    refactored = ref_msg.content.strip()
    if refactored.startswith("```"):
        refactored = "\n".join(refactored.splitlines()[1:-1]).strip()

    synthesizer = ChatPromptTemplate.from_messages(
        [("system", SYNTHESIZER_SYSTEM), ("human", SYNTHESIZER_HUMAN)]
    ) | _llm(0.2).with_structured_output(SynthesizerOutput)
    synth: SynthesizerOutput = await synthesizer.ainvoke(
        {
            "programming_language": language,
            "strategy_plan": "\n".join(f"- {s}" for s in strategy_plan),
            "findings": _fmt_findings(findings),
            "refactored_code": refactored,
        }
    )

    return {
        "strategy_plan": strategy_plan,
        "findings": [f.model_dump() for f in findings],
        "refactored_code": refactored,
        "quality_score": synth.quality_score,
        "executive_summary": synth.executive_summary,
    }
