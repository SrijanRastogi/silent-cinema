"""Worker entrypoint.

M1 ships the process boundary only. The PostgreSQL-backed queue is implemented
in M3; this module must not pretend to process jobs before then.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "silent-cinema worker: the job queue arrives in M3. "
        "No jobs were claimed and no work was performed.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
