"""Main chatbot application."""

import gradio as gr

gr.ChatInterface(
    lambda message, history: "TODO: Implement the actual chatbot logic",
    title="Aguefort",
    description="A chatbot for asking about D&D tips powered by Dropout's Adventuring Academy knowledge and LLMs.",
    retry_btn=None,
    undo_btn=None,
    clear_btn=None,
).launch()
