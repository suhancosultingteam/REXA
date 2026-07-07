"""Compatibility wrapper for the operational preemptive-message entrypoint."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.preemptive_message.main as _impl
from scripts.preemptive_message.main import (  # noqa: F401
    AD_MESSAGE_WINDOW_END,
    AD_MESSAGE_WINDOW_START,
    CHUNK_SIZE,
    KST,
    RETRY_BACKOFF_SECONDS,
    _chunked,
    _load_env_config,
    _send_chunk_with_retry,
    _within_ad_message_window,
    main,
    run_broadcast,
)

time = _impl.time


if __name__ == "__main__":
    main()
