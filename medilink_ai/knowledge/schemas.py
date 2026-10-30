from datetime import date
from pydantic import BaseModel, Field, field_validator


class DocumentMetadataRequest(BaseModel):
    organization_id: str = Field(min_length=1, max_length=100)
    facility_id: str = Field(min_length=1, max_length=100)
    department_id: str | None = Field(default=None, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    document_type: str = Field(min_length=1, max_length=100)
    classification: str = Field(min_length=1, max_length=50)
    version: str = Field(min_length=1, max_length=50)
    allowed_roles: list[str] = Field(default_factory=list, max_length=50)
    allowed_users: list[str] = Field(default_factory=list, max_length=100)
    effective_from: date | None = None
    effective_until: date | None = None

    @field_validator("effective_until")
    @classmethod
    def valid_date_window(cls, value: date | None, info):
        start = info.data.get("effective_from")
        if value and start and value < start:
            raise ValueError("effective_until must be on or after effective_from")
        return value

    @field_validator("classification")
    @classmethod
    def normalize_classification(cls, value: str) -> str:
        return value.strip().upper()


class IngestionResponse(BaseModel):
    status: str
    document_id: str
    title: str
    source_filename: str
    extracted_characters: int
    chunk_count: int
    message: str
