"""Threat intelligence aggregation package."""

from .aggregator import ThreatIntelligenceAggregator
from .correlator import ThreatCorrelator
from .models import (
    AttackTechnique,
    CorrelatedThreat,
    FeedResult,
    Indicator,
    IndicatorType,
    IntelligenceConfig,
    IntelligenceReport,
    ThreatActorProfile,
    VulnerabilityRecord,
)

__all__ = [
    "AttackTechnique",
    "CorrelatedThreat",
    "FeedResult",
    "Indicator",
    "IndicatorType",
    "IntelligenceConfig",
    "IntelligenceReport",
    "ThreatActorProfile",
    "ThreatIntelligenceAggregator",
    "ThreatCorrelator",
    "VulnerabilityRecord",
]
