"""Script for generating the Adventuring Academy knowledge base."""

import json
from pathlib import Path

from yaspin import yaspin

EPISODES_PATH = Path(__file__).parent.parent.joinpath("data/episodes.jsonl")
CAPTIONS_PATH = Path(__file__).parent.parent.joinpath("data/captions")


def main() -> None:
    """Generate the knowledge base."""

    with open(EPISODES_PATH, "r", encoding="utf-8") as f:
        episodes = list(map(json.loads, f.readlines()))

    with yaspin(text=f"Generating knowledge base from {len(episodes)} episodes", color="yellow") as sp:
        _ = _parse_captions(episodes)
        sp.write("> Captions parsed")

        # TODO:
        # - Chunk captions (make sure to preserve the right metadata for each chunk)
        # - Embed captions using SentenceTransformers
        # - Create qdrant collection
        # - Upload the embeddings along with the metadata for each chunk to the collection

        sp.ok("✔")


def _parse_captions(episodes: list[dict]) -> list[dict]:
    episodes_with_captions = []
    for episode in episodes:
        with open(CAPTIONS_PATH.joinpath(f"{episode['season']}-{episode['episode']}.vtt"), "r", encoding="utf-8") as f:
            captions = "".join(
                [line for line in f.readlines() if not line.strip().startswith("WEBVTT") and not "-->" in line]
            ).strip()
            episode["captions"] = captions
            episodes_with_captions.append(episode)

    return episodes_with_captions


if __name__ == "__main__":
    main()
