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
from app.services.workflow_service import workflow_session_manager
from app.api.v1.endpoints.schemas.resumes import (
    ResumeSummary,
    ATSAnalysis,
    WorkflowOptimizeRequest,
    WorkflowSessionDetails,
    WorkflowSessionList,
    WorkflowSessionInfo,
    WorkflowContinueRequest,
    HitlContinueResponse,
    WorkflowStepRequirement,
    UserInputFieldSchema,
    AdaptFullResponse,
)
from agents.utils.hitl_utils import (
    extract_ats_analysis,
    extract_optimized_resume,
    get_workflow_status,
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


def extract_text_from_pdf(file: UploadFile) -> str:
    """Extrai texto de um arquivo PDF usando pypdf."""
    pdf_reader = PdfReader(BytesIO(file.file.read()))
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def _convert_step_requirements(step_requirements) -> List[WorkflowStepRequirement]:
    """Converte StepRequirements do Agno para schema Pydantic."""
    if not step_requirements:
        return []
    
    result = []
    for req in step_requirements:
        # Converte user_input_schema
        schema_items = []
        if hasattr(req, 'user_input_schema') and req.user_input_schema:
            for item in req.user_input_schema:
                if hasattr(item, '__dict__'):
                    schema_items.append(UserInputFieldSchema(
                        name=getattr(item, 'name', 'unknown'),
                        field_type=getattr(item, 'field_type', 'str'),
                        description=getattr(item, 'description', None),
                        required=getattr(item, 'required', True),
                    ))
                elif isinstance(item, dict):
                    schema_items.append(UserInputFieldSchema(**item))
        
        result.append(WorkflowStepRequirement(
            step_id=req.step_id,
            step_name=req.step_name,
            requires_user_input=req.requires_user_input,
            user_input_message=req.user_input_message,
            user_input_schema=schema_items,
            is_resolved=req.is_resolved,
        ))
    
    return result


router = APIRouter()

# ==================== Endpoints de Currículos ====================

@router.post("/", status_code=201)
async def create_resume(
    file: UploadFile = File(..., description="Arquivo PDF do currículo"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Faz upload de um currículo em PDF e extrai seu texto.

    O currículo é salvo no banco de dados para posterior otimização.
    Use o `id` retornado para chamar `/optimize-with-workflow`.
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
        "raw_text": resume.raw_text,
        "message": "Currículo enviado com sucesso! Use o id para otimizar."
    }


@router.get("/", response_model=List[ResumeSummary])
async def list_resumes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os currículos do usuário."""
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
    """Obtém detalhes de um currículo específico."""
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
    """Deleta um currículo."""
    resume = session.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")

    session.delete(resume)
    session.commit()

    return {"message": "Currículo deletado com sucesso!"}


# ==================== Endpoints de Workflow HITL ====================

@router.post("/optimize-with-workflow", response_model=WorkflowSessionDetails)
async def optimize_with_workflow(
    request: WorkflowOptimizeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Executa o workflow completo de otimização com HITL.

    Fluxo:
    1. Executa workflow até o step ATS Analysis
    2. Se pausado: retorna status='paused' com análise ATS e steps_requiring_user_input
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
            "curriculo": json.dumps(resume.parsed_data if resume.parsed_data else resume.raw_text, ensure_ascii=False),
            "info_adicional": request.additional_info or "",
            "resume_id": request.resume_id,
        }

        # Inicia workflow via session manager
        run_response, wf_session = workflow_session_manager.start_workflow(
            input_text="Otimizar currículo para vaga",
            additional_data=additional_data,
            user_id=current_user.id,
            resume_id=request.resume_id,
        )

        # Extrai análise ATS e currículo otimizado
        step_outputs = run_response.step_outputs if hasattr(run_response, 'step_outputs') else {}
        ats_analysis_dict = extract_ats_analysis(step_outputs)
        optimized_resume = extract_optimized_resume(step_outputs)

        # Converte ATS analysis para schema
        ats_analysis = None
        if ats_analysis_dict:
            try:
                ats_analysis = ATSAnalysis(**ats_analysis_dict)
            except Exception:
                pass

        # Determina status e mensagem
        status = get_workflow_status(run_response)
        message = (
            "Workflow pausado! Revise a análise ATS e decida se deseja prosseguir."
            if status == "paused"
            else "Currículo otimizado com sucesso!"
        )

        # Converte step requirements
        steps_requiring_input = _convert_step_requirements(
            run_response.steps_requiring_user_input if hasattr(run_response, 'steps_requiring_user_input') else None
        )

        return WorkflowSessionDetails(
            session_id=wf_session.session_id,
            run_id=wf_session.run_id,
            status=status,  # type: ignore
            ats_analysis=ats_analysis,
            optimized_resume=optimized_resume,
            steps_requiring_user_input=steps_requiring_input,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no workflow: {str(e)}")


@router.post("/workflow/continue", response_model=WorkflowSessionDetails)
async def continue_workflow(
    request: WorkflowContinueRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Continua um workflow pausado fornecendo user_input (HITL).

    Fluxo:
    1. Recupera sessão do workflow
    2. Verifica se está pausada
    3. Resolve step requirements com user_input
    4. Continua execução do workflow
    5. Retorna resultado

    Se user_proceeds=False, o workflow é cancelado.
    """
    try:
        # Recupera sessão
        wf_session = workflow_session_manager.get_session(request.session_id)
        if not wf_session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada.")

        # Verifica se é do usuário atual
        if wf_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acesso não permitido.")

        # Verifica status
        if wf_session.status != "paused":
            raise HTTPException(status_code=400, detail=f"Workflow não está pausado: {wf_session.status}")

        # Verifica se usuário deseja cancelar
        user_proceeds = request.user_input.get("user_proceeds", True)
        if not user_proceeds:
            workflow_session_manager.cancel_workflow(request.session_id)
            return WorkflowSessionDetails(
                session_id=request.session_id,
                run_id=request.run_id,
                status="cancelled",  # type: ignore
                message="Otimização cancelada pelo usuário.",
            )

        # Continua workflow
        continued_response, updated_session = workflow_session_manager.continue_workflow(
            session_id=request.session_id,
            user_input=request.user_input,
        )

        # Extrai resultados
        step_outputs = continued_response.step_outputs if hasattr(continued_response, 'step_outputs') else {}
        ats_analysis_dict = extract_ats_analysis(step_outputs)
        optimized_resume = extract_optimized_resume(step_outputs)

        # Converte ATS analysis
        ats_analysis = None
        if ats_analysis_dict:
            try:
                ats_analysis = ATSAnalysis(**ats_analysis_dict)
            except Exception:
                pass

        # Determina status
        status = get_workflow_status(continued_response)
        message = (
            "Workflow completado com sucesso!"
            if status == "completed"
            else "Workflow ainda possui steps pendentes."
        )

        return WorkflowSessionDetails(
            session_id=updated_session.session_id,
            run_id=updated_session.run_id,
            status=status,  # type: ignore
            ats_analysis=ats_analysis,
            optimized_resume=optimized_resume,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao continuar workflow: {str(e)}")


@router.get("/workflow/sessions", response_model=WorkflowSessionList)
async def list_workflow_sessions(
    current_user: User = Depends(get_current_user)
):
    """
    Lista todas as sessões de workflow do usuário.

    Retorna sessões em todos os estados: running, paused, completed, cancelled.
    """
    try:
        sessions = workflow_session_manager.get_user_sessions(current_user.id)
        
        session_list = [
            WorkflowSessionInfo(
                session_id=s.session_id,
                run_id=s.run_id,
                status=s.status,  # type: ignore
                created_at=s.created_at.isoformat(),
                resume_id=s.resume_id,
            )
            for s in sessions
        ]
        
        return WorkflowSessionList(sessions=session_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar sessões: {str(e)}")


@router.get("/workflow/{session_id}", response_model=WorkflowSessionDetails)
async def get_workflow_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtém detalhes de uma sessão de workflow específica.

    Retorna:
    - status: 'paused', 'completed', 'cancelled', ou 'running'
    - ats_analysis: Análise ATS completa (se disponível)
    - optimized_resume: Currículo otimizado (se completado)
    - steps_requiring_user_input: Steps pendentes (se pausado)
    """
    try:
        wf_session = workflow_session_manager.get_session(session_id)
        if not wf_session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada.")

        # Verifica se é do usuário atual
        if wf_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acesso não permitido.")

        run_response = wf_session.last_run_response
        if not run_response:
            raise HTTPException(status_code=404, detail="Run não encontrado.")

        # Extrai resultados
        step_outputs = run_response.step_outputs if hasattr(run_response, 'step_outputs') else {}
        ats_analysis_dict = extract_ats_analysis(step_outputs)
        optimized_resume = extract_optimized_resume(step_outputs)

        # Converte ATS analysis
        ats_analysis = None
        if ats_analysis_dict:
            try:
                ats_analysis = ATSAnalysis(**ats_analysis_dict)
            except Exception:
                pass

        # Converte step requirements
        steps_requiring_input = _convert_step_requirements(
            run_response.steps_requiring_user_input if hasattr(run_response, 'steps_requiring_user_input') else None
        )

        return WorkflowSessionDetails(
            session_id=wf_session.session_id,
            run_id=wf_session.run_id,
            status=wf_session.status,  # type: ignore
            ats_analysis=ats_analysis,
            optimized_resume=optimized_resume,
            steps_requiring_user_input=steps_requiring_input,
            message="Sessão recuperada com sucesso.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar sessão: {str(e)}")


@router.post("/workflow/{session_id}/cancel")
async def cancel_workflow_session(
    session_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cancela uma sessão de workflow em pausa (HITL - usuário opta por não prosseguir).

    Esta endpoint marca o workflow como cancelado, impedindo continuidade.
    """
    try:
        wf_session = workflow_session_manager.get_session(session_id)
        if not wf_session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada.")

        # Verifica se é do usuário atual
        if wf_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acesso não permitido.")

        # Cancela sessão
        updated_session = workflow_session_manager.cancel_workflow(session_id)

        # Atualiza currículo no banco (remove se existir)
        if wf_session.resume_id:
            resume = session.get(Resume, wf_session.resume_id)
            if resume and resume.user_id == current_user.id:
                # Marca como cancelado no parsed_data
                resume.parsed_data = {"cancelled": True, "reason": "Usuário cancelou otimização"}
                session.add(resume)
                session.commit()

        return {
            "session_id": session_id,
            "status": "cancelled",
            "message": "Workflow cancelado pelo usuário."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar workflow: {str(e)}")


# ==================== Endpoint Adapt-Full (Upload + Otimização) ====================

@router.post("/adapt-full", response_model=AdaptFullResponse)
async def adapt_resume_full(
    file: UploadFile = File(..., description="Arquivo PDF do currículo"),
    vacancy_text: str = Form(..., description="Descrição da vaga"),
    additional_info: Optional[str] = Form(None, description="Informações adicionais"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Fluxo completo: Upload do PDF + Otimização com workflow.

    1. Extrai texto do PDF
    2. Salva currículo no banco
    3. Executa workflow de otimização
    4. Retorna currículo otimizado em JSON ou análise ATS para revisão (HITL)

    Respostas possíveis:
    - status='completed': Currículo otimizado com sucesso
    - status='paused': Workflow pausado, requer confirmação do usuário
    """
    from fastapi import Form
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    try:
        raw_text = extract_text_from_pdf(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")

    if not raw_text:
        raise HTTPException(status_code=400, detail="PDF vazio ou não foi possível extrair texto.")

    # Salva currículo no banco
    resume = Resume(
        user_id=current_user.id,
        raw_text=raw_text,
        parsed_data={}
    )

    session.add(resume)
    session.commit()
    session.refresh(resume)

    # Executa workflow de otimização
    try:
        additional_data = {
            "vaga": vacancy_text,
            "curriculo": raw_text,
            "info_adicional": additional_info or "",
            "resume_id": resume.id,
        }

        run_response, wf_session = workflow_session_manager.start_workflow(
            input_text="Otimizar currículo para vaga",
            additional_data=additional_data,
            user_id=current_user.id,
            resume_id=resume.id,
        )

        # Extrai análise ATS e currículo otimizado
        step_outputs = run_response.step_outputs if hasattr(run_response, 'step_outputs') else {}
        ats_analysis_dict = extract_ats_analysis(step_outputs)
        optimized_resume = extract_optimized_resume(step_outputs)

        # Converte ATS analysis
        ats_analysis = None
        if ats_analysis_dict:
            try:
                ats_analysis = ATSAnalysis(**ats_analysis_dict)
            except Exception:
                pass

        # Verifica se workflow está pausado
        status = get_workflow_status(run_response)
        if status == "paused" and not optimized_resume:
            return AdaptFullResponse(
                status="paused",
                ats_analysis=ats_analysis,
                session_id=wf_session.session_id,
                run_id=wf_session.run_id,
                message="Workflow pausado. Revise a análise ATS e confirme para prosseguir."
            )

        # Se chegou aqui, workflow completou
        if optimized_resume:
            resume.parsed_data = optimized_resume
            session.add(resume)
            session.commit()

            return AdaptFullResponse(
                status="completed",
                optimized_resume=optimized_resume,
                message="Currículo otimizado com sucesso!"
            )
        else:
            raise HTTPException(status_code=500, detail="Não foi possível gerar o currículo otimizado.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no workflow de otimização: {str(e)}")