from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import re
import os
import asyncio
from dotenv import load_dotenv

# Try to import OpenAI, handle if not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI library not available. LLM features will use fallback methods.")

load_dotenv()

@dataclass
class EditRequest:
    """Data class for edit requests"""
    action: str  # "replace", "highlight", "modify_heading"
    target_text: str
    replacement_text: Optional[str] = None
    context: Optional[str] = None

class LLMClient:
    """Client for interacting with various LLM APIs"""
    
    def __init__(self):
        self.openai_available = False
        self._setup_clients()
    
    def _setup_clients(self):
        """Initialize LLM clients based on available API keys"""
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            # Using new OpenAI client - no need to set global api_key
            self.openai_available = True
        else:
            self.openai_available = False
    
    async def parse_prompt(self, prompt: str, pdf_text: str) -> List[EditRequest]:
        """Parse user prompt into structured edit requests"""
        system_prompt = """
        You are an expert at parsing PDF editing instructions. Given a user prompt and PDF content, 
        extract specific edit requests in the following format:
        
        Action types:
        - "replace": Change specific text
        - "highlight": Add yellow highlighting to text
        - "modify_heading": Change heading text
        
        Return a JSON list of edit requests with:
        - action: the action type
        - target_text: the exact text to find
        - replacement_text: the new text (for replace/modify_heading actions)
        - context: surrounding text to help locate the target
        
        Be precise and specific about the text to find.
        """
        
        user_prompt = f"""
        PDF Content (first 2000 chars):
        {pdf_text[:2000]}
        
        User Request: {prompt}
        
        Parse this into edit requests:
        """
        
        try:
            if self.openai_available:
                response = await self._call_openai(system_prompt, user_prompt)
                return self._parse_edit_response(response)
            else:
                # Fallback to rule-based parsing
                return self._rule_based_parsing(prompt)
        except Exception as e:
            print(f"LLM parsing failed, using rule-based: {e}")
            return self._rule_based_parsing(prompt)
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to OpenAI"""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI library not available")
        
        try:
            # Use the correct new OpenAI v1.x API format and sanitize proxies
            from openai import OpenAI
            import os as _os
            # Remove potentially incompatible proxy env vars for httpx in container
            for _k in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"]:
                if _k in _os.environ and not _os.environ.get("ALLOW_PROXIES", ""):  # allow opt-in
                    _os.environ.pop(_k, None)

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise e
    
    def _parse_edit_response(self, response: str) -> List[EditRequest]:
        """Parse LLM response into EditRequest objects"""
        try:
            # Clean the response if it contains markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            import json
            edit_data = json.loads(cleaned_response)
            
            edits = []
            for item in edit_data:
                if isinstance(item, dict) and 'action' in item and 'target_text' in item:
                    edits.append(EditRequest(
                        action=item.get('action'),
                        target_text=item.get('target_text'),
                        replacement_text=item.get('replacement_text'),
                        context=item.get('context')
                    ))
            return edits
        except Exception as e:
            print(f"Failed to parse LLM JSON response: {e}")
            print(f"Response was: {response}")
            return self._rule_based_parsing(response)
    
    def _rule_based_parsing(self, prompt: str) -> List[EditRequest]:
        """Fallback rule-based prompt parsing"""
        edits = []
        print(f"Using rule-based parsing for prompt: {prompt}")
        
        # Pattern for text replacement
        replace_patterns = [
            r"change\s+['\"]([^'\"]+)['\"] to ['\"]([^'\"]+)['\"]",
            r"replace\s+['\"]([^'\"]+)['\"] with ['\"]([^'\"]+)['\"]",
            r"in the (.+?), change ['\"]([^'\"]+)['\"] to ['\"]([^'\"]+)['\"]",
            r"change\s+(?:the)?\s*([^'\"]+?)\s+to\s+([^'\"]+)",  # More flexible pattern
        ]
        
        for pattern in replace_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                print(f"Found match with pattern: {pattern}")
                print(f"Groups: {match.groups()}")
                if len(match.groups()) == 2:
                    edits.append(EditRequest(
                        action="replace",
                        target_text=match.group(1),
                        replacement_text=match.group(2)
                    ))
                elif len(match.groups()) == 3:
                    edits.append(EditRequest(
                        action="replace",
                        target_text=match.group(2),
                        replacement_text=match.group(3),
                        context=match.group(1)
                    ))
        
        # Pattern for highlighting
        highlight_patterns = [
            r"highlight\s+['\"]?([^'\"]+)['\"]?",
            r"mark\s+['\"]?([^'\"]+)['\"]?",
            r"emphasize\s+['\"]?([^'\"]+)['\"]?"
        ]
        
        for pattern in highlight_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                edits.append(EditRequest(
                    action="highlight",
                    target_text=match.group(1)
                ))
        
        # Pattern for heading changes - improved to catch more variations
        heading_patterns = [
            r"change the heading ['\"]([^'\"]+)['\"] to ['\"]([^'\"]+)['\"]",
            r"modify heading ['\"]([^'\"]+)['\"] to ['\"]([^'\"]+)['\"]",
            r"change the title ['\"]([^'\"]+)['\"] to ['\"]([^'\"]+)['\"]",
            r"change\s+(?:the)?\s*title\s+(?:from)?\s*['\"]?([^'\"]+?)['\"]?\s+to\s+['\"]?([^'\"]+?)['\"]?",
            r"change\s+(?:the)?\s*heading\s+(?:from)?\s*['\"]?([^'\"]+?)['\"]?\s+to\s+['\"]?([^'\"]+?)['\"]?",
            r"(?:replace|update|set)\s+(?:the)?\s*title\s+(?:from|of)?\s*['\"]?([^'\"]+?)['\"]?\s+to\s+['\"]?([^'\"]+?)['\"]?",
            r"(?:replace|update|set)\s+(?:the)?\s*heading\s+(?:from|of)?\s*['\"]?([^'\"]+?)['\"]?\s+to\s+['\"]?([^'\"]+?)['\"]?",
            r"(?:make|transform)\s+(?:the)?\s*title\s+['\"]?([^'\"]+?)['\"]?\s+(?:into|to)\s+['\"]?([^'\"]+?)['\"]?",
            r"title\s+(?:change|modification):\s*['\"]?([^'\"]+?)['\"]?\s+(?:to|into|→)\s+['\"]?([^'\"]+?)['\"]?",
            r"heading\s+(?:change|modification):\s*['\"]?([^'\"]+?)['\"]?\s+(?:to|into|→)\s+['\"]?([^'\"]+?)['\"]?",
            # Pattern for title with no quotes - must be at beginning of prompt
            r"^change\s+title\s+(?:from)?\s*([^\n]+?)\s+to\s+([^\n]+?)(?:\s|$)"
        ]
        
        for pattern in heading_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                print(f"Found heading match with pattern: {pattern}")
                print(f"Groups: {match.groups()}")
                edits.append(EditRequest(
                    action="modify_heading",
                    target_text=match.group(1),
                    replacement_text=match.group(2)
                ))
        
        return edits
    
    async def humanize_text(self, text: str) -> str:
        """Humanize AI-generated text to avoid detection"""
        system_prompt = """
        You are an expert at rewriting text to make it sound naturally human-written.
        Your goal is to make the text undetectable by AI detection tools while preserving meaning.
        
        Techniques:
        1. Vary sentence structure and length
        2. Use natural, conversational transitions
        3. Include subtle imperfections that humans make
        4. Add personal touches or colloquialisms where appropriate
        5. Vary vocabulary and avoid repetitive patterns
        6. Use active and passive voice naturally
        
        Keep the core meaning intact while making it sound authentically human.
        """
        
        user_prompt = f"Humanize this text: {text}"
        
        try:
            if self.openai_available:
                response = await self._call_openai(system_prompt, user_prompt)
                return response.strip()
            else:
                # Simple fallback humanization
                return self._simple_humanize(text)
        except Exception as e:
            print(f"Humanization failed: {e}")
            return self._simple_humanize(text)
    
    def _simple_humanize(self, text: str) -> str:
        """Simple rule-based text humanization"""
        # Add some natural variations
        text = text.replace("utilize", "use")
        text = text.replace("demonstrate", "show")
        text = text.replace("furthermore", "also")
        text = text.replace("in addition", "plus")
        text = text.replace("consequently", "so")
        
        # Add some natural sentence starters
        if text.startswith("The system"):
            text = text.replace("The system", "This system", 1)
        elif text.startswith("This approach"):
            text = text.replace("This approach", "Our approach", 1)
        
        return text
