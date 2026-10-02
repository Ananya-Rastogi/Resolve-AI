"""
Stratified dataset splitting for customer support ticket evaluation baseline.
Splits data/tickets_training.csv into data/train.csv (80%) and data/test.csv (20%).
"""
from pathlib import Path
from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split


def create_stratified_split(
    input_path: Path,
    train_path: Path,
    test_path: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create a reproducible, stratified train/test split based on joint (topic, sentiment) strata.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Source dataset not found at: {input_path}")

    df = pd.read_csv(input_path)

    # Validate required columns
    expected_cols = {"text", "topic", "sentiment"}
    if not expected_cols.issubset(set(df.columns)):
        raise ValueError(f"Dataset missing required columns. Expected {expected_cols}, got {list(df.columns)}")

    # Create joint stratum key for balanced stratification
    strata = df["topic"].astype(str) + "_" + df["sentiment"].astype(str)

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=strata,
    )

    # Ensure output directory exists
    train_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV without index or temporary strata
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    return train_df, test_df


def get_default_paths() -> Tuple[Path, Path, Path]:
    """Return default project paths for datasets."""
    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "data" / "tickets_training.csv"
    train_path = project_root / "data" / "train.csv"
    test_path = project_root / "data" / "test.csv"
    return input_path, train_path, test_path


if __name__ == "__main__":
    src, train, test = get_default_paths()
    print(f"Reading from: {src}")
    train_df, test_df = create_stratified_split(src, train, test)
    print(f"Stratified split created successfully:")
    print(f"  Training samples: {len(train_df)} -> {train}")
    print(f"  Test samples:     {len(test_df)} -> {test}")
