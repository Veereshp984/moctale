"""Unit tests for the data preparation utilities."""
from __future__ import annotations

import numpy as np

from app.data import pipeline


def _sample_raw_interactions() -> list[dict[str, str]]:
    return [
        {"user_id": "alice", "item_id": "track_1", "event_type": "like"},
        {"user_id": "alice", "item_id": "track_2", "event_type": "playlist_add"},
        {"user_id": "bob", "item_id": "track_2", "event_type": "like"},
        {"user_id": "carol", "item_id": "track_3", "event_type": "playlist_add"},
    ]


def test_generate_training_samples_produces_balanced_dataset() -> None:
    interactions = pipeline.normalize_interactions(_sample_raw_interactions())
    user_mapping, item_mapping = pipeline.build_id_mappings(interactions)

    user_indices, item_indices, labels = pipeline.generate_training_samples(
        interactions,
        user_mapping,
        item_mapping,
        num_negatives=2,
        seed=123,
    )

    assert len(user_indices) == len(item_indices) == len(labels)
    positives = np.sum(labels == 1.0)
    negatives = np.sum(labels == 0.0)
    assert positives == len(interactions)
    assert negatives >= positives  # ensures negative sampling occurred
    assert set(np.unique(user_indices)) == set(user_mapping.values())
    assert set(np.unique(item_indices)) <= set(item_mapping.values())


def test_popularity_scores_are_sorted_descending() -> None:
    interactions = pipeline.normalize_interactions(_sample_raw_interactions())
    popularity = pipeline.compute_item_popularity(interactions)

    scores = [score for _, score in popularity]
    assert scores == sorted(scores, reverse=True)
    # playlist additions should carry more weight than likes when counts are equal
    assert popularity[0][0] in {"track_2", "track_3"}
