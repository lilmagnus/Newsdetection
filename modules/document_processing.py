# document_processing.py
import fitz  # PyMuPDF
import os
from cache_manager import CacheManager
from text_analysis import TextAnalysis
from interaction_handler2 import InteractionHandler
from utils import estimate_token_count
from api_client import APIClient

class DocumentProcessing:
    def __init__(self):
        self.cache_manager = CacheManager()
        self.text_analysis = TextAnalysis()
        #self.interaction_handler = InteractionHandler()
        #self.estimate_token_count = estimate_token_count()
        self.api_client = APIClient()
    
    def estimate_token_count(self, text):
        return len(text.split())
    
    def save_text_to_file(self, text, output_file_path):
        try:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(text)
        except IOError as e:
            print(f"File write error: {e}")
    
    def extract_text_from_pdf(self, pdf_file_path):
        if not pdf_file_path.lower().endswith('.pdf'):
            print(f"Not a PDF file: {pdf_file_path}")
            return None
        text = ''
        with fitz.open(pdf_file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    
    def summarise_individual_documents(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                pdf_file_path = os.path.join(folder_path, filename)
                text = self.extract_text_from_pdf(pdf_file_path)
                if text:
                    output_file_path = os.path.splitext(pdf_file_path)[0] + '_output.txt'
                    self.save_text_to_file(text, output_file_path)

        all_summaries = ""
        sum_count = 1
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                print(sum_count, f"Summarizing: {filename}")
                summary = self.summarise_text(text)
                #all_summaries += f"\nDocument: {filename}\n{summary}" # Kanskje se om denne kan køddes med
                all_summaries += summary
                sum_count += 1
        #summ_summ = self.make_api_request([{"role": "user", "content": f"Reduce the length of this summary: {all_summaries}"}])
        print("="*20, "FINISHED", "="*20)
        #print(len(all_summaries))
        self.cache_manager.cache_response(folder_path, all_summaries)
        # Legg inn kall til categorize metode her, 
        # for å få med vurdering om hvilke kategorier det er snakk om
        #if len(all_summaries) > 20000:
        #    chunked_summaries = self.chunk_summary(all_summaries)
        #    return self.categorize(chunked_summaries)
            #return self.handle_interaction(chunked_summaries)
        #else:
        return all_summaries
    
    def summarise_text(self, text):
        summary = ""
        max_chunk_size = 1500  # Max tokens per chunk -- MÅ VÆRE 2000(?)
        chunk_count = 1
        while text:
            print("Summarizing chunk:", chunk_count)
            token_count = self.estimate_token_count(text)
            if token_count <= max_chunk_size:
                chunk = text
                text = ""  # Clear the text as we're processing it all in this chunk
            else:
                # Find the largest possible substring within token limit
                chunk = text[:max_chunk_size]
                cut_off_index = chunk.rfind('.') + 1  # Try to cut off at the last full sentence
                if cut_off_index == 0:
                    cut_off_index = text.rfind(' ', 0, max_chunk_size)  # If no period, cut off at the last space

                chunk = text[:cut_off_index].strip()
                text = text[cut_off_index:].strip()  # Remaining text for next iteration

            #response = self.make_api_request([{"role": "user", "content": f"Summarize this in 3 sentences or less, mention the date of the document if it is mentioned: {chunk}"}], max_chunk_size)
            response = self.api_client.make_api_request([{"role": "user", "content": f"Summarize this: {chunk}"}], max_chunk_size)

            if response:
                summary += response + "\n\n"
                chunk_count += 1
            else:
                break  # Exit the loop if there's no response
        
        return summary.strip()