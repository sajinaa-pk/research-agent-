# Research Agent

A research agent that plans search queries, searches the web, evaluates whether it has enough evidence, and writes a cited report — built as a state machine with explicit failure recovery, not a single prompt-and-pray LLM call.

## What it does

Give it a question. It will:

1. Break the question into 1-3 targeted search queries
2. Search the web for each query (via Tavily)
3. Summarize the findings relevant to the question
4. Evaluate whether it has enough evidence to answer
5. If not, search again with refined queries (up to a capped number of iterations)
6. Once it has enough, stream a final report with inline source citations

The agent's reasoning steps are streamed live to the UI as it works — you can watch it plan, search, and decide in real time.

## Why this is an agent, not just an LLM wrapper

A single API call that searches once and answers is a tool call, not an agent. What makes this a state machine:

- **A loop with a real exit condition** — the agent evaluates its own findings and decides whether to search again, rather than always doing exactly one pass
- **A hard iteration cap** — `max_iterations` prevents an indecisive evaluator from looping forever and burning API credits
- **A decision log** — every state transition (planning, searching, evaluating, deciding) is recorded and surfaced to the user, so the agent's behavior is debuggable instead of a black box
- **Failure recovery at the tool level** — the web search tool retries with exponential backoff before giving up, and the agent continues gracefully with partial results rather than crashing

## Tech Stack

- **FastAPI** — backend framework, streams agent state via Server-Sent Events
- **Groq** — LLM API (Llama 3.3 70B) for planning, summarizing, evaluating, and report writing
- **Tavily** — web search API built for AI agents (clean summarized results, not raw HTML)
- **Docker** — containerized for portability

## Project Structure

```
research-agent/
│
├── app/
│   ├── main.py      # FastAPI routes, SSE streaming of agent state + report
│   ├── agent.py     # the state machine: plan -> search -> summarize -> evaluate -> decide
│   ├── tools.py     # web search wrapper with retry + exponential backoff
│   ├── prompts.py   # one prompt per agent stage (planner, summarizer, evaluator, report)
│   └── templates/
│       └── index.html  # UI showing live agent reasoning + streamed report
│
├── .env             # API keys (never commit)
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```

## How failure recovery works

```python
def web_search(query: str, max_retries: int = 2) -> list:
    for attempt in range(max_retries + 1):
        try:
            # ... call Tavily
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 1s, then 2s
            else:
                return []  # graceful degradation, not a crash
```

If a search call fails, it retries twice with exponential backoff before giving up. On total failure it returns an empty list rather than raising — the agent treats "no results" as a valid state and continues, rather than the whole pipeline dying on one bad API call.

## Getting Started

### Prerequisites

- Docker installed
- Groq API key — free at [console.groq.com](https://console.groq.com)
- Tavily API key — free at [tavily.com](https://tavily.com)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/research-agent.git
cd research-agent
```

### 2. Add your API keys

Create a `.env` file in the root:

```
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Run with Docker

```bash
docker compose up --build
```

### 4. Open the app

Go to [http://localhost:8000](http://localhost:8000) and ask a research question.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Agent UI |
| POST | `/research` | Run the agent on a question, streams state + report via SSE |
| GET | `/health` | Health check |

### Example request

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"question": "what are the latest developments in quantum computing?"}'
```

## Local Development

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Design Decisions

**Why separate prompts for planning, summarizing, evaluating, and reporting?**
Each stage has exactly one job. This makes every stage independently testable — you can verify the planner produces good queries without running the full pipeline. It also makes the agent's behavior easier to debug: if the final report is bad, you can inspect exactly which stage went wrong.

**Why cap iterations instead of letting the agent loop until it's satisfied?**
An LLM evaluator can get stuck deciding it never has "enough" evidence, especially for vague or unanswerable questions. Without a hard cap, that's an infinite loop burning API credits with no user-facing error. The cap trades a small chance of an incomplete answer for a guaranteed bounded cost and response time — the right tradeoff for a production system.

**Why retry with exponential backoff instead of retrying immediately?**
Immediate retries on a rate-limited or struggling API just add to the load that caused the failure in the first place. Waiting longer between each retry (1s, then 2s) gives the upstream service room to recover, which is standard practice for any external API call in production.

**Why Tavily instead of a raw search API or scraping Google results?**
Tavily is purpose-built for LLM consumption — it returns clean, summarized content instead of raw HTML that would need parsing. This keeps the agent's tool-calling layer simple and reliable.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key |
| `TAVILY_API_KEY` | Your Tavily API key |

## License

MIT
