from __future__ import annotations

import sys

from .api import run_query


def main() -> None:
    queries = sys.argv[1:]
    if not queries:
        raise SystemExit("usage: python -m rexa '<question>'")

    for query in queries:
        print(run_query(query))


if __name__ == "__main__":
    main()
