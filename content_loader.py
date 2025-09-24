import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import Request

# Supported languages
LANGUAGES = {
    'en': 'English',
    'he': 'עברית'
}

DEFAULT_LANGUAGE = 'en'

class ContentLoader:
    def __init__(self):
        self.content_cache = {}
        self.content_dir = Path("content")
        self._load_all_content()
    
    def _load_all_content(self):
        """Load all markdown content into memory for fast access"""
        print("Loading content files...")
        for lang in LANGUAGES.keys():
            lang_dir = self.content_dir / lang
            if lang_dir.exists():
                self.content_cache[lang] = {}
                for md_file in lang_dir.glob("*.md"):
                    file_name = md_file.stem
                    content = self._parse_markdown_file(md_file)
                    self.content_cache[lang][file_name] = content
                    print(f"Loaded {lang}/{file_name}.md with {len(content)} keys")
    
    def reload_content(self):
        """Reload all content from disk - useful during development"""
        print("Reloading all content...")
        self.content_cache.clear()
        self._load_all_content()
        print("Content reloaded successfully!")
    
    def _parse_markdown_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a markdown file into a simple key-value structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple flat structure for easy template access
            result = {}
            current_section = None
            
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Main headers (# Title) 
                if line.startswith('# '):
                    result['page_title'] = line[2:].strip()
                    
                # Section headers (## Section)
                elif line.startswith('## '):
                    current_section = line[3:].strip().lower().replace(' ', '_').replace('-', '_')
                    
                # Direct content after sections
                elif current_section and line and not line.startswith('#'):
                    # Create section key if it doesn't exist
                    section_key = current_section
                    if section_key not in result:
                        result[section_key] = line
                    else:
                        # Append to existing content
                        result[section_key] += '\\n' + line
                
                # No section - direct mapping
                elif not line.startswith('#'):
                    if 'content' not in result:
                        result['content'] = line
                    else:
                        result['content'] += '\\n' + line
            
            return result
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}
    
    def get_content(self, language: str, page: str, key: str = None, default: str = "") -> Any:
        """Get content for a specific language, page, and key"""
        lang_content = self.content_cache.get(language)
        if not lang_content:
            # Fallback to default language
            lang_content = self.content_cache.get(DEFAULT_LANGUAGE, {})
        
        page_content = lang_content.get(page, {})
        
        if key is None:
            return page_content
        
        # Handle nested keys like "hero_section.main_title"
        if '.' in key:
            keys = key.split('.')
            result = page_content
            for k in keys:
                if isinstance(result, dict):
                    result = result.get(k, default)
                else:
                    return default
            return result
        
        return page_content.get(key, default)
    
    def get_language_from_request(self, request: Request) -> str:
        """Detect language from request (same as before)"""
        # 1. Check query parameter
        lang = request.query_params.get('lang')
        if lang and lang in LANGUAGES:
            return lang
        
        # 2. Check cookie
        lang = request.cookies.get('language')
        if lang and lang in LANGUAGES:
            return lang
        
        # 3. Check browser Accept-Language header
        accept_language = request.headers.get('accept-language')
        if accept_language:
            for lang_range in accept_language.split(','):
                lang = lang_range.strip().split(';')[0].split('-')[0].lower()
                if lang in LANGUAGES:
                    return lang
        
        # 4. Default to English
        return DEFAULT_LANGUAGE
    
    def is_rtl_language(self, language: str) -> bool:
        """Check if language requires RTL layout"""
        rtl_languages = ['he', 'ar', 'fa', 'ur']
        return language in rtl_languages
    
    def get_language_context(self, request: Request) -> Dict[str, Any]:
        """Get language context for template rendering"""
        current_lang = self.get_language_from_request(request)
        
        return {
            'current_language': current_lang,
            'is_rtl': self.is_rtl_language(current_lang),
            'languages': LANGUAGES,
            'dir': 'rtl' if self.is_rtl_language(current_lang) else 'ltr',
            'content': ContentHelper(self, current_lang)
        }

class ContentHelper:
    """Template helper class for easy content access"""
    def __init__(self, loader: ContentLoader, language: str):
        self.loader = loader
        self.language = language
    
    def get(self, page: str, key: str = None, default: str = "") -> Any:
        """Simplified content access for templates"""
        return self.loader.get_content(self.language, page, key, default)
    
    def nav(self, key: str, default: str = "") -> str:
        """Quick access to navigation content"""
        return self.loader.get_content(self.language, 'navigation', key, default)
    
    def home(self, key: str, default: str = "") -> str:
        """Quick access to homepage content"""  
        return self.loader.get_content(self.language, 'homepage', key, default)
    
    def footer(self, key: str, default: str = "") -> str:
        """Quick access to footer content"""
        return self.loader.get_content(self.language, 'footer', key, default)
    
    def methodology(self, key: str, default: str = "") -> str:
        """Quick access to methodology content"""
        return self.loader.get_content(self.language, 'methodology', key, default)
    
    def education(self, key: str, default: str = "") -> str:
        """Quick access to education content"""
        return self.loader.get_content(self.language, 'education', key, default)
    
    def pricing(self, key: str, default: str = "") -> str:
        """Quick access to pricing content"""
        return self.loader.get_content(self.language, 'pricing', key, default)
    
    def faq(self, key: str, default: str = "") -> str:
        """Quick access to FAQ content"""
        return self.loader.get_content(self.language, 'faq', key, default)
    
    def support(self, key: str, default: str = "") -> str:
        """Quick access to support content"""
        return self.loader.get_content(self.language, 'support', key, default)
    
    def legal_disclaimers(self, key: str, default: str = "") -> str:
        """Quick access to legal disclaimers content"""
        return self.loader.get_content(self.language, 'legal-disclaimers', key, default)
    
    def risk_assessment(self, key: str, default: str = "") -> str:
        """Quick access to risk assessment content"""
        return self.loader.get_content(self.language, 'risk-assessment', key, default)

# Global content loader instance
content_loader = ContentLoader()