# Prompt-Driven PDF Editor

A proof-of-concept intelligent PDF editor that uses Large Language Models (LLM) to modify document content based on simple text prompts with humanized content generation.
check it out @http://159.223.198.145:8000

## Features

- **Text Replacement**: Change specific sentences or paragraphs
- **Heading Alteration**: Modify heading text
- **Text Highlighting**: Apply yellow highlights to specified text
- **Humanized Content**: AI-generated text designed to avoid detection
- **Document Integrity**: Preserves original layout and formatting

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## API Endpoints

- `GET /` - Web interface
- `POST /api/edit-pdf` - Edit PDF with prompt
- `GET /api/health` - Health check

## Usage

1. Upload a PDF file
2. Enter a prompt describing the desired changes
3. Download the modified PDF

## Example Prompts

- "In the second paragraph, change 'The system is efficient' to 'The system demonstrates high levels of operational efficiency.'"
- "Change the heading 'Chapter 2: Background' to 'Chapter 2: Foundational Concepts.'"
- "Highlight the sentence discussing financial projections."

## Tech Stack

- **Backend**: FastAPI (Python)
- **PDF Processing**: PyMuPDF (Fitz)
- **LLM Integration**: OpenAI API, Anthropic Claude, Google Gemini
- **Deployment**: Vercel/Netlify compatible
