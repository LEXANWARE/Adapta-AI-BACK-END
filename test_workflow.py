import json
import traceback
import logging
from agents.workflow import (
    ResumeOptimizerWorkflow, 
    ResumeQualityWorkflow, 
    AtsCheckWorkflow
)

# Configura logging simplificado
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

curriculo_texto = """LUCAS MELO DE SOUZA
Telefone: +55 (85) 99968-6875 | E-mail: lucasouza280604@gmail.com

Github: lucas-twygz | LinkedIn: Lucas Melo de Souza

Educação

Universidade de Fortaleza (UNIFOR) – Jan. 2022 – Est. Jun. 2026
Bacharelando em Ciência da Computação

Programação Web, Mobile e Orientada a Objetos

Banco de Dados, Engenharia de Software

Metodologias Ágeis

Experiência Profissional

APM TERMINALS / A.P. Moller-Maersk – Presencial
Automation, Development and Network IT Apprentice – Jun. 2025 – Atualmente

Desenvolvi um app Android em Kotlin e dashboard web com Python/Flask para monitoramento de rede.

Realizei manutenção e configuração de dispositivos móveis e pontos de acesso.

Participei de reuniões e suporte internacional em inglês.

EMPREENDIMENTOS PAGUE MENOS – Presencial
Estagiário de Governança de TI e Desenvolvimento – Fev. 2025 – Jun. 2025

Desenvolvi uma aplicação em React para automatizar geração de documentos.

Auxiliei no fluxo de notas fiscais e envio de equipamentos.

Dei suporte na implementação de processos internos.

UNIVERSIDADE DE FORTALEZA (UNIFOR) – Híbrido
Extensionista Desenvolvedor de Aplicações Mobile – Fev. 2025 – Set. 2025

Desenvolvi aplicações web e mobile com React e Kotlin.

Participei de reuniões de equipe e definições de melhorias.

Projetos

TCC – Truth Chrome Checker

Extensão para Chrome que analisa a veracidade de notícias usando Readability.js e APIs externas, interface em HTML, CSS e JavaScript.

VaultGame – E-commerce

Plataforma de e-commerce para jogos em React + Node.js e Python/Django, com gerenciamento de catálogo e carrinho de compras.

Hard Skills

Linguagens: Python, JavaScript/Node.js, Kotlin

Frontend: React, HTML/CSS, Bootstrap

Backend: Python, Node.js, Flask, Django

Banco de Dados: MySQL, SQLite

Mobile: Kotlin, Android Nativo

Documentação: Markdown

Infraestrutura/DevOps: Git/Github, Docker

Idiomas: Inglês (Fluente C1), Português (Nativo)"""

input_usuario_enrich = """informações adicionais / Fit para BTG:

Experiência com desenvolvimento de aplicações financeiras e ferramentas internas de automação.

Noções de Cloud Computing (AWS) e integração de APIs RESTful para sistemas corporativos.

Conhecimento básico em mensageria na minha experencia na  apm terminals e arquitetura de microsserviços.

Experiência em ambientes colaborativos com metodologias ágeis, focando em resultados e qualidade do código.

Forte raciocínio lógico, comunicação clara e inglês fluente, com disponibilidade para trabalho híbrido em São Paulo."""

descricao_vaga = """O Banco BTG Pactual é o maior comercializador de energia elétrica do Brasil, com operações em expansão para a América Latina e Europa. Buscamos profissionais comprometidos, com sólida formação técnica e interesse genuíno em atuar em projetos que exigem responsabilidade, precisão e impacto direto no mercado financeiro.

No time de IT Energy, você terá papel fundamental na evolução dos sistemas que suportam operações críticas do banco, incluindo custódia, faturamento e integrações com sistemas internos e externos. Cada entrega é realizada com rigor e contribui para a excelência, agilidade e resiliência das operações do BTG Pactual.

O Que Você Vai Encontrar

Ambiente colaborativo, com forte interface entre áreas de negócio, operações, finanças, comercial, portfólio e projetos.
Projetos construídos em equipe, valorizando comunicação, proatividade e aprendizado contínuo.
Stack tecnológica moderna: Python, AWS, Postgres. Não exigimos domínio total, mas sim disposição para aprender e evoluir junto com o time.
Desafios de escala e flexibilidade, com oportunidades de atuar em novas funcionalidades, expansão internacional e novos produtos.
Espaço para extrair insights dos dados e gerar impacto direto no negócio.

Buscamos Pessoas Que

Entregam com excelência e senso de urgência, sem abrir mão da qualidade.
Compreendem o negócio e o impacto do próprio trabalho.
Valorizam trabalho em equipe, comunicação clara e aprendizado constante.
Tenham disponibilidade para trabalho presencial em modalidade híbrida no nosso escritório de SP.

Requisitos Essenciais

Formação em Engenharia, Ciência da Computação ou áreas correlatas (formado ou em fase final).
Fit cultural com o BTG.
Boa comunicação e raciocínio lógico apurado.
Proatividade e vontade de aprender.
Conhecimento em linguagens orientadas a objeto (Python, C#, Java etc.).
Noções de SQL, arquitetura de microsserviços e mensageria.
Familiaridade com Git e versionamento de código.

Diferenciais Valorizados

Experiência com serviços em nuvem (AWS ou Azure).
Sólida experiência em desenvolvimento Web com Python.
Interesse ou vivência no mercado financeiro.
Experiência com Front-end (React).

Benefícios

Participação nos Lucros e Resultados (PLR);
Remuneração variável por performance (bônus anual);
Auxílio Alimentação e Refeição;
Plano Médico;
Plano Odontológico;
Auxílio Creche/Babá;
Vale Transporte;
WellHub;
TotalPass;
Programa de Apoio Pessoal (EAP);
Planos por adesão como Previdência Privada e Seguro de Vida;
Desconto em Farmácia;
Programa de Nutrição;
Programa de Gestantes;
Licença Maternidade e Paternidade Estendida – empresa Cidadã."""


def test_full_pipeline():
    """
    Executa os três workflows de forma independente e estruturada.
    """
    
    # 1. TESTE DE QUALIDADE (Auditores Humanos)
    print("\n" + "="*50)
    print("🔍 INICIANDO AUDITORIA DE QUALIDADE")
    print("="*50)
    
    try:
        quality_wf = ResumeQualityWorkflow()
        q_response = quality_wf.run(raw_resume=curriculo_texto)
        
        if q_response and q_response.content:
            q_data = q_response.content
            
            # Verifica se q_data é o objeto esperado antes de acessar atributos
            if hasattr(q_data, "presentation_score"):
                print(f"✅ Score de Apresentação: {q_data.presentation_score}/100")
                print(f"📝 Feedback: {q_data.presentation_feedback}")
                
                if q_data.language_issues:
                    print("\nErros Linguísticos Encontrados:")
                    for issue in q_data.language_issues:
                        print(f"  - [{issue.category}]: '{issue.original_text}' -> {issue.suggestion}")
                
                with open("qualidade.json", "w", encoding="utf-8") as f:
                    json.dump(q_data.model_dump(), f, indent=4, ensure_ascii=False)
                    print("\n💾 Arquivo 'qualidade.json' salvo com sucesso.")
            else:
                print(f"⚠️ Resposta de qualidade não estruturada como esperado: {type(q_data)}")
                print(f"Conteúdo: {q_data}")
    except Exception as e:
        print(f"❌ Falha no teste de qualidade: {str(e)}")

    
    # 2. TESTE DE OTIMIZAÇÃO (Melhoria Estratégica)
    print("\n" + "="*50)
    print("🚀 INICIANDO OTIMIZAÇÃO DE CURRÍCULO")
    print("="*50)
    
    try:
        opt_wf = ResumeOptimizerWorkflow()

        # Passamos os inputs via additional_data para que os steps acessem
        opt_response = opt_wf.run(
            vaga=descricao_vaga,
            curriculo=curriculo_texto,
            info_adicional=input_usuario_enrich
        )
        
        if opt_response and opt_response.content:
            # Aqui opt_response.content já é um objeto ResumeScheme
            optimized_resume = opt_response.content
            if hasattr(optimized_resume, "basics"):
                print(f"✅ Currículo Otimizado Gerado para: {optimized_resume.basics.name}")
                print(f"📈 Resumo Proposto: {optimized_resume.basics.summary[:100]}...")
                
                # Salva o resultado para conferência
                with open("curriculo_otimizado.json", "w", encoding="utf-8") as f:
                    json.dump(optimized_resume.model_dump(), f, indent=4, ensure_ascii=False)
                    print("\n💾 Arquivo 'curriculo_otimizado.json' salvo com sucesso.")
            else:
                print(f"⚠️ Currículo otimizado não estruturado como esperado: {type(optimized_resume)}")
    except Exception as e:
        print(f"❌ Falha no teste de otimização: {str(e)}")

    # 3. TESTE ATS (Score de Robôs)
    print("\n" + "="*50)
    print("📊 ANÁLISE DE COMPATIBILIDADE ATS")
    print("="*50)
    
    try:
        ats_wf = AtsCheckWorkflow()
        # Analisamos o currículo original contra a vaga
        ats_response = ats_wf.run(vaga=descricao_vaga, curriculo=curriculo_texto)
        
        if ats_response and ats_response.content:
            ats_data = ats_response.content
            if hasattr(ats_data, "ats_score"):
                print(f"🤖 Score ATS: {ats_data.ats_score}/100")
                print(f"✅ Keywords Encontradas: {len(ats_data.matched_keywords)}")
                print(f"❌ Keywords Ausentes: {len(ats_data.missing_keywords)}")
                
                print("\nTop Recomendações ATS:")
                for rec in ats_data.recommendations[:3]:
                    print(f"  - {rec}")
                
                with open("ats.json", "w", encoding="utf-8") as f:
                    json.dump(ats_data.model_dump(), f, indent=4, ensure_ascii=False)
                    print("\n💾 Arquivo 'ats.json' salvo com sucesso.")
            else:
                print(f"⚠️ Análise ATS não estruturada como esperado: {type(ats_data)}")
    except Exception as e:
        print(f"❌ Falha no teste ATS: {str(e)}")
        print("\n💾 Arquivo 'ats.json' salvo com sucesso.")

if __name__ == "__main__":
    try:
        test_full_pipeline()
    except Exception as e:
        logger.error(f"Erro fatal no teste: {str(e)}")
        traceback.print_exc()