from __future__ import annotations

import subprocess
import json

from judge import GemmaJudge


def get_windows_host() -> str:
    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                "ip route show "
                "| grep -i default "
                "| awk '{ print $3 }'"
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    host = result.stdout.strip()

    if not host:
        raise RuntimeError(
            "Could not detect Windows host."
        )

    return host


def main() -> None:
    host = get_windows_host()

    judge = GemmaJudge(
        base_url=(
            f"http://{host}:11434"
        )
    )

    result = judge.judge(
        question=(
            "How often should the enterprise "
            "asset inventory be reviewed?"
        ),
        gold_answer=(
            "The inventory should be reviewed "
            "and updated bi-annually, or more "
            "frequently."
        ),
        generated_answer=(
            "CIS recommends reviewing and "
            "updating the enterprise asset "
            "inventory twice per year or more often."
        ),
        retrieved_context=(
            "Establish and maintain an accurate, "
            "detailed, and up-to-date inventory. "
            "Review and update the inventory "
            "bi-annually, or more frequently."
        ),
        answerable=True,
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()