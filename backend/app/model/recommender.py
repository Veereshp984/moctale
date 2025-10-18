"""Recommendation service powered by a TensorFlow collaborative filtering model."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import tensorflow as tf


class RecommendationService:
    """Loads a trained model and serves user-level recommendations."""

    def __init__(self, model_dir: str | Path):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "model.keras"
        metadata_path = self.model_dir / "metadata.json"

        if not self.model_path.exists():
            raise FileNotFoundError(f"Unable to locate saved model at {self.model_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file missing at {metadata_path}")

        with metadata_path.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)

        self.user_mapping: Dict[str, int] = metadata.get("user_mapping", {})
        self.item_mapping: Dict[str, int] = metadata.get("item_mapping", {})
        self._reverse_item_mapping: Dict[int, str] = {index: item_id for item_id, index in self.item_mapping.items()}

        user_interactions = metadata.get("user_interactions", {})
        self.user_interactions: Dict[str, set[str]] = {
            user_id: set(items) for user_id, items in user_interactions.items()
        }

        item_popularity = metadata.get("item_popularity", [])
        self.popular_items: List[Tuple[str, float]] = self._normalise_popularity(item_popularity)

        self.model = tf.keras.models.load_model(self.model_path)
        self._all_item_indices = np.arange(len(self.item_mapping), dtype=np.int32)

    @staticmethod
    def _normalise_popularity(raw_popularity: Sequence[object]) -> List[Tuple[str, float]]:
        normalised: List[Tuple[str, float]] = []
        for entry in raw_popularity:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                item_id, score = entry[0], float(entry[1])
            elif isinstance(entry, dict):
                item_id = entry.get("item_id")
                score = float(entry.get("score", 0.0)) if item_id is not None else 0.0
            else:
                continue
            if item_id is not None:
                normalised.append((str(item_id), float(score)))
        normalised.sort(key=lambda item: item[1], reverse=True)
        return normalised

    def recommend_for_user(self, user_id: str, limit: int = 10) -> Tuple[List[str], bool]:
        """Return a list of recommended item IDs for the provided user.

        The boolean flag indicates whether popularity fallback logic was used when
        generating the response (e.g. unknown user or insufficient personalised items).
        """

        if limit <= 0:
            return [], True

        if user_id not in self.user_mapping:
            return self._fallback_recommendations(limit), True

        user_idx = self.user_mapping[user_id]
        exclude_items = set(self.user_interactions.get(user_id, set()))

        user_vector = np.full_like(self._all_item_indices, fill_value=user_idx)
        predictions = self.model.predict(
            {
                "user_id": user_vector,
                "item_id": self._all_item_indices,
            },
            verbose=0,
        ).reshape(-1)

        ranked_positions = np.argsort(predictions)[::-1]
        recommendations: List[str] = []
        for position in ranked_positions:
            item_idx = int(self._all_item_indices[position])
            item_id = self._reverse_item_mapping.get(item_idx)
            if item_id is None or item_id in exclude_items:
                continue
            recommendations.append(item_id)
            if len(recommendations) == limit:
                break

        fallback_used = len(recommendations) < limit
        if fallback_used:
            already_suggested = exclude_items.union(recommendations)
            recommendations.extend(self._fallback_recommendations(limit - len(recommendations), already_suggested))

        return recommendations[:limit], fallback_used

    def _fallback_recommendations(
        self,
        limit: int,
        exclude: Iterable[str] | None = None,
    ) -> List[str]:
        if limit <= 0:
            return []
        exclude_set = set(exclude or [])
        results: List[str] = []
        for item_id, _ in self.popular_items:
            if item_id in exclude_set:
                continue
            results.append(item_id)
            if len(results) == limit:
                break
        return results
