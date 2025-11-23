# 🤖 Agentic AI in Retail Analytics System

An Agentic AI-Powered Intelligence Platform transforming static retail data into actionable, real-time conversations.

## About Nexus Corp

Nexus Corp Analytics is a premier retail showroom specializing in top-brand mobile phones, high-performance laptops, smart gadgets, and electronic appliances. Operating in the hyper-competitive consumer electronics market, Nexus Corp deals with high-value transactions and rapidly changing consumer trends. To maintain its market leadership, the leadership requires precise, real-time insights to optimize pricing strategies, maximize profit margins, and understand regional sales performance instantly. This dashboard serves as the central intelligence hub for their data-driven growth.

## ⏳ Problem Statement

Decision-makers face a critical "Insight Gap":

- **Technical Barrier:** Advanced data querying requires SQL knowledge, leaving non-technical managers dependent on static reports.
- **Missed Opportunities:** Manual reporting is slow; by the time insights are available, the opportunity may have passed.
- **Speed Bottleneck:** Complex questions (e.g., "Why did revenue dip in April?") often take days of back-and-forth with analysts.
- **Context Void:** Internal data shows what happened but not why (e.g., competitor actions, macro trends).
- **Visualization Bottleneck:** Managers often wait for analysts to export to Excel to create simple visualizations.

## 🤝 Solution Overview

NexusCorpus is an autonomous Multi-Agent System (MAS) — a virtual team of AI specialists that treat each user question as a project. The system routes subtasks to specialist agents that collaborate to return synthesized, evidence-backed answers in seconds.

## 👨‍💼 Agent Architecture

![Agent Architecture](https://github.com/adarshms444/Real-Time-News-Sentiment-Analysis-and-Visualization/blob/main/architecture.png)


Agent Name | Role | Functionality
---|---:|---
Supervisor Agent | Project Manager | Orchestrates the workflow (LangGraph). Analyzes user intent and routes tasks to specialist agents.
SQL Agent | Data Analyst | Connects to PostgreSQL and translates natural language into precise SQL queries to retrieve internal metrics (Sales, Profit, Margins).
Web Search Agent | Market Researcher | Uses Tavily API to find external context — competitor news, economic trends, local events — explaining the "why".
Visualization Agent | Graphic Designer | Generates interactive Plotly charts (Bar, Line, Pie) with style rules for the dark theme.
Summarizer Agent | Report Writer | Synthesizes internal data, external context, and visuals into a coherent narrative.
Email Agent | Executive Assistant | Formats HTML emails and sends reports via SMTP, aware of conversation context and previous analyses.

## Key Features & Capabilities

- **Dynamic Data Interaction:** Natural language querying, live filtering (Year, Region, Category), and instant updates via Pandas logic.
- **Hybrid Intelligence:** Combines internal DB metrics with live web context to explain trends and anomalies.
- **Intelligent Visualization:** Auto-selects chart types and styles them for a dark, glassmorphism UI (transparent backgrounds, white text).
- **Automated Reporting:** One-click emailing of reports, smart context-aware references to previous conversation history, and currency localization to Indian Rupees (₹).
- **Modern UI/UX:** Streamlit frontend with custom CSS for a polished, glassmorphism look and a collapsed sidebar for maximal workspace.

## 💻 Technical Stack

- Orchestration: LangGraph, LangChain
- Frontend: Streamlit (Python)
- Database: PostgreSQL (SQLAlchemy)
- LLM: OpenAI GPT-4o / Groq (configurable)
- Tools: Tavily Search API, Plotly, SMTP

## 📁 Project Structure

```
nexuscorpus-dashboard/
├── app.py                  # Main Streamlit entry point & CSS styling
├── requirements.txt        # Python dependencies
├── .env                    # API keys & DB credentials (not committed)
├── assets/
│   └── business_tech_bg.jpg # Background image
├── components/
│   ├── llm.py              # LLM configuration
│   └── tools.py            # Tool definitions (Email, Search)
├── agents/
│   ├── sql_agent.py        # SQL query generation
│   ├── web_agent.py        # Web search logic
│   ├── viz_agent.py        # Plotly generation
│   └── email_agent.py      # HTML email composer
└── graph/
    └── supervisor.py       # LangGraph state machine & routing logic
```

## Prerequisites

1. Python 3.10+ installed
2. PostgreSQL installed and running
3. A database named `gadgethub` with `master_sales` and `category_breakdown` tables populated (or adapt the DB and table names)

## 💻 Setup & Run

1. Clone the repository:

```bash
git clone https://github.com/your-username/nexuscorpus-dashboard.git
cd nexuscorpus-dashboard
```

2. Create a virtual environment and activate it (Windows):

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file at project root and add the following keys (replace with real values):

```
# Database
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gadgethub

# API Keys
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...

# Email
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

5. Run the app:

```bash
streamlit run app.py
```

6. Open the dashboard at `http://localhost:8501`.


---


