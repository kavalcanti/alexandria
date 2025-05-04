from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.keys import Keys


lorem = """

The standard Lorem Ipsum passage, used since the 1500s

"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
Section 1.10.32 of "de Finibus Bonorum et Malorum", written by Cicero in 45 BC

"Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?"
1914 translation by H. Rackham

"But I must explain to you how all this mistaken idea of denouncing pleasure and praising pain was born and I will give you a complete account of the system, and expound the actual teachings of the great explorer of the truth, the master-builder of human happiness. No one rejects, dislikes, or avoids pleasure itself, because it is pleasure, but because those who do not know how to pursue pleasure rationally encounter consequences that are extremely painful. Nor again is there anyone who loves or pursues or desires to obtain pain of itself, because it is pain, but because occasionally circumstances occur in which toil and pain can procure him some great pleasure. To take a trivial example, which of us ever undertakes laborious physical exercise, except to obtain some advantage from it? But who has any right to find fault with a man who chooses to enjoy a pleasure that has no annoying consequences, or one who avoids a pain that produces no resultant pleasure?"
Section 1.10.33 of "de Finibus Bonorum et Malorum", written by Cicero in 45 BC

"At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat."
1914 translation by H. Rackham

"On the other hand, we denounce with righteous indignation and dislike men who are so beguiled and demoralized by the charms of pleasure of the moment, so blinded by desire, that they cannot foresee the pain and trouble that are bound to ensue; and equal blame belongs to those who fail in their duty through weakness of will, which is the same as saying through shrinking from toil and pain. These cases are perfectly simple and easy to distinguish. In a free hour, when our power of choice is untrammelled and when nothing prevents our being able to do what we like best, every pleasure is to be welcomed and every pain avoided. But in certain circumstances and owing to the claims of duty or the obligations of business it will frequently occur that pleasures have to be repudiated and annoyances accepted. The wise man therefore always holds in these matters to this principle of selection: he rejects pleasures to secure other greater pleasures, or else he endures pains to avoid worse pains."

"""



chat_buffer = Buffer(read_only=True)
msg_buffer = Buffer()
chats_buffer = Buffer()

chat_content = Window(BufferControl(buffer=chat_buffer),wrap_lines=True)
chat_window = ScrollablePane(content=chat_content)

msg_window = Window(BufferControl(buffer=msg_buffer), height=5, wrap_lines=True)
chats_window = Window(BufferControl(buffer=chats_buffer), width=20)

kb = KeyBindings()

body_a = HSplit(
    [
        chat_window,

        Window(height=1, char="-", style="class:line"),

        msg_window
    ]
)


body_b = VSplit(
    [
        body_a,
        Window(width=1, char="#", style="class:line"),
        chats_window
    ]
)


def get_titlebar_text():
    return [
        ("class:title", " Hello world "),
        ("class:title", " (Press [Ctrl-Q] to quit, [Ctrl+A] to send msg.)"),
    ]


root_container = HSplit(
    [
        # The titlebar.
        Window(
            height=1,
            content=FormattedTextControl(get_titlebar_text),
            align=WindowAlign.CENTER,
        ),

        Window(height=1, char="-", style="class:line"),

        body_b,
    ]
)


application = Application(
    layout=Layout(root_container, focused_element=msg_window),
    key_bindings=kb,
    # Let's add mouse support!
    mouse_support=True,
    # Using an alternate screen buffer means as much as: "run full screen".
    # It switches the terminal to an alternate screen.
    full_screen=True,
)

# from src.vllm_model_calls import llm
# from vllm.sampling_params import SamplingParams
# sampling_params = SamplingParams(max_tokens=8192, temperature=0.0)


@kb.add('c-m' ,eager=True)
def _(event):
    event.app.layout.focus(msg_window)

@kb.add('c-n',eager=True)
def _(event):
    event.app.layout.focus(chat_window)

@kb.add("c-q", eager=True)
def _(event):
    """
    Pressing Ctrl-Q or Ctrl-C will exit the user interface.
    """
    event.app.exit()

@kb.add('c-space', eager=True)
def _(event):
    """
    Handle Control+Enter key press to send input.
    """
    user_input = msg_buffer.text

    conversation = [
    {
        "role": "system",
        "content": "You are a helpful assistant"
    },
    {
        "role": "user",
        "content": "Hello"
    },
    {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
    },
    {
        "role": "user",

        "content": user_input,
    },
]


    if user_input.strip(): # Only send if input is not empty
        msg_buffer.text = "AI is busy." # Clear input field

        # response = llm.chat(conversation, sampling_params=sampling_params)
        
        msg_buffer.text = "" # Clear input field
        # TODO: Process user_input (send to LLM)
        # TODO: Append user message to chat_buffer
        # TODO: Get LLM response and append to chat_buffer
        chat_buffer.insert_text(f"You: {user_input}\n",byp)
        # Simulate LLM response (replace with actual LLM call)


        # chat_buffer.insert_text(f"LLM: {response[0].outputs[0].text}")
        chat_buffer.insert_text(f"LLM: {lorem}")
    else:
        # Optionally, handle empty input (e.g., do nothing or show a message)
        pass


