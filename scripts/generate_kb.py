"""Script for generating the Adventuring Academy knowledge base."""

import json
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from yaspin import yaspin

EPISODES_PATH = Path(__file__).parent.parent.joinpath("data/episodes.jsonl")
CAPTIONS_PATH = Path(__file__).parent.parent.joinpath("data/captions")
KB_PATH = Path(__file__).parent.parent.joinpath("data/adventuring_academy_kb")


def main() -> None:
    """Generate the knowledge base."""

    with open(EPISODES_PATH, "r", encoding="utf-8") as f:
        episodes = list(map(json.loads, f.readlines()))

    with yaspin(text=f"Generating knowledge base from {len(episodes)} episodes", color="yellow") as sp:
        episodes_with_captions = _parse_captions(episodes)
        sp.write("> Captions parsed")

        chunks = _chunk_captions(episodes_with_captions)
        sp.write("> Captions chunked")

        # pylint: disable=no-member
        db = FAISS.from_documents(chunks, HuggingFaceEmbeddings(model_name="msmarco-distilbert-base-v4"))
        db.save_local(KB_PATH)
        sp.write("> Captions embedded and indexed")

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


def _chunk_captions(episodes_with_captions: str) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=50)
    texts = [episode["captions"] for episode in episodes_with_captions]
    metadatas = [{k: episode[k] for k in episode.keys() if k != "captions"} for episode in episodes_with_captions]
    chunks = splitter.create_documents(texts, metadatas)

    return chunks


if __name__ == "__main__":
    main()
