#api_request_handler.py
import json
import openai
from api_client import APIClient  # Ensure this imports your APIClient correctly

class APIRequestHandler:
    def __init__(self):
        self.api_client = APIClient()

    def chunk_text(self, text):
        """Breaks down text into manageable chunks."""
        chunks = []
        max_length=1500
        while text:
            chunk = text[:max_length].rsplit(' ', 1)[0]
            chunks.append(chunk)
            text = text[len(chunk):].lstrip()
        return chunks

    def send_request_with_chunking(self, text):
        """Sends API requests, handling token limit errors by chunking text."""
        # Handle the token limit error by chunking the text.
        chunks = self.chunk_text(text)
        chunk_count = 1
        responses = ""
        for chunk in chunks: # Få det inn i enkel string eller????
            print(f"Parsing chunk: {chunk_count}")
            response = self.api_client.make_api_request([{"role": "user", "content": f"Reduce the length of this text by removing any duplicate information or texts that are simply repeating what has already been said. {chunk}"}])
            responses += response +'\n'
            chunk_count += 1
        return responses

# Example usage of how you might integrate a prompt template into your requests.
# This will depend heavily on how your `APIClient` and OpenAI API usage are structured.
