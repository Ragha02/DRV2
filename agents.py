import os
import time
import re
import json
from typing import Type, List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

# Load environment variables
load_dotenv()

# Try to import LinkupClient with error handling
try:
    from linkup import LinkupClient

    LINKUP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LinkupClient import failed: {e}")
    print("Please install linkup-sdk: pip install linkup-sdk")
    LINKUP_AVAILABLE = False


@dataclass
class Source:
    """Data class to store source information"""
    title: str
    url: str
    domain: str
    snippet: str
    source_type: str = "web"  # web, paper, article, news
    publication_date: str = ""
    authors: List[str] = field(default_factory=list)
    doi: str = ""
    journal: str = ""


@dataclass
class ResearchResult:
    """Data class to store research results with sources"""
    content: str
    sources: List[Source] = field(default_factory=list)
    citations: Dict[str, int] = field(default_factory=dict)


def get_llm_client():
    """Initialize and return the Gemini LLM client with enhanced settings"""
    return LLM(
        model="gemini/gemini-2.5-pro",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.3,  # Lower for more consistent citation handling
        max_tokens=6000,  # Increased for longer reports with citations
        request_timeout=150,
        max_retries=3,
    )


class LinkUpSearchInput(BaseModel):
    """Input schema for LinkUp Search Tool."""
    query: str = Field(description="The search query to perform")
    depth: str = Field(default="standard", description="Depth of search: 'standard' or 'deep'")
    output_type: str = Field(default="searchResults",
                             description="Output type: 'searchResults', 'sourcedAnswer', or 'structured'")
    focus: str = Field(default="general", description="Focus area: 'general', 'academic', 'news', 'technical'")


# Global variables for search management
_global_search_count = 0
_max_searches = 8  # Increased for more comprehensive research
_research_sources = []  # Store all sources across searches


def reset_search_counter():
    """Reset the global search counter and sources for a new research session"""
    global _global_search_count, _research_sources
    _global_search_count = 0
    _research_sources = []


def increment_search_counter():
    """Increment and return the current search count"""
    global _global_search_count
    _global_search_count += 1
    return _global_search_count


def get_search_count():
    """Get the current search count"""
    return _global_search_count


def add_research_source(source: Source):
    """Add a source to the global research sources"""
    global _research_sources
    _research_sources.append(source)


def get_research_sources():
    """Get all research sources"""
    return _research_sources


def extract_sources_from_response(response_data: Any) -> List[Source]:
    """Extract source information from LinkUp response"""
    sources = []

    try:
        # Convert response to string if it's not already
        response_str = str(response_data)

        # Try to parse as JSON if possible
        if hasattr(response_data, 'results') or 'results' in response_str:
            # Handle structured response
            if hasattr(response_data, 'results'):
                results = response_data.results
            else:
                # Try to extract results from string representation
                import ast
                try:
                    # This is a simplified extraction - you may need to adjust based on actual response format
                    results = []
                except:
                    results = []

            for result in results:
                if hasattr(result, 'url') and hasattr(result, 'title'):
                    source_type = classify_source_type(result.url, result.title)
                    source = Source(
                        title=getattr(result, 'title', ''),
                        url=getattr(result, 'url', ''),
                        domain=extract_domain(getattr(result, 'url', '')),
                        snippet=getattr(result, 'snippet', ''),
                        source_type=source_type,
                        publication_date=getattr(result, 'date', ''),
                    )
                    sources.append(source)
        else:
            # Fallback: Extract URLs from string representation
            url_pattern = r'https?://[^\s\)]+(?:\([^\)]*\))?[^\s\)]*'
            urls = re.findall(url_pattern, response_str)

            for url in urls[:10]:  # Limit to first 10 URLs
                domain = extract_domain(url)
                source_type = classify_source_type(url, "")
                source = Source(
                    title=f"Source from {domain}",
                    url=url,
                    domain=domain,
                    snippet="",
                    source_type=source_type
                )
                sources.append(source)

    except Exception as e:
        print(f"Error extracting sources: {e}")

    return sources


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except:
        return url.split('/')[2] if '/' in url else url


def classify_source_type(url: str, title: str) -> str:
    """Classify source type based on URL and title"""
    url_lower = url.lower()
    title_lower = title.lower()

    # Academic sources
    academic_indicators = [
        'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'scholar.google.com',
        'researchgate.net', 'ieee.org', 'acm.org', 'springer.com',
        'sciencedirect.com', 'nature.com', 'science.org', 'cell.com',
        'plos.org', 'biorxiv.org', 'medrxiv.org', '.edu/', 'jstor.org'
    ]

    # News sources
    news_indicators = [
        'reuters.com', 'bbc.com', 'cnn.com', 'nytimes.com', 'wsj.com',
        'theguardian.com', 'washingtonpost.com', 'bloomberg.com',
        'forbes.com', 'techcrunch.com', 'wired.com', 'news.'
    ]

    # Technical/Industry sources
    tech_indicators = [
        'github.com', 'stackoverflow.com', 'medium.com', 'dev.to',
        'hackernews.com', 'techcrunch.com', 'arstechnica.com'
    ]

    for indicator in academic_indicators:
        if indicator in url_lower:
            return "academic"

    for indicator in news_indicators:
        if indicator in url_lower:
            return "news"

    for indicator in tech_indicators:
        if indicator in url_lower:
            return "technical"

    # Check title for academic keywords
    academic_keywords = ['research', 'study', 'paper', 'journal', 'analysis', 'review']
    if any(keyword in title_lower for keyword in academic_keywords):
        return "academic"

    return "web"


class EnhancedLinkUpSearchTool(BaseTool):
    name: str = "Enhanced LinkUp Search"
    description: str = "Search the web for information with enhanced source tracking and citation support"
    args_schema: Type[BaseModel] = LinkUpSearchInput

    def __init__(self):
        super().__init__()
        if not LINKUP_AVAILABLE:
            raise ImportError("LinkupClient is not available")

    def _run(self, query: str, depth: str = "standard", output_type: str = "searchResults",
             focus: str = "general") -> str:
        """Execute enhanced LinkUp search with source tracking"""
        if not LINKUP_AVAILABLE:
            return "Error: LinkupClient is not available"

        current_count = get_search_count()
        if current_count >= _max_searches:
            return f"Maximum search limit ({_max_searches}) reached. Please analyze existing results."

        try:
            api_key = os.getenv("LINKUP_API_KEY")
            if not api_key:
                return "Error: LINKUP_API_KEY not set"

            linkup_client = LinkupClient(api_key=api_key)
            time.sleep(1.5)  # Rate limiting

            # Enhance query based on focus
            enhanced_query = self._enhance_query(query, focus)

            # Use deep search for academic/technical queries
            search_depth = "deep" if focus in ["academic", "technical"] or "research" in query.lower() else depth

            search_response = linkup_client.search(
                query=enhanced_query,
                depth=search_depth,
                output_type=output_type
            )

            new_count = increment_search_counter()

            # Extract and store sources
            sources = extract_sources_from_response(search_response)
            for source in sources:
                add_research_source(source)

            response_str = str(search_response)
            if len(response_str) > 5000:
                response_str = response_str[
                               :5000] + f"\n... [Results truncated, search {new_count} using {search_depth} depth]"

            return f"Search {new_count}/{_max_searches} ({search_depth} depth) - Focus: {focus}:\n{response_str}\n\nSources found: {len(sources)}"

        except Exception as e:
            return f"Error during search: {str(e)}"

    def _enhance_query(self, query: str, focus: str) -> str:
        """Enhance query based on focus area"""
        if focus == "academic":
            return f'{query} site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov OR site:scholar.google.com OR "research paper" OR "study"'
        elif focus == "news":
            return f'{query} site:reuters.com OR site:bbc.com OR site:nytimes.com OR "news" OR "latest"'
        elif focus == "technical":
            return f'{query} site:github.com OR site:stackoverflow.com OR "technical" OR "implementation"'
        else:
            return query


def create_enhanced_research_crew(query: str):
    """Create research crew with enhanced citation capabilities"""

    if not LINKUP_AVAILABLE:
        raise ImportError("LinkupClient is not available")

    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY not set")

    if not os.getenv("LINKUP_API_KEY"):
        raise ValueError("LINKUP_API_KEY not set")

    # Initialize enhanced tools
    enhanced_search_tool = EnhancedLinkUpSearchTool()
    client = get_llm_client()

    # Enhanced research agent
    research_agent = Agent(
        role="Advanced Research Specialist",
        goal="Conduct comprehensive research across multiple source types including academic papers, news articles, and technical documentation",
        backstory="""You are an expert researcher with advanced skills in finding and analyzing diverse sources. 
        You excel at:
        - Identifying high-quality academic sources and research papers
        - Finding recent news articles and industry reports
        - Locating technical documentation and implementation guides
        - Conducting systematic searches across different domains
        - Tracking and organizing source information for citations""",
        verbose=True,
        allow_delegation=False,
        tools=[enhanced_search_tool],
        llm=client,
        max_execution_time=400,
        max_iter=4,
    )

    # Enhanced writing agent
    citation_writer = Agent(
        role="Research Writer with Citation Expertise",
        goal="Create comprehensive research reports with proper citations, links, and source attribution",
        backstory="""You are a skilled academic and technical writer who excels at:
        - Creating well-structured research reports
        - Properly citing academic papers and sources
        - Formatting citations and references
        - Organizing information with clear source attribution
        - Maintaining academic integrity and proper referencing standards""",
        verbose=True,
        allow_delegation=False,
        tools=[],
        llm=client,
        max_execution_time=300,
        max_iter=3,
    )

    # Enhanced research task
    comprehensive_research_task = Task(
        description=f"""
        Conduct comprehensive research on: {query}

        Execute 8 strategic searches with different focus areas:
        1. General overview (focus: general)
        2. Academic research and papers (focus: academic)
        3. Recent news and developments (focus: news)
        4. Technical documentation (focus: technical)
        5. Statistical data and reports (focus: general)
        6. Expert opinions and analysis (focus: general)
        7. Case studies and examples (focus: academic)
        8. Industry perspectives (focus: technical)

        For each search:
        - Use targeted queries for the specific focus area
        - Prioritize high-quality, authoritative sources
        - Look for research papers, academic articles, and peer-reviewed content
        - Collect recent news articles and industry reports
        - Gather technical documentation and implementation guides
        - Note publication dates, authors, and source credibility
        - Extract DOIs, journal names, and publication details when available

        Pay special attention to:
        - ArXiv preprints and research papers
        - PubMed medical research
        - IEEE and ACM publications
        - University research publications
        - Government and institutional reports
        - Industry whitepapers and technical documentation
        """,
        agent=research_agent,
        expected_output="Comprehensive research results with diverse source types, including academic papers, news articles, technical documentation, and web sources with detailed source information",
        tools=[enhanced_search_tool],
        max_execution_time=400
    )

    # Enhanced writing task
    citation_report_task = Task(
        description=f"""
        Create a comprehensive research report about: {query}

        Requirements:
        - Target length: 2000-2500 words
        - Include proper citations and source links throughout
        - Structure with clear sections and subsections
        - Add a comprehensive References section at the end

        Report Structure:
        1. Executive Summary (200-250 words)
        2. Introduction and Background (400-500 words)
        3. Literature Review (if academic sources available) (300-400 words)
        4. Key Findings and Analysis (600-800 words)
        5. Recent Developments and News (300-400 words)
        6. Technical Considerations (if applicable) (200-300 words)
        7. Conclusion and Future Implications (200-300 words)
        8. References and Sources (comprehensive list)

        Citation Guidelines:
        - Use in-text citations like [1], [2], etc.
        - Include direct links to sources where possible
        - Separate academic sources from news/web sources
        - Include DOIs for academic papers when available
        - Format: Author(s), Title, Journal/Source, Date, URL
        - Prioritize recent and authoritative sources
        - Include publication dates and access dates

        Content Guidelines:
        - Synthesize information from multiple sources
        - Highlight conflicting viewpoints when present
        - Include specific data, statistics, and examples
        - Reference expert opinions and quotes
        - Maintain academic tone while being accessible
        - Ensure all claims are properly supported by citations
        """,
        agent=citation_writer,
        expected_output="A comprehensive 2000-2500 word research report with proper citations, source links, and a complete references section",
        context=[comprehensive_research_task],
        max_execution_time=300
    )

    # Create enhanced crew
    crew = Crew(
        agents=[research_agent, citation_writer],
        tasks=[comprehensive_research_task, citation_report_task],
        verbose=True,
        process=Process.sequential,
        max_execution_time=800,
        memory=False,
    )

    return crew


def run_enhanced_research(query: str) -> str:
    """Run enhanced research with citation tracking"""
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # Reset for new session
            reset_search_counter()

            if attempt > 0:
                time.sleep(retry_delay * attempt)

            crew = create_enhanced_research_crew(query)
            result = crew.kickoff()

            # Get sources for additional processing
            sources = get_research_sources()

            # Enhance result with source summary
            enhanced_result = result.raw

            if sources:
                enhanced_result += "\n\n---\n\n## Source Summary\n\n"

                # Group sources by type
                source_groups = {}
                for source in sources:
                    if source.source_type not in source_groups:
                        source_groups[source.source_type] = []
                    source_groups[source.source_type].append(source)

                for source_type, type_sources in source_groups.items():
                    enhanced_result += f"\n### {source_type.title()} Sources ({len(type_sources)})\n\n"
                    for i, source in enumerate(type_sources[:10], 1):  # Limit to 10 per type
                        enhanced_result += f"{i}. **{source.title}**\n"
                        enhanced_result += f"   - URL: {source.url}\n"
                        enhanced_result += f"   - Domain: {source.domain}\n"
                        if source.publication_date:
                            enhanced_result += f"   - Date: {source.publication_date}\n"
                        enhanced_result += "\n"

            return enhanced_result

        except Exception as e:
            error_msg = str(e).lower()

            if "overloaded" in error_msg or "rate limit" in error_msg:
                if attempt < max_retries - 1:
                    print(f"Rate limit encountered, waiting {retry_delay * (attempt + 1)} seconds...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return f"API Rate Limited: Please try again later. Consider breaking your query into smaller parts."

            if attempt < max_retries - 1:
                print(f"Error on attempt {attempt + 1}, retrying...")
                time.sleep(retry_delay)
                continue
            else:
                return f"Research Error: {str(e)}\n\nTips:\n1. Simplify your query\n2. Check API configurations\n3. Try again later"

    return "Maximum retries exceeded. Please try again later."


# Keep the original function for backward compatibility
def run_research(query: str) -> str:
    """Wrapper for backward compatibility"""
    return run_enhanced_research(query)