"""
统一系统引擎
Backward-compatible exports for the unified consultation package.
"""

from .consult.engine import (
    ConsultationEngine,
    build_consult_context,
    consultation_engine,
    fallback_consultation_summary,
    has_complete_birth_payload,
)
from .consult.models import TraceGraph, TraceStep, UnifiedConsultRequest
from .consult.router import MODULE_LABELS, infer_consult_modules, module_label, normalize_matter_type, normalize_purpose
from .consult.summarizers import (
    generate_simple_analysis,
    get_balance_advice,
    summarize_bazi_result,
    summarize_liuyao_result,
    summarize_meihua_result,
    summarize_qimen_result,
    summarize_zeri_result,
)
from .consult.trace import build_trace_graph
from .llm_helper import llm_helper

__all__ = [
    "ConsultationEngine",
    "MODULE_LABELS",
    "TraceGraph",
    "TraceStep",
    "UnifiedConsultRequest",
    "build_consult_context",
    "build_trace_graph",
    "consultation_engine",
    "fallback_consultation_summary",
    "generate_simple_analysis",
    "get_balance_advice",
    "has_complete_birth_payload",
    "infer_consult_modules",
    "llm_helper",
    "module_label",
    "normalize_matter_type",
    "normalize_purpose",
    "summarize_bazi_result",
    "summarize_liuyao_result",
    "summarize_meihua_result",
    "summarize_qimen_result",
    "summarize_zeri_result",
]
