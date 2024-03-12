"""Script for downloading captions from Dropout's Adventure Academy episodes."""

import json
import subprocess
import time
from pathlib import Path

from yaspin import yaspin

MAX_RETRIES = 3


def main(episodes: list[dict]) -> None:
    """Download captions from the given episodes.

    :param episodes: List of episodes to download captions from.
    :type episodes: list[dict]
    """

    with yaspin(text=f"Downloading captions from {len(episodes)} episodes", color="yellow") as sp:
        for episode in episodes:
            _download_captions(episode)
            sp.write(f"> {episode['title']} - Done")
            time.sleep(5)
        sp.ok("✔")


def _download_captions(episode: dict) -> None:
    command = [
        "docker",
        "run",
        "--rm",
        "-it",
        "-v",
        "./login:/app/login",
        "-v",
        "./data/captions:/Downloads",
        "dropout-dl",
        "--output-directory",
        "/Downloads",
        "-co",
        "-e",
        episode["url"],
        "-o",
        f"{episode['season']}-{episode['episode']}",
    ]

    successful = False
    for i in range(MAX_RETRIES):
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            successful = True
            break
        except subprocess.CalledProcessError:
            # Exponentially backoff
            time.sleep(2**i)

    if not successful:
        raise RuntimeError(f"Failed to download captions for {episode['title']}")


if __name__ == "__main__":
    with open(Path(__file__).parent.parent.joinpath("data/episodes.jsonl"), "r", encoding="utf-8") as f:
        eps = list(map(json.loads, f.readlines()))

    main(eps)
