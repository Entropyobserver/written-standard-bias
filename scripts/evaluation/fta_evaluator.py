import json
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .base_evaluator import BaseEvaluator


LANG_KEY_MAP = {
    "en": None,
    "de": "de",
    "fr": "fr",
    "nl": "nl",
    "no": "no",
}


class FTAEvaluator(BaseEvaluator):
    def __init__(
        self,
        glossary_path: str,
        src_lang: str = "en",
        tgt_lang: str = "no",
        use_comet: bool = False,
    ):
        super().__init__(use_comet=use_comet)
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

        with open(glossary_path, encoding="utf-8") as f:
            glossary = json.load(f)

        self.term_pairs = self._load_term_pairs(glossary, src_lang, tgt_lang)
        self.target_to_sources = self._build_target_index(self.term_pairs)

    @staticmethod
    def _normalize_term(term: str) -> str:
        return " ".join(term.lower().split())

    def _load_term_pairs(self, glossary, src_lang: str, tgt_lang: str) -> List[Tuple[str, str]]:
        """
        Supports the glossary formats used in this project:
        - [{"en": "...", "no": "..."}]
        - {"English term": "Norwegian term"}
        - {"English term": {"no": "...", "de": "..."}}
        """
        src_key = LANG_KEY_MAP.get(src_lang) or src_lang
        tgt_key = tgt_lang
        pairs = []

        if isinstance(glossary, list):
            for item in glossary:
                source_term = item.get(src_key) or item.get(src_lang) or item.get("en")
                target_term = item.get(tgt_key)
                if source_term and target_term:
                    pairs.append(
                        (self._normalize_term(source_term), self._normalize_term(target_term))
                    )
            return pairs

        for en_term, translations in glossary.items():
            if isinstance(translations, str):
                source_term = en_term
                target_term = translations
            else:
                source_term = en_term if src_lang == "en" else translations.get(src_key, en_term)
                target_term = translations.get(tgt_key, "")

            if source_term and target_term:
                pairs.append(
                    (self._normalize_term(source_term), self._normalize_term(target_term))
                )

        return pairs

    def _terms_in(self, source: str) -> List[Tuple[str, str]]:
        source_lower = source.lower()
        return [
            (source_term, target_term)
            for source_term, target_term in self.term_pairs
            if source_term in source_lower
        ]

    @staticmethod
    def _build_target_index(term_pairs: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        target_to_sources = defaultdict(list)
        for source_term, target_term in term_pairs:
            target_to_sources[target_term].append(source_term)
        return dict(target_to_sources)

    def _target_terms_in(self, prediction: str) -> List[str]:
        prediction_lower = prediction.lower()
        return [
            target_term
            for target_term in self.target_to_sources
            if target_term in prediction_lower
        ]

    def compute_fta_single(
        self,
        source: str,
        prediction: str,
    ) -> Optional[float]:
        terms = self._terms_in(source)
        if not terms:
            return None

        prediction_lower = prediction.lower()
        hits = sum(1 for _, target_term in terms if target_term in prediction_lower)
        return hits / len(terms)

    def compute_term_metrics_single(self, source: str, prediction: str) -> Dict[str, float]:
        source_terms = self._terms_in(source)
        predicted_terms = self._target_terms_in(prediction)

        prediction_lower = prediction.lower()
        source_lower = source.lower()

        hits = sum(1 for _, target_term in source_terms if target_term in prediction_lower)
        false_positives = sum(
            1
            for target_term in predicted_terms
            if not any(source_term in source_lower for source_term in self.target_to_sources[target_term])
        )

        recall = hits / len(source_terms) if source_terms else 0.0
        precision = (len(predicted_terms) - false_positives) / len(predicted_terms) if predicted_terms else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

        return {
            "term_recall": recall,
            "term_precision": precision,
            "term_f1": f1,
            "term_hits": hits,
            "term_source_instances": len(source_terms),
            "term_prediction_instances": len(predicted_terms),
            "term_false_positives": false_positives,
        }

    def compute_fta(
        self,
        sources: List[str],
        predictions: List[str],
    ) -> Dict[str, float]:
        recall_scores = []
        total_hits = 0
        source_instances = 0
        prediction_instances = 0
        false_positives = 0
        source_sentences = 0
        prediction_sentences = 0

        for source, prediction in zip(sources, predictions):
            metrics = self.compute_term_metrics_single(source, prediction)

            total_hits += metrics["term_hits"]
            source_instances += metrics["term_source_instances"]
            prediction_instances += metrics["term_prediction_instances"]
            false_positives += metrics["term_false_positives"]

            if metrics["term_source_instances"]:
                source_sentences += 1
                recall_scores.append(metrics["term_recall"])
            if metrics["term_prediction_instances"]:
                prediction_sentences += 1

        if not sources:
            return {
                "fta": 0.0,
                "fta_mean_sentence": 0.0,
                "fta_coverage": 0.0,
                "fta_sentences": 0,
                "fta_terms_total": 0,
                "term_recall": 0.0,
                "term_precision": 0.0,
                "term_f1": 0.0,
                "term_source_coverage": 0.0,
                "term_prediction_coverage": 0.0,
                "term_source_instances": 0,
                "term_prediction_instances": 0,
                "term_hits": 0,
                "term_false_positives": 0,
            }

        term_recall = total_hits / source_instances if source_instances else 0.0
        true_prediction_terms = prediction_instances - false_positives
        term_precision = true_prediction_terms / prediction_instances if prediction_instances else 0.0
        term_f1 = (
            2 * term_precision * term_recall / (term_precision + term_recall)
            if term_precision + term_recall
            else 0.0
        )

        return {
            "fta": term_recall,
            "fta_mean_sentence": sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
            "fta_coverage": source_sentences / len(sources),
            "fta_sentences": source_sentences,
            "fta_terms_total": source_instances,
            "term_recall": term_recall,
            "term_precision": term_precision,
            "term_f1": term_f1,
            "term_source_coverage": source_sentences / len(sources),
            "term_prediction_coverage": prediction_sentences / len(sources),
            "term_source_instances": source_instances,
            "term_prediction_instances": prediction_instances,
            "term_hits": total_hits,
            "term_false_positives": false_positives,
        }

    def evaluate_all(
        self,
        sources: List[str],
        predictions: List[str],
        references: List[str],
    ) -> Dict[str, float]:
        metrics = super().evaluate_all(sources, predictions, references)
        metrics.update(self.compute_fta(sources, predictions))
        return metrics
