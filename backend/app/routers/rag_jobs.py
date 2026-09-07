from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_rag_job_service
from app.models.user import User
from app.schemas.rag_job import RagJobListResponse, RagJobResponse
from app.services.rag_job_service import RagJobService

router = APIRouter(prefix="/api/rag-jobs", tags=["rag-jobs"])


@router.get("/active", response_model=RagJobResponse | None)
async def get_active_job(
    user: User = Depends(get_current_user),
    service: RagJobService = Depends(get_rag_job_service),
):
    return await service.get_active_job(user.id)


@router.get("/", response_model=RagJobListResponse)
async def list_jobs(
    user: User = Depends(get_current_user),
    service: RagJobService = Depends(get_rag_job_service),
):
    return await service.list_jobs(user.id)
