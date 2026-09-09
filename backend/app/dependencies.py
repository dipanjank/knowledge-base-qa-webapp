import uuid

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_aws import BedrockEmbeddings, ChatBedrockConverse
from langchain_postgres import PGVector
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import create_sync_session_factory, get_db
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.rag_job_repository import RagJobRepository
from app.repositories.user_repository import UserRepository
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.qa_service import QAService
from app.services.rag_job_service import RagJobService
from app.services.s3_service import S3Service
from app.services.sqs_service import SQSService
from app.utils.auth import decode_token

bearer_scheme = HTTPBearer()


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_service(repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(repo)


def get_admin_service(repo: UserRepository = Depends(get_user_repo)) -> AdminService:
    return AdminService(repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await repo.get_by_id(uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_refresh_token(refresh_token: str | None = Cookie(default=None)) -> str:
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    return refresh_token


def get_document_repo(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_rag_job_repo(db: AsyncSession = Depends(get_db)) -> RagJobRepository:
    return RagJobRepository(db)


def get_s3_service() -> S3Service:
    return S3Service(bucket=settings.s3_bucket_name, region=settings.aws_region)


def get_sqs_service() -> SQSService:
    return SQSService(queue_url=settings.sqs_queue_url, region=settings.aws_region)


def get_document_service(
    document_repo: DocumentRepository = Depends(get_document_repo),
    rag_job_repo: RagJobRepository = Depends(get_rag_job_repo),
    s3_service: S3Service = Depends(get_s3_service),
    sqs_service: SQSService = Depends(get_sqs_service),
) -> DocumentService:
    return DocumentService(document_repo, rag_job_repo, s3_service, sqs_service)


def get_rag_job_service(
    rag_job_repo: RagJobRepository = Depends(get_rag_job_repo),
) -> RagJobService:
    return RagJobService(rag_job_repo)


_vector_store = None
_llm = None
_sync_session_factory = None


def _get_vector_store() -> PGVector:
    global _vector_store
    if _vector_store is None:
        embeddings = BedrockEmbeddings(
            model_id=settings.bedrock_embedding_model_id,
            region_name=settings.aws_region,
        )
        _vector_store = PGVector(
            embeddings=embeddings,
            collection_name="document_chunks",
            connection=settings.database_url,
            use_jsonb=True,
        )
    return _vector_store


def _get_llm() -> ChatBedrockConverse:
    global _llm
    if _llm is None:
        _llm = ChatBedrockConverse(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
        )
    return _llm


def _get_sync_session_factory():
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = create_sync_session_factory(settings.database_url)
    return _sync_session_factory


def get_conversation_repo(db: AsyncSession = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db)


def get_qa_service(
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
) -> QAService:
    return QAService(conversation_repo, _get_vector_store(), _get_llm(), _get_sync_session_factory())
