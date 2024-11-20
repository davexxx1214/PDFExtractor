import os
import json
import csv
import glob
from typing import Dict, Any, Tuple
import requests
from PyPDF2 import PdfReader
import re

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

def split_text_into_chunks(text: str, max_tokens: int = 1000) -> list[str]:
    """Split text into chunks that won't exceed the token limit"""
    # 使用简单的估算：平均每个单词4个字符，每个token约等于4个字符
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    
    # 如果文本长度在限制之内，直接返回
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # 按段落分割文本
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        # 如果当前段落加上现有chunk不会超过限制，就添加到当前chunk
        if len(current_chunk) + len(paragraph) <= max_chars:
            current_chunk += paragraph + '\n'
        else:
            # 如果当前chunk不为空，添加到chunks列表
            if current_chunk:
                chunks.append(current_chunk.strip())
            # 开始新的chunk
            current_chunk = paragraph + '\n'
    
    # 添加最后一个chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def fix_json_format(json_str: str) -> str:
    """修复常见的JSON格式问题"""
    import re
    
    # 移除所有控制字符（除了换行和制表符）
    json_str = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', json_str)
    
    # 处理公司名称中的特殊字符
    def fix_company_name(match):
        key = match.group(1)
        value = match.group(2)
        
        # 如果是InvestmentName字段，需要特殊处理
        if key == "InvestmentName":
            # 转义引号和其他特殊字符
            value = value.replace('"', '\\"')
            # 处理公司名称中的常见后缀
            suffixes = [", L.P.", ", LP", ", Inc.", ", LLC", ", Ltd.", ", Limited", ", Corp.", ", Corporation"]
            for suffix in suffixes:
                if suffix in value:
                    # 确保后缀前的引号被正确处理
                    parts = value.split(suffix)
                    value = parts[0] + suffix.replace(", ", "\\, ")
        
        return f'"{key}": "{value}"'
    
    # 修复日期格式问题
    json_str = re.sub(r'"([^"]+?)",\s*(\d{4})"', r'\1, \2', json_str)
    
    # 修复字段值中的特殊字符
    pattern = r'"([^"]+)"\s*:\s*"([^"}]*?)(?:"|,|\})'
    json_str = re.sub(pattern, fix_company_name, json_str)
    
    # 确保所有键值对正确结束
    json_str = re.sub(r'",\s*([}\]])', '"\1', json_str)
    
    # 修复可能的多余逗号
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # 修复可能的转义问题
    json_str = json_str.replace('\\"', '"').replace('\\,', ',')
    
    try:
        # 尝试解析JSON，如果成功则返回格式化后的字符串
        parsed = json.loads(json_str)
        return json.dumps(parsed)
    except json.JSONDecodeError:
        # 如果解析失败，返回原始修复的字符串
        return json_str

def convert_date_format(date_str: str) -> str:
    """将各种日期格式转换为MM/DD/YYYY格式"""
    if not date_str or date_str.strip() == "":
        return ""
        
    import re
    from datetime import datetime
    
    # 清理日期字符串
    date_str = date_str.strip()
    
    # 常见的月份名称映射
    month_names = {
        'january': '1', 'jan': '1',
        'february': '2', 'feb': '2',
        'march': '3', 'mar': '3',
        'april': '4', 'apr': '4',
        'may': '5',
        'june': '6', 'jun': '6',
        'july': '7', 'jul': '7',
        'august': '8', 'aug': '8',
        'september': '9', 'sep': '9',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12'
    }
    
    try:
        # 如果已经是MM/DD/YYYY格式，直接返回
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            return date_str
            
        # 移除多余的引号和空格
        date_str = re.sub(r'["\']', '', date_str).strip()
        
        # 处理月份名称格式 (例如: July 28, 2024)
        month_pattern = r'([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*,?\s*(\d{4})?'
        match = re.match(month_pattern, date_str, re.IGNORECASE)
        if match:
            month = month_names.get(match.group(1).lower())
            day = match.group(2)
            year = match.group(3) or str(datetime.now().year)
            if month:
                return f"{int(month):02d}/{int(day):02d}/{year}"
        
        # 处理YYYY-MM-DD格式
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{int(month):02d}/{int(day):02d}/{year}"
        
        # 处理DD-MM-YYYY或MM-DD-YYYY格式
        match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_str)
        if match:
            m1, m2, year = match.groups()
            # 假设第一个数字如果大于12则为日期，否则为月份
            if int(m1) > 12:
                day, month = m1, m2
            else:
                month, day = m1, m2
            return f"{int(month):02d}/{int(day):02d}/{year}"
        
        # 如果没有年份，添加当前年份
        if not re.search(r'\d{4}', date_str):
            date_str = f"{date_str}, {datetime.now().year}"
            # 重新尝试转换
            return convert_date_format(date_str)
            
        print(f"警告：无法解析日期格式: {date_str}")
        return date_str
        
    except Exception as e:
        print(f"日期转换错误 '{date_str}': {str(e)}")
        return date_str

def process_single_chunk(text: str, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single chunk of text with the LLM API"""
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
    
    llm_response = response.json()['choices'][0]['message']['content']
    
    # 清理响应文本
    llm_response = llm_response.strip()
    
    # 移除markdown代码块标记
    if llm_response.startswith('```json'):
        llm_response = llm_response[7:]
    elif llm_response.startswith('```'):
        llm_response = llm_response[3:]
    if llm_response.endswith('```'):
        llm_response = llm_response[:-3]
    
    # 清理文本
    llm_response = llm_response.strip()
    
    # 修复JSON格式
    llm_response = fix_json_format(llm_response)
    
    try:
        # 尝试解析JSON
        result = json.loads(llm_response)
        
        # 清理投资名称中的特殊字符
        if 'InvestmentName' in result:
            # 移除多余的空格
            result['InvestmentName'] = result['InvestmentName'].strip()
            # 标准化公司后缀
            suffixes = [", L.P.", ", LP", ", Inc.", ", LLC", ", Ltd.", ", Limited", ", Corp.", ", Corporation"]
            for suffix in suffixes:
                if suffix.upper() in result['InvestmentName'].upper():
                    # 获取基本名称和后缀
                    base_name = result['InvestmentName'].upper().split(suffix.upper())[0]
                    # 重建标准化的名称
                    result['InvestmentName'] = base_name + suffix
                    break
        
        # 转换日期格式
        if 'DocDate' in result:
            result['DocDate'] = convert_date_format(result['DocDate'])
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误。响应内容：\n{llm_response}")
        print(f"错误信息：{str(e)}")
        
        # 如果解析失败，尝试提取和清理各个字段
        try:
            # 使用正则表达式提取可能的值
            doc_type_match = re.search(r'"documentType"\s*:\s*"([^"]*)"', llm_response)
            doc_date_match = re.search(r'"DocDate"\s*:\s*"([^"}]*?)(?:"\s*,\s*\d{4})?(?:"|,|\})', llm_response)
            inv_name_match = re.search(r'"InvestmentName"\s*:\s*"([^"}]*?)(?:"|,|\})', llm_response)
            
            # 清理并标准化投资名称
            investment_name = ""
            if inv_name_match:
                investment_name = inv_name_match.group(1).strip()
                # 标准化公司后缀
                suffixes = [", L.P.", ", LP", ", Inc.", ", LLC", ", Ltd.", ", Limited", ", Corp.", ", Corporation"]
                for suffix in suffixes:
                    if suffix.upper() in investment_name.upper():
                        base_name = investment_name.upper().split(suffix.upper())[0]
                        investment_name = base_name + suffix
                        break
            
            # 清理并转换日期格式
            doc_date = ""
            if doc_date_match:
                doc_date = doc_date_match.group(1)
                year_match = re.search(r'(\d{4})', llm_response)
                if year_match and year_match.group(1) not in doc_date:
                    doc_date = f"{doc_date}, {year_match.group(1)}"
                doc_date = convert_date_format(doc_date)
            
            return {
                "documentType": doc_type_match.group(1) if doc_type_match else "",
                "DocDate": doc_date,
                "InvestmentName": investment_name,
                "isDocTypeCorrect": False
            }
        except Exception as ex:
            print(f"提取字段失败：{str(ex)}")
            return {
                "documentType": "",
                "DocDate": "",
                "InvestmentName": "",
                "isDocTypeCorrect": False
            }

def merge_analysis_results(results: list[Dict[str, Any]]) -> Dict[str, Any]:
    """合并多个文本块的分析结果"""
    if not results:
        return {
            "documentType": "",
            "DocDate": "",
            "InvestmentName": "",
            "isDocTypeCorrect": False
        }
    
    if len(results) == 1:
        return results[0]
    
    from collections import Counter
    
    # 初始化合并结果
    merged = {
        "documentType": "",
        "DocDate": "",
        "InvestmentName": "",
        "isDocTypeCorrect": False
    }
    
    # 收集所有非空值
    doc_types = []
    dates = []
    names = []
    
    for result in results:
        if result.get("documentType"):
            doc_types.append(result["documentType"])
        if result.get("DocDate"):
            dates.append(result["DocDate"])
        if result.get("InvestmentName"):
            names.append(result["InvestmentName"])
    
    # 1. documentType: 使用出现最多的类型
    if doc_types:
        doc_type_counter = Counter(doc_types)
        merged["documentType"] = doc_type_counter.most_common(1)[0][0]
    
    # 2. DocDate: 使用最新的有效日期
    valid_dates = []
    for date in dates:
        try:
            # 将日期转换为datetime对象进行比较
            from datetime import datetime
            # 假设日期格式为MM/DD/YYYY
            date_obj = datetime.strptime(date, "%m/%d/%Y")
            valid_dates.append((date_obj, date))
        except (ValueError, TypeError):
            continue
    
    if valid_dates:
        # 选择最新的日期
        merged["DocDate"] = sorted(valid_dates, reverse=True)[0][1]
    
    # 3. InvestmentName: 使用最完整的名称
    if names:
        # 选择最长的名称，假设它最完整
        # 如果长度相同，选择出现次数最多的
        name_counter = Counter(names)
        longest_names = sorted(names, key=lambda x: (len(x), name_counter[x]), reverse=True)
        merged["InvestmentName"] = longest_names[0]
    
    # 4. 添加合并统计信息
    merged["_merge_stats"] = {
        "total_chunks": len(results),
        "doc_type_agreement": f"{doc_types.count(merged['documentType'])}/{len(doc_types)}" if doc_types else "0/0",
        "date_candidates": len(valid_dates),
        "name_candidates": len(set(names))
    }
    
    return merged

def get_llm_analysis(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get analysis from LLM API with support for long texts"""
    with open('prompt.txt', 'r') as f:
        prompt = f.read()

    # 分割文本为多个块
    text_chunks = split_text_into_chunks(text)
    
    # 如果只有一个块，直接处理
    if len(text_chunks) == 1:
        return process_single_chunk(text_chunks[0], prompt, config)
    
    # 如果有多个块，分别处理每个块
    all_results = []
    for i, chunk in enumerate(text_chunks):
        chunk_prompt = f"{prompt}\n注意：这是文档的第{i+1}/{len(text_chunks)}部分，请分析这部分内容。"
        chunk_result = process_single_chunk(chunk, chunk_prompt, config)
        all_results.append(chunk_result)
    
    # 合并所有结果
    merged_result = merge_analysis_results(all_results)
    
    # 移除合并统计信息（如果不需要输出到最终结果）
    if "_merge_stats" in merged_result:
        del merged_result["_merge_stats"]
    
    return merged_result

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
