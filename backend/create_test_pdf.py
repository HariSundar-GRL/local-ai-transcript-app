"""
Create a simple test PDF for the PDF extraction feature.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_test_pdf():
    """Create a test PDF with sample content."""
    filename = "why_llm_cant_develop_software.pdf"

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph("Why LLMs Can't Fully Develop Software", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 20))

    # Paragraphs
    paragraphs = [
        "Large Language Models have revolutionized many aspects of software development, "
        "providing powerful tools for code generation, debugging assistance, and documentation. "
        "However, despite their impressive capabilities, they face fundamental limitations "
        "that prevent them from fully replacing human software developers.",
        "One critical limitation is the lack of true understanding and reasoning. LLMs operate "
        "by pattern matching and statistical prediction based on their training data, rather "
        "than genuine comprehension of software architecture, business requirements, or system "
        "constraints. This makes them excellent at generating syntactically correct code but "
        "potentially poor at making high-level design decisions.",
        "Context windows present another significant challenge. Even the most advanced LLMs "
        "have limited context windows, typically handling tens of thousands of tokens at most. "
        "Real-world software projects often involve millions of lines of code across thousands "
        "of files, making it impossible for an LLM to maintain full awareness of the entire "
        "codebase simultaneously.",
        "Additionally, LLMs struggle with long-term planning and consistency. Software "
        "development requires maintaining coherent architecture across weeks, months, or even "
        "years of development. LLMs lack the ability to maintain this kind of persistent "
        "state and evolving understanding over extended periods.",
        "Testing and debugging represent another area where human developers excel beyond "
        "current AI capabilities. While LLMs can suggest fixes for specific errors, they "
        "cannot systematically reason about edge cases, security vulnerabilities, or subtle "
        "integration issues that emerge in complex systems.",
    ]

    for para_text in paragraphs:
        para = Paragraph(para_text, styles["BodyText"])
        story.append(para)
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"✅ Created test PDF: {filename}")


if __name__ == "__main__":
    create_test_pdf()
