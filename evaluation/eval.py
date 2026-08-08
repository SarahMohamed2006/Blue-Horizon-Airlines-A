import time
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from rag.rag_pipeline import OperationalRAGPipeline


def run_retrieval_evaluation():
    print("\n" + "=" * 60)
    print("📊 BLUE HORIZON AIRLINES - RAG ARCHITECTURES EVALUATION")
    print("=" * 60)

    try:
        rag = OperationalRAGPipeline()
    except Exception as e:
        print(f"Error initializing RAG Pipeline: {e}")
        return

    # One question per required category so the comparison table actually
    # exercises the case each architecture is supposed to win on:
    #   - general: naive vector search should do fine
    #   - citation-heavy: exact identifiers should favor hybrid (BM25) search
    #   - multi-part/decomposition: should favor agentic RAG's multi-hop retrieval
    test_questions = [
        "What is the standard fasting or reporting window before operational flight duties?",
        "What does Protocol 4.2b specify regarding severe weather delay protocols?",
        "For a flight facing both a crew duty-hour limit and an aircraft maintenance "
        "hold, what steps and approvals are required before it can depart?",
    ]

    print(f"Loaded {len(test_questions)} domain-specific test cases.\n")

    def estimate_tokens(text: str) -> int:
        """
        Lightweight, dependency-free token estimate (~1.3 tokens/word),
        applied to whatever text was actually sent to/retrieved by the
        pipeline for this call, rather than a fixed placeholder number.
        """
        words = text.split()
        return max(1, int(len(words) * 1.3))

    metrics = {
        "Naive RAG": {"correct": 0, "total_latency": 0.0, "total_tokens": 0, "queries": len(test_questions)},
        "Hybrid Search": {"correct": 0, "total_latency": 0.0, "total_tokens": 0, "queries": len(test_questions)},
        "Agentic RAG": {"correct": 0, "total_latency": 0.0, "total_tokens": 0, "queries": len(test_questions)},
    }

    for i, q in enumerate(test_questions, 1):
        print(f"Testing Question {i}: '{q}'")

        t0 = time.time()
        naive_docs = rag.naive_rag(q, top_k=3)
        t_naive = time.time() - t0
        naive_passed = rag.self_rag_verification(q, naive_docs)

        metrics["Naive RAG"]["total_latency"] += t_naive
        metrics["Naive RAG"]["total_tokens"] += estimate_tokens(q + " " + " ".join(naive_docs))
        if naive_passed:
            metrics["Naive RAG"]["correct"] += 1

        time.sleep(3)

        t0 = time.time()
        hybrid_docs = rag.hybrid_search(q, top_k=3)
        t_hybrid = time.time() - t0
        hybrid_passed = rag.self_rag_verification(q, hybrid_docs)

        metrics["Hybrid Search"]["total_latency"] += t_hybrid
        metrics["Hybrid Search"]["total_tokens"] += estimate_tokens(q + " " + " ".join(hybrid_docs))
        if hybrid_passed:
            metrics["Hybrid Search"]["correct"] += 1

        time.sleep(3)

        t0 = time.time()
        agentic_docs = rag.agentic_rag(q)
        t_agentic = time.time() - t0
        agentic_passed = rag.self_rag_verification(q, agentic_docs)

        metrics["Agentic RAG"]["total_latency"] += t_agentic
        # Agentic RAG also spends tokens on the critique/refinement call itself,
        # not just the final retrieved docs, so include the query twice to
        # roughly account for the extra LLM round-trip.
        metrics["Agentic RAG"]["total_tokens"] += estimate_tokens(
            q + " " + q + " " + " ".join(agentic_docs)
        )
        if agentic_passed:
            metrics["Agentic RAG"]["correct"] += 1

        time.sleep(5)

    print("\n" + "=" * 60)
    print("📈 EVALUATION COMPARISON RESULTS (For README Table)")
    print("=" * 60)
    print(f"{'Architecture':<20} | {'Accuracy':<10} | {'Avg Latency (s)':<15} | {'Avg Tokens (Est)'}")
    print("-" * 65)

    for arch, data in metrics.items():
        q_count = data['queries']
        acc_str = f"{data['correct']}/{q_count}"
        avg_lat = (data['total_latency'] / q_count) if q_count > 0 else 0.0
        avg_tokens = (data['total_tokens'] / q_count) if q_count > 0 else 0
        print(f"{arch:<20} | {acc_str:<10} | {avg_lat:<15.2f} | {avg_tokens:.0f}")
    print("=" * 60)


if __name__ == "__main__":
    run_retrieval_evaluation()