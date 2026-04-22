import json
from io import BytesIO
from pypdf import PdfReader
from typing import List, Optional
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from app.models.user import User
from app.models.resume import Resume
from app.db.session import get_session
from app.core.security import get_current_user
from app.services.workflow_service import workflow_service
from app.api.v1.endpoints.schemas.resumes import (
    ResumeSummary,
    ResumeDetail,
    OptimizeRequest,
    OptimizeResponse,
    QualityAnalysisResponse,
    ATSAnalysisResponse,
    FullPipelineRequest,
    FullPipelineResponse,
)


def extract_text_from_pdf(file: UploadFile) -> str:
    """Extrai texto de um arquivo PDF usando pypdf."""
    pdf_reader = PdfReader(BytesIO(file.file.read()))
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


router = APIRouter()


# ==================== CRUD de Currículos ====================

@router.post("/upload", status_code=201)
async def upload_resume(
    file: UploadFile = File(..., description="Arquivo PDF do currículo"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Faz upload de um currículo em PDF e extrai seu texto.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    try:
        raw_text = extract_text_from_pdf(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")

    if not raw_text:
        raise HTTPException(status_code=400, detail="PDF vazio ou não foi possível extrair texto.")

    resume = Resume(
        user_id=current_user.id,
        raw_text=raw_text,
        parsed_data={}
    )

    session.add(resume)
    session.commit()
    session.refresh(resume)

    return {
        "id": resume.id,
        "raw_text_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
        "message": "Currículo enviado com sucesso!"
    }


@router.get("/", response_model=List[ResumeSummary])
async def list_resumes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os currículos do usuário."""
    statement = select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
    resumes = session.exec(statement).all()

    return [
        ResumeSummary(
            id=r.id,
            created_at=r.created_at.isoformat(),
            has_optimized_version=bool(r.parsed_data)
        )
        for r in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeDetail)
async def get_resume(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtém detalhes de um currículo específico."""
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    return ResumeDetail(
        id=resume.id,
        raw_text=resume.raw_text,
        parsed_data=resume.parsed_data,
        created_at=resume.created_at.isoformat()
    )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Deleta um currículo."""
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    session.delete(resume)
    session.commit()

    return {"message": "Currículo deletado com sucesso!"}


# ==================== Workflows de Otimização ====================

@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume(
    request: OptimizeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Otimiza um currículo para uma vaga específica.
    
    Fluxo completo:
    1. Parse da vaga (extrai keywords e requisitos)
    2. Parse do currículo original
    3. Geração do currículo otimizado
    
    O resultado é salvo no campo parsed_data do currículo.
    """
    resume = session.get(Resume, request.resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    try:
        result = workflow_service.optimize_resume(
            vaga=request.vacancy_text,
            curriculo=resume.raw_text,
            info_adicional=request.additional_info
        )
        
        optimized_resume = result.get("optimized_resume")
        vacancy_analysis = result.get("vacancy_analysis")
        
        if optimized_resume:
            # Salva o currículo otimizado
            resume.parsed_data = optimized_resume
            session.add(resume)
            session.commit()
        
        return OptimizeResponse(
            resume_id=resume.id,
            optimized_resume=optimized_resume,
            vacancy_analysis=vacancy_analysis,
            message="Currículo otimizado com sucesso!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na otimização: {str(e)}")


@router.post("/analyze-quality", response_model=QualityAnalysisResponse)
async def analyze_quality(
    resume_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Executa auditoria de qualidade no currículo.
    
    Analisa:
    - Gramática e ortografia
    - Branding e senioridade percebida
    - Estrutura e completude das experiências
    - Links e presença digital
    """
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    try:
        quality_result = workflow_service.analyze_quality(resume.raw_text)
        
        return QualityAnalysisResponse(
            resume_id=resume_id,
            analysis=quality_result.model_dump() if quality_result else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de qualidade: {str(e)}")


@router.post("/check-ats", response_model=ATSAnalysisResponse)
async def check_ats(
    resume_id: int,
    vacancy_text: str = Form(..., description="Descrição da vaga"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula score ATS de compatibilidade entre currículo e vaga.
    
    Retorna:
    - Score de 0-100
    - Keywords encontradas e ausentes
    - Recomendações para melhorar o score
    """
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    try:
        ats_result = workflow_service.check_ats(
            vaga=vacancy_text,
            curriculo=resume.raw_text
        )
        
        return ATSAnalysisResponse(
            resume_id=resume_id,
            analysis=ats_result.model_dump() if ats_result else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise ATS: {str(e)}")


@router.post("/full-pipeline", response_model=FullPipelineResponse)
async def full_pipeline(
    request: FullPipelineRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Pipeline completo: Quality → ATS → Optimize.
    
    Executa todas as análises e otimização em uma única chamada.
    O currículo otimizado é salvo automaticamente.
    """
    resume = session.get(Resume, request.resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    try:
        result = workflow_service.full_pipeline(
            vaga=request.vacancy_text,
            curriculo=resume.raw_text,
            info_adicional=request.additional_info
        )
        
        optimized_resume = result.get("optimized_resume")
        
        if optimized_resume:
            resume.parsed_data = optimized_resume
            session.add(resume)
            session.commit()
        
        return FullPipelineResponse(
            resume_id=resume.id,
            quality_analysis=result.get("quality_analysis"),
            ats_analysis=result.get("ats_analysis"),
            optimized_resume=optimized_resume,
            vacancy_analysis=result.get("vacancy_analysis"),
            message="Pipeline completo executado com sucesso!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline: {str(e)}")


# ==================== Endpoint Adapt-Full (Upload + Otimização) ====================

@router.post("/adapt-full", response_model=FullPipelineResponse)
async def adapt_resume_full(
    file: UploadFile = File(..., description="Arquivo PDF do currículo"),
    vacancy_text: str = Form(..., description="Descrição da vaga"),
    additional_info: Optional[str] = Form(None, description="Informações adicionais"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Fluxo completo: Upload do PDF + Pipeline completo.
    
    1. Extrai texto do PDF
    2. Salva currículo no banco
    3. Executa pipeline completo (Quality + ATS + Optimize)
    4. Retorna todos os resultados
    
    Ideal para uso único sem necessidade de múltiplas chamadas.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    try:
        raw_text = extract_text_from_pdf(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")

    if not raw_text:
        raise HTTPException(status_code=400, detail="PDF vazio ou não foi possível extrair texto.")

    # Salva currículo
    resume = Resume(
        user_id=current_user.id,
        raw_text=raw_text,
        parsed_data={}
    )
    session.add(resume)
    session.commit()
    session.refresh(resume)

    try:
        result = workflow_service.full_pipeline(
            vaga=vacancy_text,
            curriculo=raw_text,
            info_adicional=additional_info
        )
        
        optimized_resume = result.get("optimized_resume")
        
        if optimized_resume:
            resume.parsed_data = optimized_resume
            session.add(resume)
            session.commit()
        
        return FullPipelineResponse(
            resume_id=resume.id,
            quality_analysis=result.get("quality_analysis"),
            ats_analysis=result.get("ats_analysis"),
            optimized_resume=optimized_resume,
            vacancy_analysis=result.get("vacancy_analysis"),
            message="Upload e pipeline completo executados com sucesso!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline: {str(e)}")