# document_processing.py
import fitz  # PyMuPDF

class DocumentProcessing:
    @staticmethod
    def extract_text_from_pdf(pdf_file_path):
        if not pdf_file_path.lower().endswith('.pdf'):
            raise ValueError("The file is not a PDF.")
        text = ''
        with fitz.open(pdf_file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text