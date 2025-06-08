# utils/processing.py
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import re
from bs4 import BeautifulSoup
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_website_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        return f"Error processing website: {str(e)}"

def extract_youtube_transcript(video_url):
    try:
        video_id = video_url.split("v=")[-1].split("&")[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([entry['text'] for entry in transcript])
    except Exception as e:
        return f"Error processing YouTube video: {str(e)}"

def process_inputs(pdf_files=None, url=None, yt_link=None):
    combined_text = ""
    
    if pdf_files:
        combined_text += get_pdf_text(pdf_files) + "\n"
        
    if url:
        combined_text += extract_website_content(url) + "\n"
        
    if yt_link:
        combined_text += extract_youtube_transcript(yt_link) + "\n"
        
    return chunk_text(combined_text)

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return splitter.split_text(text)

def create_vector_db(chunks):
    embedder = HuggingFaceEmbeddings()
    return FAISS.from_texts(chunks, embedder)