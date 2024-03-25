"""Main chatbot application."""

import argparse
from typing import Generator

import gradio as gr
from answer_generator import AnswerGenerator


def main(history: int) -> None:
    """Main function to launch the chatbot interface.

    :param history: Max number of previous messages from the chat history to use as context.
    :type history: int
    :yield: The chatbot response in a streaming fashion.
    :rtype: _type_
    """

    answer_generator = AnswerGenerator(max_message_history=history)

    def _chat(message: str, history: list[list[str]]) -> Generator[str, None, None]:
        answer, quotes = answer_generator.generate_answer(message, history)
        response = f"{answer}\n\n**Relevant Quotes:**\n{quotes}"

        for i in range(len(response)):
            yield response[: i + 1]

    gr.ChatInterface(
        _chat,
        title="Aguefort",
        description="A chatbot for asking about D&D tips powered by Dropout's Adventuring Academy knowledge and LLMs.",
        retry_btn=None,
        undo_btn=None,
    ).queue().launch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history",
        type=int,
        default=5,
        help="Max number of previous messages from the chat history to use as context. Defaults to 5.",
    )
    args = parser.parse_args()

    main(args.history)
