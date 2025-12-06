# Shopify Concierge - Agentic AI Customer Support
### Intelligent, Context-Aware Support Powered by Fine-Tuned Mistral 12B

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Mistral](https://img.shields.io/badge/Mistral%20AI-Mistral%2012B-orange?style=for-the-badge)
![Unsloth](https://img.shields.io/badge/Unsloth-2x%20Faster%20Fine--Tuning-yellow?style=for-the-badge)
![LangChain](https://img.shields.io/badge/LangChain-Agentic%20Workflow-green?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-Premium%20UI-red?style=for-the-badge)
![Pinecone](https://img.shields.io/badge/Pinecone-RAG%20Vector%20DB-blue?style=for-the-badge)

---

## 🚀 Problem & Solution

### The Problem
Traditional customer support chatbots are often frustratingly generic. They lack deep product knowledge, fail to understand context, and cannot take meaningful action (like escalating a ticket). They act as simple FAQ retrieval systems rather than intelligent agents.

### The Solution: Shopify Concierge
**Shopify Concierge** is an **Agentic AI System** designed to solve customer issues autonomously. Unlike standard chatbots, it combines:
1.  **Deep Knowledge:** Fine-tuned on 1,500+ Q&A pairs from official docs and Reddit threads.
2.  **Agentic Behavior:** It "thinks" before answering—analyzing sentiment, consulting memory, and deciding whether to answer or escalate.
3.  **Actionable Tools:** It can autonomously create support tickets in the database and email the support team when a customer is distressed.

---

## 🏗️ System Architecture

The project implements a full end-to-end pipeline from data engineering to agentic inference.

```mermaid
graph TD
    subgraph "Data Pipeline"
        A[Official Docs Scraper] --> B[Cleaning & formatting]
        C[Reddit Community Scraper] --> B
        B --> D[Q&A Dataset (JSONL)]
    end

    subgraph "Model Engine"
        D --> E[Fine-Tuning Mistral 12B]
        E -->|Unsloth Optimization| F[Custom LoRA Adapter]
    end

    subgraph "Agentic Inference"
        User --> G[Streamlit UI]
        G --> H[Support Agent]
        H --> I{Sentiment Router}
        I -->|Negative/Escalate| J[Ticket Tool]
        I -->|Neutral/Positive| K[RAG Engine]
        K -->|Retrieve| L[Pinecone Vector DB]
        L --> M[LLM Response]
        M --> G
    end
```

---

## 🧠 Key Technologies & Skills

### 1. Agentic AI & Orchestration
The core of the system is the `SupportAgent` (in `agents/support_agent.py`), which acts as an autonomous orchestrator:
-   **Sentiment Routing:** Uses VADER/RoBERTa analysis to detect customer frustration. If sentiment drops below a threshold, the agent automatically offers to create a ticket.
-   **Tool Use:** The LLM is equipped with function calling capabilities (`create_support_ticket`), allowing it to perform backend actions rather than just generating text.
-   **Conversation Memory:** Maintains state across the session to answer follow-up questions effectively.

### 2. Fine-Tuning with Unsloth (Mistral 12B)
To achieve domain mastery, I fine-tuned **Mistral 12B** using **Unsloth**, a library that accelerates training by 2x and reduces memory usage by 60%.
-   **Dataset:** 1,521 high-quality Q&A pairs scraped from Shopify Help Center and r/Shopify.
-   **Technique:** LoRA (Low-Rank Adaptation) for efficient parameter updates.
-   **Result:** A model that understands Shopify-specific terminology ("Liquid", "themes", "Shopify Payments") far better than base models.

### 3. Advanced RAG (Retrieval-Augmented Generation)
-   **Vector Store:** Pinecone is used to store embeddings of the documentation.
-   **Hybrid Search:** Combines semantic search (embeddings) with keyword matching for precision.
-   **Source Citation:** The agent retrieves context to provide accurate, hallucination-free answers.

---

## 🛠️ Project Structure

```bash
├── agents/               # Agentic Logic
│   ├── support_agent.py  # Main orchestrator (State, RAG, Tools)
│   ├── sentiment_agent.py# Sentiment analysis & routing
│   └── summarization_agent.py
├── llm/                  # Model Wrappers
│   └── __init__.py       # Google Gemini / Mistral Wrapper
├── rag/                  # RAG Implementation
├── tickets/              # Ticket Management System
│   ├── database.py       # SQLite / SQLAlchemy models
│   └── email_service.py  # SMTP integration
├── scraper.py            # Official Documentation Scraper
├── reddit_scraper_no_api.py # Selenium-based Reddit Scraper
├── app.py                # Streamlit Premium UI
└── config.py             # Environment Configuration
```

---

## 💻 Installation & Usage

### Prerequisites
- Python 3.10+
- Pinecone API Key
- Google Gemini API Key (for current inference) or GPU for local Mistral inference.

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/shopify-concierge.git
cd shopify-concierge
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file:
```env
PINECONE_API_KEY=your_key
GOOGLE_API_KEY=your_key
HUGGINGFACE_API_KEY=your_key
GMAIL_EMAIL=your_email (for ticket alerts)
GMAIL_APP_PASSWORD=your_app_password
```

### 3. Run the Application
Launch the premium chatbot interface:
```bash
streamlit run app.py
```

### 4. (Optional) Run Data Pipeline
If you want to regenerate the dataset:
```bash
# Scrape official docs
python scraper.py

# Scrape Reddit (Headless Browser)
python reddit_scraper_no_api.py
```

---

## ✨ Features Checklist
- [x] **Premium UI:** Custom CSS-styled Streamlit interface with user profiles and stats.
- [x] **Sentiment Analysis:** Real-time emotion tracking displayed in the sidebar.
- [x] **Auto-Escalation:** System detects anger and proactively creates support tickets.
- [x] **Email Integration:** Sends real emails to support teams when tickets are created.
- [x] **Encrypted Session:** Secure session management.

---

**Built by Sarah Jenkins**
*Agentic AI | LLM Fine-Tuning | Full-Stack Data Engineering*
