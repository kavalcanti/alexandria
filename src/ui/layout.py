"""
Layout components for the Alexandria UI.

This module defines the UI layout structure and styling for the Alexandria application,
including the chat window, thinking pane, and status bars.
"""
from typing import Dict, Tuple
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style

def create_markdown_style() -> Style:
    """
    Create style definitions for Markdown elements in the UI.
    
    Returns:
        Style: A prompt_toolkit Style object containing color and formatting definitions
              for various Markdown elements and UI components
    """
    return Style.from_dict({
        # Headers
        'heading-1': 'bold underline #00aaaa',  # bright blue
        'heading-2': 'bold underline #257ba3',  # medium blue
        'heading-3': 'bold underline #136868',  # cyan
        'heading-4': 'underline #136868',
        'heading-5': 'italic #136868',
        'heading-6': '#00aaaa',
        
        # Code
        'code-block': 'bg:#222222 #ffffff',
        'code-inline': 'bg:#222222 #ffffff',
        
        # Text formatting
        'bold': 'bold',
        'italic': 'italic',
        'list': '',
        
        # UI elements
        'role': 'bold #00aa00',  # green
        'title': 'reverse',
        'line': '#666666',
        'shortcut': 'bold #ffaa00',  # orange
    })

def create_layout_components() -> Tuple[HSplit, Buffer, FormattedTextControl, FormattedTextControl, ScrollablePane, ScrollablePane, Window, Style]:
    """
    Create and return the main UI layout components.
    
    This function creates all necessary UI components including:
    - Message input buffer and window
    - Chat display window with scrolling
    - Thinking process display window with scrolling
    - Status bars with shortcuts
    - Visual separators and margins
    
    Returns:
        Tuple containing:
        - root_container (HSplit): The root UI container
        - msg_buffer (Buffer): Buffer for message input
        - chat_formatted_text (FormattedTextControl): Control for chat display
        - thinking_formatted_text (FormattedTextControl): Control for thinking display
        - chat_window (ScrollablePane): Scrollable chat window
        - thinking_window (ScrollablePane): Scrollable thinking window
        - msg_window (Window): Message input window
        - style (Style): UI style definitions
    """
    # Text controls and buffers
    msg_buffer = Buffer(multiline=True)
    chat_formatted_text = FormattedTextControl(focusable=True)
    thinking_formatted_text = FormattedTextControl()

    # Windows
    side_margin = Window(width=1)
    msg_window = Window(BufferControl(buffer=msg_buffer), height=5, wrap_lines=True)
    
    chat_content = Window(
        chat_formatted_text,
        wrap_lines=True,
        ignore_content_width=True,
        dont_extend_width=False
    )
    chat_window = ScrollablePane(
        content=chat_content,
        keep_cursor_visible=True,
        keep_focused_window_visible=True
    )

    thinking_content = Window(
        thinking_formatted_text,
        wrap_lines=True,
        ignore_content_width=True,
        dont_extend_width=False
    )
    thinking_window = ScrollablePane(
        content=thinking_content
    )

    # Status bars
    top_bar_text = [
        ("class:bold", " Alexandria - Terminal-based Local LLM Inference "),
    ]

    bottom_bar_text = [
        ("class:bold", " Essential: "),
        ("class:shortcut", "Ctrl+Space"),
        ("class:bold", ": Send | "),
        ("class:shortcut", "Ctrl+Q"),
        ("class:bold", ": Quit | "),
        ("class:shortcut", "Ctrl+O"),
        ("class:bold", ": Reset | "),
        ("class:shortcut", "Ctrl+S"),
        ("class:bold", ": Save\n"),
        ("class:bold", " Navigation: "),
        ("class:shortcut", "Ctrl+↑/↓"),
        ("class:bold", ": Chat scroll | "),
        ("class:shortcut", "Shift+↑/↓"),
        ("class:bold", ": Thoughts scroll"),
    ]

    # Chat side composite
    chat_side_composite = HSplit([
        chat_window,
        Window(height=1, char="-", style="class:line"),
        msg_window,
    ])

    # Thinking window composite
    thinking_window_composite = VSplit([
        side_margin,
        thinking_window
    ])

    # Main composite
    main_composite = VSplit([
        chat_side_composite,
        Window(width=1, char="#", style="class:line"),
        thinking_window_composite,
    ], width=Dimension(weight=1))

    # Root container
    root_container = HSplit([
        Window(
            height=1,
            content=FormattedTextControl(top_bar_text),
            align=WindowAlign.CENTER,
        ),
        Window(height=1, char="-", style="class:line"),
        main_composite,
        Window(height=1, char="-", style="class:line"),
        Window(
            height=2,
            content=FormattedTextControl(bottom_bar_text),
            align=WindowAlign.LEFT,
        ),
    ])

    return (
        root_container,
        msg_buffer,
        chat_formatted_text,
        thinking_formatted_text,
        chat_window,
        thinking_window,
        msg_window,
        create_markdown_style()  # Return the style object
    ) 