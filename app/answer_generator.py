"""A module to generate answers to questions using Adventuring Academy knowledge and LLMs."""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains.llm import LLMChain
from langchain_community.chat_models.bedrock import BedrockChat
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

load_dotenv()


# pylint: disable=too-few-public-methods
class AnswerGenerator:
    """A class to generate answers to questions using Adventuring Academy knowledge and LLMs.

    :param max_message_history: The maximum number of messages to use from the chat history as context.
    :type max_message_history: int
    """

    def __init__(self, max_message_history: int) -> None:
        self._llm = BedrockChat(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            model_kwargs={"temperature": 0.0, "top_p": 0.8, "top_k": 15, "max_tokens": 1024},
            region_name=os.getenv("AWS_REGION"),
        )
        self._docs_chain = self._create_docs_chain()
        self._retrieval_chain = self._create_retrieval_chain()
        self._max_message_history = max_message_history

    def generate_answer(self, question: str, history: list[list[str, str]]) -> tuple[str, str]:
        """Generates an answer to the given question along with relevant quotes.

        :param question: The question to answer.
        :type question: str
        :param history: The chat history between the user and the AI assistant.
        Each inner list consists of a pair of user input and bot response.
        :type history: list[list[str, str]]
        :return: The answer to the question and relevant quotes.
        :rtype: tuple[str, str]
        """

        # Only use the last `max_message_history` messages from the chat history
        chat_history = history[-self._max_message_history :] if history is not None else []
        result = self._retrieval_chain.invoke({"question": question, "chat_history": chat_history})

        # Extract the quotes and the answer from the result
        quotes = re.search(r"<quotes>(.*?)</quotes>", result["answer"], re.DOTALL).group(1).strip()
        answer = re.search(r"<answer>(.*?)</answer>", result["answer"], re.DOTALL).group(1).strip()

        return answer, quotes

    def _create_docs_chain(self) -> StuffDocumentsChain:
        instructions = """
You are an assistant designed to help answer questions related to role-playing games using conversations from a podcast hosted by DM Brennan Lee Mulligan.

Here are the conversations you will use to answer the question:
<conversations>
{context}
</conversations>

First, find the quotes from the conversations that are most relevant to answering the question, and then print them in numbered order inside <quotes></quotes> XML tags. Quotes should be relatively short.
The quotes should also include the title of the conversation they are from, like this: [1] "quote" from S1E1: Title of the Episode.

If there are no relevant quotes, write "No relevant quotes" instead inside <quotes></quotes> XML tags.

Then, answer the question, inside <answer></answer> XML tags. Do not include or reference quoted content verbatim in the answer. Don't say "According to Quote [1]" when answering. Instead make references to quotes relevant to each section of the answer solely by adding their bracketed numbers at the end of relevant sentences.

Thus, the format of your overall response should look like what's shown between the <example></example> tags. Make sure to follow the formatting and spacing exactly.
<example>
<quotes>
[1] "A nat20 should be used for incredible moments, not just for a random check. It's a moment that should be remembered." from S1E1: What to do with a Nat20?
[2] "The DM should be the one to decide when a nat20 is used, not the player." from S1E1: What to do with a Nat20?
</quotes>

<answer>
A natural 20 is a critical hit in Dungeons & Dragons. It's a moment that should be remembered and used for incredible moments, not just for a random check. [1] The Dungeon Master should be the one to decide when a nat20 is used, not the player. [2]
</answer>
</example>

If the question cannot be answered by the context, say "It seems Brennan and his guests haven't talked about this before. Try being more specific or asking a different question." inside <answer></answer> XML tags.

Here is the question you need to answer:
<question>
{question}
</question>
"""
        prompt = ChatPromptTemplate.from_messages([("user", instructions)])
        doc_prompt = PromptTemplate.from_template(
            "<conversation><title>S{season}E{episode}: {title}</title><content>{page_content}</content></conversation>"
        )

        return StuffDocumentsChain(
            llm_chain=LLMChain(llm=self._llm, prompt=prompt),
            document_prompt=doc_prompt,
            document_variable_name="context",
            document_separator="\n",
        )

    def _create_retrieval_chain(self) -> ConversationalRetrievalChain:
        retriever = FAISS.load_local(
            Path(__file__).parent.parent.joinpath("data/adventuring_academy_kb"),
            # Make sure to use the same embeddings as the ones used to generate the knowledge base
            HuggingFaceEmbeddings(model_name="msmarco-distilbert-base-v4"),
            allow_dangerous_deserialization=True,
        ).as_retriever(search_kwargs={"k": 10, "fetch_k": 50})

        instructions = """
I'm going to give you a chat history between a user and an AI assistant, along with a follow-up question.

Here is the chat history:
<chat_history>
{chat_history}
</chat_history>

And here is the follow-up question:
<question>
{question}
</question>

Combine the chat history and the follow-up question into a standalone question that will be used to retrieve the most relevant documents from the knowledge base.
Make sure the standalone question clearly represents the user's intent and has all the necessary context to be useful for the retrieval process.
Write your standalone question inside <standalone></standalone> XML tags.
"""
        prompt = ChatPromptTemplate.from_messages([("user", instructions)])
        question_generator = LLMChain(
            llm=self._llm, prompt=prompt, output_parser=_RegexOutputParser(regex=r"<standalone>(.*?)</standalone>")
        )

        def _get_chat_history(chat_history: list[tuple[str, str]]) -> str:
            # Format the chat history as a string of H (human) and A (assistant) messages
            # This is needed because models like Claude require the chat history to be formatted in this way
            # instead of the default "Human: message\nAssistant: message" format
            return "\n".join([f"H: {turn[0]}\nA: {turn[1]}" for turn in chat_history])

        return ConversationalRetrievalChain(
            combine_docs_chain=self._docs_chain,
            retriever=retriever,
            question_generator=question_generator,
            get_chat_history=_get_chat_history,
        )


class _RegexOutputParser(BaseOutputParser[str]):
    """OutputParser that parses the output using a regular expression."""

    regex: str = ""

    def parse(self, text: str) -> str:
        """Returns the text that matches the regular expression.
        It assumes that the regular expression has a single capturing group.

        :param text: The text to parse.
        :type text: str
        :return: The text that matches the regular expression.
        :rtype: str
        """
        return re.search(self.regex, text, re.DOTALL).group(1).strip()
