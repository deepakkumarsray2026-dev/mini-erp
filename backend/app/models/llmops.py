import enum
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings


class ConversationStatus(str, enum.Enum):
    ACTIVE   = "active"
    ARCHIVED = "archived"


class LLMConversation(Base):
    """A chat session between a user and the Finance Chat assistant."""
    __tablename__ = "llm_conversations"
    __table_args__ = {"schema": "mlops"}

    id:               Mapped[str]                 = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    user_id:          Mapped[str]                 = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    title:            Mapped[str | None]          = mapped_column(String(200))
    status:           Mapped[ConversationStatus]  = mapped_column(String(20), default=ConversationStatus.ACTIVE)
    created_at:       Mapped[datetime]            = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_message_at:  Mapped[datetime | None]     = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["LLMChatMessage"]] = relationship(
        "LLMChatMessage", back_populates="conversation", cascade="all, delete-orphan",
        order_by="LLMChatMessage.created_at",
    )


class LLMChatMessage(Base):
    """A single message within a conversation (user or assistant turn)."""
    __tablename__ = "llm_chat_messages"
    __table_args__ = {"schema": "mlops"}

    id:              Mapped[str]        = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    conversation_id: Mapped[str]        = mapped_column(UUID(as_uuid=False), ForeignKey("mlops.llm_conversations.id"), nullable=False, index=True)
    role:            Mapped[str]        = mapped_column(String(20), nullable=False)   # "user" | "assistant"
    content:         Mapped[str]        = mapped_column(Text, nullable=False)
    sql_query:       Mapped[str | None] = mapped_column(Text)
    sql_results:     Mapped[dict | None]= mapped_column(JSONB)
    context_used:    Mapped[dict | None]= mapped_column(JSONB)
    input_tokens:    Mapped[int | None] = mapped_column(Integer)
    output_tokens:   Mapped[int | None] = mapped_column(Integer)
    latency_ms:      Mapped[int | None] = mapped_column(Integer)
    created_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[LLMConversation] = relationship("LLMConversation", back_populates="messages")


class LLMEmbedding(Base):
    """Vector embeddings for documents used for similarity search."""
    __tablename__ = "llm_embeddings"
    __table_args__ = {"schema": "mlops"}

    id:              Mapped[str]        = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    document_type:   Mapped[str]        = mapped_column(String(50), nullable=False, index=True)
    document_id:     Mapped[str]        = mapped_column(String(100), nullable=False, index=True)
    content_hash:    Mapped[str | None] = mapped_column(String(64), index=True)
    embedding_model: Mapped[str]        = mapped_column(String(100), default=settings.EMBEDDING_MODEL)
    embedding:       Mapped[list | None]= mapped_column(Vector(settings.EMBEDDING_DIM))
    metadata_:       Mapped[dict | None]= mapped_column("metadata", JSONB)
    created_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


