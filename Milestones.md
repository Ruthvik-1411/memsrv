# Milestones and Next steps

### **Project Milestones**

<details>
    <summary>Planned Milestones</summary>

#### **Milestone 1: Foundational Fact Pipeline** ✅
*Objective: Establish the core, non-vector pipeline for extracting facts from conversations and storing them with associated metadata.*

-   [x] **Parse & Store Session Data:** Develop a function to process conversation histories (events/messages) into a structured dictionary or JSON format.
-   [x] **Fact Extraction Prompting:** Write a robust prompt using the `google-genai` library to accurately extract key facts from the conversation data.
-   [x] **Initial Vector DB Integration:** Set up a `ChromaDB` instance and implement code to add the generated facts along with their metadata (e.g., `user_id`, `session_id`). Embeddings will be ignored at this stage.
-   [x] **Metadata-Based Retrieval:** Create a service function to fetch stored facts from ChromaDB using only metadata filters.

#### **Milestone 2: Introducing Semantic Search** ✅
*Objective: Integrate vector embeddings to enable semantic retrieval and expose the core functionality via a web API.*

-   [x] **Generate & Store Embeddings:** Enhance the fact creation process to generate vector embeddings for each fact using `google-genai` and store them in ChromaDB.
-   [x] **Implement Similarity Search:** Develop the logic to retrieve memories based on a combination of semantic query similarity and metadata filtering.
-   [x] **Expose via API:** Create a basic `FastAPI` application to expose the core memory services (add, metadata query, semantic query) as REST endpoints.

#### **Milestone 3: Advanced Memory Management**
*Objective: Implement a strategy for handling memory updates and make the service more interactive.*

-   [x] **Expose CRUD as Tools:** Enhance the API to expose full Create, Read, Update, and Delete (CRUD) operations, making them usable as "tools" by an AI agent.
-   [x] **Develop Memory Update Strategy:** Design and implement a baseline mechanism for updating memories. This will handle cases where new information contradicts or refines existing facts (e.g., implementing an "rewriting using LLM" or "append and retrieve latest" logic).

#### **Milestone 4: Refactoring for Extensibility**
*Objective: Optimize the existing code and refactor it into a modular, pluggable architecture to support multiple backends.*

-   [x] **Optimize Core Services:** Review and optimize the performance of the fact generation and memory update pipelines.
-   [x] **Create a Database Adapter Interface:** Refactor the database-specific code (ChromaDB) to sit behind a generic `VectorDBAdapter` interface. This will make the core service agnostic to the underlying vector database.
-   [x] **Abstract LLM/Embedding Logic:** Refactor the `google-genai` specific code to sit behind a generic `LLMProvider` interface, preparing for future support of other models and libraries like LangChain.

#### **Milestone 5: Demonstrating Modularity**✅
*Objective: Prove the success of the new pluggable architecture by adding support for a second database.*

-   [x] **Implement a Second DB Adapter:** Build a new adapter for a different vector database, such as **Postgres with pgvector**, by implementing the `VectorDBAdapter` interface created in the previous milestone.
-   [x] **Enable DB Switching:** Add configuration management to allow the service to easily switch between ChromaDB and Postgres at startup.

#### **Milestone 6: Future Exploration - Multimodality**
*Objective: Scope the work required to expand the service beyond text-only conversations.*

-   [ ] **Research & Design for Multimodality:** Investigate the requirements for handling multimodal memories (e.g., storing image data alongside text).
-   [ ] **Prototype Multimodal Similarity:** Explore and test multimodal embedding models to understand how similarity matching would work across different data types.
</details>

### Key dates
<details>
    <summary>Click here to see key dates</summary>

- Aug 10, 2025 - Repo created
- Aug 14, 2025 - Milestones definition
- Aug 23, 2025 - Baseline memory service creation with fastapi and chromaDB
- Aug 31, 2025 - Added postgres and defined datamodels and **memory consolidation**
- Sep 06, 2025 - Refactored all methods to async
- Sep 12, 2025 - Added linting, modified examples and optimize service initialization
</details>

### Future Plans

Since the service initializations and creation has been centralized into one file <a href="src/memsrv/utils/factory.py">`src/memsrv/utils/factory.py`</a> the service can be exposed as an MCP server or it can be cloned and the methods can be directly used as needed in any codebase.

These modifications will done once all active and important issues have been closed/implemented. The aim is to fully optimize and document the existing service and then move to build different usage methods.