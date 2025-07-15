# DRV2 - Enhanced Agentic Deep Researcher

An advanced AI-powered research system that combines multiple specialized agents to conduct deep, comprehensive research with academic citations and source verification. The system leverages CrewAI framework to orchestrate intelligent agents that can search, analyze, and synthesize information from various sources while maintaining citation integrity.

## 🚀 Features

### Core Research Capabilities
- **Multi-Agent Research System**: Utilizes CrewAI framework with specialized agents for different research tasks
- **Academic Citation Integration**: Automatic citation generation with proper academic formatting
- **Source Verification**: Real-time source validation and credibility assessment
- **Deep Web Search**: Integration with LinkUp SDK for comprehensive web research
- **Multiple Output Formats**: Generate reports in text, markdown, JSON, and PDF formats

### Advanced Search & Analysis
- **Intelligent Query Processing**: Natural language query understanding and expansion
- **Source Categorization**: Automatic classification of sources (academic, news, technical, general)
- **Citation Management**: Structured citation tracking with DOI, journal, and author information
- **Content Synthesis**: AI-driven analysis and synthesis of multiple sources
- **Real-time Progress Tracking**: Live updates during research process

### Academic Integration
- **Google Scholar Integration**: Direct access to academic papers and citations
- **ArXiv Support**: Research paper retrieval from ArXiv repository
- **CrossRef Integration**: DOI resolution and journal metadata extraction
- **PubMed Access**: Medical and life science literature search
- **BioPython Support**: Specialized biological research capabilities

### User Interfaces
- **Streamlit Web Interface**: Interactive web application for research queries
- **MCP Server Support**: Model Context Protocol server for integration with other systems
- **CLI Tools**: Command-line interface for automated research workflows
- **API Endpoints**: RESTful API for programmatic access

## 🛠 Technology Stack

### Core AI & Research
- **CrewAI**: Multi-agent orchestration framework
- **OpenAI/Gemini**: LLM integration for natural language processing
- **LinkUp SDK**: Advanced web search capabilities
- **Pydantic**: Data validation and settings management

### Academic & Scientific Libraries
- **Scholarly**: Google Scholar API integration
- **CrossRef Commons**: DOI and citation metadata
- **ArXiv**: Scientific paper repository access
- **BioPython**: Biological research tools
- **PubMed Lookup**: Medical literature search

### Web & Data Processing
- **BeautifulSoup4**: HTML parsing and web scraping
- **Requests**: HTTP client for web requests
- **Pandas & NumPy**: Data analysis and manipulation
- **NLTK & spaCy**: Natural language processing
- **TextStat**: Text readability analysis

### User Interface & Reporting
- **Streamlit**: Web application framework
- **ReportLab**: PDF generation
- **Markdown**: Document formatting
- **Click & Typer**: CLI interface development

## 📋 Prerequisites

- Python 3.11 or higher
- LinkUp API key (for web search)
- OpenAI or Gemini API key (for LLM integration)

## 🔧 Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/Ragha02/DRV2.git
cd DRV2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Enhanced Features Installation

```bash
# For advanced academic features
pip install -e ".[academic]"

# For enhanced text processing
pip install -e ".[enhanced-processing]"

# Install all optional dependencies
pip install -e ".[dev,academic,enhanced-processing]"
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required API Keys
LINKUP_API_KEY=your_linkup_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Alternative to Gemini

# Optional Configuration
MAX_SEARCHES=8
SEARCH_DEPTH=standard
OUTPUT_FORMAT=markdown
```

### API Key Setup

1. **LinkUp API Key**: Sign up at [LinkUp](https://linkup.com) for web search capabilities
2. **Gemini API Key**: Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **OpenAI API Key**: Alternative LLM option from [OpenAI Platform](https://platform.openai.com)

## 🚀 Usage

### Web Interface (Streamlit)

Launch the interactive web application:

```bash
streamlit run app.py
```

Features available in the web interface:
- Real-time research queries
- Source visualization and verification
- Multiple download formats (PDF, JSON, Markdown)
- Citation management
- Progress tracking

### MCP Server

Start the Model Context Protocol server:

```bash
python server.py
```

Available MCP tools:
- `enhanced_crew_research(query, include_sources)`: Run comprehensive research
- `get_research_sources_info()`: Retrieve detailed source information

### Python API

```python
from agents import run_enhanced_research, get_research_sources, reset_search_counter

# Reset for new research session
reset_search_counter()

# Run research
result = run_enhanced_research("Impact of artificial intelligence on healthcare")

# Get sources used
sources = get_research_sources()

# Process results
for source in sources:
    print(f"Title: {source.title}")
    print(f"URL: {source.url}")
    print(f"Type: {source.source_type}")
    if source.doi:
        print(f"DOI: {source.doi}")
```

### Command Line Interface

```bash
# Basic research query
python -m enhanced_agentic_deep_researcher "climate change impact on agriculture"

# With specific output format
python -m enhanced_agentic_deep_researcher "quantum computing advances" --format json

# Academic focus with citations
python -m enhanced_agentic_deep_researcher "machine learning in medicine" --focus academic --citations
```

## 📊 Data Structures

### Source Object
```python
@dataclass
class Source:
    title: str
    url: str
    domain: str
    snippet: str
    source_type: str = "web"  # web, paper, article, news
    publication_date: str = ""
    authors: List[str] = field(default_factory=list)
    doi: str = ""
    journal: str = ""
```

### Research Result
```python
@dataclass
class ResearchResult:
    content: str
    sources: List[Source] = field(default_factory=list)
    citations: Dict[str, int] = field(default_factory=dict)
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=enhanced_agentic_deep_researcher

# Run specific test categories
pytest tests/test_agents.py
pytest tests/test_search.py
```

## 📁 Project Structure

```
DRV2/
├── agents.py              # Core agent definitions and research logic
├── app.py                 # Streamlit web interface
├── server.py              # MCP server implementation
├── pyproject.toml         # Project configuration and dependencies
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/              # Usage examples
```

## 🔌 Integration Examples

### Custom Agent Integration

```python
from crewai import Agent
from agents import get_llm_client, LinkUpSearchTool

# Create custom research agent
custom_agent = Agent(
    role="Specialized Researcher",
    goal="Research specific domain topics",
    backstory="Expert in domain-specific research",
    tools=[LinkUpSearchTool()],
    llm=get_llm_client(),
    verbose=True
)
```

### API Integration

```python
import requests

# Using MCP server endpoint
response = requests.post("http://localhost:8000/research", 
                        json={"query": "renewable energy trends"})
result = response.json()
```

## 🛡️ Security & Best Practices

- API keys are loaded from environment variables
- Input validation using Pydantic models
- HTML content sanitization with Bleach
- Rate limiting for API calls
- Error handling with retry logic using Tenacity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Tools

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks for code quality

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- CrewAI team for the multi-agent framework
- LinkUp for advanced search capabilities
- Google AI for Gemini LLM integration
- Academic API providers (Google Scholar, ArXiv, CrossRef)

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/Ragha02/DRV2/issues)
- Documentation: Check the `/docs` directory for detailed guides
- Examples: See `/examples` for implementation examples

---

*Built with ❤️ for researchers, analysts, and knowledge workers who need comprehensive, cited research at scale.*
