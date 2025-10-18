"""Utilities for ingesting user interaction data and preparing training samples."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import numpy as np

DEFAULT_EVENT_WEIGHTS: Mapping[str, float] = {
    "like": 1.0,
    "playlist_add": 1.5,
}


@dataclass(frozen=True)
class Interaction:
    """Normalized representation of a user's interaction with an item."""

    user_id: str
    item_id: str
    event_type: str
    weight: float

    @classmethod
    def from_raw(
        cls,
        payload: Mapping[str, str],
        event_weights: Mapping[str, float] | None = None,
    ) -> "Interaction":
        if "user_id" not in payload or "item_id" not in payload or "event_type" not in payload:
            missing = {key for key in ("user_id", "item_id", "event_type") if key not in payload}
            raise ValueError(f"Interaction payload missing fields: {missing}")
        event = payload["event_type"]
        weights = dict(DEFAULT_EVENT_WEIGHTS)
        if event_weights:
            weights.update(event_weights)
        weight = weights.get(event)
        if weight is None:
            raise ValueError(f"Unsupported event type '{event}' encountered during normalization")
        return cls(
            user_id=str(payload["user_id"]),
            item_id=str(payload["item_id"]),
            event_type=event,
            weight=float(weight),
        )


def load_interactions(
    path: str | Path,
    event_weights: Mapping[str, float] | None = None,
) -> List[Interaction]:
    """Load interactions from a JSON Lines or JSON file."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Interaction file not found: {path}")

    content = path.read_text().strip()
    if not content:
        return []

    def _read_payloads(text: str) -> Iterable[Mapping[str, str]]:
        if text.lstrip().startswith("["):
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("Expected a list of interaction objects in JSON file")
            yield from data
        else:
            for line in text.splitlines():
                if line.strip():
                    yield json.loads(line)

    return normalize_interactions(_read_payloads(content), event_weights)


def normalize_interactions(
    raw_interactions: Iterable[Mapping[str, str]],
    event_weights: Mapping[str, float] | None = None,
) -> List[Interaction]:
    """Convert raw interaction payloads to :class:`Interaction` objects."""

    interactions: List[Interaction] = []
    for payload in raw_interactions:
        interactions.append(Interaction.from_raw(payload, event_weights))
    return interactions


def build_id_mappings(
    interactions: Sequence[Interaction],
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Create stable index mappings for users and items."""

    user_ids = sorted({interaction.user_id for interaction in interactions})
    item_ids = sorted({interaction.item_id for interaction in interactions})
    user_mapping = {user_id: idx for idx, user_id in enumerate(user_ids)}
    item_mapping = {item_id: idx for idx, item_id in enumerate(item_ids)}
    return user_mapping, item_mapping


def generate_training_samples(
    interactions: Sequence[Interaction],
    user_mapping: Mapping[str, int],
    item_mapping: Mapping[str, int],
    *,
    num_negatives: int = 4,
    seed: int | None = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Produce positive and negative samples for implicit feedback training."""

    if not interactions:
        return (np.array([], dtype=np.int32), np.array([], dtype=np.int32), np.array([], dtype=np.float32))

    rng = random.Random(seed)
    all_item_ids = list(item_mapping.keys())
    user_history: Dict[str, set[str]] = {}
    for interaction in interactions:
        user_history.setdefault(interaction.user_id, set()).add(interaction.item_id)

    user_indices: List[int] = []
    item_indices: List[int] = []
    labels: List[float] = []

    for interaction in interactions:
        user_idx = user_mapping[interaction.user_id]
        item_idx = item_mapping[interaction.item_id]
        user_indices.append(user_idx)
        item_indices.append(item_idx)
        labels.append(1.0)

        available_negatives = [item_id for item_id in all_item_ids if item_id not in user_history[interaction.user_id]]
        if not available_negatives:
            continue
        if num_negatives >= len(available_negatives):
            negatives = available_negatives
        else:
            negatives = rng.sample(available_negatives, num_negatives)
        for negative_item_id in negatives:
            negative_item_idx = item_mapping[negative_item_id]
            user_indices.append(user_idx)
            item_indices.append(negative_item_idx)
            labels.append(0.0)

    return (
        np.asarray(user_indices, dtype=np.int32),
        np.asarray(item_indices, dtype=np.int32),
        np.asarray(labels, dtype=np.float32),
    )


def compute_item_popularity(interactions: Sequence[Interaction]) -> List[Tuple[str, float]]:
    """Aggregate interactions into a popularity ranking."""

    scores: MutableMapping[str, float] = {}
    for interaction in interactions:
        scores[interaction.item_id] = scores.get(interaction.item_id, 0.0) + interaction.weight
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def build_user_history(interactions: Sequence[Interaction]) -> Dict[str, List[str]]:
    """Return a mapping of user IDs to unique item IDs they have interacted with."""

    history: Dict[str, set[str]] = {}
    for interaction in interactions:
        history.setdefault(interaction.user_id, set()).add(interaction.item_id)
    return {user_id: sorted(items) for user_id, items in history.items()}


def to_serializable_interactions(interactions: Sequence[Interaction]) -> List[Dict[str, object]]:
    """Helper to convert interactions back to serializable dictionaries."""

    return [
        {
            "user_id": interaction.user_id,
            "item_id": interaction.item_id,
            "event_type": interaction.event_type,
            "weight": interaction.weight,
        }
        for interaction in interactions
    ]
