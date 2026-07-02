import sys
from dotenv import load_dotenv

from rexa import run

load_dotenv()


if __name__ == "__main__":
    tests = [
        "강남역과 경복궁 인근 거래 찾아줘",
        "경복궁이랑 세종로 1-1 같은 곳이야?",
        "경복궁 주차장 있어?",
        "세종로 1-1 어디야?",
        "오늘 날씨 어때?",
    ]

    queries = sys.argv[1:] if len(sys.argv) > 1 else tests

    for q in queries:
        print(f"\n{'='*60}")
        print(f"입력: {q}")
        print(f"{'─'*60}")
        answer = run(q)
        print(answer)
        print(f"{'='*60}")
