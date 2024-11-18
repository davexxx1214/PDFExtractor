# PDF Text Extractor with OpenAI Processing

A Python tool that extracts text from PDF files and processes it using OpenAI's GPT models.

## Features

- PDF text extraction
- OpenAI GPT processing
- Configurable prompts and settings
- Simple command-line interface

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

# Edit prompt.txt with your desired system prompt
# The default prompt is already provided
```

5. Edit `config.json` with your OpenAI API key and settings:
```json
{
    "api_base": "https://api.openai.com/v1",
    "api_key": "your-api-key-here",
    "model": "gpt-4-mini"
}
```

6. (Optional) Customize the system prompt in `prompt.txt`:
```text
You are a helpful assistant that specializes in summarizing documents. Please provide clear and concise summaries.
```

## Usage

1. Place your PDF files in the `pdfs` directory:
```
PDFExtractor/
├── pdfs/
│   ├── document1.pdf
│   └── document2.pdf
```

2. Run the program:
```bash
python main.py document1.pdf
```

Example output:
```
Extracting text from PDF...
Successfully extracted text, length: 1234 characters
Processing text with OpenAI...

Result:
[OpenAI's response will appear here]
```

## Directory Structure

```
PDFExtractor/
├── pdfs/              # Place your PDF files here
├── src/
│   ├── pdf_processor.py
│   └── openai_client.py
├── config.json        # Your configuration file
├── config.json.example
├── prompt.txt         # Your system prompt file
├── requirements.txt
├── README.md
└── main.py
```

## Error Handling

- If the `pdfs` directory doesn't exist, it will be created automatically
- If the specified PDF file is not found, you'll get a helpful error message
- Configuration errors will be reported with clear instructions

## Common Issues

1. "config.json not found":
   - Make sure you've copied `config.json.example` to `config.json`
   - Update the API key in `config.json`

2. "PDF file not found":
   - Ensure your PDF file is in the `pdfs` directory
   - Check the filename matches exactly

## License

[Your chosen license]