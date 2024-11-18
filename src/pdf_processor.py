import PyPDF2
from pathlib import Path

class PDFProcessor:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text.strip()
        except Exception as e:
            raise Exception(f"PDF processing error: {str(e)}")
