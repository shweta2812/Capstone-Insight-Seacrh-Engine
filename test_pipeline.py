"""
test_pipeline.py
Run this once to verify your AWS Bedrock connection and RAG pipeline work.

Usage:
    python test_pipeline.py
"""

from dotenv import load_dotenv
load_dotenv()

from ingestion  import ingest_text
from rag_engine import search, collection

SAMPLE_DATA = [
    {
        "text": """Anthem Blue Cross California 2024 Individual PPO Plan:
Monthly premium starts at $389 for a 30-year-old nonsmoker.
Deductible is $1,500 individual / $3,000 family.
Out-of-pocket maximum is $7,500 individual.
Primary care visit copay is $30 after deductible.
Specialist visit copay is $60 after deductible.
Urgent care copay is $75.
Emergency room copay is $350.
Generic drug copay is $15, preferred brand $45, non-preferred brand $75.
Network includes Cedars-Sinai, UCLA Health, and USC Keck Medicine.""",
        "source": "Anthem Blue Cross CA 2024 PPO",
    },
    {
        "text": """Kaiser Permanente California 2024 HMO Plan Summary:
Monthly premium starts at $310 for a 30-year-old nonsmoker.
Deductible is $0 (no deductible for most services).
Out-of-pocket maximum is $6,500 individual.
Primary care visit copay is $20.
Specialist visit copay is $35.
Urgent care copay is $35.
Emergency room copay is $150 (waived if admitted).
Integrated care model: insurance and medical group are the same organization.
All care must be received within Kaiser network except emergencies.
Known for preventive care focus and electronic health records integration.""",
        "source": "Kaiser Permanente CA 2024 HMO",
    },
    {
        "text": """UnitedHealthcare California SignatureValue Advantage HMO 2024:
Monthly premium starts at $355 for a 30-year-old nonsmoker.
Deductible is $500 individual.
Out-of-pocket maximum is $8,150 individual.
Primary care visit copay is $25 after deductible.
Telehealth visits: $0 copay via UnitedHealth virtual care.
Strong digital app with real-time cost estimator tool.
Partners with OptumRx for pharmacy benefits.
Network includes Sutter Health and Dignity Health in Northern California.""",
        "source": "UnitedHealthcare CA SignatureValue 2024",
    },
]

def run_tests():
    print("=" * 60)
    print("STEP 1: Ingesting sample competitor data...")
    print("=" * 60)
    for item in SAMPLE_DATA:
        n = ingest_text(item["text"], source_name=item["source"])
        print(f"  ✓ {item['source']}: {n} chunks")

    print(f"\nVector store now has {collection.count()} total chunks.\n")

    print("=" * 60)
    print("STEP 2: Running test queries...")
    print("=" * 60)

    queries = [
        "Which competitor has the lowest deductible?",
        "How does Kaiser Permanente's copay compare to Anthem for specialist visits?",
        "Which plan has telehealth benefits?",
    ]

    for q in queries:
        print(f"\nQ: {q}")
        result = search(q)
        print(f"A: {result['answer'][:300]}...")
        print(f"   Sources used: {result['sources']}")

    print("\n✅ Pipeline test complete!")

if __name__ == "__main__":
    run_tests()
