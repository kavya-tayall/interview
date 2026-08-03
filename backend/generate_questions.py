import json
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
load_dotenv(BASE_DIR / ".env")

class PracticeQuestion(BaseModel):
    question: str

    category: Literal[
    "coding",
    "system_design",
    "behavioral",
    "technical",
    "product",
    "other",
]

    source_type: Literal["reported_pattern", "standard"]

    difficulty: Literal["easy", "medium", "hard"]

    reason_selected: str
    follow_up_questions: list[str]
    
class QuestionSet(BaseModel):
    company: str
    role: str
    level: str
    duration_minutes: int
    questions: list[PracticeQuestion]
        
def build_prompt(
    company: str,
    role: str,
    level: str,
    duration_minutes: int,
    reports: list[dict],
) -> str:
    reported_questions = []
    reported_topics = []

    for report in reports:
        report_company = report.get("company") or "Unknown company"
        report_role = report.get("role") or "Unknown role"

        for question in report.get("questions", []):
            question_text = question.get("question")

            if question_text:
                reported_questions.append(
                    f"- [{report_company} | {report_role}] "
                    f"{question_text}"
                )

        for topic in report.get("topics", []):
            if topic:
                reported_topics.append(topic)

    unique_topics = sorted(set(reported_topics))

    question_text = (
        "\n".join(reported_questions)
        if reported_questions
        else "- No reported questions were available."
    )

    topic_text = (
        "\n".join(f"- {topic}" for topic in unique_topics)
        if unique_topics
        else "- No reported topics were available."
    )

    return f"""
Create a realistic practice interview.

Requested interview:
- Company: {company}
- Role: {role}
- Level: {level}
- Interview duration: {duration_minutes} minutes

Available interview-report topics:
{topic_text}

Available reported question patterns:
{question_text}

Requirements:
Choose the number of main questions based on the interview duration,
role, and candidate level.

Guidelines:
- 20 minutes: usually 2 or 3 main questions
- 30 minutes: usually 3 or 4 main questions
- 45 minutes: usually 3 to 5 main questions
- 60 minutes: usually 4 to 6 main questions
- System-design and senior interviews should generally use fewer main
  questions with deeper discussion.
- Intern and new-grad interviews can use more varied questions with
  shorter discussion.
- These are guidelines, not strict requirements.

- Customize every question for the requested role and level.
- Use the requested company only as general context.
- Do not claim that a question was asked by the requested company unless
  the supplied report explicitly supports that claim.
- Use up to 4 relevant reported patterns when useful.
- Fill the remaining positions with standard interview questions.
- If the reports are not relevant, prefer standard questions instead.
- Avoid duplicate or nearly identical questions.
- Include a useful mixture of coding, technical, system-design, and
  behavioral questions based on the requested role.
- Intern and new-grad questions should emphasize fundamentals.
- Mid-level questions should explore implementation choices and tradeoffs.
- Senior questions should explore architecture, scalability, leadership,
  failure modes, and tradeoffs.
- Every question must include 2 or 3 possible follow-up questions.
- Follow-up questions are suggestions, not mandatory questions.

source_type rules:
- Use "reported_pattern" only when the question is based on the supplied
  interview reports.
- Use "standard" for normally generated interview questions.

Return the requested company, role, and level exactly as provided.
"""

def load_report_corpus() -> list[dict]:
    corpus_path = DATA_DIR / "all_extracted_reports.json"

    if not corpus_path.exists():
        return []

    file_text = corpus_path.read_text(encoding="utf-8")
    data = json.loads(file_text)

    if not isinstance(data, list):
        raise ValueError(
            "all_extracted_reports.json must contain a JSON list."
        )

    return data

def generate_with_gemini(prompt: str) -> QuestionSet:
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

    if not api_key:
        raise RuntimeError("Gemini API key is missing.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuestionSet,
        ),
    )

    if response.parsed is None:
        raise RuntimeError("Gemini did not return structured data.")

    if isinstance(response.parsed, QuestionSet):
        return response.parsed

    return QuestionSet.model_validate(response.parsed)

def generate_question_set(
    company: str,
    role: str,
    level: str,
    duration_minutes: Optional[int] = None,
) -> QuestionSet:
    reports = load_report_corpus()

    resolved_duration = (
        duration_minutes
        if duration_minutes is not None
        else recommend_duration(role, level)
    )

    prompt = build_prompt(
        company=company,
        role=role,
        level=level,
        duration_minutes=resolved_duration,
        reports=reports,
    )

    question_set = generate_with_gemini(prompt)

    return question_set.model_copy(
        update={
            "company": company,
            "role": role,
            "level": level,
            "duration_minutes": resolved_duration,
        }
    )

def recommend_duration(
    role: str,
    level: str,
) -> int:
    role_lower = role.lower()
    level_lower = level.lower()

    if (
        "senior" in level_lower
        or "manager" in role_lower
        or "architect" in role_lower
    ):
        return 60

    if "intern" in level_lower:
        return 30

    return 45

def main():
    question_set = generate_question_set(
        company="ExampleCo",
        role="backend software engineer",
        level="new-grad",
        duration_minutes=None,
    )

    output_path = DATA_DIR / "generated_questions.json"

    output_path.write_text(
        question_set.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print(question_set.model_dump_json(indent=2))

if __name__ == "__main__":
    main()