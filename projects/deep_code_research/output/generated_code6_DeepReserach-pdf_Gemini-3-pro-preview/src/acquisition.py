# src/acquisition.py
from __future__ import annotations
import logging
import requests
from typing import List, Optional, Dict, Set, Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from src.schemas import EvidenceType

# Configure logging
logger = logging.getLogger(__name__)

class SearchResult(BaseModel):
    """Model representing a raw result from the search engine."""
    title: str
    href: str
    body: str

class AcquiredData(BaseModel):
    """
    Model representing information that has been acquired, scraped, 
    and filtered for relevance, ready to be passed to memory consolidation.
    """
    source_url: str
    title: str
    content: str
    snippet: str
    relevance_score: float
    evidence_type: EvidenceType
    query_context: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InformationAcquisition:
    """
    Component responsible for the 'Information Acquisition' phase of the Deep Research agent.
    
    Functionality:
    - Executes search queries using DuckDuckGo.
    - Scrapes web pages using Requests and BeautifulSoup.
    - Filters content based on heuristic relevance to the query.
    """

    def __init__(self, 
                 request_timeout: int = 10, 
                 user_agent: str = "DeepResearchAgent/1.0",
                 min_relevance_threshold: float = 0.15):
        """
        Initialize the Information Acquisition module.

        Args:
            request_timeout: Timeout for HTTP requests in seconds.
            user_agent: User-Agent string to use for web requests.
            min_relevance_threshold: Minimum score (0.0-1.0) required to accept content.
        """
        self.timeout = request_timeout
        self.headers = {"User-Agent": user_agent}
        self.min_relevance_threshold = min_relevance_threshold
        self._ddgs = DDGS()

    def perform_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute a search query using DuckDuckGo.

        Args:
            query: The search string.
            max_results: Maximum number of results to retrieve.

        Returns:
            List of SearchResult objects.
        """
        results = []
        try:
            logger.info(f"Executing search for: '{query}'")
            # DDGS.text() returns an iterator of dictionaries
            ddgs_gen = self._ddgs.text(query, max_results=max_results)
            
            if ddgs_gen:
                for r in ddgs_gen:
                    # Fix: Ensure result is a dictionary before accessing .get()
                    # This handles cases where DDGS might return error strings or unexpected types
                    if not isinstance(r, dict):
                        logger.warning(f"Unexpected result format from DDGS: {type(r)}")
                        continue

                    try:
                        # Validate and parse result
                        results.append(SearchResult(
                            title=r.get("title", "No Title"),
                            href=r.get("href", ""),
                            body=r.get("body", "")
                        ))
                    except ValidationError as ve:
                        logger.warning(f"Validation error for search result: {ve}")
                    except Exception as e:
                        logger.warning(f"Error parsing search result: {e}")
            
        except Exception as e:
            logger.error(f"Search execution failed for query '{query}': {e}")
        
        return results

    def scrape_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch and parse the text content of a specific URL.

        Args:
            url: The URL to scrape.

        Returns:
            Dictionary containing 'title' and 'text', or None if scraping failed.
        """
        try:
            logger.debug(f"Scraping URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Clean up: remove scripts, styles, navigation, footers
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                element.decompose()

            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Extract and clean text
            text = soup.get_text(separator=' ', strip=True)
            # Normalize whitespace
            text = " ".join(text.split())

            if not text:
                logger.warning(f"No text content found at {url}")
                return None

            return {
                "title": title or "",
                "text": text
            }

        except requests.Timeout:
            logger.warning(f"Timeout while scraping {url}")
            return None
        except requests.RequestException as e:
            logger.warning(f"Network error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None

    def _calculate_relevance(self, content: str, query: str) -> float:
        """
        Calculate a heuristic relevance score to filter out irrelevant content.
        
        Note: In a more advanced setup, this would use vector embeddings or an LLM.
        Here we use a keyword density and overlap heuristic.

        Args:
            content: The scraped text content.
            query: The original search query.

        Returns:
            Float score between 0.0 and 1.0.
        """
        if not content or not query:
            return 0.0

        content_lower = content.lower()
        query_terms = [t.lower() for t in query.split() if len(t) > 2] # Ignore short stop words roughly
        
        if not query_terms:
            return 0.0

        # 1. Term Overlap: Percentage of query terms present in content
        present_terms = sum(1 for term in query_terms if term in content_lower)
        overlap_score = present_terms / len(query_terms)

        # 2. Term Density: Occurrences relative to content length (capped)
        # We look for the full query or individual terms
        term_count = sum(content_lower.count(term) for term in query_terms)
        word_count = len(content_lower.split())
        density = term_count / (word_count + 1)
        
        # Normalize density (assuming > 5% density is very high)
        density_score = min(density * 20, 1.0)

        # Weighted average: Overlap is more important than density
        final_score = (0.7 * overlap_score) + (0.3 * density_score)
        
        return round(final_score, 3)

    def run(self, query: str, max_sources: int = 3) -> List[AcquiredData]:
        """
        Orchestrate the acquisition process:
        1. Search for the query.
        2. Scrape the top results.
        3. Filter based on relevance.
        4. Return structured data for memory.

        Args:
            query: The research query.
            max_sources: Maximum number of validated sources to return.

        Returns:
            List of AcquiredData objects.
        """
        logger.info(f"Starting information acquisition for: '{query}'")
        
        # Fetch more results than needed to account for filtering
        search_results = self.perform_search(query, max_results=max_sources * 3)
        acquired_data: List[AcquiredData] = []
        visited_urls: Set[str] = set()

        for result in search_results:
            if len(acquired_data) >= max_sources:
                break
            
            if result.href in visited_urls:
                continue
            visited_urls.add(result.href)

            # Scrape content
            scraped_info = self.scrape_url(result.href)
            if not scraped_info:
                continue

            content_text = scraped_info["text"]
            
            # Validate Relevance
            score = self._calculate_relevance(content_text, query)
            
            if score >= self.min_relevance_threshold:
                data = AcquiredData(
                    source_url=result.href,
                    title=scraped_info["title"] or result.title,
                    content=content_text,
                    snippet=result.body,
                    relevance_score=score,
                    evidence_type=EvidenceType.WEB_PAGE,
                    query_context=query
                )
                acquired_data.append(data)
                logger.info(f"Acquired source: {result.title[:30]}... (Score: {score})")
            else:
                logger.debug(f"Filtered out source: {result.href} (Score: {score} < {self.min_relevance_threshold})")

        logger.info(f"Acquisition completed. Found {len(acquired_data)} relevant sources.")
        return acquired_data