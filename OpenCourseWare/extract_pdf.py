import pymupdf4llm

def extract_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using pymupdf4llm for optimal LLM understanding."""
    try:
        text = pymupdf4llm.to_markdown(pdf_path)
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

