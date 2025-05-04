# Viability

### llm response object parsing
must parse <think> tag or disable temporarily
token count extraction

### Make chat window track bottom
chat window must always focus on end of previos usr/llm message

### Create rolling history from prompt toolkit n=5
pydantic/class object 
enables point below

### Use prompt toolkit buffer as llm history
create object to translate buffer <-> llm history
enables point below

### Edit chat buffer -> history
feeds into buffer -> prompt loop

# Feat

## UI

### Side panel chat select
will require db integration and title generation

display msg/token count (msg/tkn) (TITLE)

# Backend

## DB

### Connect DB
msg and chat history

embeddings table for local docs

#### Expand db models

### Title generation
based on 2 first exchanges

### msg count update
init with 0

cumsum llm+usr msg count

## LLM
chaining

vector query builder

### Agentic
search plan

web search?

reiterate over wiki dataset search


## RAG
pgvector embedding
pgvector retrieval
wikipedia dataset
