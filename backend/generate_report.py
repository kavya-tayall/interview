import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from generate_questions import PracticeQuestion


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class ReportMessage(BaseModel):
    speaker: Literal["interviewer", "candidate"]
    text: str
    question_index: int


class InterviewReportRequest(BaseModel):
    company: str
    role: str
    level: str
    duration_minutes: int

    questions: list[PracticeQuestion]
    messages: list[ReportMessage]

    completed_reason: Literal[
        "finished_questions",
        "time_expired",
    ]


class QuestionFeedback(BaseModel):
    question_index: int
    question: str
    score: int = Field(ge=0, le=10)

    what_went_well: list[str]
    what_to_improve: list[str]
    better_answer_outline: list[str]


class InterviewReportResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)

    readiness: Literal[
        "needs_practice",
        "developing",
        "interview_ready",
        "strong",
    ]

    summary: str
    overall_strengths: list[str]
    overall_improvements: list[str]
    question_feedback: list[QuestionFeedback]


def generate_interview_report(
    request: InterviewReportRequest,
) -> InterviewReportResponse:
    api_key = os.getenv("GEMINI_API_KEY")

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from backend/.env"
        )

    client = genai.Client(api_key=api_key)

    question_text = "\n\n".join(
        (
            f"Question index: {index}\n"
            f"Question: {question.question}\n"
            f"Category: {question.category}\n"
            f"Difficulty: {question.difficulty}"
        )
        for index, question in enumerate(request.questions)
    )

    transcript_text = "\n".join(
        (
            f"[Question {message.question_index}] "
            f"{message.speaker}: {message.text}"
        )
        for message in request.messages
    )

    prompt = f"""
You are evaluating a completed practice interview.

This is coaching feedback, not a real hiring decision.

Interview context:
- Company: {request.company}
- Role: {request.role}
- Candidate level: {request.level}
- Planned duration: {request.duration_minutes} minutes
- Completion reason: {request.completed_reason}

Main questions:
{question_text}

Interview transcript:
{transcript_text}

Create a useful interview report.

Rules:
- Base all feedback only on the transcript.
- Adjust expectations for the role and candidate level.
- Do not invent anything the candidate did not say.
- Do not penalize questions that were not reached.
- Only evaluate questions that received a candidate response.
- Consider answers to follow-up questions.
- Give specific and constructive feedback.
- question_index must match the zero-based index in the transcript.
- better_answer_outline should contain coaching points, not a full script.

Score guidelines:
- 0 to 39: needs practice
- 40 to 59: developing
- 60 to 79: interview ready
- 80 to 100: strong
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InterviewReportResponse,
            temperature=0.2,
        ),
    )

    if response.parsed is None:
        raise RuntimeError(
            "Gemini did not return an interview report."
        )

    if isinstance(
        response.parsed,
        InterviewReportResponse,
    ):
        return response.parsed

    return InterviewReportResponse.model_validate(
        response.parsed
    )