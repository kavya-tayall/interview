from typing import Literal

from pydantic import BaseModel, Field

from generate_questions import PracticeQuestion


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

