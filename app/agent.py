from groq import Groq
import os
from dotenv import load_dotenv
from app.tools import web_search
from app.prompts import (
    get_planner_prompt,
    get_summarizer_prompt,
    get_evaluator_prompt,
    get_report_prompt
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def plan_queries(question: str) -> list:
    prompt = get_planner_prompt(question)
    response = call_llm(prompt)
    queries = [q.strip() for q in response.split("\n") if q.strip()]
    return queries[:3]

def run_search_phase(queries: list) -> list:
    all_results = []
    for query in queries:
        results = web_search(query)
        all_results.extend(results)
    return all_results

def format_results_for_prompt(results: list) -> str:
    formatted = []
    for r in results:
        formatted.append(f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content'][:500]}")
    return "\n\n".join(formatted)

def summarize_findings(question: str, results: list) -> str:
    if not results:
        return "No search results were found."
    formatted = format_results_for_prompt(results)
    prompt = get_summarizer_prompt(question, formatted)
    return call_llm(prompt)

def evaluate_findings(question: str, findings: str) -> bool:
    prompt = get_evaluator_prompt(question, findings)
    decision = call_llm(prompt)
    return "ENOUGH" in decision.upper()

def generate_report(question: str, findings: str):
    prompt = get_report_prompt(question, findings)
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text

def run_research_agent(question: str, max_iterations: int = 2):
    """
    The state machine. Loops: plan -> search -> summarize -> evaluate -> (search again or finish)
    """
    all_findings = []
    state_log = []

    for iteration in range(max_iterations):
        state_log.append(f"Iteration {iteration + 1}: planning queries")
        queries = plan_queries(question)
        state_log.append(f"Queries: {queries}")

        state_log.append("Searching...")
        results = run_search_phase(queries)
        state_log.append(f"Found {len(results)} results")

        state_log.append("Summarizing...")
        findings = summarize_findings(question, results)
        all_findings.append(findings)

        combined_findings = "\n\n".join(all_findings)

        state_log.append("Evaluating if enough...")
        has_enough = evaluate_findings(question, combined_findings)

        if has_enough:
            state_log.append("Decision: ENOUGH. Generating report.")
            break
        else:
            state_log.append("Decision: need more research.")

    final_findings = "\n\n".join(all_findings)
    return final_findings, state_log


'''
run_research_agent is the orchestrator — it's a loop with a clear exit condition, not an open-ended "keep calling tools until something happens" pattern
max_iterations=2 — this caps the loop. Without this, a stubborn evaluator could loop forever and burn API credits. This is a real production safeguard
state_log — tracks every decision the agent makes. This is what makes agent behavior debuggable instead of a black box
The loop body is exactly the 5 states from the diagram: plan → search → summarize → evaluate → decide

'''