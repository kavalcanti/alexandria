# Alexandria User Guide

## Interface Overview

Alexandria features a sophisticated terminal-based interface with three main sections:
1. Chat Window (Left Panel)
2. Thinking Window (Right Panel)
3. Input Area (Bottom)

## Keyboard Controls

### Essential Commands
- `Ctrl+Space`: Send message
- `Ctrl+Q`: Quit application
- `Ctrl+O`: Reset conversation (clears history and context)

### Navigation
- `Ctrl+Up/Down`: Scroll chat history up/down
- `Shift+Up/Down`: Scroll thinking window up/down

### Input Controls
The input area supports standard terminal text editing:
- Use arrow keys for cursor movement
- Standard copy/paste shortcuts work as expected
- Multi-line input is supported

## Interface Sections

### Chat Window (Left Panel)
- Displays the conversation history
- Shows both user messages and AI responses
- Automatically scrolls to new messages
- Manual scrolling with `Ctrl+Up/Down`

### Thinking Window (Right Panel)
- Shows the AI's reasoning process
- Displays token usage and processing steps
- Scroll through thinking history with `Shift+Up/Down`
- Helps understand how the AI reaches its conclusions

### Status Bar
- Top: Displays application title and status
- Bottom: Shows available keyboard shortcuts

## Best Practices

### Effective Communication
1. Be specific in your queries
2. Use multi-line input for complex questions
3. Monitor the thinking window for insight into the AI's process

### Session Management
1. Use `Ctrl+O` to start fresh when changing topics
2. Scroll through history to reference previous exchanges
3. Check the thinking window for token usage to optimize long conversations

### Troubleshooting
1. If the AI seems stuck, check the thinking window
2. Use `Ctrl+O` to reset if the context becomes confused
3. Monitor the status bar for system messages

## Advanced Features

### Context Window
- The system maintains a sliding context window
- Previous conversation history influences responses
- Reset with `Ctrl+O` if context becomes irrelevant

### Model Behavior
- Responses are generated in real-time
- The thinking window shows token usage and processing
- Response time varies based on query complexity

### Persistence
- Conversations are automatically saved
- History is maintained between sessions
- Use `Ctrl+O` to explicitly start fresh 