from dotenv import load_dotenv
import os
load_dotenv()

class Settings:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    