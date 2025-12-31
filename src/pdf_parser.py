"""
PDF Parser for extracting content from pitch decks
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pdfplumber
from PyPDF2 import PdfReader


@dataclass
class PageContent:
    """Content extracted from a single PDF page"""
    page_number: int
    text: str
    tables: List[List[str]]
    has_images: bool


@dataclass
class ParsedPitchDeck:
    """Complete parsed pitch deck"""
    filename: str
    total_pages: int
    pages: List[PageContent]
    metadata: Dict[str, Any]
    full_text: str
    
    def get_text_by_page(self, page_num: int) -> str:
        """Get text for a specific page"""
        for page in self.pages:
            if page.page_number == page_num:
                return page.text
        return ""


class PitchDeckParser:
    """
    Parses pitch deck PDFs to extract text, tables, and structure.
    Uses pdfplumber for accurate text extraction and table detection.
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def parse(self, pdf_path: str) -> ParsedPitchDeck:
        """
        Parse a pitch deck PDF and extract all content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ParsedPitchDeck with all extracted content
        """
        pages = []
        metadata = {}
        
        # Extract metadata using PyPDF2
        try:
            reader = PdfReader(pdf_path)
            if reader.metadata:
                metadata = {
                    'title': reader.metadata.get('/Title', ''),
                    'author': reader.metadata.get('/Author', ''),
                    'creator': reader.metadata.get('/Creator', ''),
                    'creation_date': str(reader.metadata.get('/CreationDate', '')),
                }
        except Exception as e:
            metadata = {'error': str(e)}
        
        # Extract content using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # Extract text
                text = page.extract_text() or ""
                
                # Clean up text
                text = self._clean_text(text)
                
                # Extract tables
                tables = []
                try:
                    raw_tables = page.extract_tables()
                    if raw_tables:
                        for table in raw_tables:
                            # Clean table cells
                            cleaned_table = [
                                [str(cell) if cell else "" for cell in row]
                                for row in table if row
                            ]
                            tables.append(cleaned_table)
                except Exception:
                    pass
                
                # Check for images
                has_images = len(page.images) > 0 if hasattr(page, 'images') else False
                
                pages.append(PageContent(
                    page_number=i + 1,
                    text=text,
                    tables=tables,
                    has_images=has_images
                ))
        
        # Combine all text
        full_text = "\n\n".join([p.text for p in pages])
        
        return ParsedPitchDeck(
            filename=pdf_path.split('/')[-1],
            total_pages=len(pages),
            pages=pages,
            metadata=metadata,
            full_text=full_text
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()
    
    def extract_company_name(self, parsed_deck: ParsedPitchDeck) -> str:
        """
        Attempt to extract the company name from the pitch deck.
        Usually found on the first page or in metadata.
        """
        # Check metadata first
        if parsed_deck.metadata.get('title'):
            return parsed_deck.metadata['title']
        
        # Look at first page - company name is usually prominent
        if parsed_deck.pages:
            first_page = parsed_deck.pages[0].text
            lines = first_page.split('\n')
            
            # First non-empty line is often the company name
            for line in lines:
                line = line.strip()
                if line and len(line) < 50:  # Company names are usually short
                    # Skip common header text
                    if not any(skip in line.lower() for skip in ['confidential', 'pitch deck', 'presentation']):
                        return line
        
        return "Unknown Company"
    
    def extract_sections(self, parsed_deck: ParsedPitchDeck) -> Dict[str, str]:
        """
        Identify and extract common pitch deck sections.
        """
        sections = {}
        section_keywords = {
            'problem': ['problem', 'challenge', 'pain point'],
            'solution': ['solution', 'our product', 'how we solve'],
            'market': ['market', 'tam', 'sam', 'som', 'market size', 'opportunity'],
            'business_model': ['business model', 'revenue model', 'how we make money', 'monetization'],
            'traction': ['traction', 'metrics', 'growth', 'customers', 'users'],
            'competition': ['competition', 'competitive', 'landscape', 'competitors'],
            'team': ['team', 'founders', 'leadership', 'about us'],
            'financials': ['financials', 'projections', 'revenue', 'forecast'],
            'ask': ['ask', 'funding', 'investment', 'raise', 'use of funds'],
        }
        
        full_text_lower = parsed_deck.full_text.lower()
        
        for section_name, keywords in section_keywords.items():
            for keyword in keywords:
                if keyword in full_text_lower:
                    sections[section_name] = True
                    break
        
        return sections

