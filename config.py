"""
Configuration settings for the PDF Editor application
"""

import os
from pathlib import Path
from typing import List

# Base directory
BASE_DIR = Path(__file__).parent

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# File handling
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
ALLOWED_FILE_TYPES = ["pdf"]
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# PDF Processing
DEFAULT_FONT_SIZE = 12
HEADING_FONT_SIZE_MULTIPLIER = 1.2
HIGHLIGHT_COLOR = (1, 1, 0)  # Yellow in RGB (0-1 scale)

# LLM Configuration
OPENAI_MODEL = "gpt-3.5-turbo"
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
LLM_TEMPERATURE = 0.1
MAX_TOKENS = 1000

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://your-domain.vercel.app"
]

# Humanization patterns
AI_INDICATORS = [
    "demonstrates", "showcases", "furthermore", "moreover", 
    "consequently", "thus", "therefore", "in addition",
    "operational efficiency", "high levels", "significant impact",
    "comprehensive", "facilitate", "optimize", "leverage"
]

# Humanization replacements
HUMANIZATION_REPLACEMENTS = {
    "utilize": "use",
    "demonstrate": "show",
    "furthermore": "also",
    "in addition": "plus",
    "consequently": "so",
    "facilitate": "help",
    "optimize": "improve",
    "leverage": "use",
    "comprehensive": "complete",
    "methodology": "method"
}

# File cleanup settings
CLEANUP_INTERVAL_HOURS = 1
MAX_FILE_AGE_HOURS = 24
