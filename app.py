import streamlit as st 
import json 
import os 
import time
import sys
from dotenv import load_dotenv
import requests
from pytube import YouTube
from pathlib import Path
from langchain.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator

load_dotenv()
api_token = os.getenv('ASSEMBLY_AI_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

base_url = "https://api.assemblyai.com/v2"

headers = {
    "authorization": api_token,
    "content-type": "application/json"
}

# PyTube function for YouTube video
def save_audio(url):
    yt = YouTube(url)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download()
    base, ext = os.path.splitext(out_file)
    file_name = base + '.mp3'
    try:
        os.rename(out_file, file_name)
    except WindowsError:
        os.remove(file_name)
        os.rename(out_file, file_name)
    audio_filename = Path(file_name).stem+'.mp3'
    return audio_filename

# Assembly AI speech to text
def assemblyai_stt(audio_filename):
    with open(audio_filename , "rb") as f:
        response = requests.post(base_url + "/upload",
                                headers=headers,
                                data=f)

    upload_url = response.json()["upload_url"]
    data = {
        "audio_url": upload_url
    }
    url = base_url + "/transcript"
    response = requests.post(url, json=data, headers=headers)
    transcript_id = response.json()['id']
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()

        if transcription_result['status'] == 'completed':
            break

        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

        else:
            print("Processing...")
            time.sleep(3)
    print(transcription_result['text'])
    file = open('docs/transcription.txt', 'w')
    file.write(transcription_result['text'])
    file.close()
    return transcription_result['text']

# Open AI code
def langchain_qa(query):
    loader = TextLoader('docs/transcription.txt')
    index = VectorstoreIndexCreator().from_loaders([loader])
    query = query
    result = index.query(query)
    return result


#Streamlit Code
st.set_page_config(layout="wide", page_title="ChatAudio", page_icon="🔊")

st.title("Chat with Your Audio using LLM")

input_source = st.text_input("Enter the YouTube video URL")

if input_source is not None:
    col1, col2 = st.columns(2)

    with col1:
        st.info("Your uploaded video")
        st.video(input_source)
        audio_filename = save_audio(input_source)
        transription = assemblyai_stt(audio_filename)
        st.info(transription)
    with col2:
        st.info("Chat Below")
        query = st.text_area("Ask your Query here...")
        if query is not None:
            if st.button("Ask"):
                st.info("Your Query is: " + query)
                result = langchain_qa(query)
                st.success(result)


import streamlit as st 
import json 
import os 
import time
from dotenv import load_dotenv
import requests

load_dotenv()
api_token = os.getenv('ASSEMBLY_AI_KEY')

base_url = "https://api.assemblyai.com/v2"

headers = {
    "authorization": api_token,
    "content-type": "application/json"
}



def assemblyai_stt(url):
    data = {
        "audio_url": url # You can also use a URL to an audio or video file on the web
    }
    url = base_url + "/transcript"
    response = requests.post(url, json=data, headers=headers)
    transcript_id = response.json()['id']
    return transcript_id


#Assembly AI LLM Code
transcript_id = "transcript_id"

def post_lemur(transcript_id, query):
    url = "https://api.assemblyai.com/v2/generate/question-answer"    

    questions = [
    {
        "question": query,
        "answer_format": "Short sentence"
    }]

    data = {
        "transcript_ids": [transcript_id],
        "questions": questions
    }

    response = requests.post(url, json=data, headers=headers)
    return response

#Streamlit Code
st.set_page_config(layout="wide", page_title="ChatAudio", page_icon="🔊")

st.title("Chat with Your Audio using LLM")

input_source = st.text_input("Enter the YouTube video URL")

if input_source is not None:
    col1, col2 = st.columns(2)

    with col1:
        st.info("Your uploaded video")
        st.video(input_source)
        transription_id = assemblyai_stt(input_source)
        #st.info(transription_id)
    with col2:
        st.info("Chat Below")
        query = st.text_area("Ask your Query here...")
        if query is not None:
            if st.button("Ask"):
                st.info("Your Query is: " + query)
                lemur_output = post_lemur(transcript_id, query)
                lemur_response = lemur_output.json()
                st.success(lemur_response)




