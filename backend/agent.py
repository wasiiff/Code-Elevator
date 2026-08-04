"""LangChain LCEL orchestration for code evaluation (no LangGraph).

Two sequential stages rather than four:

    1. analyse    — plan the review and produce findings in one structured call
    2. refactor + score — run concurrently, since scoring rates the submitted
                          code and so does not depend on the refactor

An optional ``on_progress`` callback reports stage transitions so the UI can
show what the pipeline is doing instead of an undifferentiated spinner.
"""
import asyncio
import os
import warnings
from typing import Any, Awaitable, Callable, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

import env_loader  # noqa: F401 — loads backend/.env before reading os.environ
from prompts import (
    ANALYST_HUMAN,
    ANALYST_SYSTEM,
    REFACTORER_HUMAN,
    REFACTORER_SYSTEM,
    SYNTHESIZER_HUMAN,
    SYNTHESIZER_SYSTEM,
)
from schemas import Finding, StrategyAndFindings, SynthesizerOutput

_PLACEHOLDER_KEY = "your_gemini_api_key_here"

ProgressHook = Callable[[Dict[str, Any]], Awaitable[None]]

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


def _clean_strategy(items: List[str]) -> List[str]:
    cleaned = []
    for raw in items:
        line = (raw or "").strip().lstrip("-•*").strip()
        if line:
            cleaned.append(line)
    return cleaned[:5] or ["Review security, performance, and clean code."]


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


def _strip_fences(text: str) -> str:
    out = text.strip()
    if out.startswith("```"):
        out = "\n".join(out.splitlines()[1:-1]).strip()
    return out


async def run_evaluation(
    language: str,
    source_code: str,
    on_progress: Optional[ProgressHook] = None,
) -> Dict[str, Any]:
    async def emit(stage: str, **extra: Any) -> None:
        if on_progress:
            await on_progress({"stage": stage, **extra})

    await emit("analyzing")
    analyst = ChatPromptTemplate.from_messages(
        [("system", ANALYST_SYSTEM), ("human", ANALYST_HUMAN)]
    ) | _llm(0.1).with_structured_output(StrategyAndFindings)
    analysis: StrategyAndFindings = await analyst.ainvoke(
        {"programming_language": language, "source_code": source_code}
    )
    strategy_plan = _clean_strategy(analysis.strategy_plan)
    findings = analysis.findings
    findings_text = _fmt_findings(findings)

    await emit(
        "refactoring",
        findings_count=len(findings),
        strategy_count=len(strategy_plan),
    )

    refactorer = ChatPromptTemplate.from_messages(
        [("system", REFACTORER_SYSTEM), ("human", REFACTORER_HUMAN)]
    ) | _llm(0.2)
    synthesizer = ChatPromptTemplate.from_messages(
        [("system", SYNTHESIZER_SYSTEM), ("human", SYNTHESIZER_HUMAN)]
    ) | _llm(0.2).with_structured_output(SynthesizerOutput)

    ref_msg, synth = await asyncio.gather(
        refactorer.ainvoke(
            {
                "programming_language": language,
                "findings": findings_text,
                "source_code": source_code,
            }
        ),
        synthesizer.ainvoke(
            {
                "programming_language": language,
                "strategy_plan": "\n".join(f"- {s}" for s in strategy_plan),
                "findings": findings_text,
                "source_code": source_code,
            }
        ),
    )

    return {
        "strategy_plan": strategy_plan,
        "findings": [f.model_dump() for f in findings],
        "refactored_code": _strip_fences(_text(ref_msg)),
        "quality_score": synth.quality_score,
        "executive_summary": synth.executive_summary,
    }
