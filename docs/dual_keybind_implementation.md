# Dual Keybind Implementation for RAG and Standard Generation

## Overview

Alexandria now supports separate keybinds for standard and RAG-enabled generation, allowing users to choose between quick responses and knowledge-enhanced responses on a per-message basis.

## Keybind Changes

### Previous Behavior
- **Ctrl+Space**: Automatically used RAG when enabled, otherwise standard generation

### New Behavior
- **Ctrl+Space**: Always uses standard generation (no RAG)
- **Shift+Space**: Uses RAG-enabled generation when available

## Technical Implementation

### Files Modified

1. **`src/ui/keybindings.py`**
   - Split the original `c-space` handler into two separate handlers
   - `c-space`: Standard generation with state manager handling context
   - `s-space`: RAG generation with direct UI updates to avoid double context management

2. **`src/ui/state_manager.py`**
   - Updated documentation to clarify usage patterns
   - Context management now primarily for standard generation

3. **`src/ui/layout.py`**
   - Updated status bar to show both keybind options
   - Reorganized layout for better space utilization

4. **Documentation Updates**
   - `README.md`: Updated keybind reference
   - `docs/userguide.md`: Added explanation of dual modes
   - `docs/UI_RAG_Integration.md`: Updated with new keybind system

### Context Management Strategy

#### Standard Generation (Ctrl+Space)
```
User Input → State Manager → Context Window → LLM → Response → State Manager → UI
```
- State manager handles both UI updates and context window management
- Clean separation of concerns

#### RAG Generation (Shift+Space)
```
User Input → UI Update → RAG Manager → Context Window → LLM → Response → UI Update
```
- RAG manager handles context window management internally
- Keybind handler manages UI updates directly to avoid duplication

## Benefits

1. **User Choice**: Users can choose response type per message
2. **Performance**: Standard generation is faster when RAG isn't needed
3. **Consistency**: RAG responses still benefit from document context
4. **Flexibility**: Can mix standard and RAG responses in same conversation

## Usage Patterns

### When to Use Ctrl+Space (Standard)
- Quick questions that don't require document lookup
- General conversation and brainstorming
- When speed is more important than enhanced context

### When to Use Shift+Space (RAG)
- Technical questions that benefit from documentation
- Research queries requiring factual accuracy
- When you want to leverage your knowledge base

## Testing

A test script (`test_keybinds.py`) verifies:
- Standard generation works correctly
- RAG generation functions when enabled
- Context window management is consistent
- No double-addition of messages

## Migration Notes

### For Users
- **No breaking changes**: Existing workflows continue to work
- **New capability**: Can now choose generation type per message
- **Visual feedback**: Status bar shows both options

### For Developers
- Context management logic simplified
- Clear separation between RAG and standard paths
- Better error handling for RAG unavailability

## Future Enhancements

1. **Visual Indicators**: Show which mode was used for each response
2. **Configurable Defaults**: Allow setting preferred default mode
3. **Hybrid Mode**: Automatic fallback from RAG to standard if no documents found
4. **Performance Metrics**: Display generation time for each mode 