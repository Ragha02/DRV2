import asyncio
import json
from typing import Dict, List, Any
from mcp.server.fastmcp import FastMCP
from agents import run_enhanced_research, get_research_sources, reset_search_counter

# Create FastMCP instance with enhanced capabilities
mcp = FastMCP("enhanced_crew_research")


@mcp.tool()
async def enhanced_crew_research(query: str, include_sources: bool = True) -> str:
    """Run enhanced CrewAI-based research system with academic citations and source links.

    Args:
        query (str): The research query or question.
        include_sources (bool): Whether to include detailed source information.

    Returns:
        str: The enhanced research response with citations and source links.
    """
    try:
        # Reset search counter for new research session
        reset_search_counter()

        # Run enhanced research
        result = run_enhanced_research(query)

        if include_sources:
            # Get sources and add structured information
            sources = get_research_sources()

            if sources:
                # Add source summary
                result += "\n\n---\n\n## Detailed Source Information\n\n"

                # Group sources by type
                source_groups = {}
                for source in sources:
                    if source.source_type not in source_groups:
                        source_groups[source.source_type] = []
                    source_groups[source.source_type].append(source)

                for source_type, type_sources in source_groups.items():
                    result += f"\n### {source_type.title()} Sources ({len(type_sources)})\n\n"

                    for i, source in enumerate(type_sources, 1):
                        result += f"**{i}. {source.title}**\n"
                        result += f"- **URL**: {source.url}\n"
                        result += f"- **Domain**: {source.domain}\n"
                        result += f"- **Type**: {source.source_type}\n"

                        if source.snippet:
                            result += f"- **Snippet**: {source.snippet[:150]}...\n"
                        if source.publication_date:
                            result += f"- **Date**: {source.publication_date}\n"
                        if source.authors:
                            result += f"- **Authors**: {', '.join(source.authors)}\n"
                        if source.journal:
                            result += f"- **Journal**: {source.journal}\n"
                        if source.doi:
                            result += f"- **DOI**: {source.doi}\n"

                        result += "\n"

        return result

    except Exception as e:
        return f"Error in enhanced research: {str(e)}"


@mcp.tool()
async def get_research_sources_info() -> str:
    """Get detailed information about sources from the last research session.

    Returns:
        str: JSON string containing detailed source information.
    """
    try:
        sources = get_research_sources()

        if not sources:
            return "No sources available from recent research session."

        # Convert sources to dictionaries for JSON serialization
        sources_data = []
        for source in sources:
            source_dict = {
                "title": source.title,
                "url": source.url,
                "domain": source.domain,
                "snippet": source.snippet,
                "source_type": source.source_type,
                "publication_date": source.publication_date,
                "authors": source.authors,
                "doi": source.doi,
                "journal": source.journal
            }
            sources_data.append(source_dict)

        # Group by source type
        source_groups = {}
        for source_data in sources_data:
            source_type = source_data["source_type"]
            if source_type not in source_groups:
                source_groups[source_type] = []
            source_groups[source_type].append(source_data)

        result = {
            "total_sources": len(sources_data),
            "source_types": {k: len(v) for k, v in source_groups.items()},
            "sources_by_type": source_groups,
            "all_sources": sources_data
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error getting source information: {str(e)}"


@mcp.tool()
async def search_academic_papers(query: str, max_results: int = 10) -> str:
    """Search specifically for academic papers and research articles.

    Args:
        query (str): The search query focused on academic content.
        max_results (int): Maximum number of results to return.

    Returns:
        str: Academic sources with proper citations and links.
    """
    try:
        # Enhance query for academic focus
        academic_query = f'{query} site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov OR site:scholar.google.com OR "research paper" OR "peer reviewed" OR "study" OR "journal article"'

        # Run research with academic focus
        result = run_enhanced_research(academic_query)

        # Filter sources for academic content
        sources = get_research_sources()
        academic_sources = [s for s in sources if s.source_type == "academic"]

        if academic_sources:
            result += "\n\n---\n\n## Academic Sources Found\n\n"

            for i, source in enumerate(academic_sources[:max_results], 1):
                result += f"**{i}. {source.title}**\n"
                result += f"- **URL**: {source.url}\n"
                result += f"- **Domain**: {source.domain}\n"

                if source.authors:
                    result += f"- **Authors**: {', '.join(source.authors)}\n"
                if source.journal:
                    result += f"- **Journal**: {source.journal}\n"
                if source.doi:
                    result += f"- **DOI**: {source.doi}\n"
                if source.publication_date:
                    result += f"- **Publication Date**: {source.publication_date}\n"
                if source.snippet:
                    result += f"- **Abstract/Snippet**: {source.snippet[:200]}...\n"

                result += "\n"

        return result

    except Exception as e:
        return f"Error searching academic papers: {str(e)}"


@mcp.tool()
async def get_source_statistics() -> str:
    """Get statistics about sources from the last research session.

    Returns:
        str: Statistics about source types, domains, and quality.
    """
    try:
        sources = get_research_sources()

        if not sources:
            return "No sources available for analysis."

        # Calculate statistics
        total_sources = len(sources)

        # Source type distribution
        type_counts = {}
        for source in sources:
            type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1

        # Domain distribution
        domain_counts = {}
        for source in sources:
            domain_counts[source.domain] = domain_counts.get(source.domain, 0) + 1

        # Quality indicators
        sources_with_dates = sum(1 for s in sources if s.publication_date)
        sources_with_authors = sum(1 for s in sources if s.authors)
        sources_with_doi = sum(1 for s in sources if s.doi)

        stats = f"""# Source Statistics

## Overview
- **Total Sources**: {total_sources}
- **Sources with Publication Dates**: {sources_with_dates} ({sources_with_dates / total_sources * 100:.1f}%)
- **Sources with Author Information**: {sources_with_authors} ({sources_with_authors / total_sources * 100:.1f}%)
- **Sources with DOI**: {sources_with_doi} ({sources_with_doi / total_sources * 100:.1f}%)

## Source Types
"""

        for source_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_sources * 100
            stats += f"- **{source_type.title()}**: {count} ({percentage:.1f}%)\n"

        stats += "\n## Top Domains\n"
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = count / total_sources * 100
            stats += f"- **{domain}**: {count} ({percentage:.1f}%)\n"

        return stats

    except Exception as e:
        return f"Error calculating source statistics: {str(e)}"


@mcp.tool()
async def format_citations(content: str, citation_style: str = "apa") -> str:
    """Format citations in the research content according to specified style.

    Args:
        content (str): The research content with citations.
        citation_style (str): Citation style (apa, mla, chicago).

    Returns:
        str: Content with properly formatted citations.
    """
    try:
        sources = get_research_sources()

        if not sources:
            return content + "\n\n*No sources available for citation formatting.*"

        # Add formatted references section
        formatted_content = content + "\n\n---\n\n## References\n\n"

        if citation_style.lower() == "apa":
            for i, source in enumerate(sources, 1):
                citation = f"[{i}] "

                if source.authors:
                    citation += f"{', '.join(source.authors)} "

                if source.publication_date:
                    citation += f"({source.publication_date}). "

                citation += f"*{source.title}*. "

                if source.journal:
                    citation += f"{source.journal}. "

                if source.doi:
                    citation += f"https://doi.org/{source.doi}"
                else:
                    citation += source.url

                formatted_content += citation + "\n\n"

        elif citation_style.lower() == "mla":
            for i, source in enumerate(sources, 1):
                citation = f"[{i}] "

                if source.authors:
                    citation += f"{source.authors[0]}. "

                citation += f'"{source.title}." '

                if source.journal:
                    citation += f"*{source.journal}*, "

                if source.publication_date:
                    citation += f"{source.publication_date}. "

                citation += f"Web. {source.url}"

                formatted_content += citation + "\n\n"

        else:  # Default to simple format
            for i, source in enumerate(sources, 1):
                citation = f"[{i}] {source.title}. {source.url}"
                if source.publication_date:
                    citation += f" (Accessed: {source.publication_date})"
                formatted_content += citation + "\n\n"

        return formatted_content

    except Exception as e:
        return f"Error formatting citations: {str(e)}"


# Keep original function for backward compatibility
@mcp.tool()
async def crew_research(query: str) -> str:
    """Original CrewAI research function for backward compatibility.

    Args:
        query (str): The research query or question.

    Returns:
        str: The research response from the CrewAI pipeline.
    """
    return await enhanced_crew_research(query, include_sources=True)


# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")