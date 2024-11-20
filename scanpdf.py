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
    """估算文本的token数量
    
    使用简单的估算方法：
    - 英文单词约等于1个token
    - 中文字符约等于2个token
    - 标点符号和空格约等于0.25个token
    """
    # 移除多余的空白字符
    text = ' '.join(text.split())
    
    # 计算中文字符数量
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    
    # 计算英文单词数量（简单估算）
    words = len(text.split())
    
    # 计算标点符号和空格数量
    punctuation = sum(1 for char in text if not char.isalnum())
    
    # 估算总token数
    estimated_tokens = (
        chinese_chars * 2 +  # 中文字符
        words +             # 英文单词
        punctuation * 0.25  # 标点和空格
    )
    
    return int(estimated_tokens)

def truncate_text_by_tokens(text: str, max_tokens: int, reserved_tokens: int = 200) -> str:
    """将文本截断到指定的token数量以内，使用简单字符估算方法"""
    if not text:
        return text
        
    estimated_total = estimate_tokens(text)
    
    if estimated_total <= max_tokens:
        return text
    
    # 计算截断比例
    ratio = max_tokens / estimated_total
    target_length = int(len(text) * ratio)
    
    # 截取文本
    truncated_text = text[:target_length]
    
    # 找到最后一个完整段落
    last_para = truncated_text.rfind('\n\n')
    if last_para > 0:
        truncated_text = truncated_text[:last_para]
    
    # 计算最终token数
    final_tokens = estimate_tokens(truncated_text)
    print(f"文本已截断：原始token估算={estimated_total}, 截断后token估算={final_tokens}")
    
    return truncated_text.strip()

def get_llm_analysis(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get analysis from LLM API"""
    with open('prompt.txt', 'r') as f:
        prompt = f.read()
    
    # 从配置中获取token限制
    max_tokens = config.get('max_tokens', 8192)  # 默认值为8192
    reserved_tokens = config.get('reserved_tokens', 200)  # 默认值为200
    
    # 计算prompt的token数量
    prompt_tokens = estimate_tokens(prompt)
    # 为文本内容预留token空间
    max_text_tokens = max_tokens - prompt_tokens - reserved_tokens
    
    # 使用简单估算方法进行token计数和截断
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

def clear_csv_file() -> None:
    """清空CSV文件并写入表头"""
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

def main():
    # Create pdfs directory if it doesn't exist
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")
        print("Created 'pdfs' directory. Please place your PDF files in appropriate subdirectories.")
        return

    # 清空CSV文件并写入表头
    clear_csv_file()

    # Load configuration
    config = load_config()
    
    # Process all PDF files in the pdfs directory and its subdirectories
    for pdf_path in find_pdf_files():
        try:
            # Get the correct document type from directory name
            correct_doc_type = get_correct_document_type(pdf_path)
            # Get the root folder name (first subdirectory under pdfs)
            root_folder = os.path.basename(os.path.dirname(pdf_path))
            
            # Process PDF file
            process_pdf(pdf_path, config, root_folder)
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")

def process_pdf(pdf_path: str, config: Dict[str, Any], root_folder: str = "") -> None:
    """Process a single PDF file"""
    try:
        print(f"Processing {pdf_path}...")
        
        # 提取文本
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(f"Warning: No text extracted from {pdf_path}")
            return
            
        # 获取分析结果
        result = get_llm_analysis(text, config)
        if not result:
            print(f"Warning: No analysis result for {pdf_path}")
            return
            
        # 准备CSV数据
        csv_data = {
            'file_name': os.path.basename(pdf_path),
            'root_folder': root_folder,
            'documentType': result.get('documentType', ''),
            'DocDate': result.get('DocDate', ''),
            'InvestmentName': result.get('InvestmentName', ''),
            'isDocTypeCorrect': result.get('isDocTypeCorrect', '')
        }
        
        # 写入CSV
        write_to_csv(csv_data)
        print(f"Successfully processed {pdf_path}")
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")

if __name__ == "__main__":
    main()
