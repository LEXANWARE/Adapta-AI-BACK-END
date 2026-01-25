from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid

from app.services.pdf import extract_text_from_pdf
from app.db.session import get_session
from app.models.user import User
from app.models.resume import Resume
from app.core.security import get_current_user
from agents.models import resume_agent, resume_enricher_agent, resume_upgrade_agent
from app.utils.pdf import gerar_pdf_arquivo

router = APIRouter()

class EnrichRequest(BaseModel):
    resume_id: int
    additional_info: str

class AdaptRequest(BaseModel):
    resume_id: int
    vacancy_text: str

class ResumeSummary(BaseModel):
    id: int
    title: str
    created_at: str

@router.get("/", response_model=List[ResumeSummary])
async def list_resumes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
    resumes = session.exec(statement).all()

    summary_list = []

    for resume in resumes:
        data = resume.parsed_data or {}
        basics = data.get("basics", {})
        job_title = basics.get("label", "Currículo Base")
        display_title = f"{job_title} (#{resume.id})"

        summary_list.append(ResumeSummary(
            id=resume.id,
            title=display_title,
            created_at=resume.created_at.strftime("%d/%m/%Y %H:%M")
        ))

    return summary_list

@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Apenas PDF permitido.")

    text = await extract_text_from_pdf(file)

    try:
        response = resume_agent.run(text)
        resume_data = response.content.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {e}")

    new_resume = Resume(
        user_id=current_user.id,
        raw_text=text,
        parsed_data=resume_data
    )
    session.add(new_resume)
    session.commit()
    session.refresh(new_resume)

    return new_resume

@router.post("/enrich")
async def enrich_resume(
    request: EnrichRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resume = session.get(Resume, request.resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    prompt = f"""
    CURRÍCULO ATUAL (JSON):
    {resume.parsed_data}

    INFORMAÇÕES ADICIONAIS DO USUÁRIO:
    {request.additional_info}
    """

    try:
        response = resume_enricher_agent.run(prompt)
        new_data = response.content.model_dump()

        resume.parsed_data = new_data
        session.add(resume)
        session.commit()
        session.refresh(resume)

        return resume

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enriquecer: {e}")

@router.post("/adapt")
async def adapt_resume(
    request: AdaptRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resume = session.get(Resume, request.resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    prompt = f"""
    A VAGA É ESTA:
    {request.vacancy_text}

    O CURRÍCULO ORIGINAL É ESTE:
    {resume.parsed_data}

    Reescreva o currículo mantendo a verdade, mas destacando pontos que conectem com a vaga.
    """

    try:
        response = resume_upgrade_agent.run(prompt)
        adapted_data = response.content.model_dump()

        adapted_resume = Resume(
            user_id=current_user.id,
            raw_text=resume.raw_text,
            parsed_data=adapted_data
        )
        session.add(adapted_resume)
        session.commit()
        session.refresh(adapted_resume)

        return adapted_resume

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adaptar: {e}")

@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    return resume

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    session.delete(resume)
    session.commit()

    return {"message": "Currículo deletado com sucesso!"}

@router.get("/preview/{resume_id}")
async def preview_resume_pdf(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    temp_filename = f"preview_{uuid.uuid4()}.pdf"
    file_path = f"/tmp/{temp_filename}" if os.name != 'nt' else temp_filename

    try:
        gerar_pdf_arquivo(resume.parsed_data, file_path)

        return FileResponse(
            path=file_path, 
            media_type='application/pdf',
            headers={"Content-Disposition": "inline; filename=preview.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Preview: {e}")

@router.get("/download/{resume_id}")
async def download_resume_pdf(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    temp_filename = f"resume_{uuid.uuid4()}.pdf"
    file_path = f"/tmp/{temp_filename}" if os.name != 'nt' else temp_filename

    try:
        gerar_pdf_arquivo(resume.parsed_data, file_path)
        return FileResponse(
            path=file_path, 
            filename="Curriculo_Adaptado.pdf", 
            media_type='application/pdf'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {e}")