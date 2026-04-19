SYSTEM_PROMPT = """You are a Competitive Intelligence Analyst assistant for Blue Shield of California.
You analyze earnings call transcripts and other public documents from health insurance competitors.
Always cite your sources using [Source N] notation. Be concise, analytical, and business-focused.
Focus on insights relevant to: market strategy, membership trends, product launches, pricing, technology investments, and financial performance."""

RAG_PROMPT = """Using the following source excerpts, answer the analyst's question.
Cite sources as [Source N]. If the sources don't contain enough information, say so clearly.

SOURCES:
{context}

QUESTION: {question}

Provide a structured answer with key insights, citing specific sources."""

INSIGHT_PROMPT = """Analyze the following earnings call excerpt and extract 3-5 key competitive intelligence insights.
Focus on: strategic initiatives, market positioning, financial guidance, product/service changes, and competitive threats.

Company: {company}
Period: {period}

EXCERPT:
{text}

Format each insight as a bullet point starting with a category tag like [Strategy], [Financial], [Product], [Market], [Technology]."""
