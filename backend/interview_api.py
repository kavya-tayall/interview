from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from generate_questions import QuestionSet, generate_question_set

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
    model_name = os.getenv("GEMINI_MODEL")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    if not model_name:
        raise RuntimeError("GEMINI_MODEL is missing.")

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

Possible follow-up ideas prepared for this question:
{request.suggested_follow_ups}

Conversation history:
{conversation_text}

Candidate's newest response:
{request.candidate_response}

Decide how the interviewer should respond.

Your goal is to collect enough evidence to evaluate the candidate's
understanding while keeping the interview natural and efficient.

Follow-up behavior:
- There is no fixed number of follow-up questions.
- You may ask zero, one, or multiple follow-ups depending on the context.
- Ask a follow-up only when it would reveal meaningful additional signal.
- Do not ask a follow-up merely to keep the conversation going.
- Do not repeat something already answered in the conversation history.
- Move to the next main question once the candidate has demonstrated
  enough understanding for their expected level.
- Adjust the depth of follow-ups to the role and candidate level.
- A junior candidate should not automatically be judged by senior-level
  expectations.
- For senior candidates, explore tradeoffs, scalability, failure modes,
  and design decisions when relevant.
  
  Interview timing:
- Total duration: {request.duration_minutes} minutes
- Remaining time: {request.seconds_remaining} seconds

Use the remaining time when deciding whether to ask another
follow-up or move to the next main question.

Response rules:

1. If the candidate asks a clarification question:
   - Answer the clarification naturally.
   - action must be "stay_on_question".
   - response_type must be "clarification".

2. If the answer is incomplete:
   - Ask one focused follow-up about the most important missing concept.
   - action must be "stay_on_question".
   - response_type must be "partial_answer".

3. If the answer is complete but one valuable deeper question would
   reveal additional relevant understanding:
   - Ask exactly one focused follow-up.
   - action must be "stay_on_question".
   - response_type must be "complete_answer".

4. If the candidate has demonstrated enough understanding:
   - Briefly acknowledge the response.
   - Do not ask another question in the reply.
   - action must be "next_question".
   - response_type must be "complete_answer".

5. If the response is unrelated:
   - Redirect the candidate back to the current topic.
   - action must be "stay_on_question".
   - response_type must be "off_topic".

Consistency rules:
- If the reply asks a question, action must be "stay_on_question".
- If action is "next_question", the reply must not contain a question.
- Never repeat a follow-up already present in the conversation history.
- Keep the response concise and conversational.
- Do not reveal the complete ideal answer.
- Do not invent company-specific interview standards that were not provided.
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

    # Safety check:
    # A reply that asks a question must remain on the current question.
    if "?" in result.reply and result.action == "next_question":
        result = result.model_copy(
            update={"action": "stay_on_question"}
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
   
    
    