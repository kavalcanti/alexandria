"""
Layout components for the Alexandria UI.
"""
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.styles import Style

def create_markdown_style() -> Style:
    """Create style definitions for Markdown elements."""
    return Style.from_dict({
        # Headers
        'heading-1': 'bold #0088ff',  # bright blue
        'heading-2': 'bold #0066cc',  # medium blue
        'heading-3': 'bold #00aaaa',  # cyan
        'heading-4': 'underline #00aaaa',
        'heading-5': 'italic #00aaaa',
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

def create_layout_components():
    """
    Create and return the main UI layout components.
    
    Returns:
        tuple: Contains all necessary layout components and controls
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
        ("class:title", " Alexandria - Terminal-based Local LLM Interface "),
    ]

    bottom_bar_text = [
        ("class:title", " Essential: "),
        ("class:shortcut", "Ctrl+Space"),
        ("class:title", ": Send | "),
        ("class:shortcut", "Ctrl+Q"),
        ("class:title", ": Quit | "),
        ("class:shortcut", "Ctrl+O"),
        ("class:title", ": Reset\n"),
        ("class:title", " Navigation: "),
        ("class:shortcut", "Ctrl+↑/↓"),
        ("class:title", ": Chat scroll | "),
        ("class:shortcut", "Shift+↑/↓"),
        ("class:title", ": Thoughts scroll"),
    ]

    # Main chat composite
    main_chat_composite = VSplit([
        side_margin,
        chat_window,
        side_margin
    ])

    # Message window composite
    msg_window_composite = VSplit([
        side_margin,
        msg_window,
        side_margin
    ])

    # Chat side composite
    chat_side_composite = HSplit([
        main_chat_composite,
        Window(height=1, char="-", style="class:line"),
        msg_window_composite,
    ])

    # Thinking window composite
    thinking_window_composite = VSplit([
        side_margin,
        thinking_window,
        side_margin
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