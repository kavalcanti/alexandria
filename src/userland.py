import asyncio
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout
from src.model_calls import ConversationHandler
import time

llm_model = "Qwen/Qwen3-1.7B"

# handler = ConversationHandler(llm_model)

msg_buffer = Buffer()
msg_window = Window(BufferControl(buffer=msg_buffer), height=5, wrap_lines=True)

chat_formatted_text = FormattedTextControl()
chat_content = Window(chat_formatted_text, wrap_lines=True)
chat_window = ScrollablePane(content=chat_content, keep_cursor_visible=True, keep_focused_window_visible=True)

thinking_formatted_text = FormattedTextControl()
thinking_content = Window(thinking_formatted_text, wrap_lines=True)
thinking_window = ScrollablePane(content=thinking_content)

kb = KeyBindings()

titlebar_text = [
        ("class:title", " Welcome to the world of tomorrow "),
        ("class:title", "A CLI interface for LLMs"),
    ]

helpbar_l1 = [
        ("class:title", "(Press [Ctrl-Q] to quit, [Ctrl+Space] to send msg."),
]

helpbar_l2 =  [
        ("class:title", "Ctrl+Arrow to scroll chat Shift+Arrow to scroll thinking"),
    ]



# Chat and message
msg_and_chat_composite = HSplit(
                            [
                                chat_window,
                                Window(height=1, char="-", style="class:line"),
                                msg_window,
                            ]
                        )


chat_and_thinking_composite = VSplit(
    width=Dimension(weight=1),
    children=[
        msg_and_chat_composite,
        Window(width=1, char="#", style="class:line"),
        thinking_window,
    ]
)

# Main app container
root_container = HSplit(
    [
        Window(
            height=1,
            content=FormattedTextControl(titlebar_text),
            align=WindowAlign.CENTER,
        ),

        Window(height=1, char="-", style="class:line"),

        chat_and_thinking_composite,

        Window(height=1, char="-", style="class:line"),

        Window(
            height=1,
            content=FormattedTextControl(helpbar_l1),
            align=WindowAlign.LEFT,
        ),

        Window(
            height=1,
            content=FormattedTextControl(helpbar_l2),
            align=WindowAlign.LEFT,
        ),
    ]
)

application = Application(
    layout=Layout(root_container, focused_element=msg_window),
    key_bindings=kb,
    mouse_support=True,
    full_screen=True,
)

@kb.add('c-up')
def _(event):
    """Scroll chat window up by one line."""
    # Decrease the vertical scroll offset, ensuring it doesn't go below 0
    chat_window.vertical_scroll = max(0, chat_window.vertical_scroll - 1)
    event.app.invalidate() # Redraw the UI

@kb.add('c-down')
def _(event):
    """Scroll chat window down by one line."""
    # Increase the vertical scroll offset
    chat_window.vertical_scroll += 1
    event.app.invalidate() # Redraw the UI

@kb.add('s-up')
def _(event):
    """Scroll chat window up by one line."""
    # Decrease the vertical scroll offset, ensuring it doesn't go below 0
    thinking_window.vertical_scroll = max(0, chat_window.vertical_scroll - 1)
    event.app.invalidate() # Redraw the UI

@kb.add('s-down')
def _(event):
    """Scroll chat window down by one line."""
    # Increase the vertical scroll offset
    thinking_window.vertical_scroll += 1
    event.app.invalidate() # Redraw the UI

@kb.add('c-m')
def _(event):
    event.app.layout.focus(msg_window)

@kb.add('c-n')
def _(event):
    event.app.layout.focus(chat_content)

@kb.add("c-q")
def _(event):
    """
    Pressing Ctrl-Q or Ctrl-C will exit the user interface.
    """
    event.app.exit()

@kb.add('c-o')
def _(event):
    chat_formatted_text.text == "Generating new handler instance."
    thinking_formatted_text == "Generating new handler instance."
    get_app().invalidate()
    handler = ConversationHandler(llm_model)
    chat_formatted_text.text == ""
    thinking_formatted_text == ""

### --- Main chat send loop --- ###

@kb.add('c-space')
async def _(event):
    """
    Handle Control+Enter key press to send input.
    """
    user_input = msg_buffer.text

    if user_input.strip(): 

        msg_buffer.text = "AI is busy." 

        current_chat_text = chat_formatted_text.text
        chat_formatted_text.text = current_chat_text + f"You:\n {user_input}\n"
        get_app().invalidate()

        handler.manage_context_window("user", user_input)

        ai_thinking, ai_answer = await asyncio.to_thread(handler.generate_chat_response)
        
        current_chat_text = chat_formatted_text.text
        chat_formatted_text.text = current_chat_text + f"LLM:\n {ai_answer}\n"

        current_thinking_text = thinking_formatted_text.text
        thinking_formatted_text.text = current_thinking_text + f"Thoughts:\n {ai_thinking}\n"

        get_app().invalidate()

        handler.manage_context_window("assistant", ai_answer)

        msg_buffer.text = ""

    else:

        pass


