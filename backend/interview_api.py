import os
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel

from generate_questions import (
    QuestionSet,
    generate_question_set,
)
from report_api import router as report_router


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)


class ConversationMessage(BaseModel):
    speaker: Literal["interviewer", "candidate"]
    text: str


class InterviewRequest(BaseModel):
    company: str
    role: str
    level: str

    current_question: str
    question_category: str
    question_difficulty: str
    suggested_follow_ups: list[str]

    candidate_response: str
    conversation_history: list[ConversationMessage]

    duration_minutes: int
    seconds_remaining: int


class InterviewResponse(BaseModel):
    reply: str

    action: Literal[
        "stay_on_question",
        "next_question",
    ]

    response_type: Literal[
        "clarification",
        "partial_answer",
        "complete_answer",
        "off_topic",
    ]


class StartInterviewRequest(BaseModel):
    company: str
    role: str
    level: str
    duration_minutes: Optional[int] = None


def generate_interviewer_response(
    request: InterviewRequest,
) -> InterviewResponse:
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

    conversation_text = "\n".join(
        f"{message.speaker}: {message.text}"
        for message in request.conversation_history
    )

    prompt = f"""
You are conducting a realistic job interview.

Interview context:
- Company: {request.company}
- Role: {request.role}
- Candidate level: {request.level}

Current main question:
{request.current_question}

Question category:
{request.question_category}

Question difficulty:
{request.question_difficulty}

Possible follow-up ideas:
{request.suggested_follow_ups}

Conversation history:
{conversation_text}

Candidate's newest response:
{request.candidate_response}

Interview timing:
- Total duration: {request.duration_minutes} minutes
- Remaining time: {request.seconds_remaining} seconds

Your goal is to collect enough evidence to evaluate the candidate's
understanding while keeping the interview natural and efficient.

Follow-up behavior:
- There is no fixed number of follow-up questions.
- Ask a follow-up only when it provides useful additional information.
- Do not repeat something already answered.
- Adjust the depth to the candidate's role and level.
- Use the remaining time when deciding whether to ask a follow-up.
- Move to the next main question when enough understanding is shown.
- When time is low, avoid unnecessary follow-up questions.

Response rules:

1. If the candidate asks for clarification:
   - Answer the clarification naturally.
   - action must be "stay_on_question".
   - response_type must be "clarification".

2. If the answer is incomplete:
   - Ask one focused follow-up about the most important missing idea.
   - action must be "stay_on_question".
   - response_type must be "partial_answer".

3. If the answer is complete but one deeper question would provide
   useful information:
   - Ask one focused follow-up.
   - action must be "stay_on_question".
   - response_type must be "complete_answer".

4. If the candidate has shown enough understanding:
   - Briefly acknowledge the response.
   - Do not ask another question in the reply.
   - action must be "next_question".
   - response_type must be "complete_answer".

5. If the answer is unrelated:
   - Redirect the candidate to the current question.
   - action must be "stay_on_question".
   - response_type must be "off_topic".

Main-question transition rules:
- Never create a new main interview problem yourself.
- Follow-up questions must remain directly related to the current main question.
- Do not say "let's move on" and then ask another question.
- When the candidate has demonstrated enough understanding, return
  action "next_question".
- When action is "next_question", reply only with a short acknowledgment,
  such as "Great, let's move on."
- The frontend is responsible for presenting the next main question.

Consistency rules:
- If the reply contains a question, action must be "stay_on_question".
- If action is "next_question", the reply must not ask a question.
- Keep the response concise and conversational.
- Do not reveal the complete ideal answer.
- Do not invent company-specific interview standards.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InterviewResponse,
            temperature=0.2,
        ),
    )

    if response.parsed is None:
        raise RuntimeError(
            "Gemini did not return a structured response."
        )

    if isinstance(response.parsed, InterviewResponse):
        result = response.parsed
    else:
        result = InterviewResponse.model_validate(
            response.parsed
        )

    if (
        "?" in result.reply
        and result.action == "next_question"
    ):
        result = result.model_copy(
            update={
                "action": "stay_on_question",
            }
        )

    return result


@app.post(
    "/interview/respond",
    response_model=InterviewResponse,
)
def respond_to_candidate(
    request: InterviewRequest,
) -> InterviewResponse:
    return generate_interviewer_response(request)


@app.post(
    "/interview/start",
    response_model=QuestionSet,
)
def start_interview(
    request: StartInterviewRequest,
) -> QuestionSet:
    return generate_question_set(
        company=request.company,
        role=request.role,
        level=request.level,
        duration_minutes=request.duration_minutes,
    )



