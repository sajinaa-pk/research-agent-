from tavily import TavilyClient
import os
from dotenv import load_dotenv
import time

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def web_search(query: str, max_retries: int = 2) -> list:
    """
    Searches the web using Tavily. Retries with backoff on failure.
    Returns a list of results, or an empty list if all retries fail.
    """
    for attempt in range(max_retries + 1):
        try:
            response = tavily_client.search(
                query=query,
                max_results=4,
                search_depth="basic"
            )
            results = response.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", "")
                }
                for r in results
            ]
        except Exception as e:
            print(f"Search attempt {attempt + 1} failed for '{query}': {e}")
            if attempt < max_retries:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"All retries exhausted for query: {query}")
                return []
            

'''

max_retries=2 — tries up to 3 times total before giving up
wait_time = 2 ** attempt — this is exponential backoff: wait 1 second, then 2 seconds, then give up. This prevents hammering a struggling API with rapid retries
Returns an empty list on total failure instead of crashing — the agent can handle "no results" gracefully instead of the whole pipeline dying

'''