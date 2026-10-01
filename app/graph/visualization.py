"""
Graph visualization utility for LangGraph workflow.
Generates Mermaid diagram directly from the compiled StateGraph.
"""
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is importable when executed directly
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.graph.workflow import get_compiled_workflow


def get_graph_mermaid() -> str:
    """Generate Mermaid syntax directly from the compiled LangGraph."""
    app = get_compiled_workflow()
    return app.get_graph().draw_mermaid()


def save_graph_visualization(output_path: Optional[Path] = None) -> Path:
    """Save the generated Mermaid graph diagram to a file."""
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "workflow_graph.mermaid"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mermaid_code = get_graph_mermaid()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)

    return output_path


def get_ascii_graph() -> str:
    """Return a clean ASCII-safe text diagram of the hybrid triage workflow."""
    return """
       [START]
          |
          v
   [classification] (TF-IDF + Naive Bayes / LogReg)
          |
          v
   <Confidence Check> (Threshold >= 0.50)
     +--- HIGH -------------------------+
     |                                  |
     v (LOW)                            |
   [llm_classification] (Structured)    |
     |                                  |
     +--------------------------------->+
                                        |
                                        v
                                    [priority]
                                        |
                                        v
                                     [routing]
                                        |
                                        v
                                   [escalation]
                                        |
                                        v
                                  [rag_retrieval]
                                        |
                                        v
                                    [response]
                                        |
                                        v
                                      [END]
"""


if __name__ == "__main__":
    saved = save_graph_visualization()
    print(f"Mermaid graph saved to: {saved}\n")
    print("Mermaid Output:")
    print(get_graph_mermaid())
    print("\nASCII Architecture:")
    print(get_ascii_graph())
