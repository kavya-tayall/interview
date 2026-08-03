import os
from pathlib import Path
from typing import Literal, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# Locate the backend and data folders.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Load variables from backend/.env.
load_dotenv(BASE_DIR / ".env")


# The required structure for one extracted question.
class ExtractedQuestion(BaseModel):
    question: str

    category: Literal[
        "coding",
        "system_design",
        "behavioral",
        "technical",
        "product",
        "other",
    ]

    explicitly_reported: bool
    evidence: str
    confidence: float = Field(ge=0, le=1)


# The required structure for the whole interview report.
class InterviewReport(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    level: Optional[str] = None
    interview_date: Optional[str] = None

    rounds: list[str]
    questions: list[ExtractedQuestion]
    topics: list[str]


def extract_report(report_text: str) -> InterviewReport:
    """Send an interview report to Gemini and return structured data."""

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY was not found in backend/.env"
        )

    # Create the connection to Gemini.
    client = genai.Client(api_key=api_key)

    # Send the report to Gemini.
    response = client.models.generate_content(
        model=model_name,
        contents=report_text,
        config=types.GenerateContentConfig(
            system_instruction="""
You extract structured information from interview-experience reports.

Rules:
1. Extract only information directly supported by the report.
2. Do not invent interview questions.
3. You may lightly rewrite a question for clarity, but do not change
   its meaning.
4. Set explicitly_reported to true only when the report says or
   strongly indicates that the question was asked.
5. Include a short source passage as evidence for every question.
6. Use null when the company, role, level, or date is unknown.
7. Confidence must be between 0 and 1.
8. Return an empty list when no rounds, questions, or topics are found.
""",
            response_mime_type="application/json",
            response_schema=InterviewReport,
            temperature=0.1,
        ),
    )

    # response.parsed contains the structured result.
    if response.parsed is None:
        raise RuntimeError(
            "Gemini responded, but no structured result was returned."
        )

    # Gemini will normally return an InterviewReport directly.
    if isinstance(response.parsed, InterviewReport):
        return response.parsed

    # This handles cases where Gemini returns a Python dictionary.
    return InterviewReport.model_validate(response.parsed)


def main() -> None:
    input_path = DATA_DIR / "sample_report.txt"
    output_path = DATA_DIR / "extracted_report.json"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Could not find the input file: {input_path}"
        )

    report_text = input_path.read_text(encoding="utf-8")

    if not report_text.strip():
        raise ValueError("sample_report.txt is empty.")

    extracted_report = extract_report(report_text)

    json_text = extracted_report.model_dump_json(indent=2)

    output_path.write_text(
        json_text,
        encoding="utf-8",
    )

    print(json_text)
    print(f"\nSaved result to: {output_path}")


if __name__ == "__main__":
    main()