"""Phase 2: recommend a size per brand from the user's measurements.

Needs each brand's size chart per category. Asking "what size do you wear in
brand X?" and comparing charts is often more accurate than measurements alone.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

FitPreference = Literal["slim", "regular", "loose"]


@dataclass(frozen=True)
class BodyMeasurements:
    height_cm: float
    weight_kg: float | None = None
    chest_cm: float | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    foot_length_cm: float | None = None
    # Sizes the user already knows fit them, e.g. {"Levi's": "32"}.
    known_sizes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SizeRecommendation:
    size: str
    confidence: float  # 0-1
    note: str | None = None  # e.g. "Runs small; size up if between sizes"


class SizeRecommender(Protocol):
    def recommend(
        self, body: BodyMeasurements, brand: str, category: str, fit: FitPreference = "regular"
    ) -> SizeRecommendation | None: ...
