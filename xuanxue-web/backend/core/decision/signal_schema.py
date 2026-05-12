"""
统一信号模型
Unified signal schema for decision support.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class ModuleSignal:
    module: str
    layer: str
    baseline_strength: float
    timing_window: float
    external_support: float
    internal_resistance: float
    risk_exposure: float
    certainty: float
    actionability: float
    direction_score: float
    rationale: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedEnergyVector:
    decision_type: str
    signals: List[ModuleSignal]
    aggregate: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_type": self.decision_type,
            "signals": [signal.to_dict() for signal in self.signals],
            "aggregate": self.aggregate,
        }
