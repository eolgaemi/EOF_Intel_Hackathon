import whisper
from googletrans import translate
from langchain_community.llms import Replicate
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import ConversationalRetrievalChain


loader = PyPDFLoader("resources/User_Manual.pdf")
documents = loader.load()
# PDF 파일 내용 분할 / 벡터화
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
all_splits = text_splitter.split_documents(documents)
# 자연어 처리에서 텍스트의 특징을 추출하기 위해 벡터화를 해야한다.
# 허깅페이스에서 제공하는 embedding 모델을 사용
model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {"device": "cpu"}
embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs)
# FAISS는 고차원 벡터 데이터의 유사성 검색을 빠르게 수행하는 도구
vectorstore = FAISS.from_documents(all_splits, embeddings)
vectorstore.save_local('./erwr')
