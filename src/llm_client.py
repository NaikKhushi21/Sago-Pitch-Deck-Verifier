"""
LLM Client - Abstraction layer for different LLM providers
Supports: Google Gemini (Free!), OpenAI, Anthropic
"""
from typing import Optional, Dict, Any
from .config import config


class LLMClient:
    """
    Unified interface for LLM providers.
    Default: Google Gemini (free tier available)
    """
    
    def __init__(
        self, 
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider or config.llm_provider
        self.model = model or config.llm_model
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                
                if not config.gemini_api_key:
                    raise ValueError(
                        "GEMINI_API_KEY not set in .env file.\n"
                        "Get your free API key at: https://aistudio.google.com/app/apikey"
                    )
                
                genai.configure(api_key=config.gemini_api_key)
                self._client = genai.GenerativeModel(self.model or 'gemini-1.5-flash')
                print(f"✓ Connected to Gemini ({self.model or 'gemini-1.5-flash'})")
                
            except ImportError:
                raise ImportError(
                    "Google Generative AI package not installed.\n"
                    "Run: pip install google-generativeai"
                )
                
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                
                if not config.openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set in .env file.")
                
                self._client = OpenAI(api_key=config.openai_api_key)
                print(f"✓ Connected to OpenAI ({self.model})")
                
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
                
        elif self.provider == "anthropic":
            try:
                import anthropic
                
                if not config.anthropic_api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set in .env file.")
                
                self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
                print(f"✓ Connected to Anthropic ({self.model})")
                
            except ImportError:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def complete(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
            
        Returns:
            The LLM's response text
        """
        if self.provider == "gemini":
            return self._gemini_complete(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "openai":
            return self._openai_complete(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic_complete(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _gemini_complete(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Google Gemini API completion"""
        # Combine system prompt with user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Configure generation settings
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = self._client.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def _openai_complete(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI API completion"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def _anthropic_complete(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Anthropic Claude API completion"""
        message = self._client.messages.create(
            model=self.model if 'claude' in self.model else "claude-3-opus-20240229",
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        
        return message.content[0].text
    
    def complete_with_json(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion and parse as JSON.
        """
        import json
        
        # Add JSON instruction to prompt
        json_prompt = f"""{prompt}

IMPORTANT: Return ONLY valid JSON, no other text or markdown formatting."""
        
        response = self.complete(json_prompt, system_prompt, temperature=0.1)
        
        # Clean response
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            response = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
        
        # Find JSON in response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            response = response[start:end]
        
        return json.loads(response)
