from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from app.agent import run_research_agent, generate_report
import json

app = FastAPI()

class ResearchRequest(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/templates/index.html") as f:
        return HTMLResponse(content=f.read())

@app.post("/research")
async def research(request: ResearchRequest):
    async def generate():
        findings, state_log = run_research_agent(request.question)

        for log_line in state_log:
            yield f"data: {json.dumps({'type': 'log', 'content': log_line})}\n\n"

        yield f"data: {json.dumps({'type': 'report_start'})}\n\n"

        for chunk in generate_report(request.question, findings):
            yield f"data: {json.dumps({'type': 'report_chunk', 'content': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok"}



''''
We're streaming two kinds of data — the agent's internal reasoning steps (state_log) AND the final report text. This is why we wrap each chunk in JSON with a type field — the frontend needs to tell them apart and render them differently
This is real SSE (text/event-stream) instead of plain text streaming — proper format for structured streaming events


'''