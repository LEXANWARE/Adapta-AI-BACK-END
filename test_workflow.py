import json
import traceback
from agents.workflow import resume_optimizer_workflow
from agents.utils.hitl_utils import (
    extract_ats_analysis,
    extract_optimized_resume,
    handle_hitl_requirement,
    get_workflow_status,
    extract_workflow_result,
)

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

def handle_hitl(run_response):
    """Função para lidar com HITL no workflow"""
    if hasattr(run_response, 'steps_requiring_user_input') and run_response.steps_requiring_user_input:
        print("\n" + "="*80)
        print("🔴 WORKFLOW PAUSADO - Aguardando input do usuário")
        print("="*80)

        for requirement in run_response.steps_requiring_user_input:
            print(f"\n📌 Step: {requirement.step_name}")
            print(f"📝 Mensagem: {requirement.user_input_message}")
            print("-" * 40)

            # Coleta os inputs conforme schema
            user_data = {}
            for field in requirement.user_input_schema or []:
                field_name = field.name if hasattr(field, 'name') else field.get('name')
                field_type = field.field_type if hasattr(field, 'field_type') else field.get('field_type')
                description = field.description if hasattr(field, 'description') else field.get('description')

                if field_type == "bool":
                    prompt = f"{description} (s/n): "
                    value = input(prompt).strip().lower()
                    user_data[field_name] = value in ['s', 'sim', 'yes', 'y', 'true', '1']
                else:
                    prompt = f"{description}: "
                    user_data[field_name] = input(prompt).strip()

            # ✅ Resolve o requirement usando set_user_input diretamente
            try:
                if hasattr(requirement, 'set_user_input'):
                    requirement.set_user_input(**user_data)
                    print(f"\n✅ Input registrado: {user_data}")
                else:
                    print(f"\n❌ Requirement não tem método set_user_input")
                    return False
            except Exception as e:
                print(f"\n❌ Erro ao registrar input: {e}")
                return False

        print("\n⏩ Retomando execução do workflow...")
        return True
    return False

def extract_final_result(run_response):
    """Extrai o resultado final do workflow usando função utilitária."""
    return extract_workflow_result(run_response)

if __name__ == "__main__":
    print("="*80)
    print("🚀 INICIANDO WORKFLOW DE OTIMIZAÇÃO DE CURRÍCULO")
    print("="*80)

    try:
        # Executa o workflow
        run_response = resume_optimizer_workflow.run(
            input="Otimize meu currículo para esta vaga",
            additional_data={
                'curriculo': curriculo_texto,
                'vaga': descricao_vaga,
                'info_adicional': input_usuario_enrich
            }
        )

        # Loop para lidar com múltiplas pausas (se houver)
        while True:
            status = get_workflow_status(run_response)
            print(f"\n📊 Status do workflow: {status}")
            
            if status != "paused":
                break
                
            # Processa HITL
            if handle_hitl(run_response):
                # Continua execução após HITL
                run_response = resume_optimizer_workflow.continue_run(
                    run_response=run_response,
                    step_requirements=run_response.step_requirements if hasattr(run_response, 'step_requirements') else None,
                )
            else:
                break

        # Exibe resultado final
        print("\n" + "="*80)
        print("✅ WORKFLOW CONCLUÍDO")
        print("="*80)

        final_content = extract_final_result(run_response)

        if final_content:
            print("\n📄 RESULTADO FINAL:")
            print("-" * 40)
            content_str = str(final_content)
            # Se for muito grande, mostra os primeiros 2000 caracteres
            if len(content_str) > 2000:
                print(content_str[:2000])
                print(f"\n... (conteúdo truncado, total de {len(content_str)} caracteres)")
            else:
                print(content_str)

            # Tenta salvar o resultado em arquivo
            try:
                output_file = "currículo_otimizado.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content_str)
                print(f"\n💾 Resultado salvo em: {output_file}")
            except Exception as e:
                print(f"\n⚠️  Não foi possível salvar arquivo: {e}")
        else:
            print("\n⚠️  Nenhum conteúdo retornado pelo workflow")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        traceback.print_exc()