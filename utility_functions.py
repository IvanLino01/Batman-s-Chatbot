import os
import json

def get_all_chat_files():
    chat_history_path = get_chat_history_base_path()
    return [f for f in os.listdir(chat_history_path) if f.startswith("chat_history_")]

def create_new_chat_file():
    chat_history_path = get_chat_history_base_path()
    files = get_all_chat_files()
    if files:
        last_file = sorted(files)[-1]
        new_index = int(last_file.split("_")[-1].split(".")[0]) + 1
    else:
        new_index = 1
    new_file_name = f"chat_history_{new_index}.json"
    new_file_path = os.path.join(chat_history_path, new_file_name)
    with open(new_file_path, 'w') as f:
        f.write("{}")
    return new_file_name

def load_chat_history(file_name):
    chat_history_path = get_chat_history_base_path()
    file_path = os.path.join(chat_history_path, file_name)
    try:
        with open(file_path, 'r') as file:
            content = json.load(file)
            return content if isinstance(content, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    
def save_chat_history(history, file_name):
    chat_history_path = get_chat_history_base_path()
    
    file_path = os.path.join(chat_history_path, file_name)
    with open(file_path, 'w') as file:
        json.dump(history, file)

def get_chat_history_base_path():
    current_directory = os.getcwd()
    return os.path.join(current_directory, "chat_history")

def display_chat_history(chat_history):
    return '\n'.join([f"{entry['time']}\nQ: {entry['question']} \nA: {entry['answer']}\n" for entry in chat_history])

def get_content_from_date(history, target_date):
  messages_on_date = [entry for entry in history if entry['time'].startswith(target_date)]
  return messages_on_date

