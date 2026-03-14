from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import uuid

from app.services.pdf import extract_text_from_pdf


def _to_dict(content) -> dict:
    """Converte response.content (modelo, dict ou string JSON) em dict."""
    if content is None:
        return {}
    if isinstance(content, dict):
        return content
    if hasattr(content, "model_dump"):
        return content.model_dump()
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Resposta da IA não é JSON válido.")
    raise HTTPException(status_code=500, detail="Resposta da IA em formato inesperado.")


from agents.models import vacancy_agent
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
        resume_data = _to_dict(response.content)
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
        new_data = _to_dict(response.content)

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
        adapted_data = _to_dict(response.content)

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

@router.post("/adapt-full")
async def adapt_resume_full(
    file: UploadFile = File(...),
    vacancy_text: str = Form(...),
    additional_info: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """Recebe currículo (PDF), vaga e informações adicionais. Retorna JSON adaptado sem persistir."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Apenas PDF permitido.")

    curriculum_text = await extract_text_from_pdf(file)
    if not curriculum_text.strip():
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do PDF.")

    try:
        vacancy_response = vacancy_agent.run(vacancy_text)
        resume_response = resume_agent.run(curriculum_text)
        vacancy_analysis = str(_to_dict(vacancy_response.content)) if vacancy_response.content else ""
        resume_analysis = str(_to_dict(resume_response.content)) if resume_response.content else ""

        enriched_resume = ""
        if additional_info and additional_info.strip():
            resume_dict = _to_dict(resume_response.content)
            enrich_prompt = f"""
CURRÍCULO ATUAL (JSON):
{json.dumps(resume_dict, ensure_ascii=False, indent=2)}

INFORMAÇÕES ADICIONAIS DO USUÁRIO:
{additional_info}
"""
            enrich_response = resume_enricher_agent.run(enrich_prompt)
            enriched_resume = str(_to_dict(enrich_response.content)) if enrich_response.content else ""
        else:
            enriched_resume = "(Nenhuma informação adicional fornecida)"

        combined_prompt = f"""
## CURRÍCULO ORIGINAL:
{curriculum_text}

## ANÁLISE DA VAGA (Requisitos Identificados):
{vacancy_analysis}

## ANÁLISE DO CURRÍCULO ATUAL:
{resume_analysis}

## CURRÍCULO ENRIQUECIDO COM INFORMAÇÕES ADICIONAIS:
{enriched_resume}

---
TAREFA: Com base nas análises acima, crie um currículo otimizado no formato JSON Resume.
- Destaque as qualificações alinhadas aos requisitos da vaga
- Use palavras-chave identificadas na análise da vaga
- Foque em resultados e conquistas mensuráveis
- Mantenha a estrutura completa do JSON Resume (incluindo basics, work, education, skills, profiles, etc.)
- Retorne APENAS o JSON válido
"""
        upgrade_response = resume_upgrade_agent.run(combined_prompt)
        adapted_data = _to_dict(upgrade_response.content)

        return adapted_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na adaptação: {str(e)}")

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