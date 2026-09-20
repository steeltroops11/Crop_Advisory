import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.retriever import CropKnowledgeRetriever

def run_tests():
    print("🌾 Running PAU Knowledge Base Retrieval Tests...")
    retriever = CropKnowledgeRetriever()

    test_cases = [
        {
            "query": "PR 126 lagayi hai 25 din ho gaye, urea kab daalu?",
            "crop": "paddy",
            "expected_id_prefix": "pau_paddy_fert",
            "description": "Paddy PR 126 urea timing inquiry (Hinglish)"
        },
        {
            "query": "Wheat crop me pehla paani kab aur kitne din baad lagana hai?",
            "crop": "wheat",
            "expected_id_prefix": "pau_wheat_irrig_01",
            "description": "Wheat 1st irrigation CRI stage inquiry"
        },
        {
            "query": "ਕਣਕ ਵਿੱਚ ਪੀਲੀ ਕੁੰਗੀ ਦੇ ਲੱਛਣ ਅਤੇ ਰੋਕਥਾਮ ਕਿਵੇਂ ਕਰੀਏ?",
            "crop": "wheat",
            "expected_id_prefix": "pau_wheat_disease_01",
            "description": "Wheat Yellow Rust inquiry in Punjabi"
        },
        {
            "query": "Kya paddy me DAP daalna padega agar pehle wheat me DAP dali thi?",
            "crop": "paddy",
            "expected_id_prefix": "pau_paddy_fert_03",
            "description": "Paddy DAP carryover inquiry"
        },
        {
            "query": "Hawa tez chal rahi hai kya kanak nu paani laa sakde han?",
            "crop": "wheat",
            "expected_id_prefix": "pau_wheat",
            "description": "High wind irrigation risk in wheat"
        }
    ]

    passed = 0
    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[{idx}/{len(test_cases)}] Testing: {tc['description']}")
        print(f"Query: \"{tc['query']}\"")
        results = retriever.retrieve(tc["query"], crop_filter=tc["crop"], top_k=2)

        if not results:
            print("❌ FAIL: No results retrieved.")
            continue

        top_match = results[0]
        top_id = top_match["id"]
        print(f"-> Top retrieved ID: {top_id} (Title: {top_match['metadata'].get('title')})")

        matched = top_id.startswith(tc["expected_id_prefix"])
        if matched:
            print(f"✅ PASS (Distance: {top_match['distance']:.4f})")
            passed += 1
        else:
            print(f"⚠️ Soft match / check manually. Expected prefix: {tc['expected_id_prefix']}")

    print(f"\n==========================================")
    print(f"Summary: {passed}/{len(test_cases)} test cases matched target rule prefix perfectly.")

if __name__ == "__main__":
    run_tests()
