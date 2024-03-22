"""A module to generate answers to questions using Adventuring Academy knowledge and LLMs."""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.chat_models.bedrock import BedrockChat
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

load_dotenv()


# pylint: disable=too-few-public-methods
class AnswerGenerator:
    """A class to generate answers to questions using Adventuring Academy knowledge and LLMs."""

    def __init__(self) -> None:
        self._retriever = FAISS.load_local(
            Path(__file__).parent.parent.joinpath("data/adventuring_academy_kb"),
            # Make sure to use the same embeddings as the ones used to generate the knowledge base
            HuggingFaceEmbeddings(model_name="msmarco-distilbert-base-v4"),
            allow_dangerous_deserialization=True,
        ).as_retriever(search_kwargs={"k": 10, "fetch_k": 50})
        self._instructions = """
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
{input}
</question>
"""
        self._prompt = ChatPromptTemplate.from_messages([("user", self._instructions)])
        self._doc_prompt = PromptTemplate.from_template(
            "<conversation><title>S{season}E{episode}: {title}</title><content>{page_content}</content></conversation>"
        )
        self._llm = BedrockChat(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            model_kwargs={"temperature": 0.0, "top_p": 0.8, "top_k": 15, "max_tokens": 1024},
            region_name=os.getenv("AWS_REGION"),
        )
        self._docs_chain = create_stuff_documents_chain(
            self._llm, self._prompt, document_prompt=self._doc_prompt, document_separator="\n"
        )
        self._retrieval_chain = create_retrieval_chain(self._retriever, self._docs_chain)

    def generate_answer(self, question: str) -> tuple[str, str]:
        """Generates an answer to the given question along with relevant quotes.

        :param question: The question to answer.
        :type question: str
        :return: The answer to the question and relevant quotes.
        :rtype: tuple[str, str]
        """

        result = self._retrieval_chain.invoke({"input": question})
        # Extract the quotes and the answer from the result
        quotes = re.search(r"<quotes>(.*?)</quotes>", result["answer"], re.DOTALL).group(1).strip()
        answer = re.search(r"<answer>(.*?)</answer>", result["answer"], re.DOTALL).group(1).strip()

        return answer, quotes
