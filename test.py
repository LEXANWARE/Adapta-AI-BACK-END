import os
from dotenv import load_dotenv

load_dotenv()

try:
    from agents.models import resume_agent, vacancy_agent
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    exit(1)

def imprimir_resposta(nome_teste, response):
    print(f"\n✅ RESULTADO DO {nome_teste}:")
    print("-" * 30)
    
    # VERIFICAÇÃO DE SEGURANÇA
    if isinstance(response.content, str):
        print("⚠️ AVISO: A IA retornou texto puro (falhou em gerar JSON):")
        print(response.content)
    else:
        # Se for um objeto Pydantic, imprime bonito
        print(response.content.model_dump_json(indent=2))
    print("-" * 30)

def testar_resume_parser():
    print("\n🤖 --- TESTE 1: AGENTE DE CURRÍCULO ---")
    texto_curriculo = """
    Carlos Henrique Silva
    Engenheiro de Software | Python
    Contato: carlos@email.com
    Resumo: Dev apaixonado com 5 anos de exp.
    """
    try:
        print("⏳ Enviando para a IA...")
        response = resume_agent.run(texto_curriculo)
        imprimir_resposta("CURRÍCULO", response)
    except Exception as e:
        print(f"❌ ERRO: {e}")

def testar_vacancy_parser():
    print("\n🤖 --- TESTE 2: AGENTE DE VAGAS ---")
    vaga = "Vaga: Dev Python. Requisitos: FastAPI e AWS."
    try:
        print("⏳ Analisando vaga...")
        response = vacancy_agent.run(vaga)
        imprimir_resposta("VAGA", response)
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  AVISO: Sem OPENROUTER_API_KEY no .env")
    
    testar_resume_parser()
    testar_vacancy_parser()