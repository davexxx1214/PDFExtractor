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

## Advanced Features

### Text Chunking Algorithm

The system implements a sophisticated text chunking algorithm to handle large PDF documents that exceed OpenAI's token limits:

1. **Chunk Size Control**
   - Default maximum chunk size: 1000 tokens
   - Estimated using character count (4 characters ≈ 1 token)
   - Configurable through the `max_tokens` parameter

2. **Intelligent Splitting**
   - Splits text at paragraph boundaries to maintain context
   - Preserves document structure and readability
   - Handles both short and long paragraphs efficiently

3. **Process Flow**
   ```
   PDF Text → Paragraphs → Chunks → API Processing → Merged Results
   ```

4. **Chunk Processing**
   - Each chunk is processed independently
   - Custom prompt indicating chunk position (e.g., "Part 1/3")
   - Parallel processing capability for efficiency

### JSON Merging Strategy

The system uses an intelligent strategy to merge results from multiple chunks:

1. **Document Type (documentType)**
   - Uses majority voting system
   - Selects the most frequently occurring document type
   - Helps filter out occasional misclassifications

2. **Document Date (DocDate)**
   - Collects all valid dates (MM/DD/YYYY format)
   - Selects the most recent date
   - Handles various date formats and normalizes them
   - Ignores invalid or malformed dates

3. **Investment Name (InvestmentName)**
   - Selects the most complete version of the name
   - Primary criteria: longest name version
   - Secondary criteria: frequency of occurrence
   - Handles variations in company name formats

4. **Merge Statistics**
   - Tracks total number of chunks processed
   - Monitors document type agreement ratio
   - Counts valid date candidates
   - Records unique name variations
   - Used for quality assurance and debugging

5. **Error Handling**
   - Graceful handling of parsing failures
   - Fallback mechanisms for incomplete data
   - Maintains data consistency across chunks

Example of merged results:
```json
{
  "documentType": "Financial Statement",  // Most common across chunks
  "DocDate": "07/28/2024",              // Most recent valid date
  "InvestmentName": "NVIDIA Corporation" // Most complete name version
}
```

### Quality Assurance

1. **Validation Checks**
   - Document type consistency across chunks
   - Date format standardization
   - Investment name normalization

2. **Error Recovery**
   - Handles malformed JSON responses
   - Recovers partial information when possible
   - Maintains data integrity

## Error Handling

- Failed PDF processing is logged in `result.csv` with:
  - `documentType`: "ERROR"
  - `DocDate`: Error message
  - `isDocTypeCorrect`: false

## Customization

- Modify `prompt.txt` to adjust the LLM's behavior
- Update document type directories as needed
- Configure API settings in `config.json`