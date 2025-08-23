# memsrv
A simple, self-hosted memory service boilerplate for LLMs and agent frameworks.

(Refined my milestones using Gemini)
### **Project Milestones**

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

-   [ ] **Expose CRUD as Tools:** Enhance the API to expose full Create, Read, Update, and Delete (CRUD) operations, making them usable as "tools" by an AI agent.
-   [ ] **Develop Memory Update Strategy:** Design and implement a baseline mechanism for updating memories. This will handle cases where new information contradicts or refines existing facts (e.g., implementing an "rewriting using LLM" or "append and retrieve latest" logic).

#### **Milestone 4: Refactoring for Extensibility**
*Objective: Optimize the existing code and refactor it into a modular, pluggable architecture to support multiple backends.*

-   [ ] **Optimize Core Services:** Review and optimize the performance of the fact generation and memory update pipelines.
-   [x] **Create a Database Adapter Interface:** Refactor the database-specific code (ChromaDB) to sit behind a generic `VectorDBAdapter` interface. This will make the core service agnostic to the underlying vector database.
-   [x] **Abstract LLM/Embedding Logic:** Refactor the `google-genai` specific code to sit behind a generic `LLMProvider` interface, preparing for future support of other models and libraries like LangChain.

#### **Milestone 5: Demonstrating Modularity**
*Objective: Prove the success of the new pluggable architecture by adding support for a second database.*

-   [ ] **Implement a Second DB Adapter:** Build a new adapter for a different vector database, such as **Postgres with pgvector**, by implementing the `VectorDBAdapter` interface created in the previous milestone.
-   [x] **Enable DB Switching:** Add configuration management to allow the service to easily switch between ChromaDB and Postgres at startup.

#### **Milestone 6: Future Exploration - Multimodality**
*Objective: Scope the work required to expand the service beyond text-only conversations.*

-   [ ] **Research & Design for Multimodality:** Investigate the requirements for handling multimodal memories (e.g., storing image data alongside text).
-   [ ] **Prototype Multimodal Similarity:** Explore and test multimodal embedding models to understand how similarity matching would work across different data types.