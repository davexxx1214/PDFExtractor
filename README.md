# PDF Text Extractor with OpenAI Processing

A Python tool that extracts text from PDF files and processes it using OpenAI's GPT models to identify document types, dates, and investment names.

## Features

- PDF text extraction
- OpenAI GPT processing
- Automatic document type classification
- Date and investment name extraction
- Single file and batch processing modes
- Directory-based validation
- Results export to CSV
- Configurable prompts and settings

## Prerequisites

- Python 3.10 or higher
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PDFExtractor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up configuration files:
```bash
# Copy and edit config.json
copy config.json.example config.json  # Windows
cp config.json.example config.json    # Linux/Mac
```

5. Edit `config.json` with your API settings:
```json
{
    "api_base": "your-api-base-url",
    "api_key": "your-api-key-here",
    "model": "your-model-name"
}
```

## Directory Structure

```
PDFExtractor/
├── pdfs/                      # Root directory for PDF files
│   ├── Financial Statement/   # Subdirectory for financial statements
│   │   ├── report1.pdf
│   │   └── report2.pdf
│   ├── Cash Notice/          # Subdirectory for cash notices
│   │   └── notice1.pdf
│   └── [Other Document Types]/
├── config.json               # Configuration file
├── config.json.example
├── prompt.txt               # System prompt file
├── requirements.txt
├── scanpdf.py              # PDF scanning and analysis script
└── README.md
```

## Usage

### Single File Processing

1. To process a single PDF file and get JSON output:
```bash
python main.py "Financial Statement/app.pdf"
```

Example output:
```json
{
  "documentType": "Financial Statement",
  "DocDate": "12/30/2023",
  "InvestmentName": "Apple Inc."
}
```

### Batch Processing

1. Create subdirectories in the `pdfs` directory for each document type:
   - The directory name should match exactly with the expected document type
   - Example directory names:
     - `Financial Statement`
     - `Cash Notice`
     - `K-1 and Tax Information`
     - etc.

2. Place PDF files in their corresponding type directories:
   ```
   pdfs/
   ├── Financial Statement/
   │   ├── q4_report.pdf
   │   └── annual_statement.pdf
   ├── Cash Notice/
   │   └── payment_notice.pdf
   ```

3. Run the scanning script for batch processing:
```bash
python scanpdf.py
```

4. The script will:
   - Scan all PDF files in the `pdfs` directory and its subdirectories
   - Extract text from each PDF
   - Process the text using the configured LLM
   - Compare LLM's classification with the directory name
   - Generate a `result.csv` file with the results

### Results

#### Single File Output
When processing a single file using `main.py`, the output will be a JSON object containing:
- `documentType`: Document type identified by the LLM
- `DocDate`: Date extracted from the document
- `InvestmentName`: Investment name found in the document

Example:
```json
{
  "documentType": "Financial Statement",
  "DocDate": "12/30/2023",
  "InvestmentName": "Apple Inc."
}
```

#### Batch Processing Output
The `result.csv` file from batch processing contains:
- `file_name`: Name of the processed PDF file
- `root_folder`: Name of the parent directory under `pdfs/`
- `documentType`: Document type identified by the LLM
- `DocDate`: Date extracted from the document
- `InvestmentName`: Investment name found in the document
- `isDocTypeCorrect`: Whether LLM's classification matches the directory name (true/false)

Example CSV content:
```csv
file_name,root_folder,documentType,DocDate,InvestmentName,isDocTypeCorrect
q4_report.pdf,Financial Statement,Financial Statement,2023-12-31,ABC Fund,true
payment_notice.pdf,Cash Notice,Cash Notice,2024-01-15,XYZ Investment,true
invalid.pdf,K-1 and Tax Information,ERROR,Failed to extract text,,false
```

## Error Handling

- Failed PDF processing is logged in `result.csv` with:
  - `documentType`: "ERROR"
  - `DocDate`: Error message
  - `isDocTypeCorrect`: false

## Customization

- Modify `prompt.txt` to adjust the LLM's behavior
- Update document type directories as needed
- Configure API settings in `config.json`