# Development Plan: Multi-Agent AI Chatroom

> **Note:** This file is a legacy high-level design document for the original multi-agent chatroom. The **live per-project planning artifacts** are now maintained under each project's `scratch/shared/` folder:
>
> - `master_plan.md` – long-form architecture and phase plan (Architect-only writer).
> - `devplan.md` – Architect's internal tracker for phases, tasks, and technical notes.
> - `dashboard.md` – auto-generated, user-facing project dashboard rendered in the TUI.
>
> See `handoff.md` for the latest swarm orchestration notes.

## Project Overview

This document outlines the complete design for a multi-agent AI chatroom system using the Z.ai API. The system enables multiple AI agents with distinct personas to converse together while maintaining memory, with support for human participation via WebSocket and Discord.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Terminal   │  │  WebSocket   │  │   Discord    │          │
│  │     CLI      │  │   Browser    │  │     Bot      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
└─────────┼─────────────────┼─────────────────┼────────────────────┘
          │                 │                 │
┌─────────┴─────────────────┴─────────────────┴────────────────────┐
│                         ORCHESTRATION LAYER                       │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      CHATROOM                               │  │
│  │  • Message routing & history                               │  │
│  │  • Round management                                        │  │
│  │  • Broadcast system                                        │  │
│  │  • Human message handling                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────────────────────────┐
│                           AGENT LAYER                             │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Professor  │ │   HexMage   │ │   Synthia   │ │ Bureaucrat │ │
│  │    Byte     │ │             │ │             │ │   -9000    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│  ┌─────────────┐ ┌─────────────┐                                │
│  │    Lumen    │ │    Krait    │                                │
│  └─────────────┘ └─────────────┘                                │
│                                                                   │
│  Each agent has:                                                 │
│  • Unique system prompt & persona                                │
│  • Assigned Z.ai model                                           │
│  • Speaking probability                                          │
│  • Temperature settings                                          │
└──────────────────────────────────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────────────────────────┐
│                          MEMORY LAYER                             │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────┐  ┌────────────────────────────────┐  │
│  │    SHORT-TERM MEMORY   │  │      LONG-TERM MEMORY          │  │
│  │  • Rolling 10-message  │  │  • SQLite database             │  │
│  │    window per agent    │  │  • Facts, summaries            │  │
│  │  • In-memory storage   │  │  • Importance scoring          │  │
│  └────────────────────────┘  └────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      SUMMARIZER                             │  │
│  │  • Periodic conversation summaries                         │  │
│  │  • Fact extraction from messages                           │  │
│  │  • Memory lifecycle management                             │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
          │
┌─────────┴────────────────────────────────────────────────────────┐
│                           API LAYER                               │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Z.AI API CLIENT                          │  │
│  │  • Async HTTP with aiohttp                                 │  │
│  │  • Semaphore-limited concurrency                           │  │
│  │  • Multiple model support                                  │  │
│  │  • Error handling & retries                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Endpoint: POST https://api.z.ai/v1/chat/completions             │
│  Headers: Authorization: Bearer $ZAI_API_KEY                     │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Message Flow
```
Human/Agent Message
        │
        ▼
┌───────────────┐
│   Chatroom    │
│  add_message  │
└───────┬───────┘
        │
        ├──────────────────┐
        ▼                  ▼
┌───────────────┐  ┌───────────────┐
│  History Add  │  │  Broadcast    │
│  State Update │  │  to Listeners │
└───────┬───────┘  └───────────────┘
        │
        ▼
┌───────────────┐
│ Agent Memory  │
│    Update     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Check Summary │
│   Threshold   │
└───────┬───────┘
        │ (every 5 messages)
        ▼
┌───────────────┐
│   Summarize   │
│ Extract Facts │
└───────────────┘
```

### Agent Response Flow
```
run_conversation_round()
        │
        ▼
┌───────────────────────┐
│ Shuffle Agent Order   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  For Each Agent:      │
│  • Check speak_prob   │──────▶ Skip if random > prob
│  • Build context      │
│  • Call Z.ai API      │
│  • Clean response     │
│  • Create Message     │
└───────────┬───────────┘
            │ (concurrent with semaphore)
            ▼
┌───────────────────────┐
│  Collect Responses    │
│  Shuffle Order        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  Broadcast Each       │
│  with Natural Delay   │
└───────────────────────┘
```

## Component Specifications

### 1. Agent System Prompts

Each agent receives a comprehensive system prompt including:

1. **Core Personality Traits** - Fundamental character attributes
2. **Speaking Style** - How the agent communicates
3. **Conversational Behaviors** - Interaction patterns
4. **Signature Phrases** - Unique expressions
5. **Forbidden Behaviors** - What to avoid
6. **Memory Usage Instructions** - How to leverage memory
7. **Response Format** - Structure and length guidelines

### 2. Memory Schema

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- 'fact', 'summary', 'observation'
    importance REAL DEFAULT 0.5,
    timestamp TEXT NOT NULL,
    source_messages TEXT,  -- JSON array of message IDs
    embedding TEXT  -- Reserved for vector search
);

CREATE INDEX idx_memories_agent ON memories(agent_id);
CREATE INDEX idx_memories_type ON memories(agent_id, memory_type);
CREATE INDEX idx_memories_importance ON memories(agent_id, importance DESC);
```

### 3. API Request Format

```json
{
    "model": "glm-4",
    "messages": [
        {"role": "system", "content": "<system_prompt_with_memories>"},
        {"role": "user", "content": "[ProfessorByte]: Previous message..."},
        {"role": "assistant", "content": "[HexMage]: Another message..."},
        {"role": "user", "content": "[Human]: Latest message..."}
    ],
    "temperature": 0.8,
    "max_tokens": 500
}
```

### 4. WebSocket Protocol

**Client → Server:**
```json
{"type": "chat", "content": "Hello agents!"}
{"type": "ping"}
{"type": "status"}
```

**Server → Client:**
```json
{
    "type": "welcome",
    "data": {
        "user_id": "uuid",
        "username": "User",
        "history": [...],
        "status": {...}
    }
}
```
```json
{
    "type": "message",
    "data": {
        "id": "uuid",
        "sender_name": "HexMage",
        "content": "ohoho interesting...",
        "timestamp": "2024-01-01T12:00:00",
        "role": "assistant"
    }
}
```

## Extension Points

### Adding Custom Integrations

```python
# Register a custom message listener
chatroom.on_message(my_custom_handler)

# The handler receives Message objects
async def my_custom_handler(message: Message):
    # Forward to Slack, log to file, trigger webhooks, etc.
    await slack_client.send(message.content)
```

### Custom Memory Backends

```python
class VectorMemoryStore(MemoryStore):
    """Replace SQLite with vector database."""
    
    async def search_memories(self, agent_id, query, limit):
        # Use embeddings for semantic search
        embedding = await self.embed(query)
        return self.vector_db.search(embedding, limit)
```

### Event System (Future)

```python
class Chatroom:
    async def _check_triggers(self, message):
        if "help" in message.content.lower():
            await self._emit("help_requested", message)
        
        if message.sender_name == "HexMage" and "chaos" in message.content:
            await self._emit("chaos_mode_activated")
```

## Scaling Considerations

### Current Limits
- 5 concurrent API calls (configurable)
- 10 messages in short-term memory
- 100 messages in saved history

### Future Scaling
- **Horizontal**: Multiple chatroom instances with shared memory
- **Memory**: Switch to Redis for cross-instance state
- **API**: Rate limiting and request queuing
- **Storage**: Archive old messages to cold storage

## Security Notes

1. **API Keys**: Never commit `.env` files
2. **WebSocket**: Consider adding authentication for production
3. **Discord**: Use environment variables for tokens
4. **Input**: Messages are sanitized in web client
5. **Memory**: SQLite file should be protected

## Testing Strategy

### Unit Tests
- Agent response generation
- Memory storage and retrieval
- Message formatting

### Integration Tests
- Full conversation rounds
- WebSocket connection lifecycle
- Discord command handling

### Load Tests
- Multiple concurrent human users
- Sustained conversation rounds
- Memory growth over time
