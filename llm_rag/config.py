from dotenv import load_dotenv
import os


load_dotenv()


AI_API_URL = os.getenv("AI_API_URL")
AI_TOKEN = os.getenv("AI_TOKEN")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
DB_PATH = os.getenv("DB_PATH")
