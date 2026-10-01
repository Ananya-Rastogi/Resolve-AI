"""
Canonical FAQ Dataset Preprocessing for RAG.
Reads data/faq_question_answer_dataset.csv (30,000 synthetic rows)
and creates data/rag_faqs.csv with 30 deduplicated, canonical FAQ documents.
"""
from pathlib import Path
from typing import Tuple, List, Dict, Any
import pandas as pd


def _get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_canonical_faqs(
    source_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """
    Extract canonical FAQ units by deduplicating primarily on the Answer
    and consolidating alternative question variants.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source FAQ dataset not found at: {source_path}")

    df = pd.read_csv(source_path)

    canonical_rows: List[Dict[str, Any]] = []

    # Group by Answer to find unique canonical knowledge units
    answer_groups = df.groupby("Answer", sort=False)

    for idx, (answer, group) in enumerate(answer_groups, start=1):
        unique_questions = group["Question"].unique().tolist()

        # Separate base question from alternative question variant (e.g., ' Please help.')
        if len(unique_questions) >= 2:
            sorted_qs = sorted(unique_questions, key=len)
            base_question = sorted_qs[0]
            alt_question = sorted_qs[1]
        else:
            base_question = unique_questions[0]
            alt_question = ""

        # Most representative metadata for this canonical answer
        category = group["Category"].iloc[0]
        intent = group["Intent"].iloc[0]
        keywords = group["Keywords"].iloc[0]
        subcategory = group["Subcategory"].mode().iloc[0]
        response_type = group["Response_Type"].mode().iloc[0]
        difficulty_level = group["Difficulty_Level"].mode().iloc[0]
        language = group["Language"].iloc[0]
        source_faq_id = group["FAQ_ID"].iloc[0]

        canonical_rows.append({
            "canonical_answer_id": idx,
            "faq_id": f"FAQ_{idx:03d}",
            "source_faq_id": source_faq_id,
            "question": base_question,
            "alternative_question": alt_question,
            "answer": answer,
            "category": category,
            "subcategory": subcategory,
            "intent": intent,
            "keywords": keywords,
            "response_type": response_type,
            "difficulty_level": difficulty_level,
            "language": language,
            "source_occurrences": len(group),
        })

    canonical_df = pd.DataFrame(canonical_rows)

    # Ensure target directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_df.to_csv(output_path, index=False)

    return canonical_df


if __name__ == "__main__":
    root = _get_project_root()
    src = root / "data" / "faq_question_answer_dataset.csv"
    dst = root / "data" / "rag_faqs.csv"

    print(f"Reading from: {src}")
    faqs = build_canonical_faqs(src, dst)
    print(f"Successfully created canonical FAQ dataset:")
    print(f"  Canonical FAQs: {len(faqs)} records saved to {dst}")
    print(f"  Categories covered: {faqs['category'].nunique()} ({list(faqs['category'].unique())})")
