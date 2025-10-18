"""Training utilities for the collaborative filtering recommendation model."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import tensorflow as tf

from app.data import pipeline


def build_model(
    num_users: int,
    num_items: int,
    *,
    embedding_dim: int = 32,
    learning_rate: float = 0.001,
    seed: int | None = 42,
) -> tf.keras.Model:
    """Construct a simple neural collaborative filtering model."""

    user_input = tf.keras.Input(shape=(), dtype=tf.int32, name="user_id")
    item_input = tf.keras.Input(shape=(), dtype=tf.int32, name="item_id")

    user_embedding = tf.keras.layers.Embedding(
        num_users,
        embedding_dim,
        embeddings_initializer=tf.keras.initializers.GlorotUniform(seed=seed),
        name="user_embedding",
    )(user_input)
    item_embedding = tf.keras.layers.Embedding(
        num_items,
        embedding_dim,
        embeddings_initializer=tf.keras.initializers.GlorotUniform(seed=seed),
        name="item_embedding",
    )(item_input)

    user_vec = tf.keras.layers.Flatten()(user_embedding)
    item_vec = tf.keras.layers.Flatten()(item_embedding)

    x = tf.keras.layers.Concatenate()([user_vec, item_vec])
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    x = tf.keras.layers.Dense(32, activation="relu")(x)
    output = tf.keras.layers.Dense(1, activation="sigmoid", name="score")(x)

    model = tf.keras.Model(inputs={"user_id": user_input, "item_id": item_input}, outputs=output)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate), loss="binary_crossentropy")
    return model


def build_training_dataset(
    user_indices: np.ndarray,
    item_indices: np.ndarray,
    labels: np.ndarray,
    *,
    batch_size: int,
    seed: int | None = 42,
) -> tf.data.Dataset:
    dataset = tf.data.Dataset.from_tensor_slices(
        (
            {
                "user_id": user_indices,
                "item_id": item_indices,
            },
            labels,
        )
    )
    dataset = dataset.shuffle(buffer_size=len(labels), seed=seed, reshuffle_each_iteration=True)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset


def train_model_from_interactions(
    interactions: Sequence[pipeline.Interaction],
    *,
    model_dir: str | Path,
    embedding_dim: int = 32,
    epochs: int = 10,
    batch_size: int = 256,
    learning_rate: float = 0.001,
    num_negatives: int = 4,
    seed: int | None = 42,
) -> tf.keras.Model:
    """Train the collaborative filtering model and persist artifacts."""

    if not interactions:
        raise ValueError("Cannot train model without interactions")

    user_mapping, item_mapping = pipeline.build_id_mappings(interactions)
    if not user_mapping or not item_mapping:
        raise ValueError("Insufficient unique users or items for training")

    user_indices, item_indices, labels = pipeline.generate_training_samples(
        interactions,
        user_mapping,
        item_mapping,
        num_negatives=num_negatives,
        seed=seed,
    )
    if len(labels) == 0:
        raise ValueError("Failed to generate training samples")

    dataset = build_training_dataset(
        user_indices,
        item_indices,
        labels,
        batch_size=min(batch_size, len(labels)),
        seed=seed,
    )

    model = build_model(
        len(user_mapping),
        len(item_mapping),
        embedding_dim=embedding_dim,
        learning_rate=learning_rate,
        seed=seed,
    )
    model.fit(dataset, epochs=epochs, verbose=0)

    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "model.keras"
    if model_path.exists():
        model_path.unlink()
    model.save(model_path)

    metadata = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "user_mapping": user_mapping,
        "item_mapping": item_mapping,
        "user_interactions": pipeline.build_user_history(interactions),
        "item_popularity": [
            {"item_id": item_id, "score": score}
            for item_id, score in pipeline.compute_item_popularity(interactions)
        ],
        "event_weights": dict(pipeline.DEFAULT_EVENT_WEIGHTS),
        "training": {
            "embedding_dim": embedding_dim,
            "epochs": epochs,
            "batch_size": min(batch_size, len(labels)),
            "learning_rate": learning_rate,
            "num_negatives": num_negatives,
            "seed": seed,
            "num_samples": int(len(labels)),
        },
    }

    metadata_path = model_dir / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    return model


def train_from_file(
    data_path: str | Path,
    *,
    model_dir: str | Path,
    embedding_dim: int = 32,
    epochs: int = 10,
    batch_size: int = 256,
    learning_rate: float = 0.001,
    num_negatives: int = 4,
    seed: int | None = 42,
) -> tf.keras.Model:
    interactions = pipeline.load_interactions(data_path)
    return train_model_from_interactions(
        interactions,
        model_dir=model_dir,
        embedding_dim=embedding_dim,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        num_negatives=num_negatives,
        seed=seed,
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the recommendation model from interaction data")
    parser.add_argument("--data-path", type=str, required=True, help="Path to JSON/JSONL interactions file")
    parser.add_argument(
        "--model-dir",
        type=str,
        default="backend/models/latest",
        help="Directory to store the trained model artifacts",
    )
    parser.add_argument("--embedding-dim", type=int, default=32, help="Number of latent factors for embeddings")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=256, help="Training batch size")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Optimizer learning rate")
    parser.add_argument(
        "--num-negatives",
        type=int,
        default=4,
        help="Number of negative samples to generate per positive interaction",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    train_from_file(
        data_path=args.data_path,
        model_dir=args.model_dir,
        embedding_dim=args.embedding_dim,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_negatives=args.num_negatives,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
