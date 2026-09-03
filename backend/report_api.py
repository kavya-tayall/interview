from fastapi import APIRouter

from generate_report import (
    InterviewReportRequest,
    InterviewReportResponse,
    generate_interview_report,
)


router = APIRouter(
    prefix="/interview",
    tags=["Interview Report"],
)


@router.post(
    "/report",
    response_model=InterviewReportResponse,
)
def create_interview_report(
    request: InterviewReportRequest,
) -> InterviewReportResponse:
    return generate_interview_report(request)