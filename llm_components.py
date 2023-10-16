import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

def load_document(file):
  name, extension = os.path.splitext(file)
  if extension == '.pdf':
    from langchain.document_loaders import PyPDFLoader
    print(f'Loading {file}')
    loader = PyPDFLoader(file)

  elif extension == '.docx':
    from langchain.document_loaders import Docx2txtLoader
    print(f'Loading {file}')
    loader = Docx2txtLoader(file)
  elif extension == '.txt':
    from langchain.document_loaders import TextLoader
    loader = TextLoader(file)
  else:
    print('Document format is not supported')
    return None
  data = loader.load()
  return data

def chunk_data(data, chunk_size=256, chunk_overlap=20):
  from langchain.text_splitter import RecursiveCharacterTextSplitter
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                                 chunk_overlap=0)
  chunks = text_splitter.split_documents(data)
  return chunks

def create_embeddings(chunks):
  embeddings = OpenAIEmbeddings()
  vector_store = Chroma.from_documents(chunks, embeddings)
  return vector_store