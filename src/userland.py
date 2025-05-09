import asyncio
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout
from src.model_calls import ConversationHandler
import time

llm_model = "Qwen/Qwen3-1.7B"

handler = ConversationHandler(llm_model)

msg_buffer = Buffer()
msg_window = Window(BufferControl(buffer=msg_buffer), height=5, wrap_lines=True)

chat_formatted_text = FormattedTextControl()
chat_content = Window(chat_formatted_text, wrap_lines=True)
chat_window = ScrollablePane(content=chat_content, keep_cursor_visible=True, keep_focused_window_visible=True)

thinking_formatted_text = FormattedTextControl()
thinking_content = Window(thinking_formatted_text, wrap_lines=True)
thinking_window = ScrollablePane(content=thinking_content)

kb = KeyBindings()

helpbar_text =  [
        ("class:title", " Ctrl-Q: exit. Ctrl-Space: Send message. "),
        # ("class:title", " (Press [Ctrl-Q] to quit, [Ctrl+A] to send msg.)"),
    ]

titlebar_text = [
        ("class:title", " Hello world "),
        ("class:title", " (Press [Ctrl-Q] to quit, [Ctrl+A] to send msg.)"),
    ]

# Chat, msg, sperators and helpbar container
body_a = HSplit(
    [
        chat_window,


        Window(height=1, char="-", style="class:line"),

        msg_window,
        Window(height=1, char="-", style="class:line"),
        Window(height=1, content=FormattedTextControl(helpbar_text)),
    ]
)

# Future conversation logs container
body_b = VSplit(
    [
        body_a,
        Window(width=1, char="#", style="class:line"),
        thinking_window
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

        body_b,
    ]
)

application = Application(
    layout=Layout(root_container, focused_element=msg_window),
    key_bindings=kb,
    mouse_support=True,
    full_screen=True,
)


### --- Utility Keybinds --- ###


# @kb.add('c-up')
# def _(event):
#     """Scroll chat window up by one line, respecting bounds."""
#     pane = chat_window # Access the ScrollablePane
#     # Ensure render_info is available before accessing sizes
#     if pane.render_info and pane.content.render_info:
#         # Get rendered heights of the pane and its content
#         window_height = pane.render_info.window_height
#         content_height = pane.content.render_info.content_height
#         # Calculate maximum scroll offset (0 if content fits within the window)
#         max_scroll = max(0, content_height - window_height)

#         # Decrease scroll by one line
#         new_scroll = pane.vertical_scroll - 1
#         # Ensure the new scroll value is within the valid range [0, max_scroll]
#         pane.vertical_scroll = max(0, min(max_scroll, new_scroll))

#     event.app.invalidate() # Redraw the UI

# @kb.add('c-down')
# def _(event):
#     """Scroll chat window down by one line, respecting bounds."""
#     pane = chat_window # Access the ScrollablePane
#     # Ensure render_info is available before accessing sizes
#     if pane.render_info and pane.content.render_info:
#         # Get rendered heights of the pane and its content
#         window_height = pane.render_info.window_height
#         content_height = pane.content.render_info.content_height
#         # Calculate maximum scroll offset (0 if content fits within the window)
#         max_scroll = max(0, content_height - window_height)

#         # Increase scroll by one line
#         new_scroll = pane.vertical_scroll + 1
#          # Ensure the new scroll value is within the valid range [0, max_scroll]
#         pane.vertical_scroll = max(0, min(max_scroll, new_scroll))

#     event.app.invalidate() # Redraw the UI


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

@kb.add('c-m' ,eager=True)
def _(event):
    event.app.layout.focus(msg_window)

@kb.add('c-n',eager=True)
def _(event):
    event.app.layout.focus(chat_content)

@kb.add("c-q", eager=True)
def _(event):
    """
    Pressing Ctrl-Q or Ctrl-C will exit the user interface.
    """
    event.app.exit()

### --- Main chat send loop --- ###

@kb.add('c-space', eager=True)
async def _(event):
    """
    Handle Control+Enter key press to send input.
    """
    user_input = msg_buffer.text

    if user_input.strip(): 

        msg_buffer.text = "AI is busy." 

        current_chat_text = chat_formatted_text.text
        chat_formatted_text.text = current_chat_text + f"You: {user_input}\n"
        get_app().invalidate()

        handler.manage_context_window("user", user_input)

        ai_thinking, ai_answer = await asyncio.to_thread(handler.generate_chat_response)
        
        current_chat_text = chat_formatted_text.text
        chat_formatted_text.text = current_chat_text + f"LLM: {ai_answer}\n"

        current_thinking_text = thinking_formatted_text.text
        thinking_formatted_text.text = current_thinking_text + f"Thoughts: {ai_thinking}\n"

        get_app().invalidate()

        handler.manage_context_window("assistant", ai_answer)

        msg_buffer.text = ""

    else:

        pass


