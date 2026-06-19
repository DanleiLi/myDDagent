import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import settings
from app.database.models import DDSchema, Project
from app.database.schemas import DDSchemaCreate, DDSchemaRead
from app.database.session import get_db_session

router = APIRouter(prefix="/api/schema", tags=["schema"])


@router.get("/{project_id}", response_model=DDSchemaRead)
async def get_schema(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DDSchemaRead:
    await _verify_project_ownership(project_id, current_user.id, db)

    result = await db.execute(
        select(DDSchema).where(DDSchema.project_id == project_id)
    )
    schema = result.scalar_one_or_none()
    if schema is None:
        raise HTTPException(status_code=404, detail="Schema not found for this project")
    return DDSchemaRead.model_validate(schema)


@router.post("/{project_id}", response_model=DDSchemaRead, status_code=201)
async def create_or_replace_schema(
    project_id: str,
    body: DDSchemaCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DDSchemaRead:
    await _verify_project_ownership(project_id, current_user.id, db)

    fields_data = [f.model_dump() for f in body.fields]

    # Upsert: replace if exists, create if not
    result = await db.execute(
        select(DDSchema).where(DDSchema.project_id == project_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.fields = fields_data
        schema = existing
    else:
        schema = DDSchema(project_id=project_id, fields=fields_data)
        db.add(schema)

    await db.commit()
    await db.refresh(schema)

    # Mirror to data/schemas/ for script access
    schemas_dir = settings.data_dir / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    schema_file = schemas_dir / f"{project_id}.json"
    schema_file.write_text(json.dumps(fields_data, indent=2))

    return DDSchemaRead.model_validate(schema)


async def _verify_project_ownership(
    project_id: str, user_id: str, db: AsyncSession
) -> None:
    result = await db.execute(
        select(Project.id).where(Project.id == project_id, Project.user_id == user_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")
