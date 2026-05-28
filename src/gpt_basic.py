from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key= api_key)

def get_ai_response(messages):
    response = client.chat.completions.create(
        model= "gpt-4o",
        temperature=0.1,
        messages=messages,
    )
    return response.choices[0].message.content
    
messages = [
     {"role":"system","content":"YOU ARE A DAVID LYNCH YOU SPEAK IN ALL CAPS JUST LIKE HIS CHARACTER IN TWIN PEAKS."},
     ]

while True:
    user_input = input("user: ")
    if user_input == "exit":
        break
    messages.append({"role":"user","content":user_input})
    ai_response = get_ai_response(messages)
    messages.append({"role":"user","content":user_input})
    print("AI:"+ ai_response)

