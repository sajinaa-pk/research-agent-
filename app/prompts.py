PLANNER_PROMPT = """You are a research planning assistant. Given a user's question, break it down into 1-3 specific search queries that would help answer it.

Question: {question}

Respond with ONLY the search queries, one per line, no numbering, no extra text.
"""

SUMMARIZER_PROMPT = """You are a research assistant. Summarize the key findings from the search results below, related to this question: {question}

Search results:
{results}

Instructions:
- Extract only the facts relevant to the question
- Be concise — a few bullet points per source
- Note the source URL for each fact
"""

EVALUATOR_PROMPT = """You are evaluating whether enough information has been gathered to answer this question.

Question: {question}

Findings so far:
{findings}

Respond with ONLY one word: "ENOUGH" if the findings sufficiently answer the question, or "SEARCH_MORE" if more research is needed.
"""

REPORT_PROMPT = """You are a research assistant writing a final report. Based on the findings below, write a clear, well-organized answer to the question.

Question: {question}

Findings:
{findings}

Instructions:
- Write in clear paragraphs, not just bullet points
- Cite sources inline using the URLs provided
- Be thorough but concise
- If findings are incomplete, acknowledge what's uncertain
"""

def get_planner_prompt(question: str) -> str:
    return PLANNER_PROMPT.format(question=question)

def get_summarizer_prompt(question: str, results: str) -> str:
    return SUMMARIZER_PROMPT.format(question=question, results=results)

def get_evaluator_prompt(question: str, findings: str) -> str:
    return EVALUATOR_PROMPT.format(question=question, findings=findings)

def get_report_prompt(question: str, findings: str) -> str:
    return REPORT_PROMPT.format(question=question, findings=findings)