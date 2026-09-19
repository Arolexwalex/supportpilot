# eval.py
from app.rag import generate_answer

eval_cases = [
    {"question": "What are your support hours?", "must_contain": "9"},
    {"question": "How do I reset my password?", "must_contain": "reset link"},
]

def run_eval():
    passed = 0
    for case in eval_cases:
        answer, _ = generate_answer(case["question"])
        if case["must_contain"].lower() in answer.lower():
            passed += 1
        else:
            print(f"FAILED: {case['question']}\n  -> {answer}\n")
    print(f"{passed}/{len(eval_cases)} passed")

if __name__ == "__main__":
    run_eval()