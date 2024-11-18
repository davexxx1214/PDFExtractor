from src.pdf_processor import PDFProcessor
from src.openai_client import OpenAIClient
import argparse
from pathlib import Path

DEFAULT_PDF_DIR = "pdfs"

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='PDF Text Extraction and OpenAI Processing Tool')
    parser.add_argument('pdf_name', help='Name of the PDF file in the pdfs directory (e.g., document.pdf)')
    args = parser.parse_args()

    try:
        # Ensure pdfs directory exists
        pdf_dir = Path(DEFAULT_PDF_DIR)
        if not pdf_dir.exists():
            pdf_dir.mkdir(exist_ok=True)
            print(f"Created '{DEFAULT_PDF_DIR}' directory for PDF files")
            print(f"Please place your PDF files in the '{DEFAULT_PDF_DIR}' directory")
            return

        # Construct full PDF path
        pdf_path = pdf_dir / args.pdf_name
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {args.pdf_name}\nPlease place your PDF file in the '{DEFAULT_PDF_DIR}' directory")

        # Initialize OpenAI client
        openai_client = OpenAIClient()
        
        # Extract PDF text
        print("Extracting text from PDF...")
        text = PDFProcessor.extract_text(str(pdf_path))
        print(f"Successfully extracted text, length: {len(text)} characters")
        
        # Process text
        print("Processing text ...")
        result = openai_client.process_text(text)
        print("\nResult:")
        print(result)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
