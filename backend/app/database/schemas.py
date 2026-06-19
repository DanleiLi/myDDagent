from datetime import datetime

from pydantic import BaseModel, Field

from app.database.models import (
    AnalysisStatus,
    DocumentStatus,
    FlagType,
    MessageRole,
    ProjectStatus,
)


# ── Projects ──


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(ProjectBase):
    id: str
    status: ProjectStatus
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Documents ──


class DocumentRead(BaseModel):
    id: str
    project_id: str
    filename: str
    storage_path: str | None
    converted_path: str | None
    mime_type: str | None
    status: DocumentStatus

    model_config = {"from_attributes": True}


# ── Messages ──


class MessageRead(BaseModel):
    id: str
    project_id: str
    role: MessageRole
    content: str
    tool_calls: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Gap Flags ──


class GapFlagRead(BaseModel):
    id: str
    project_id: str
    field_name: str
    flag_type: FlagType
    description: str
    resolved: bool

    model_config = {"from_attributes": True}


# ── Analysis Outputs ──


class AnalysisOutputRead(BaseModel):
    id: str
    project_id: str
    script_name: str
    output_path: str
    status: AnalysisStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceChunkRead(BaseModel):
    id: str
    document_id: str
    project_id: str
    filename: str
    chunk_index: int
    chunk_index_end: int | None = None
    content: str

    model_config = {"from_attributes": True}


class ReportCitationRead(BaseModel):
    citation_id: str
    filename: str
    chunk_index: int
    chunk_index_end: int | None = None
    chunk_id: str | None = None
    document_id: str | None = None
    label: str


class ReportDetailRead(AnalysisOutputRead):
    report_text: str
    citations: list[ReportCitationRead] = Field(default_factory=list)


class ReportCitationLookupRead(BaseModel):
    report_id: str
    citation: ReportCitationRead
    chunks: list[EvidenceChunkRead] = Field(default_factory=list)


# ── DD Schema ──


class SchemaField(BaseModel):
    name: str
    description: str
    required: bool = True
    expected_type: str = "text"


class DDSchemaCreate(BaseModel):
    fields: list[SchemaField]


class DDSchemaRead(BaseModel):
    id: str
    project_id: str
    fields: list[dict]

    model_config = {"from_attributes": True}


# ── Chat ──


class ChatRequest(BaseModel):
    project_id: str
    message: str
