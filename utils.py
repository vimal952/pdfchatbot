from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

prompt = ChatPromptTemplate.from_template(
    """
Based only on the provided context, answer the question directly and concisely.
Answer in English only.
Do not add extra information, restate the question, or generate additional questions.
Start your response immediately with the answer.
<context>
{context}
</context>
Question: {input}
Answer:
"""
)

endpoint_url = (
    "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
)
llm = HuggingFaceEndpoint(endpoint_url=endpoint_url, temperature=0.2, max_tokens=400)


async def make_vec_db(pdf_path, pdf_name):
    """
    Create a vector database from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.
        pdf_name (str): Name of the PDF file.

    ReturnspdfMetadata:
        vector database (FAISS)
    """
    document = PyPDFLoader(pdf_path).load()
    splitter = RecursiveCharacterTextSplitter()
    documents = splitter.split_documents(document)

    db = FAISS.from_documents(documents, HuggingFaceEmbeddings())
    db.save_local(UPLOADS_DIR / "vec_dbs" / pdf_name)


def create_retriever(db):
    """
    Create a retrieval chain from a vector database.
    Args:
        db (FAISS): Vector database.
    Returns:
        retriever_chain
    """
    retriever = db.as_retriever()

    document_chain = create_stuff_documents_chain(llm, prompt)
    retrival_chain = create_retrieval_chain(retriever, document_chain)

    return retrival_chain


async def generate_response(pdf_name, question):
    """
    It takes pdf name and the question as argument and then loads the vector database of that pdf and generates response to that question.

    Args:
        pdf_name (str): The name of the PDF file to use for generating the response.
        question (str): The question to ask based on the PDF content.

    Returns:
        str: The generated response to the question.
    """
    vector_db_path = UPLOADS_DIR / "vec_dbs" / pdf_name
    vector_db = FAISS.load_local(
        vector_db_path,
        embeddings=HuggingFaceEmbeddings(),
        allow_dangerous_deserialization=True,
    )

    retriever = create_retriever(vector_db)
    response = retriever.invoke({"input": question})
    return response["answer"]
