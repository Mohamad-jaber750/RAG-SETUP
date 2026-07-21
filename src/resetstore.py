from __future__ import annotations

import subprocess

import weaviate
from weaviate.classes.init import AdditionalConfig, Timeout


COLLECTION_NAME = "CISControls"


def get_windows_host() -> str:
    result = subprocess.run(
        [
            "bash",
            "-lc",
            "ip route show | grep -i default | awk '{ print $3 }'",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    host = result.stdout.strip()

    if not host:
        raise RuntimeError(
            "Could not detect the Windows host IP."
        )

    return host


def main() -> None:
    host = get_windows_host()

    client = weaviate.connect_to_local(
        host=host,
        port=8080,
        grpc_port=50051,
        additional_config=AdditionalConfig(
            timeout=Timeout(
                init=30,
                query=60,
                insert=120,
            )
        ),
    )

    try:
        if client.collections.exists(
            COLLECTION_NAME
        ):
            print(
                f"Deleting collection: "
                f"{COLLECTION_NAME}"
            )

            client.collections.delete(
                COLLECTION_NAME
            )

            print("Collection deleted")
        else:
            print(
                f"Collection does not exist: "
                f"{COLLECTION_NAME}"
            )

    finally:
        client.close()


if __name__ == "__main__":
    main()