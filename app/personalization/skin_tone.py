"""Phase 2: detect skin tone from a photo and score product colours against it.

Plan: find the face (e.g. MediaPipe), sample cheek/forehead skin, convert to
CIELAB, place it on the 10-shade Monk Skin Tone scale and estimate undertone.
Lighting skews this a lot, so the app must show the result and let the user
correct it. Product colours come from the product image after background removal.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

Undertone = Literal["warm", "cool", "neutral"]


@dataclass(frozen=True)
class SkinTone:
    monk_scale: int  # 1 (lightest) to 10 (deepest)
    undertone: Undertone
    confidence: float  # 0-1; ask the user to confirm when low


class SkinToneDetector(Protocol):
    def detect(self, photo: bytes) -> SkinTone: ...


class ColorMatcher(Protocol):
    def score(self, tone: SkinTone, product_colors: Sequence[str]) -> float:
        """0-1: how well the product's colours suit this skin tone."""
        ...
