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
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            try:
                text += page.extract_text() + "\n"
            except Exception as e:
                print(f"Warning: Error extracting text from page in {pdf_path}: {str(e)}")
                continue
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {str(e)}")
        return ""

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in the text
    
    Using a simple estimation method:
    - English words are approximately 1 token
    - Chinese characters are approximately 2 tokens
    - Punctuation and spaces are approximately 0.25 tokens
    """
    # Remove extra whitespace characters
    text = ' '.join(text.split())
    
    # Calculate the number of Chinese characters
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    
    # Calculate the number of English words (simple estimation)
    words = len(text.split())
    
    # Calculate the number of punctuation and spaces
    punctuation = sum(1 for char in text if not char.isalnum())
    
    # Estimate the total number of tokens
    estimated_tokens = (
        chinese_chars * 2 +  # Chinese characters
        words +             # English words
        punctuation * 0.25  # Punctuation and spaces
    )
    
    return int(estimated_tokens)

def truncate_text_by_tokens(text: str, max_tokens: int, reserved_tokens: int = 200) -> str:
    """Truncate the text to the specified number of tokens, using a simple character estimation method"""
    if not text:
        return text
        
    estimated_total = estimate_tokens(text)
    
    if estimated_total <= max_tokens:
        return text
    
    # Calculate the truncation ratio
    ratio = max_tokens / estimated_total
    target_length = int(len(text) * ratio)
    
    # Truncate the text
    truncated_text = text[:target_length]
    
    # Find the last complete paragraph
    last_para = truncated_text.rfind('\n\n')
    if last_para > 0:
        truncated_text = truncated_text[:last_para]
    
    # Calculate the final number of tokens
    final_tokens = estimate_tokens(truncated_text)
    print(f"Text truncated: Original tokens={estimated_total}, After truncation={final_tokens}")
    
    return truncated_text.strip()

def get_llm_analysis(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get analysis from LLM API"""
    with open('prompt.txt', 'r') as f:
        prompt = f.read()
    
    # Get the token limit from the configuration
    max_tokens = config.get('max_tokens', 8192)  # Default value is 8192
    reserved_tokens = config.get('reserved_tokens', 200)  # Default value is 200
    
    # Calculate the number of tokens in the prompt
    prompt_tokens = estimate_tokens(prompt)
    # Reserve token space for the text content
    max_text_tokens = max_tokens - prompt_tokens - reserved_tokens
    
    # Use a simple estimation method for token counting and truncation
    text = truncate_text_by_tokens(
        text=text,
        max_tokens=max_text_tokens,
        reserved_tokens=reserved_tokens
    )

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

def get_correct_document_type(pdf_path: str) -> str:
    """Get the correct document type from the PDF file path (based on directory name)"""
    # Get the first subdirectory name under pdfs as the document type
    parts = pdf_path.split(os.sep)
    if 'pdfs' in parts:
        pdfs_index = parts.index('pdfs')
        if len(parts) > pdfs_index + 1:
            return parts[pdfs_index + 1]
    return ""

def find_pdf_files(base_dir: str = "pdfs") -> list[str]:
    """Recursively find all PDF files in the base directory and its subdirectories"""
    pdf_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def clear_csv_file() -> None:
    """Clear the CSV file and write the header"""
    csv_fields = ['file_name', 'root_folder', 'documentType', 'DocDate', 'InvestmentName', 'isDocTypeCorrect']
    with open('result.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()
    print("Cleared result.csv and wrote header")

def write_to_csv(data: Dict[str, Any]) -> None:
    """Write data to CSV file"""
    csv_fields = ['file_name', 'root_folder', 'documentType', 'DocDate', 'InvestmentName', 'isDocTypeCorrect']
    with open('result.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writerow(data)

def process_pdf(pdf_path: str, config: Dict[str, Any], root_folder: str = "") -> None:
    """Process a single PDF file"""
    try:
        print(f"Processing file: {pdf_path}")
        
        # Get the correct document type from the directory name
        correct_doc_type = get_correct_document_type(pdf_path)
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(f"Warning: No text could be extracted from {pdf_path}")
            return
            
        # Get analysis result
        result = get_llm_analysis(text, config)
        if not result:
            print(f"Warning: No analysis result for {pdf_path}")
            return
            
        # Check if the document type matches
        is_doc_type_correct = result.get('documentType', '').strip() == correct_doc_type.strip()
        
        # Prepare CSV data
        csv_data = {
            'file_name': os.path.basename(pdf_path),
            'root_folder': root_folder,
            'documentType': result.get('documentType', ''),
            'DocDate': result.get('DocDate', ''),
            'InvestmentName': result.get('InvestmentName', ''),
            'isDocTypeCorrect': is_doc_type_correct
        }
        
        # Print processing result
        print(f"\nAnalysis Results:")
        print(f"File: {os.path.basename(pdf_path)}")
        print(f"Expected Type: {correct_doc_type}")
        print(f"Detected Type: {result.get('documentType', '')}")
        print(f"Type Match: {is_doc_type_correct}")
        print("-" * 50)
        
        # Write to CSV
        write_to_csv(csv_data)
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        # Write error record
        csv_data = {
            'file_name': os.path.basename(pdf_path),
            'root_folder': root_folder,
            'documentType': 'ERROR',
            'DocDate': str(e),
            'InvestmentName': '',
            'isDocTypeCorrect': False
        }
        write_to_csv(csv_data)

def main():
    # Create pdfs directory if it doesn't exist
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")
        print("Created 'pdfs' directory. Please place your PDF files in appropriate subdirectories.")
        return

    # Clear CSV file and write header
    clear_csv_file()
    print("Starting PDF processing...")

    # Load configuration
    config = load_config()
    
    # Process all PDF files
    pdf_files = find_pdf_files()
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    for pdf_path in pdf_files:
        try:
            # Get the root folder name (first subdirectory under pdfs)
            root_folder = os.path.basename(os.path.dirname(pdf_path))
            process_pdf(pdf_path, config, root_folder)
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
    
    print("\nProcessing completed. Results have been saved to result.csv")

if __name__ == "__main__":
    main()
