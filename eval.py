import time
from rag_pipeline import OperationalRAGPipeline

def evaluate_operations_rag():
    pipeline = OperationalRAGPipeline()
    
    test_cases = [
        {
            "query": "backup aircraft maintenance delay policy", 
            "expected_keywords": ["120 minutes", "duty operations manager", "45 minutes", "line maintenance"],
            "should_pass_verification": True
        },
        {
            "query": "crew reassignment rest period rules", 
            "expected_keywords": ["flight duty period", "10 hours", "fatigue"],
            "should_pass_verification": True
        },
        {
            "query": "secondary aircraft reassignment weather delay",
            "expected_keywords": ["24 hours", "operational supervisor", "reassignment"],
            "should_pass_verification": True
        },
        {
            "query": "catering inflight meal options for international routes",
            "expected_keywords": [],
            "should_pass_verification": False  # Negative test case (Out-of-scope)
        }
    ]

    total_time = 0.0
    successful_queries = 0
    total_keyword_matches = 0
    total_expected_keywords = 0
    verification_matches = 0

    print("📊 --- Running Operations RAG & Self-RAG Evaluation ---")
    print("=" * 75)

    for idx, case in enumerate(test_cases, 1):
        start_time = time.time()
        docs = pipeline.hybrid_search(case["query"], top_k=3)
        elapsed_time = time.time() - start_time
        total_time += elapsed_time

        retrieved_text = " ".join(docs).lower()
        expected_kws = case["expected_keywords"]
        
        # 1. Keyword Match Calculation
        if expected_kws:
            matches = sum(1 for kw in expected_kws if kw.lower() in retrieved_text)
            precision = matches / len(expected_kws)
            total_keyword_matches += matches
            total_expected_keywords += len(expected_kws)
        else:
            matches = 0
            precision = 1.0

        # 2. Self-RAG Verification Testing
        is_verified = pipeline.self_rag_verification(case["query"], docs)
        verification_passed = (is_verified == case["should_pass_verification"])
        if verification_passed:
            verification_matches += 1

        # 3. Overall Retrieval Success (Hit Rate)
        query_passed = (precision >= 0.5) if expected_kws else (not is_verified)
        if query_passed and verification_passed:
            successful_queries += 1

        status_flag = "✅ PASS" if (query_passed and verification_passed) else "❌ FAIL"
        
        print(f"[{idx}] Query: '{case['query']}' | Status: {status_flag}")
        print(f"    ├─ Latency: {elapsed_time:.4f}s")
        print(f"    ├─ Keyword Match: {matches}/{len(expected_kws)} ({precision*100:.1f}%)")
        print(f"    └─ Self-RAG Verification: {is_verified} (Expected: {case['should_pass_verification']})\n")

    # Aggregate Metrics Calculation
    avg_latency = total_time / len(test_cases)
    overall_accuracy = (successful_queries / len(test_cases)) * 100
    keyword_recall = (total_keyword_matches / total_expected_keywords * 100) if total_expected_keywords > 0 else 100.0
    verification_accuracy = (verification_matches / len(test_cases)) * 100

    print("=" * 75)
    print("✅ --- FINAL EVALUATION METRICS ---")
    print(f"• Query Accuracy Rate:       {overall_accuracy:.2f}%")
    print(f"• Keyword Recall Rate:      {keyword_recall:.2f}%")
    print(f"• Self-RAG Guardrail Acc:   {verification_accuracy:.2f}%")
    print(f"• Average Latency:           {avg_latency:.4f} seconds")
    print("=" * 75)

if __name__ == "__main__":
    evaluate_operations_rag()