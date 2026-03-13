from agents.workflow import resume_optimizer_workflow
from agents.utils.pdf import imprimir_json, salvar_json_final, gerar_pdf

curriculo_texto_pdf = """LUCAS MELO DE SOUZA
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

Documentação: LaTeX, Markdown

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

resume_optimizer_workflow.run(
    input="Otimize meu currículo para esta vaga",
    additional_data={
        'curriculo': curriculo_texto_pdf,
        'vaga': descricao_vaga,
        'info_adicional': input_usuario_enrich
    }
)