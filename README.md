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


### How Data Gets Saved in Memory: From PDF Ingestion to Model Working
I'll explain this step by step based on the project's codebase. This Legal Case RAG system processes PDF documents (e.g., legal rulings) through ingestion, stores them in a hybrid way (vector embeddings for semantic search and BM25 for keyword search), and uses them in a Retrieval-Augmented Generation (RAG) pipeline powered by an Ollama LLM. "Memory" here refers to two things:

- Data storage for retrieval : Chunks of PDF text saved in an in-memory vector store (DocArray) and a pickled BM25 index on disk.
- Conversation memory : A separate manager that tracks query history and extracts key entities (e.g., case types like "contract dispute") into a dictionary for context-aware responses.
This is drawn from key files like `retrieval.py` , `routes.py` , `rag_chain.py` , and the `README.md` . Note: The vector store is rebuilt in-memory on each ingest or query, so it's not persistently "saved" to disk like the BM25 index—it's efficient for quick local use but resets on app restart.
 1. PDF Ingestion Process
Ingestion happens when you upload a PDF via the Streamlit UI ( `app.py` ) or directly via the API (e.g., /ingest endpoint). Here's the flow:

- Upload and Temporary Storage :
  
  - The PDF is uploaded to the backend (FastAPI server).
  - It's saved temporarily to the data/ directory (e.g., data/upload_{filename}.pdf ). This path is configured in `settings.py` as DATA_DIR (default: data/ ).
  - Example: If you upload "Ram_Mandir_Judgment.pdf", it's written to disk as a binary file.
- Loading and Chunking the PDF :
  
  - The system uses LangChain's PyPDFLoader to read the PDF content (from `retrieval.py` ).
  - Raw text is extracted page-by-page into Document objects (each with page_content and metadata like page number).
  - Text is split into smaller chunks using RecursiveCharacterTextSplitter :
    - Chunk size: 900 characters (to keep chunks manageable for embedding).
    - Overlap: 150 characters (to preserve context across chunks).
  - Result: A list of Document objects, e.g., one PDF might become 50-100 chunks depending on length.
- Updating the BM25 Index (Keyword-Based Search) :
  
  - BM25 is a sparse retrieval method for exact keyword matching.
  - If an existing BM25 index exists (as a pickle file at data/bm25_docs.pkl ), it's loaded.
  - New chunks from the PDF are appended to the existing ones.
  - The combined list is pickled (serialized) back to data/bm25_docs.pkl for persistence on disk.
  - A BM25Retriever is created or updated with these documents (sets k=6 to retrieve top 6 matches).
- Building the Vector Store (Semantic Search) :
  
  - Uses Ollama embeddings (via OllamaEmbeddings from `llm.py` , default model: "nomic-embed-text").
  - Chunks are embedded into vectors (numerical representations) and stored in an in-memory DocArrayInMemorySearch vector store.
  - This is rebuilt fresh during ingestion or queries—it's not saved to disk, so it's fast but ephemeral (lost on restart).
  - The system creates a hybrid retriever: EnsembleRetriever combining vector search (55% weight) and BM25 (45% weight), retrieving top 6 from each.
- Ingestion Response :
  
  - Returns stats like number of new chunks, total BM25 docs, and whether the vector store was updated.
  - If errors occur (e.g., invalid PDF), it raises an HTTP error.
At this point, data is "saved" as:

- Persistent : Raw PDF in data/ , BM25 index in bm25_docs.pkl .
- In-Memory : Vector embeddings in DocArray (recreated as needed). 2. How Data is Saved in Memory
- In-Memory Vector Store (DocArray) :
  
  - Not truly "saved" to disk—it's an in-memory database rebuilt from the BM25 pickle's documents during queries.
  - Why? Efficiency for local dev; vectors are recomputed quickly via Ollama (local LLM server at http://localhost:11434 ).
  - Storage: Each chunk's text is embedded into a vector (e.g., 768-dimensional array) and indexed for similarity search.
- BM25 Index on Disk :
  
  - Saved as a Python pickle file ( bm25_docs.pkl ), which serializes the list of Document objects.
  - This acts as the "memory" backbone—load it, rebuild vectors if needed.
- Conversation Memory (MemoryManager) :
  
  - Separate from document data. Manages query history per user (e.g., "default_user").
  - Extracts entities like "case_type" (e.g., "contract") into a dict for contextual responses.
  - Stored in-memory (not on disk), built on-the-fly from past queries.
  - Used in the RAG chain to include history in prompts.
- No Database for Documents : Unlike production systems, this uses in-memory + pickle for simplicity. Redis is only for feedback ratings (as explained previously), not document storage. 3. How the Model Works (RAG Pipeline)
The "model" here is the end-to-end RAG system: Retrieval (fetch relevant chunks) + Generation (LLM answers using those chunks). It uses Ollama's LLM (default: "mistral:7b") with LangChain chains.

- Query Submission :
  
  - From UI or API (e.g., /query or /query_stream ).
  - Includes user query and history from MemoryManager.
- Retrieval Step :
  
  - Hybrid retriever fetches top chunks:
    - Vector search: Finds semantically similar chunks (e.g., via cosine similarity on embeddings).
    - BM25: Finds keyword matches.
    - Combines results into a context string (chunks joined with "---").
- Generation Step (RAG Chain) :
  
  - Builds a chain in `rag_chain.py` :
    - Prompt: System message + history + query + context.
    - LLM (Ollama) generates response, optionally using tools like citation_lookup (mock tool for case citations).
  - For streaming: Responses are sent token-by-token (e.g., via /query_stream ).
  - Adaptive features: If feedback rating <3, it "heals" by refining the query and re-running the chain.
- Output :
  
  - Answer with sources/metadata.
  - Memory updated with the new query/response for future context. Example Flow
1. Upload PDF → Chunks created → Appended to bm25_docs.pkl → Vectors built in-memory.
2. Query: "Breach damages?" → Retrieve chunks from hybrid index → LLM generates answer using context + history.
3. Rate low → Heal: Refine query, re-retrieve, re-generate.








### How Data Gets Saved in Memory: From PDF Ingestion to Model Working
I'll explain this step by step based on the project's codebase. This Legal Case RAG system processes PDF documents (e.g., legal rulings) through ingestion, stores them in a hybrid way (vector embeddings for semantic search and BM25 for keyword search), and uses them in a Retrieval-Augmented Generation (RAG) pipeline powered by an Ollama LLM. "Memory" here refers to two things:

- Data storage for retrieval : Chunks of PDF text saved in an in-memory vector store (DocArray) and a pickled BM25 index on disk.
- Conversation memory : A separate manager that tracks query history and extracts key entities (e.g., case types like "contract dispute") into a dictionary for context-aware responses.
This is drawn from key files like `retrieval.py` , `routes.py` , `rag_chain.py` , and the `README.md` . Note: The vector store is rebuilt in-memory on each ingest or query, so it's not persistently "saved" to disk like the BM25 index—it's efficient for quick local use but resets on app restart.
 1. PDF Ingestion Process
Ingestion happens when you upload a PDF via the Streamlit UI ( `app.py` ) or directly via the API (e.g., /ingest endpoint). Here's the flow:

- Upload and Temporary Storage :
  
  - The PDF is uploaded to the backend (FastAPI server).
  - It's saved temporarily to the data/ directory (e.g., data/upload_{filename}.pdf ). This path is configured in `settings.py` as DATA_DIR (default: data/ ).
  - Example: If you upload "Ram_Mandir_Judgment.pdf", it's written to disk as a binary file.
- Loading and Chunking the PDF :
  
  - The system uses LangChain's PyPDFLoader to read the PDF content (from `retrieval.py` ).
  - Raw text is extracted page-by-page into Document objects (each with page_content and metadata like page number).
  - Text is split into smaller chunks using RecursiveCharacterTextSplitter :
    - Chunk size: 900 characters (to keep chunks manageable for embedding).
    - Overlap: 150 characters (to preserve context across chunks).
  - Result: A list of Document objects, e.g., one PDF might become 50-100 chunks depending on length.
- Updating the BM25 Index (Keyword-Based Search) :
  
  - BM25 is a sparse retrieval method for exact keyword matching.
  - If an existing BM25 index exists (as a pickle file at data/bm25_docs.pkl ), it's loaded.
  - New chunks from the PDF are appended to the existing ones.
  - The combined list is pickled (serialized) back to data/bm25_docs.pkl for persistence on disk.
  - A BM25Retriever is created or updated with these documents (sets k=6 to retrieve top 6 matches).
- Building the Vector Store (Semantic Search) :
  
  - Uses Ollama embeddings (via OllamaEmbeddings from `llm.py` , default model: "nomic-embed-text").
  - Chunks are embedded into vectors (numerical representations) and stored in an in-memory DocArrayInMemorySearch vector store.
  - This is rebuilt fresh during ingestion or queries—it's not saved to disk, so it's fast but ephemeral (lost on restart).
  - The system creates a hybrid retriever: EnsembleRetriever combining vector search (55% weight) and BM25 (45% weight), retrieving top 6 from each.
- Ingestion Response :
  
  - Returns stats like number of new chunks, total BM25 docs, and whether the vector store was updated.
  - If errors occur (e.g., invalid PDF), it raises an HTTP error.
At this point, data is "saved" as:

- Persistent : Raw PDF in data/ , BM25 index in bm25_docs.pkl .
- In-Memory : Vector embeddings in DocArray (recreated as needed). 2. How Data is Saved in Memory
- In-Memory Vector Store (DocArray) :
  
  - Not truly "saved" to disk—it's an in-memory database rebuilt from the BM25 pickle's documents during queries.
  - Why? Efficiency for local dev; vectors are recomputed quickly via Ollama (local LLM server at http://localhost:11434 ).
  - Storage: Each chunk's text is embedded into a vector (e.g., 768-dimensional array) and indexed for similarity search.
- BM25 Index on Disk :
  
  - Saved as a Python pickle file ( bm25_docs.pkl ), which serializes the list of Document objects.
  - This acts as the "memory" backbone—load it, rebuild vectors if needed.
- Conversation Memory (MemoryManager) :
  
  - Separate from document data. Manages query history per user (e.g., "default_user").
  - Extracts entities like "case_type" (e.g., "contract") into a dict for contextual responses.
  - Stored in-memory (not on disk), built on-the-fly from past queries.
  - Used in the RAG chain to include history in prompts.
- No Database for Documents : Unlike production systems, this uses in-memory + pickle for simplicity. Redis is only for feedback ratings (as explained previously), not document storage. 3. How the Model Works (RAG Pipeline)
The "model" here is the end-to-end RAG system: Retrieval (fetch relevant chunks) + Generation (LLM answers using those chunks). It uses Ollama's LLM (default: "mistral:7b") with LangChain chains.

- Query Submission :
  
  - From UI or API (e.g., /query or /query_stream ).
  - Includes user query and history from MemoryManager.
- Retrieval Step :
  
  - Hybrid retriever fetches top chunks:
    - Vector search: Finds semantically similar chunks (e.g., via cosine similarity on embeddings).
    - BM25: Finds keyword matches.
    - Combines results into a context string (chunks joined with "---").
- Generation Step (RAG Chain) :
  
  - Builds a chain in `rag_chain.py` :
    - Prompt: System message + history + query + context.
    - LLM (Ollama) generates response, optionally using tools like citation_lookup (mock tool for case citations).
  - For streaming: Responses are sent token-by-token (e.g., via /query_stream ).
  - Adaptive features: If feedback rating <3, it "heals" by refining the query and re-running the chain.
- Output :
  
  - Answer with sources/metadata.
  - Memory updated with the new query/response for future context. Example Flow
1. Upload PDF → Chunks created → Appended to bm25_docs.pkl → Vectors built in-memory.
2. Query: "Breach damages?" → Retrieve chunks from hybrid index → LLM generates answer using context + history.
3. Rate low → Heal: Refine query, re-retrieve, re-generate.
