"""
Markdown formatting support for Alexandria UI.

This module provides Markdown parsing and formatting capabilities for the Alexandria UI,
including syntax highlighting for code blocks and support for common Markdown elements.
"""
from typing import List, Tuple, Optional, TypeAlias
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import Terminal256Formatter
from pygments.util import ClassNotFound

# Type alias for formatted text used in prompt_toolkit
FormattedText: TypeAlias = List[Tuple[str, str]]

class MarkdownFormatter:
    def __init__(self) -> None:
        """
        Initialize the Markdown formatter with CommonMark parser.
        
        Returns:
            None
        """
        self.md = MarkdownIt('commonmark')
        self._current_style = []
        
    def convert_to_formatted_text(self, markdown_text: str) -> FormattedText:
        """
        Convert markdown text to prompt_toolkit formatted text.
        
        Args:
            markdown_text: Raw markdown text to be formatted
            
        Returns:
            FormattedText: List of (style, text) tuples for prompt_toolkit rendering
        """
        if not markdown_text:
            return []
            
        tokens = self.md.parse(markdown_text)
        self._current_style = []  # Reset style stack
        
        result = self._process_tokens(tokens)
        return result
    
    def _get_current_style(self) -> str:
        """
        Get the current composite style from the style stack.
        
        Returns:
            str: Space-separated string of current style classes, or empty string if no styles
        """
        return ' '.join(self._current_style) if self._current_style else ''
    
    def _process_tokens(self, tokens) -> FormattedText:
        """
        Process markdown-it tokens into formatted text.
        
        Handles various Markdown elements including:
        - Headers (levels 1-6)
        - Code blocks and inline code
        - Bold and italic text
        - Lists and list items
        - Paragraphs and line breaks
        
        Args:
            tokens: List of markdown-it tokens to process
            
        Returns:
            FormattedText: List of (style, text) tuples for prompt_toolkit rendering
        """
        formatted_text: FormattedText = []
        in_paragraph = False
        in_list_item = False
        is_first_token = True
        
        for token in tokens:
            style = self._get_current_style()
            
            if token.type == 'heading_open':
                level = int(token.tag[1])
                if not is_first_token:  # Only add newline if not the first token
                    formatted_text.append(('', '\n'))
                self._current_style.append(f'class:heading-{level}')
                
            elif token.type == 'heading_close':
                self._current_style.pop()
                formatted_text.append(('', '\n'))
                
            elif token.type == 'code_block':
                formatted_text.extend(self._format_code_block(token.content, token.info or ''))
                
            elif token.type == 'code_inline':
                formatted_text.append(('class:code-inline', f'`{token.content}`'))
                
            elif token.type == 'strong_open':
                self._current_style.append('class:bold')
                
            elif token.type == 'strong_close':
                self._current_style.pop()
                
            elif token.type == 'em_open':
                self._current_style.append('class:italic')
                
            elif token.type == 'em_close':
                self._current_style.pop()
                
            elif token.type == 'paragraph_open':
                in_paragraph = True
                formatted_text.append(('', '\n'))
                
            elif token.type == 'paragraph_close':
                in_paragraph = False
                if not in_list_item:  # Only add newline if not in a list item
                    formatted_text.append(('', '\n'))
                
            elif token.type == 'bullet_list_open':
                self._current_style.append('class:list')
                formatted_text.append(('', '\n'))
                
            elif token.type == 'bullet_list_close':
                self._current_style.pop()
                
            elif token.type == 'list_item_open':
                in_list_item = True
                formatted_text.append(('', '- '))
                
            elif token.type == 'list_item_close':
                in_list_item = False
                formatted_text.append(('', '\n'))
                
            elif token.type == 'inline':
                # Process inline content
                if hasattr(token, 'children'):
                    formatted_text.extend(self._process_tokens(token.children))
                
            elif token.type == 'text':
                # Always include text content with current style
                if token.content:
                    formatted_text.append((style, token.content))
                
            elif token.type == 'softbreak':
                if not in_list_item:  # Only add softbreaks outside of list items
                    formatted_text.append(('', '\n'))
                
            elif token.type == 'hardbreak':
                formatted_text.append(('', '\n'))
            
            is_first_token = False
            
        return formatted_text
    
    def _format_code_block(self, code: str, language: str) -> FormattedText:
        """
        Format a code block with syntax highlighting.
        
        Args:
            code: The code content to be highlighted
            language: The programming language identifier for syntax highlighting
            
        Returns:
            FormattedText: List of (style, text) tuples containing the highlighted code
        """
        try:
            if language:
                lexer = get_lexer_by_name(language)
            else:
                lexer = TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
            
        formatter = Terminal256Formatter(style='monokai')
        highlighted = highlight(code, lexer, formatter)
        
        return [
            ('class:code-block', highlighted),
            ('class:code-block', '\n')
        ] 