# api_client.py
import openai
import time
import os
from config import API_KEY, MODEL, MAX_RETRIES, BACKOFF_TIME, MAX_TOKENS

class APIClient:
    def __init__(self):
        openai.api_key = API_KEY

    def make_api_request(self, messages):
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = openai.ChatCompletion.create(
                    model=MODEL, 
                    messages=messages, 
                    max_tokens=MAX_TOKENS
                )
                return response['choices'][0]['message']['content']
            except Exception as e:
                print(f"API request error: {e}. Retrying after {BACKOFF_TIME} seconds...")
                retry_count += 1
                time.sleep(BACKOFF_TIME)
        print("API request failed after maximum retries.")
        return None
