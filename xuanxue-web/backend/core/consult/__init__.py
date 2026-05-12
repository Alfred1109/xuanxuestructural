"""Unified consultation package."""

from .engine import ConsultationEngine, consultation_engine
from .models import TraceGraph, TraceStep, UnifiedConsultRequest
from .router import infer_consult_modules, normalize_matter_type, normalize_purpose
from .summarizers import (
    generate_simple_analysis,
    summarize_bazi_result,
    summarize_liuyao_result,
    summarize_meihua_result,
    summarize_qimen_result,
    summarize_zeri_result,
)
from .trace import build_trace_graph

__all__ = [
    "ConsultationEngine",
    "TraceGraph",
    "TraceStep",
    "UnifiedConsultRequest",
    "build_trace_graph",
    "consultation_engine",
    "generate_simple_analysis",
    "infer_consult_modules",
    "normalize_matter_type",
    "normalize_purpose",
    "summarize_bazi_result",
    "summarize_liuyao_result",
    "summarize_meihua_result",
    "summarize_qimen_result",
    "summarize_zeri_result",
]
