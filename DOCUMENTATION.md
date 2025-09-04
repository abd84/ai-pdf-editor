# PDF Editor - Technical Documentation

## Architecture Overview

The PDF Editor is built using a modern, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   LLM APIs      │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PyMuPDF       │
                       │   PDF Engine    │
                       └─────────────────┘
```

## Core Components

### 1. LLM Client (`llm_client.py`)
- Handles communication with various LLM APIs
- Parses user prompts into structured edit requests
- Humanizes AI-generated content
- Falls back to rule-based parsing when LLM is unavailable

### 2. PDF Editor (`pdf_editor.py`)
- Extracts text and metadata from PDF files
- Applies edits (replacement, highlighting, heading modification)
- Maintains document formatting and layout
- Validates PDF integrity

### 3. FastAPI Application (`main.py`)
- RESTful API endpoints
- File upload handling
- Web interface serving
- Error handling and logging

## API Endpoints

### Core Endpoints

#### `POST /api/edit-pdf`
Edit a PDF file based on a text prompt.

**Parameters:**
- `file`: PDF file (multipart/form-data)
- `prompt`: Text describing the desired changes

**Response:**
- Success: PDF file download
- Error: JSON error message

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/edit-pdf" \
  -F "file=@document.pdf" \
  -F "prompt=Change 'Chapter 1' to 'Introduction'"
```

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

#### `GET /api/examples`
Get example prompts for users.

**Response:**
```json
[
  {
    "category": "Text Replacement",
    "examples": [
      "In the second paragraph, change 'The system is efficient' to 'The system demonstrates high levels of operational efficiency.'"
    ]
  }
]
```

## Supported Edit Types

### 1. Text Replacement
Replace specific text with new content.

**Prompt Patterns:**
- "Change '[original text]' to '[new text]'"
- "Replace '[original text]' with '[new text]'"
- "In the [location], change '[original text]' to '[new text]'"

**Examples:**
```
Change 'artificial intelligence' to 'machine learning'
Replace 'data processing' with 'information analysis'
In the conclusion, change 'results show' to 'findings indicate'
```

### 2. Heading Modification
Modify heading text while preserving formatting.

**Prompt Patterns:**
- "Change the heading '[original]' to '[new]'"
- "Modify heading '[original]' to '[new]'"

**Examples:**
```
Change the heading 'Chapter 2: Background' to 'Chapter 2: Literature Review'
Modify heading 'Methodology' to 'Research Methods'
```

### 3. Text Highlighting
Add yellow highlights to specified text.

**Prompt Patterns:**
- "Highlight '[text]'"
- "Mark '[text]' in yellow"
- "Emphasize '[text]'"

**Examples:**
```
Highlight the sentence discussing financial projections
Mark all mentions of 'machine learning' in yellow
Emphasize the conclusion paragraph
```

## Content Humanization

The system automatically detects and humanizes AI-generated text using several techniques:

### Detection Patterns
The system identifies potentially AI-generated text by looking for:
- Formal language patterns
- Common AI phrases ("demonstrates", "showcases", "furthermore")
- Overly structured sentences
- Technical jargon overuse

### Humanization Techniques
1. **Vocabulary Substitution**: Replace formal words with casual alternatives
2. **Sentence Structure Variation**: Mix short and long sentences
3. **Natural Transitions**: Use conversational connectors
4. **Imperfection Introduction**: Add slight irregularities humans make
5. **Personal Touch**: Include colloquialisms where appropriate

### Example Transformation
**Before (AI-like):**
> "The system demonstrates significant operational efficiency and showcases comprehensive functionality. Furthermore, the methodology facilitates optimal performance."

**After (Humanized):**
> "This system works really well and covers everything you need. Plus, our approach helps it perform at its best."

## Configuration

### Environment Variables

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# File handling
MAX_FILE_SIZE=50000000  # 50MB
ALLOWED_FILE_TYPES=pdf

# Application settings
DEBUG=True
```

### Deployment Options

#### 1. Local Development
```bash
# Setup
chmod +x setup.sh
./setup.sh
source venv/bin/activate

# Run
python main.py
```

#### 2. Docker
```bash
# Build and run
docker-compose up --build

# Or manually
docker build -t pdf-editor .
docker run -p 8000:8000 pdf-editor
```

#### 3. Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## Error Handling

### Common Errors

#### 400 Bad Request
- Invalid file type (not PDF)
- File size exceeds limit
- Missing required parameters

#### 422 Unprocessable Entity
- Malformed request data
- Invalid JSON in request body

#### 500 Internal Server Error
- PDF processing failure
- LLM API errors
- System resource issues

### Error Response Format
```json
{
  "detail": "Error description",
  "type": "error_type",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Security Considerations

### File Upload Security
- File type validation (PDF only)
- File size limits (50MB max)
- Temporary file cleanup
- Input sanitization

### API Security
- Rate limiting (recommended in production)
- Input validation
- Error message sanitization
- CORS configuration

### Data Privacy
- Files are temporarily stored and deleted after processing
- No persistent storage of user content
- API keys stored securely in environment variables

## Performance Optimization

### PDF Processing
- Efficient text extraction using PyMuPDF
- Minimal memory footprint
- Batch processing for multiple edits

### LLM Integration
- Asynchronous API calls
- Fallback to rule-based processing
- Response caching (can be implemented)

### File Management
- Automatic cleanup of temporary files
- Streaming file responses
- Optimized file I/O operations

## Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest test_main.py -v
```

### Test Coverage
- API endpoint testing
- File upload validation
- Error handling verification
- Integration testing with mock LLMs

## Monitoring and Logging

### Application Logs
- Request/response logging
- Error tracking
- Performance metrics
- File processing statistics

### Health Monitoring
- Health check endpoint
- System resource monitoring
- API availability checks

## Troubleshooting

### Common Issues

#### "Import fitz could not be resolved"
```bash
# Install PyMuPDF
pip install PyMuPDF
```

#### "OpenAI API key not found"
```bash
# Set environment variable
export OPENAI_API_KEY="your_key_here"
```

#### "Permission denied on uploads directory"
```bash
# Fix permissions
chmod 755 uploads outputs
```

### Debug Mode
Enable debug mode for detailed error information:
```bash
export DEBUG=True
python main.py
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Make your changes
5. Run tests: `pytest`
6. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code style
- Add type hints to all functions
- Write docstrings for all public methods
- Include unit tests for new features

## License

This project is open source and available under the MIT License.
