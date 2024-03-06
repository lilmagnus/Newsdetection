# text_analysis.py
from api_client import APIClient

class TextAnalysis:
    def __init__(self):
        self.api_client = APIClient()

    def analyze_text(self, text):
        # Define your analysis request here. This is a placeholder function.
        # For example, you might want to summarize the text or get its sentiment.
        messages = [{
            "role": "system",
            "content": "Analyze the following text"
        }, {
            "role": "user",
            "content": text
        }]
        
        # Adjust the request as needed for your specific analysis task
        response = self.api_client.make_api_request(messages)
        return response
