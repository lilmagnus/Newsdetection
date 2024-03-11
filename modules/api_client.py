# api_client.py
import openai
import time
import os
from config import API_KEY, MODEL, MAX_RETRIES, BACKOFF_TIME, MAX_TOKENS

class APIClient:
    def __init__(self):
        openai.api_key = API_KEY
    
    def chunk_text(self, text, max_length=1500):
        """Utility method to chunk text into smaller parts."""
        chunks = []
        while text:
            chunk = text[:max_length].rsplit(' ', 1)[0]
            chunks.append(chunk)
            text = text[len(chunk):].lstrip()
        return chunks

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
                error_message = str(e)
                if "maximum context length" in error_message:
                    # Handle token limit error with chunking if the specific error message is detected.
                    print("Handling token limit error by chunking...")
                    text = "".join(msg.get("content", "") for msg in messages if msg["role"] == "user")
                    chunks = self.chunk_text(text)
                    responses = [self.make_api_request([{"role": "user", "content": chunk}]) for chunk in chunks]
                    print(responses)
                    return "\n".join(responses)
                else:
                    print(f"API request error: {error_message}. Retrying after {BACKOFF_TIME} seconds...")
                    time.sleep(BACKOFF_TIME)
                retry_count += 1
        print("API request failed after maximum retries.")
        return None
