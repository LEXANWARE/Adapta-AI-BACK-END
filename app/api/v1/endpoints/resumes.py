import json
from fastapi import APIRouter, Form, HTTPException, Depends
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any

from agents.workflow import resume_optimizer_workflow
from app.db.session import get_session
from app.models.user import User
from app.models.resume import Resume
from app.core.security import get_current_user
from app.api.v1.endpoints.schemas.resumes import (
    ResumeSummary,
    ATSUserInput,
    WorkflowOptimizeRequest,
    WorkflowSessionResponse,
    WorkflowContinueRequest,
)


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


# ==================== Endpoints ====================

router = APIRouter()

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

# ==================== Endpoints do Workflow com HITL ====================

@router.post("/optimize-with-workflow", response_model=WorkflowSessionResponse)
async def optimize_with_workflow(
    request: WorkflowOptimizeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Executa o workflow completo de otimização com HITL.
    
    Fluxo:
    1. Executa workflow até o step ATS Analysis
    2. Se pausado: retorna status='paused' com análise ATS
    3. Usuário envia user_input via /workflow/continue
    4. Workflow continua e gera currículo otimizado
    
    Respostas possíveis:
    - status='paused': Requer user_input para continuar
    - status='completed': Workflow finalizado com sucesso
    """
    resume = session.get(Resume, request.resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    try:
        additional_data = {
            "vaga": request.vacancy_text,
            "curriculo": json.dumps(resume.parsed_data, ensure_ascii=False),
            "info_adicional": request.additional_info or ""
        }

        run_output = resume_optimizer_workflow.run(
            input="Otimizar currículo para vaga",
            additional_data=additional_data
        )

        if run_output.is_paused:
            ats_analysis = None
            for step_content in run_output.step_outputs.values():
                if step_content and hasattr(step_content, 'content'):
                    try:
                        ats_analysis = _to_dict(step_content.content)
                        break
                    except:
                        pass

            return WorkflowSessionResponse(
                session_id=run_output.session_id,
                run_id=run_output.run_id,
                status="paused",
                ats_analysis=ats_analysis,
                user_input_required=True,
                message="Workflow pausado! Forneça input via /workflow/continue para continuar."
            )

        return WorkflowSessionResponse(
            session_id=run_output.session_id,
            run_id=run_output.run_id,
            status="completed",
            user_input_required=False,
            message="Currículo otimizado com sucesso!"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no workflow: {str(e)}")


@router.post("/workflow/continue")
async def continue_workflow(
    request: WorkflowContinueRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Continua um workflow pausado fornecendo user_input (HITL).
    
    Fluxo:
    1. Recupera sessão do workflow pelo session_id
    2. Verifica se está pausado
    3. Executa workflow novamente com user_input
    4. Retorna resultado (completo ou pausado)
    """
    try:
        user_input_data = request.user_input.model_dump()
        
        try:
            workflow_session = resume_optimizer_workflow.get_session(request.session_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Sessão não encontrada: {str(e)}")

        if not workflow_session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada.")

        try:
            run_output = workflow_session.get_run(request.run_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Run não encontrado: {str(e)}")

        if not run_output:
            raise HTTPException(status_code=404, detail="Run não encontrado.")
            
        if not run_output.is_paused:
            raise HTTPException(status_code=400, detail="Workflow não está pausado.")

        continued_output = resume_optimizer_workflow.run(
            input="Continuar otimização com feedback do usuário",
            additional_data={"user_input": user_input_data},
            session=workflow_session
        )

        if continued_output.is_paused:
            return {
                "session_id": request.session_id,
                "run_id": continued_output.run_id,
                "status": "paused",
                "message": "Workflow ainda possui steps pendentes."
            }

        optimized_resume = continued_output.get_step_content("Generate Optimized Resume")

        return {
            "session_id": request.session_id,
            "run_id": continued_output.run_id,
            "status": "completed",
            "optimized_resume": optimized_resume.model_dump() if optimized_resume else None,
            "message": "Workflow completado com sucesso!"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao continuar workflow: {str(e)}")