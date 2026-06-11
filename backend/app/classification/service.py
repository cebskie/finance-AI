import json
import logging
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from app.core.config import Settings

logger = logging.getLogger(__name__)

UNKNOWN_DOCUMENT_TYPE = "unknown"


@dataclass(frozen=True)
class PageClassificationResult:
    document_type: str
    label: str
    confidence: float
    metadata: dict


class PageClassificationService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.rules = self._load_rules()

    def classify_page(self, *, text: str, ocr_confidence: float) -> PageClassificationResult:
        normalized_text = " ".join(text.lower().split())
        scores = [self._score_rule(rule, normalized_text) for rule in self.rules["document_types"]]
        scores.sort(key=lambda item: item["score"], reverse=True)
        best = scores[0] if scores else None
        total_positive_score = sum(max(item["score"], 0.0) for item in scores)

        if not best or best["score"] < best["minimum_score"] or total_positive_score <= 0:
            return self._unknown(scores=scores, ocr_confidence=ocr_confidence)

        rule_confidence = best["score"] / total_positive_score
        confidence = max(0.0, min(1.0, rule_confidence * (ocr_confidence / 100)))
        if confidence < self.settings.classification_min_confidence:
            return self._unknown(scores=scores, ocr_confidence=ocr_confidence)

        metadata = {
            "classifier": "keyword_rules",
            "rules_source": self._rules_source(),
            "ocr_confidence": round(ocr_confidence, 2),
            "rule_confidence": round(rule_confidence, 4),
            "matched_keywords": best["matched_keywords"],
            "matched_negative_keywords": best["matched_negative_keywords"],
            "candidate_scores": scores,
        }
        return PageClassificationResult(
            document_type=best["type"],
            label=best["label"],
            confidence=confidence,
            metadata=metadata,
        )

    def _score_rule(self, rule: dict, normalized_text: str) -> dict:
        keyword_weight = float(self.rules.get("keyword_weight", 1.0))
        negative_keyword_weight = float(self.rules.get("negative_keyword_weight", -0.5))
        matched_keywords = [
            keyword
            for keyword in rule.get("keywords", [])
            if keyword.lower() in normalized_text
        ]
        matched_negative_keywords = [
            keyword
            for keyword in rule.get("negative_keywords", [])
            if keyword.lower() in normalized_text
        ]
        score = (len(matched_keywords) * keyword_weight) + (
            len(matched_negative_keywords) * negative_keyword_weight
        )
        return {
            "type": rule["type"],
            "label": rule["label"],
            "score": max(score, 0.0),
            "minimum_score": float(rule.get("minimum_score", 1.0)),
            "matched_keywords": matched_keywords,
            "matched_negative_keywords": matched_negative_keywords,
        }

    def _unknown(self, *, scores: list[dict], ocr_confidence: float) -> PageClassificationResult:
        return PageClassificationResult(
            document_type=UNKNOWN_DOCUMENT_TYPE,
            label="unknown",
            confidence=0.0,
            metadata={
                "classifier": "keyword_rules",
                "rules_source": self._rules_source(),
                "ocr_confidence": round(ocr_confidence, 2),
                "candidate_scores": scores,
                "reason": "no_candidate_met_confidence_threshold",
            },
        )

    def _load_rules(self) -> dict:
        rules_path = self._rules_source()
        with open(rules_path, encoding="utf-8") as rules_file:
            return json.load(rules_file)

    def _rules_source(self) -> str:
        if self.settings.classification_rules_path:
            return str(Path(self.settings.classification_rules_path))
        return str(files("app.classification").joinpath("default_rules.json"))
