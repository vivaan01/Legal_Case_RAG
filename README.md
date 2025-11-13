# Legal_Case_RAG

PROJECT FLOW

### Project Overview
This project is a Legal Case RAG (Retrieval-Augmented Generation) system built with Python, using technologies like FastAPI for the backend, Streamlit for the UI, LangChain for RAG pipelines, Ollama for local LLM inference, and tools for adaptive responses. It's designed to handle legal documents (e.g., PDF rulings), ingest them into a searchable database, and provide intelligent, context-aware answers to user queries about legal cases. The system is "adaptive" (it can heal low-rated responses) and "tool-enriched" (integrates tools like memory recall or external searches if needed). The project structure includes:

- Backend ( `backend` ): Handles API endpoints, retrieval, generation, and memory.
- UI ( `ui` ): A Streamlit app for uploading PDFs, querying, and rating responses.
- Data ( `data` ): Stores ingested PDFs and serialized indexes (e.g., BM25 docs).
- Supporting files like `requirements.txt` for dependencies and scripts like `upload.ps1` for testing ingestion.
The app runs locally: backend on port 8000 (via Uvicorn) and UI on port 8501 (via Streamlit). It emphasizes privacy by using local Ollama models and vector stores.

### Data Flow
The data flows through the system in a cycle of ingestion, querying, retrieval, generation, and feedback. Here's a step-by-step breakdown:

1. PDF Ingestion (User Upload to Storage) :
   
   - Entry Point : You upload PDFs via the Streamlit UI ( `app.py` ). The UI sends the file to the backend's /ingest endpoint ( `ingest_pdf` ).
   - Processing : In `retrieval.py` , the PDF is loaded, split into chunks (using RecursiveCharacterTextSplitter), embedded (using OllamaEmbeddings), and stored in a Chroma vector database. BM25 indexing is also created for keyword-based search.
   - Output : Chunks are saved in `data` (e.g., bm25_docs.pkl ), and the vector DB persists locally. This prepares the data for fast retrieval.
   - Flow : UI → Backend API → Text Splitting → Embedding → Vector Store + BM25 Index.
2. User Query (Input to Response) :
   
   - Entry Point : You enter a query in the UI (e.g., "Breach damages in contract disputes?"), which hits the backend's /query_stream or /query endpoint ( `query_stream` ).
   - Retrieval : The query is passed to an `EnsembleRetriever` (combines BM25 for keywords and vector search for semantics). Relevant documents are fetched using invoke method.
   - Context Building : In `rag_chain.py` , the retrieved docs are formatted into context. Conversation history is pulled from memory to make responses contextual.
   - Generation : The RAG chain (built with LangChain's RunnablePassthrough, prompts, and Ollama LLM) generates a response. If streaming is enabled, it yields chunks in real-time.
   - Output : The response is streamed back to the UI for display.
   - Flow : UI Query → Backend API → Retrieval (BM25 + Vector) → Context + History → LLM Generation → UI Response.
3. Feedback and Adaptation :
   
   - Entry Point : After a response, you rate it (1-5) in the UI, sending feedback to /feedback endpoint ( `submit_feedback` ).
   - Processing : In `feedback.py` , low ratings trigger a "heal" mechanism: re-run the query with adjusted parameters (e.g., more context or different tools) to improve the answer.
   - Flow : UI Rating → Backend API → Check Rating → Heal if Low → Updated Response to UI.
### Pipelines
The core pipelines are implemented using LangChain chains in the backend services:

- Ingestion Pipeline ( `retrieval.py` ):
  
  - Loads PDF → Splits text → Embeds chunks → Adds to Chroma DB → Builds BM25 index.
  - Key: Ensures hybrid retrieval (semantic + keyword) for accurate legal document search.
- RAG Pipeline ( `rag_chain.py` and `rag_chain_MINI_PROJECT.py` ):
  
  - Retrieval Step : Uses EnsembleRetriever to get docs.
  - Context Generation : Formats docs into a string (via _get_context function at line 36 in rag_chain.py).
  - Chain Assembly : Combines prompt templates, retriever, memory, and Ollama LLM into a runnable chain.
  - Tool Enrichment : Integrates tools from `tools.py` (e.g., for external data or calculations) to enhance responses.
  - Streaming/Non-Streaming : Supports real-time output for better UX.
- Feedback Pipeline ( `feedback.py` ):
  
  - Stores ratings → Triggers re-generation if rating < 3 → Uses adaptive logic (e.g., more docs or refined prompt).
These pipelines are modular, with dependencies managed in `requirements.txt` (e.g., langchain, fastapi, ollama).

### Memory Management
Memory is handled to maintain conversation context, making the system stateful (remembers past interactions for better responses).

- Implementation : In `memory.py` , it uses LangChain's ConversationBufferMemory or similar to store chat history per user (keyed by user_id).
- Integration : During query processing, history is loaded via `load_memory` and injected into the RAG chain. New messages are saved after each response.
- Tools : Memory tools from `memory_tools.py` (note: path might be under backend) allow the LLM to query past conversations if needed.
- Data Flow in Memory : Query → Load History → Include in Prompt → Generate Response → Save New Message → Persist (e.g., in-memory or file-based for persistence).
- Management : History is limited to avoid token overflow (e.g., buffer size), and it's user-specific for privacy.
