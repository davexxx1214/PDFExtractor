import os
import json
import csv
import glob
from typing import Dict, Any, Tuple
import requests
from PyPDF2 import PdfReader

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_llm_analysis(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get analysis from LLM API"""
    with open('prompt.txt', 'r') as f:
        prompt = f.read()

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": config['model'],
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
    }
    
    response = requests.post(
        f"{config['api_base']}/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    
    # Extract the JSON response from the LLM's message
    llm_response = response.json()['choices'][0]['message']['content']
    
    # Clean up the response by removing markdown code block if present
    llm_response = llm_response.strip()
    if llm_response.startswith('```json'):
        llm_response = llm_response[7:]  # Remove ```json
    if llm_response.endswith('```'):
        llm_response = llm_response[:-3]  # Remove ```
    llm_response = llm_response.strip()
    
    try:
        # Fix double quotes if present
        llm_response = llm_response.replace('""', '"')
        return json.loads(llm_response)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse LLM response as JSON: {llm_response}\nError: {str(e)}")

def get_correct_document_type(file_path: str) -> str:
    """Get the correct document type from the parent directory name"""
    # Get the parent directory name
    parent_dir = os.path.basename(os.path.dirname(file_path))
    return parent_dir

def find_pdf_files(base_dir: str = "pdfs") -> list[str]:
    """Recursively find all PDF files in the base directory and its subdirectories"""
    pdf_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def main():
    # Create pdfs directory if it doesn't exist
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")
        print("Created 'pdfs' directory. Please place your PDF files in appropriate subdirectories.")
        return

    # Load configuration
    config = load_config()
    
    # Prepare CSV file
    csv_fields = ['file_name', 'root_folder', 'documentType', 'DocDate', 'InvestmentName', 'isDocTypeCorrect']
    with open('result.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()
        
        # Process all PDF files in the pdfs directory and its subdirectories
        for pdf_path in find_pdf_files():
            try:
                # Get the correct document type from directory name
                correct_doc_type = get_correct_document_type(pdf_path)
                # Get the root folder name (first subdirectory under pdfs)
                root_folder = os.path.basename(os.path.dirname(pdf_path))
                
                # Extract text from PDF
                text = extract_text_from_pdf(pdf_path)
                
                # Get analysis from LLM
                analysis = get_llm_analysis(text, config)
                
                # Check if LLM's document type matches directory name
                is_doc_type_correct = analysis['documentType'] == correct_doc_type
                
                # Write results to CSV
                writer.writerow({
                    'file_name': os.path.basename(pdf_path),
                    'root_folder': root_folder,
                    'documentType': analysis['documentType'],
                    'DocDate': analysis['DocDate'],
                    'InvestmentName': analysis['InvestmentName'],
                    'isDocTypeCorrect': is_doc_type_correct
                })
                
                print(f"Processed: {pdf_path}")
                print(f"Root folder: {root_folder}")
                print(f"Directory type: {correct_doc_type}")
                print(f"LLM type: {analysis['documentType']}")
                print(f"Match: {is_doc_type_correct}")
                print("-" * 50)
                
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                # Write error entry to CSV
                writer.writerow({
                    'file_name': os.path.basename(pdf_path),
                    'root_folder': os.path.basename(os.path.dirname(pdf_path)),
                    'documentType': 'ERROR',
                    'DocDate': str(e),
                    'InvestmentName': '',
                    'isDocTypeCorrect': False
                })

if __name__ == "__main__":
    main()
