"""LangChain LCEL orchestration for code evaluation (no LangGraph)."""
import os
import warnings
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

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

_PLACEHOLDER_KEY = "your_gemini_api_key_here"

# Some Gemini models (e.g. gemini-3.6-flash) use fixed sampling and ignore
# `temperature`, warning once per call. The per-stage temperatures below still
# apply to models that honour them, so keep them and quiet the noise.
warnings.filterwarnings(
    "ignore", message=".*fixed sampling defaults.*", category=UserWarning
)


def _get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to backend/.env "
            f"(expected file: {env_loader.ENV_PATH})."
        )
    if key == _PLACEHOLDER_KEY:
        raise ValueError(
            "GEMINI_API_KEY is still the placeholder value. "
            "Replace it in backend/.env with a real key from "
            "https://aistudio.google.com/app/apikey"
        )
    return key


def _llm(temp: float = 0.2) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        temperature=temp,
        google_api_key=_get_gemini_api_key(),
    )


def _text(msg: Any) -> str:
    """Plain text of a model reply.

    Gemini replies arrive as a list of content blocks under langchain-core 1.x,
    while older versions return a plain string; handle both.
    """
    content = msg.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return str(content)


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
    strategy_plan = _parse_strategy(_text(plan_msg))

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
    refactored = _text(ref_msg).strip()
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
