# Try to import PyMuPDF, handle if not available
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("PyMuPDF not available. PDF processing functionality will be limited.")

from typing import List, Tuple, Optional, Dict, Any
import re
from dataclasses import dataclass
from llm_client import EditRequest, LLMClient

@dataclass
class TextBlock:
    """Represents a text block in the PDF"""
    def __init__(self, text: str, bbox: Tuple[float, float, float, float], 
                 page_num: int, font_size: float, font_name: str = None):
        self.text = text
        self.bbox = bbox  # x0, y0, x1, y1
        self.page_num = page_num
        self.font_size = font_size
        self.font_name = font_name
        
        # Determine if this is likely a heading based on text characteristics
        self.is_heading = self._is_heading()
    
    def _is_heading(self) -> bool:
        """Determine if this block is likely a heading based on various heuristics"""
        text = self.text.strip()
        
        # Empty text can't be a heading
        if not text:
            return False
            
        # Very short text (1-7 words) that's mostly capitalized is likely a heading
        words = text.split()
        word_count = len(words)
        
        if word_count <= 7:
            capitalized_ratio = sum(1 for w in words if w and w[0].isupper()) / max(1, word_count)
            if capitalized_ratio > 0.5:
                return True
        
        # Text ending with colon but not too long might be a heading
        if text.endswith(':') and word_count < 10:
            return True
            
        # All caps short text is likely a heading
        if text.isupper() and word_count < 5:
            return True
            
        # Text without punctuation (except ?, !, .) and not too long is likely a heading
        if (word_count < 12 and 
            not any(c in text for c in [',', ';', ':', '(', ')', '"', "'"])):
            return True
            
        return False

class PDFEditor:
    """Main class for PDF editing operations"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def extract_text_blocks(self, pdf_path: str) -> Tuple[List[TextBlock], str]:
        """Extract text blocks and full text from PDF"""
        doc = fitz.open(pdf_path)
        text_blocks = []
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                bbox = span["bbox"]
                                font_size = span["size"]
                                font_name = span["font"]
                                
                                # Create TextBlock object (is_heading is determined in the constructor)
                                text_block = TextBlock(
                                    text=text,
                                    bbox=bbox,
                                    page_num=page_num,
                                    font_size=font_size,
                                    font_name=font_name
                                )
                                
                                # Enhanced heading detection - combine object's built-in detection with font size check
                                avg_font_size = self._calculate_average_font_size(blocks)
                                if font_size > avg_font_size * 1.2:
                                    text_block.is_heading = True
                                
                                text_blocks.append(text_block)
                                full_text += text + " "
        
        doc.close()
        return text_blocks, full_text.strip()
    
    def _calculate_average_font_size(self, blocks: Dict) -> float:
        """Calculate average font size for heading detection"""
        font_sizes = []
        for block in blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])
        
        return sum(font_sizes) / len(font_sizes) if font_sizes else 12
    
    async def process_pdf(self, pdf_path: str, prompt: str, output_path: str) -> str:
        """Process PDF with the given prompt"""
        try:
            # Extract text from PDF
            text_blocks, full_text = self.extract_text_blocks(pdf_path)
            
            # Parse prompt using LLM
            edit_requests = await self.llm_client.parse_prompt(prompt, full_text)
            
            # Apply edits to PDF
            await self._apply_edits(pdf_path, edit_requests, text_blocks, output_path)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")
    
    async def _apply_edits(self, pdf_path: str, edit_requests: List[EditRequest], 
                          text_blocks: List[TextBlock], output_path: str):
        """Apply all edit requests to the PDF"""
        doc = None
        try:
            doc = fitz.open(pdf_path)
            
            print(f"Applying {len(edit_requests)} edit requests to PDF")
            for idx, edit_request in enumerate(edit_requests):
                print(f"Processing edit request {idx+1}: action={edit_request.action}, target='{edit_request.target_text}'")
                
                if edit_request.action == "replace":
                    await self._apply_text_replacement(doc, edit_request, text_blocks)
                elif edit_request.action == "highlight":
                    await self._apply_highlight(doc, edit_request, text_blocks)
                elif edit_request.action == "modify_heading":
                    await self._apply_heading_modification(doc, edit_request, text_blocks)
            
            doc.save(output_path)
            print(f"Saved edited PDF to {output_path}")
        except Exception as e:
            error_msg = f"Error applying edits: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        finally:
            if doc:
                doc.close()
    
    async def _apply_text_replacement(self, doc: fitz.Document, 
                                    edit_request: EditRequest, 
                                    text_blocks: List[TextBlock]):
        """Apply text replacement to PDF"""
        target_text = edit_request.target_text.strip()
        replacement_text = edit_request.replacement_text
        
        # Humanize the replacement text if it seems AI-generated
        if self._seems_ai_generated(replacement_text):
            replacement_text = await self.llm_client.humanize_text(replacement_text)
        
        # Find the target text in text blocks
        matching_blocks = self._find_matching_text_blocks(target_text, text_blocks, edit_request.context)
        
        for block in matching_blocks:
            page = doc[block.page_num]
            
            # Create a white rectangle to cover the original text
            rect = fitz.Rect(block.bbox)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Insert new text at the same location
            try:
                page.insert_text(
                    (rect.x0, rect.y0 + block.font_size * 0.8),
                    replacement_text,
                    fontsize=block.font_size,
                    fontname=block.font_name,
                    color=(0, 0, 0)
                )
            except Exception as font_error:
                print(f"Font error in text replacement: {font_error}")
                # Try fallback fonts for text replacement
                fallback_fonts = ["helv", "times", "cour", "Helvetica", "Times-Roman"]
                inserted = False
                
                for fallback_font in fallback_fonts:
                    try:
                        page.insert_text(
                            (rect.x0, rect.y0 + block.font_size * 0.8),
                            replacement_text,
                            fontsize=block.font_size,
                            fontname=fallback_font,
                            color=(0, 0, 0)
                        )
                        print(f"Used fallback font for text replacement: {fallback_font}")
                        inserted = True
                        break
                    except:
                        continue
                
                if not inserted:
                    # Basic fallback
                    page.insert_text(
                        (rect.x0, rect.y0 + block.font_size * 0.8),
                        replacement_text,
                        fontsize=12,
                        color=(0, 0, 0)
                    )
    
    async def _apply_highlight(self, doc: fitz.Document, 
                             edit_request: EditRequest, 
                             text_blocks: List[TextBlock]):
        """Apply highlighting to PDF"""
        target_text = edit_request.target_text.strip()
        
        # Find the target text in text blocks
        matching_blocks = self._find_matching_text_blocks(target_text, text_blocks)
        
        for block in matching_blocks:
            page = doc[block.page_num]
            rect = fitz.Rect(block.bbox)
            
            # Add yellow highlight
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=(1, 1, 0))  # Yellow
            highlight.update()
    
    async def _apply_heading_modification(self, doc: fitz.Document, 
                                        edit_request: EditRequest, 
                                        text_blocks: List[TextBlock]):
        """Apply heading modification to PDF"""
        target_text = edit_request.target_text.strip()
        replacement_text = edit_request.replacement_text
        context = edit_request.context
        
        print(f"Attempting to modify heading: '{target_text}' to '{replacement_text}'")
        print(f"Context: '{context}'")
        
        # Humanize the replacement text
        if self._seems_ai_generated(replacement_text):
            replacement_text = await self.llm_client.humanize_text(replacement_text)
        
        # First try to find matching headings
        heading_blocks = [block for block in text_blocks if block.is_heading]
        print(f"Found {len(heading_blocks)} potential heading blocks in document")
        
        # First try exact match on headings
        matching_blocks = self._find_matching_text_blocks(target_text, heading_blocks, context)
        
        # If no matching heading blocks, try all text blocks with heading-like properties
        if not matching_blocks:
            print(f"No matching blocks found in identified headings. Searching all blocks for heading-like text.")
            # Look for blocks with heading-like properties (larger font, fewer words, etc.)
            potential_heading_blocks = []
            for block in text_blocks:
                # Check if it could be a heading based on characteristics
                if (len(block.text.split()) < 15 and  # Not too long
                    block.font_size >= 11 and  # Not too small
                    not any(c in block.text for c in [',', ';', ':']) and  # Not too complex
                    sum(1 for w in block.text.split() if w and w[0].isupper()) / 
                      max(1, len(block.text.split())) > 0.4):  # Many capitalized words
                    potential_heading_blocks.append(block)
            
            print(f"Found {len(potential_heading_blocks)} additional potential heading blocks")
            matching_blocks = self._find_matching_text_blocks(target_text, potential_heading_blocks, context)
            
        # If still no matching blocks, try all blocks with more relaxed criteria
        if not matching_blocks:
            print(f"Still no matches. Trying all text blocks with fuzzy matching.")
            matching_blocks = self._find_matching_text_blocks(target_text, text_blocks, context)
        
        print(f"Found {len(matching_blocks)} blocks to modify")
        
        if not matching_blocks:
            print(f"WARNING: Could not find any text blocks matching '{target_text}'")
            return
        
        for block in matching_blocks:
            page = doc[block.page_num]
            
            print(f"Modifying heading on page {block.page_num+1}, text: '{block.text}'")
            
            # Create a white rectangle to cover the original heading
            rect = fitz.Rect(block.bbox)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Insert new heading text
            insertion_point = (rect.x0, rect.y0 + block.font_size * 0.8)
            font_size = block.font_size
            font_name = block.font_name or "Helvetica"
            
            print(f"Inserting text '{replacement_text}' at position {insertion_point} with font {font_name}, size {font_size}")
            
            # Try original font first, then fallback fonts
            try:
                page.insert_text(
                    insertion_point,
                    replacement_text,
                    fontsize=font_size,
                    fontname=font_name,
                    color=(0, 0, 0)
                )
            except Exception as font_error:
                print(f"Font error with {font_name}: {font_error}")
                # Try fallback fonts
                fallback_fonts = ["helv", "times", "cour", "Helvetica", "Times-Roman"]
                inserted = False
                
                for fallback_font in fallback_fonts:
                    try:
                        page.insert_text(
                            insertion_point,
                            replacement_text,
                            fontsize=font_size,
                            fontname=fallback_font,
                            color=(0, 0, 0)
                        )
                        print(f"Successfully used fallback font: {fallback_font}")
                        inserted = True
                        break
                    except:
                        continue
                
                if not inserted:
                    # Last resort - use basic text insertion
                    page.insert_text(
                        insertion_point,
                        replacement_text,
                        fontsize=12,
                        color=(0, 0, 0)
                    )
                    print(f"Used basic text insertion as final fallback")
    
    def _find_matching_text_blocks(self, target_text: str, 
                                  text_blocks: List[TextBlock], 
                                  context: Optional[str] = None) -> List[TextBlock]:
        """Find text blocks that match the target text"""
        matching_blocks = []
        
        print(f"Looking for text: '{target_text}'")
        target_text_lower = target_text.lower()
        
        # Try exact match first
        for block in text_blocks:
            if target_text_lower == block.text.lower():
                print(f"Found exact match: '{block.text}'")
                matching_blocks.append(block)
            elif target_text_lower in block.text.lower():
                print(f"Found partial match: '{block.text}'")
                matching_blocks.append(block)
        
        # If no exact match and context is provided, use fuzzy matching
        if not matching_blocks and context:
            print(f"No exact matches found. Trying with context: '{context}'")
            for block in text_blocks:
                if self._fuzzy_match(target_text, block.text, context):
                    print(f"Found fuzzy match with context: '{block.text}'")
                    matching_blocks.append(block)
        
        # If still no match, try partial matching
        if not matching_blocks:
            print(f"No exact or context matches found. Trying partial matching.")
            words = target_text_lower.split()
            for block in text_blocks:
                block_words = block.text.lower().split()
                overlap = len(set(words) & set(block_words))
                if overlap >= len(words) * 0.6:  # 60% word overlap
                    print(f"Found partial word match ({overlap}/{len(words)} words): '{block.text}'")
                    matching_blocks.append(block)
        
        print(f"Found {len(matching_blocks)} matching blocks")
        return matching_blocks
    
    def _fuzzy_match(self, target: str, text: str, context: str) -> bool:
        """Enhanced fuzzy matching with context awareness and structure detection"""
        print(f"Fuzzy matching target: '{target}' with text: '{text}'")
        
        # Direct substring match (case insensitive)
        if target.lower() in text.lower():
            print("  - Direct substring match found")
            return True
        
        # Word-level matching
        target_words = set(target.lower().split())
        text_words = set(text.lower().split())
        context_words = set(context.lower().split()) if context else set()
        
        # Calculate word overlap ratios
        word_overlap = len(target_words & text_words) / len(target_words) if target_words else 0
        context_match = len(context_words & text_words) / len(context_words) if context_words else 0
        
        print(f"  - Word overlap: {word_overlap:.2f}, Context match: {context_match:.2f}")
        
        # Check for heading-like patterns
        is_heading_like = (len(text.strip()) < 100 and 
                          (text.strip().endswith(':') or 
                           not any(c in text for c in ',.;')) and
                           sum(1 for w in text.split() if w and w[0].isupper()) / max(1, len(text.split())) > 0.5)
        
        if is_heading_like:
            print("  - Text appears to be a heading or title")
            # Lower threshold for headings
            return word_overlap >= 0.3 or context_match >= 0.3
        
        # Higher threshold for regular text
        return word_overlap >= 0.5 and (context_match >= 0.2 or not context)
    
    def _seems_ai_generated(self, text: str) -> bool:
        """Simple heuristic to detect if text might be AI-generated"""
        if not text:
            return False
            
        # Common AI-generated text patterns
        ai_indicators = [
            "demonstrates", "showcases", "furthermore", "moreover", 
            "consequently", "thus", "therefore", "in addition",
            "operational efficiency", "high levels", "significant impact"
        ]
        
        text_lower = text.lower()
        ai_score = sum(1 for indicator in ai_indicators if indicator in text_lower)
        
        # If text contains multiple AI indicators or is very formal, consider it AI-generated
        return ai_score >= 2 or (len(text.split()) > 10 and ai_score >= 1)
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """Validate that the file is a readable PDF"""
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count > 0
        except:
            return False
