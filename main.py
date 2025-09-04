from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import uvicorn
import os
import tempfile
import shutil
from pathlib import Path
import asyncio
from datetime import datetime

from pdf_editor import PDFEditor
from llm_client import LLMClient

# Initialize FastAPI app
app = FastAPI(
    title="Prompt-Driven PDF Editor",
    description="An intelligent PDF editor that uses LLM to modify document content based on text prompts",
    version="1.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize PDF editor
pdf_editor = PDFEditor()

# Constants
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50000000))  # 50MB
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

# Create necessary directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/edit-pdf")
async def edit_pdf(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    Edit PDF based on user prompt
    
    Args:
        file: PDF file to edit
        prompt: Text prompt describing the desired changes
    
    Returns:
        FileResponse: Modified PDF file
    """
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE} bytes")
    
    # Create temporary files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_filename = f"input_{timestamp}_{file.filename}"
    output_filename = f"edited_{timestamp}_{file.filename}"
    
    input_path = os.path.join(UPLOAD_DIR, input_filename)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate PDF
        if not pdf_editor.validate_pdf(input_path):
            raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")
        
        # Process PDF with prompt
        result_path = await pdf_editor.process_pdf(input_path, prompt, output_path)
        
        # Return the edited PDF
        return FileResponse(
            result_path,
            media_type="application/pdf",
            filename=f"edited_{file.filename}",
            headers={"Content-Disposition": f"attachment; filename=edited_{file.filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
    
    finally:
        # Cleanup input file
        if os.path.exists(input_path):
            os.remove(input_path)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/examples")
async def get_examples():
    """Get example prompts for users"""
    examples = [
        {
            "category": "Text Replacement",
            "examples": [
                "In the second paragraph, change 'The system is efficient' to 'The system demonstrates high levels of operational efficiency.'",
                "Replace 'artificial intelligence' with 'machine learning' in the abstract.",
                "Change 'data processing' to 'information analysis' throughout the document."
            ]
        },
        {
            "category": "Heading Modification",
            "examples": [
                "Change the heading 'Chapter 2: Background' to 'Chapter 2: Foundational Concepts.'",
                "Modify the title 'Introduction' to 'Overview and Objectives'",
                "Update section heading 'Methods' to 'Methodology and Approach'"
            ]
        },
        {
            "category": "Text Highlighting",
            "examples": [
                "Highlight the sentence discussing financial projections.",
                "Mark all mentions of 'machine learning' in yellow.",
                "Emphasize the conclusion paragraph."
            ]
        }
    ]
    return examples

@app.delete("/api/cleanup")
async def cleanup_files():
    """Cleanup old uploaded and output files"""
    try:
        # Remove files older than 1 hour
        current_time = datetime.now().timestamp()
        one_hour_ago = current_time - 3600
        
        cleaned_count = 0
        
        for directory in [UPLOAD_DIR, OUTPUT_DIR]:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < one_hour_ago:
                        os.remove(file_path)
                        cleaned_count += 1
        
        return {"message": f"Cleaned up {cleaned_count} old files"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )
