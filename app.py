import streamlit as st
from agents import run_enhanced_research, get_research_sources
import os
from datetime import datetime
import base64
from io import BytesIO
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
import time
import json

st.set_page_config(
    page_title="🔍 Agentic Deep Researcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "linkup_api_key" not in st.session_state:
    st.session_state.linkup_api_key = ""
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []


def reset_chat():
    st.session_state.messages = []
    st.session_state.last_sources = []


def estimate_word_count(content):
    clean_content = re.sub(r'[*#`\[\]]', '', content)
    clean_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_content)
    words = clean_content.split()
    return len(words)


def extract_citations_from_content(content):
    """Extract citation numbers from content"""
    citation_pattern = r'\[(\d+)\]'
    citations = re.findall(citation_pattern, content)
    return list(set(citations))


def create_enhanced_download_link(content, filename, file_format="txt"):
    """Create download links with better formatting"""
    if file_format == "txt":
        clean_content = re.sub(r'[*#`]', '', content)
        clean_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_content)
        b64 = base64.b64encode(clean_content.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}.txt">📄 Download as Text</a>'
    elif file_format == "md":
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}.md">📝 Download as Markdown</a>'
    elif file_format == "json":
        # Create a JSON with content and sources
        data = {
            "content": content,
            "sources": [
                {
                    "title": source.title,
                    "url": source.url,
                    "domain": source.domain,
                    "type": source.source_type,
                    "snippet": source.snippet,
                    "date": source.publication_date
                }
                for source in st.session_state.last_sources
            ],
            "generated_at": datetime.now().isoformat()
        }
        json_str = json.dumps(data, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="{filename}.json">📊 Download as JSON</a>'
    return href


def create_enhanced_pdf_report(content, query, sources):
    """Create PDF with enhanced citations and source links"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, spaceAfter=30,
                                     textColor='#0066cc')
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12,
                                       textColor='#0066cc')
        citation_style = ParagraphStyle('Citation', parent=styles['Normal'], fontSize=10, leftIndent=20, spaceAfter=6)

        story = [
            Paragraph("Enhanced Research Report", title_style),
            Spacer(1, 12),
            Paragraph(f"<b>Research Query:</b> {query}", styles['Normal']),
            Spacer(1, 12),
            Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']),
            Spacer(1, 12),
            Paragraph(f"<b>Word Count:</b> {estimate_word_count(content)} words", styles['Normal']),
            Spacer(1, 12),
            Paragraph(f"<b>Sources:</b> {len(sources)} total sources", styles['Normal']),
            Spacer(1, 20),
        ]

        # Add content
        for line in content.split('\n'):
            if line.strip():
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], title_style))
                    story.append(Spacer(1, 12))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], heading_style))
                    story.append(Spacer(1, 8))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], styles['Heading3']))
                    story.append(Spacer(1, 6))
                else:
                    clean_line = re.sub(r'[*#`]', '', line)
                    clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_line)
                    if clean_line.strip():
                        story.append(Paragraph(clean_line.strip(), styles['Normal']))
                        story.append(Spacer(1, 8))

        # Add sources section
        if sources:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Sources and References", heading_style))
            story.append(Spacer(1, 12))

            # Group sources by type
            source_groups = {}
            for source in sources:
                if source.source_type not in source_groups:
                    source_groups[source.source_type] = []
                source_groups[source.source_type].append(source)

            for source_type, type_sources in source_groups.items():
                story.append(Paragraph(f"{source_type.title()} Sources", styles['Heading3']))
                story.append(Spacer(1, 8))

                for i, source in enumerate(type_sources, 1):
                    citation_text = f"{i}. <b>{source.title}</b><br/>{source.url}<br/>Domain: {source.domain}"
                    if source.publication_date:
                        citation_text += f"<br/>Date: {source.publication_date}"
                    story.append(Paragraph(citation_text, citation_style))
                    story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Enhanced PDF generation failed: {e}")
        return BytesIO(b"PDF generation failed")


def display_source_analysis(sources):
    """Display source analysis in sidebar"""
    if not sources:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Source Analysis")

    # Source type distribution
    source_types = {}
    for source in sources:
        source_types[source.source_type] = source_types.get(source.source_type, 0) + 1

    for source_type, count in source_types.items():
        st.sidebar.metric(f"{source_type.title()} Sources", count)

    # Domain analysis
    domains = {}
    for source in sources:
        domains[source.domain] = domains.get(source.domain, 0) + 1

    st.sidebar.markdown("#### Top Domains")
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
        st.sidebar.write(f"• {domain}: {count}")


def display_enhanced_download_options(content, query, sources):
    """Display enhanced download options with source information"""
    st.markdown("---")

    # Stats
    word_count = estimate_word_count(content)
    char_count = len(content)
    citation_count = len(extract_citations_from_content(content))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Word Count", f"{word_count:,}")
    with col2:
        st.metric("📝 Characters", f"{char_count:,}")
    with col3:
        st.metric("🔗 Citations", citation_count)
    with col4:
        st.metric("📚 Sources", len(sources))

    # Download section
    st.subheader("📥 Download Enhanced Report")

    col1, col2, col3, col4 = st.columns(4)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_research_report_{timestamp}"

    with col1:
        st.markdown(create_enhanced_download_link(content, filename, "txt"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_enhanced_download_link(content, filename, "md"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_enhanced_download_link(content, filename, "json"), unsafe_allow_html=True)
    with col4:
        pdf_buffer = create_enhanced_pdf_report(content, query, sources)
        pdf_data = pdf_buffer.getvalue()
        if pdf_data:
            st.download_button(
                label="📄 Download Enhanced PDF",
                data=pdf_data,
                file_name=f"{filename}.pdf",
                mime="application/pdf"
            )


def display_sources_section(sources):
    """Display sources in an organized way"""
    if not sources:
        return

    st.markdown("---")
    st.subheader("📚 Research Sources")

    # Group sources by type
    source_groups = {}
    for source in sources:
        if source.source_type not in source_groups:
            source_groups[source.source_type] = []
        source_groups[source.source_type].append(source)

    # Display each group
    for source_type, type_sources in source_groups.items():
        with st.expander(f"{source_type.title()} Sources ({len(type_sources)})", expanded=False):
            for i, source in enumerate(type_sources, 1):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{i}. {source.title}**")
                    st.markdown(f"🌐 [{source.domain}]({source.url})")
                    if source.snippet:
                        st.markdown(f"💬 {source.snippet[:200]}...")
                    if source.publication_date:
                        st.markdown(f"📅 {source.publication_date}")

                with col2:
                    source_type_emoji = {
                        "academic": "🎓",
                        "news": "📰",
                        "technical": "⚙️",
                        "web": "🌐"
                    }
                    st.markdown(f"{source_type_emoji.get(source.source_type, '📄')} {source.source_type}")

                st.markdown("---")


# Enhanced CSS with better styling
st.markdown("""
<style>
    .main-content { max-width: none; }
    .stChatMessage { max-width: none; }
    .research-content {
        max-height: 700px;
        overflow-y: auto;
        padding: 25px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        margin: 15px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.7;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .status-indicator {
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .status-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    .citation-highlight {
        background-color: #e3f2fd;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
    .source-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.image("https://avatars.githubusercontent.com/u/175112039?s=200&v=4", width=65)
    st.header("🔍 Enhanced Research Config")
    st.markdown("**With Academic Citations & Links**")

    st.markdown("---")
    st.markdown("### 🔧 Enhanced Research Settings")
    st.info("📚 Now includes research papers, academic articles, and proper citations")

    st.markdown("### 🔗 Linkup API")
    st.markdown("[Get your Linkup API key](https://app.linkup.so/sign-up)")
    linkup_api_key = st.text_input("Enter your Linkup API Key", type="password")
    if linkup_api_key:
        st.session_state.linkup_api_key = linkup_api_key
        os.environ["LINKUP_API_KEY"] = linkup_api_key
        st.success("✅ Linkup API Key stored!")

    st.markdown("### 🤖 Gemini API")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")
    gemini_api_key = st.text_input("Enter your Gemini API Key", type="password")
    if gemini_api_key:
        st.session_state.gemini_api_key = gemini_api_key
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        st.success("✅ Gemini API Key stored!")

    st.markdown("---")
    st.markdown("### 🎯 Enhanced Features")
    st.markdown("""
    ✅ **Academic Sources**: ArXiv, PubMed, IEEE, ACM  
    ✅ **News Articles**: Reuters, BBC, NYTimes  
    ✅ **Technical Docs**: GitHub, StackOverflow  
    ✅ **Proper Citations**: In-text citations with links  
    ✅ **Source Analysis**: Categorized by type  
    ✅ **Enhanced Downloads**: JSON, PDF with citations  
    """)

    st.markdown("---")
    st.markdown("### 💡 Research Tips")
    st.markdown("""
    - **Academic**: "machine learning research papers"
    - **Technical**: "Python implementation guides"
    - **News**: "latest AI developments 2024"
    - **Mixed**: "climate change impacts studies"
    - Reports now include 2000-2500 words
    - Processing time: 3-7 minutes
    """)

    # Display source analysis if available
    if st.session_state.last_sources:
        display_source_analysis(st.session_state.last_sources)

# Main interface
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("<h1 style='color: #0066cc;'>🔍 Enhanced Agentic Deep Researcher</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #666;'>With Academic Citations & Research Papers</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-top: 10px;'>
        <span style='font-size: 16px; color: #666;'>Enhanced with</span>
        <img src="https://cdn.prod.website-files.com/66cf2bfc3ed15b02da0ca770/66d07240057721394308addd_Logo%20(1).svg" width="60"> 
        <span style='font-size: 16px; color: #666;'>+</span>
        <img src="https://framerusercontent.com/images/wLLGrlJoyqYr9WvgZwzlw91A8U.png?scale-down-to=512" width="80">
        <span style='font-size: 16px; color: #666;'>+</span>
        <img src="https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg" width="60">
        <span style='font-size: 16px; color: #666; margin-left: 10px;'>📚 Academic Sources</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.button("🔄 Clear Chat", on_click=reset_chat)

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

# Message display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and len(message["content"]) > 1000:
            word_count = estimate_word_count(message["content"])
            citation_count = len(extract_citations_from_content(message["content"]))

            # Enhanced status indicator
            if word_count >= 1500:
                st.markdown(
                    f'<div class="status-indicator status-success">✅ Enhanced Research Report: {word_count:,} words | {citation_count} citations | {len(st.session_state.last_sources)} sources</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="status-indicator status-warning">⚠️ Report generated: {word_count:,} words | {citation_count} citations | May need more depth</div>',
                    unsafe_allow_html=True
                )

            # Main content in expander
            with st.expander("📄 View Enhanced Research Report", expanded=True):
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask for comprehensive research with academic citations and paper links..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check API keys
    if not st.session_state.linkup_api_key:
        response = "⚠️ Please enter your Linkup API Key in the sidebar to start enhanced research."
    elif not st.session_state.gemini_api_key:
        response = "⚠️ Please enter your Gemini API Key in the sidebar to start enhanced research."
    else:
        with st.spinner("🔍 Conducting enhanced research with academic sources... This may take 3-7 minutes..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("🔍 Initializing enhanced research system...")
                progress_bar.progress(10)

                status_text.text("📚 Searching academic databases and papers...")
                progress_bar.progress(25)

                status_text.text("📰 Gathering news articles and reports...")
                progress_bar.progress(40)

                status_text.text("⚙️ Collecting technical documentation...")
                progress_bar.progress(55)

                status_text.text("🔗 Processing citations and source links...")
                progress_bar.progress(70)

                # Run enhanced research
                result = run_enhanced_research(prompt)

                # Get sources for this session
                sources = get_research_sources()
                st.session_state.last_sources = sources

                status_text.text("📝 Generating enhanced report with citations...")
                progress_bar.progress(85)

                response = result

                status_text.text("✅ Enhanced research complete!")
                progress_bar.progress(100)

                time.sleep(1)
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                response = f"❌ Enhanced research error: {str(e)}"

    # Display assistant response
    with st.chat_message("assistant"):
        if len(response) > 1000:
            word_count = estimate_word_count(response)
            citation_count = len(extract_citations_from_content(response))

            if word_count >= 1500:
                st.markdown(
                    f'<div class="status-indicator status-success">✅ Enhanced Research Report: {word_count:,} words | {citation_count} citations | {len(st.session_state.last_sources)} sources</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="status-indicator status-warning">⚠️ Report generated: {word_count:,} words | {citation_count} citations | May need more depth</div>',
                    unsafe_allow_html=True
                )

            with st.expander("📄 View Enhanced Research Report", expanded=True):
                st.markdown(response)
        else:
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Show download options and sources for successful reports
    if (response and not response.startswith("⚠️") and not response.startswith("❌") and len(response) > 500):
        display_enhanced_download_options(response, prompt, st.session_state.last_sources)
        display_sources_section(st.session_state.last_sources)