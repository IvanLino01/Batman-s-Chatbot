import streamlit as st
import os
import re
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from llm_components import load_document, chunk_data, create_embeddings
from utility_functions import (get_all_chat_files, create_new_chat_file, load_chat_history, save_chat_history, display_chat_history, get_content_from_date, get_chat_history_base_path)

load_dotenv(find_dotenv(), override=True)

chat_history_path = get_chat_history_base_path()
if not os.path.exists(chat_history_path):
    os.makedirs(chat_history_path)

batman_role ="""
In the shadows of Gotham, you stand as the enigmatic Batman, a symbol of justice and protector of 
the innocent. Whether in the midst of a perilous night patrol or contemplating the enduring struggle against crime, 
you are the embodiment of the Dark Knight. Respond to inquiries and engage in conversations as Batman. Share your thoughts, 
insights, and experiences, always keeping in mind the character's persona. 
Let your responses reflect the legendary vigilante, his values, and his unwavering commitment to his mission.
"""
joker_role ="""
A chaos-loving adversary of Batman with a haunting, maniacal laugh. I have chalk-white skin, green hair, and a sinister red smile. 
I speak with dark humor, theatricality, and twisted philosophical riddles. I'm driven by a desire to disrupt order and expose the world's madness, 
and I'm obsessed with challenging norms and Batman's ideals. I am the Joker
"""

def ask_with_context(vector_store, user_prompt, k, role):
  
  if role == "Batman":
    prompt_template = batman_role + """
      {context}
      Question: {question}"""
  elif role == "Joker":
    prompt_template = joker_role + """
      {context}
      Question: {question}"""
  PROMPT = PromptTemplate(template=prompt_template,
                          input_variables=["context", "question"])

  chain_type_kwargs = {"prompt": PROMPT}
  retriever = vector_store.as_retriever(search_type='similarity',
                                        search_kwargs={'k': k})
  chain = RetrievalQA.from_chain_type(llm=chat,
                                      chain_type="stuff",
                                      retriever=retriever,
                                      chain_type_kwargs=chain_type_kwargs)

  answer = chain.run(user_prompt)
  return answer

def ask_without_context(user_prompt, role):
  if 'messages' not in st.session_state:
    st.session_state.messages = []

    if role == "Batman":
      system_message = batman_role
    elif role == "Joker":
      system_message = joker_role
    st.write(f"Constructed Prompt: {system_message}")
    st.session_state.messages.append(SystemMessage(content=system_message))
    
  # If the user message is entered, append a HumanMessage object to the messages list
  if user_prompt:
    st.session_state.messages.append(HumanMessage(content=user_prompt))

    # Show a spinner while the model is generating a response
    with st.spinner('Working on your request ...'):
      response = chat(st.session_state.messages)

    # Append an AIMessage object with the response content to the messages list
    st.session_state.messages.append(AIMessage(content=response.content))

  # Return the response
  if st.session_state.messages:
    answer = st.session_state.messages[-1].content
    return answer

def clear_history():
  if 'history' in st.session_state:
    del st.session_state['history']

def initialize_session_state():
    st.session_state.setdefault("history", "")
    st.session_state.setdefault("selected_file", "default_filename.json")
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("chat_session", 1)
    st.session_state.setdefault("messages", [])
    
def file_upload():
    uploaded_file = st.file_uploader('Upload a file: ', type=['pdf', 'docx', 'txt'])
    if uploaded_file:
        bytes_data = uploaded_file.read()
        file_name = os.path.join('./', uploaded_file.name)
        
        with open(file_name, 'wb') as f:
            f.write(bytes_data)
            
        data = load_document(file_name)
        chunks = chunk_data(data)
        st.write(f'Chunk size: 1000, Chunks: {len(chunks)}')
        vector_store = create_embeddings(chunks)
        st.session_state.vs = vector_store
        st.success('File uploaded, chunked, and embedded successfully')

    return uploaded_file

def new_chat_history():
    if st.button("Create New Chat History"):
        file_name = create_new_chat_file()
        st.session_state.selected_file = file_name
        st.session_state.history = []
        st.session_state.chat_history = []
        st.session_state.chat_session += 1
    
def chat_history_selection():
    all_files = get_all_chat_files()
    if all_files:
        prev_selected_file = st.session_state.selected_file
        selected_file = st.selectbox("Choose Chat History", all_files, index=len(all_files)-1)
        st.session_state.selected_file = selected_file
        
        if selected_file != prev_selected_file:
          st.session_state[f"user_input_{st.session_state.chat_session}"] = ""
        loaded_history = load_chat_history(selected_file)
        st.session_state.chat_history = loaded_history
        st.session_state.history = display_chat_history(loaded_history)
        
def getting_user_prompt():
    user_prompt = st.text_input(label='Send a message',key=f"user_input_{st.session_state.chat_session}")
    
    date_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"
    date_match = re.search(date_pattern, user_prompt)
    
    if date_match:
      target_date = date_match.group(1)
      content_on_date = get_content_from_date(st.session_state.chat_history, target_date)
      
      if content_on_date:
        formatted_content = "\n".join([f"Q: {entry['question']} \nA: {entry['answer']}" for entry in content_on_date])
        
        summary_prompt = f"Summarize the following conversation from {target_date}:\n{formatted_content}"
        answer = ask_without_context(summary_prompt, st.session_state.role)
      else:
        answer = f'I could not fine any conversation from {target_date}.'
        
      display_and_save_answer(user_prompt, answer)   
      
    elif user_prompt:
        answer = fetch_answer(user_prompt)
        display_and_save_answer(user_prompt, answer)

def fetch_answer(user_prompt):
    role = st.session_state.role
    if 'vs' in st.session_state:
        vector_store = st.session_state.vs
        return ask_with_context(vector_store, user_prompt, 3, role)
    else:
        return ask_without_context(user_prompt, role)

def display_and_save_answer(user_prompt, answer):
    st.text_area('LLM Answer: ', value=answer)
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_entry = {
        'time': t,
        'question': user_prompt,
        'answer': answer
    }
    st.session_state.chat_history.append(chat_entry)
    save_chat_history(st.session_state.chat_history, st.session_state.selected_file)
    chat_display = display_chat_history(st.session_state.chat_history)
    st.text_area(label='Chat History', value=chat_display, height=400)

if __name__ == "__main__":
    initialize_session_state()
    st.subheader('ChatGPT with Gotham Characters🦇')
    chat = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.8)

    with st.sidebar:
      st.session_state.role = role = st.radio("Choose a Role:", ("Batman", "Joker"))
      uploaded_file = file_upload()
      new_chat_history()
      chat_history_selection()
     
    st.write(f"Current Role: {st.session_state.role}")

    getting_user_prompt()