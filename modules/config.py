# config.py
import os

API_KEY = os.getenv("OPENAI_API_KEY")
CACHE_FOLDER = '../gpt_cache/'
MODEL = "gpt-3.5-turbo-0125"
#MODEL = "gpt-4-0125-preview"
BASE_DELAY = 3
MAX_RETRIES = 5
BACKOFF_TIME = 60
MAX_TOKENS = 4096
