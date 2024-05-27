# document_processing.py
import fitz  # PyMuPDF
import os
from cache_manager import CacheManager
from api_client import APIClient

class DocumentProcessing:
    def __init__(self):
        self.cache_manager = CacheManager()
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
                try:
                    if text:
                        output_file_path = os.path.splitext(pdf_file_path)[0] + '_output.txt'
                        self.save_text_to_file(text, output_file_path)
                except Exception as e:
                    error_message = str(e)
                    if "cannot open broken document" in error_message:
                        continue

        all_summaries = ""
        sum_count = 1
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                print(sum_count, f"Summarizing: {filename}")
                summary = self.summarise_text(text)
                all_summaries += summary
                sum_count += 1
        print("="*20, "FINISHED", "="*20)
        self.cache_manager.cache_response(folder_path, all_summaries)
        
        return all_summaries
    
    def summarise_text(self, text):
        summary = ""
        max_chunk_size = 1500  # Max tokener per chunk
        chunk_count = 1
        while text:
            print("Summarizing chunk:", chunk_count)
            token_count = self.estimate_token_count(text)
            if token_count <= max_chunk_size:
                chunk = text
                text = ""  # Fjern teksten fordi vi prosesserer alt i denne chunken
            else:
                # Finn største mulige sub-string i chunken.
                chunk = text[:max_chunk_size]
                cut_off_index = chunk.rfind('.') + 1  # Prøv å stoppe ved siste fulle setning.
                if cut_off_index == 0:
                    cut_off_index = text.rfind(' ', 0, max_chunk_size)  # Hvis det ikke finnes punktum, stopp ved siste mellomrom.

                chunk = text[:cut_off_index].strip()
                text = text[cut_off_index:].strip()  # Gjenværende tekst for neste iterasjon

            response = self.api_client.make_api_request([{"role": "user", "content": f"Summarize this: {chunk}"}])

            if response:
                summary += response + "\n\n"
                chunk_count += 1
            else:
                break  # Exit loopen om det ikke er respons.
        
        return summary.strip()