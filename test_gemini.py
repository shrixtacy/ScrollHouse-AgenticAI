import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
try:
    print(llm.invoke("Hello"))
except Exception as e:
    print("ERROR:", e)
