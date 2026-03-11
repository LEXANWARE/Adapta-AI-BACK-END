import os
import json
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("ERRO: Cadê a GOOGLE_API_KEY no .env?")
    exit(1)

try:
    from agents.models import resume_agent, resume_upgrade_agent, resume_enricher_agent
except ImportError as e:
    print(f"Erro de importação: {e}")
    exit(1)

class PDFResume(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Times', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_section_title(self, title):
        self.ln(5)
        self.set_font('Times', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, title.upper(), 0, 1, 'L')
        self.line(self.get_x(), self.get_y(), 200, self.get_y()) 
        self.ln(2)

    def add_entry_header(self, left_text, right_text, is_bold=True):
        self.set_font('Times', 'B' if is_bold else '', 11)
        y = self.get_y()
        self.cell(130, 6, left_text, 0, 0, 'L')
        self.cell(0, 6, right_text, 0, 1, 'R')

    def add_role_subheader(self, role, location=None):
        self.set_font('Times', 'I', 11)
        text = role
        if location:
            text += f" -- {location}"
        self.cell(0, 6, text, 0, 1, 'L')

    def add_bullet_point(self, text):
        self.set_font('Times', '', 10)
        self.cell(5, 5, chr(149), 0, 0, 'R') 
        self.multi_cell(0, 5, text)
        self.ln(1)

def imprimir_json(titulo, response):
    print(f"\n {titulo}:")
    print("-" * 40)
    if response.content and not isinstance(response.content, str):
        print(response.content.model_dump_json(indent=2))
    else:
        print(response.content) 
    print("-" * 40)

def salvar_json_final(dict_final, arquivo='curriculo.json'):
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dict_final, f, ensure_ascii=False, indent=2)
    print(f"JSON final salvo em {arquivo}")

def gerar_pdf(json_data, arquivo_saida):
    pdf = PDFResume()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    basics = json_data.get('basics', {})
    work = json_data.get('work', [])
    education = json_data.get('education', [])
    skills = json_data.get('skills', [])
    
    pdf.set_font('Times', 'B', 16)
    pdf.cell(0, 8, basics.get('name', '').upper(), 0, 1, 'C')
    
    pdf.set_font('Times', '', 10)
    
    email = basics.get('email', '')
    phone = basics.get('phone', '')
    contact_line = f"Telefone: {phone} | E-mail: {email}"
    pdf.cell(0, 5, contact_line, 0, 1, 'C', link=f"mailto:{email}")
    
    profiles = basics.get('profiles', [])
    links_text = []
    if profiles:
        for p in profiles:
            links_text.append(f"{p.get('network')}: {p.get('url')}")
    
    if links_text:
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 5, " | ".join(links_text), 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)

    pdf.ln(5)

    if education:
        pdf.add_section_title("EDUCAÇÃO")
        for edu in education:
            school = edu.get('institution', '')
            start = edu.get('startDate', '')
            end = edu.get('endDate', '')
            date_str = f"{start} - {end}"
            
            pdf.add_entry_header(school, date_str)
            
            degree = f"{edu.get('studyType', '')} em {edu.get('area', '')}"
            pdf.add_role_subheader(degree)
            pdf.ln(2)

    if work:
        pdf.add_section_title("EXPERIÊNCIA PROFISSIONAL")
        for job in work:
            company = job.get('name', '')
            start = job.get('startDate', '')
            end = job.get('endDate', '')
            date_str = f"{start} - {end}"
            
            pdf.add_entry_header(company, date_str)
            pdf.add_role_subheader(job.get('position', ''))
            
            highlights = job.get('highlights', [])
            if highlights:
                for point in highlights:
                    pdf.add_bullet_point(point)
            
            pdf.ln(3)

    if skills:
        pdf.add_section_title("HARD SKILLS")
        pdf.set_font('Times', '', 10)
        
        for skill in skills:
            category = skill.get('name', '')
            keywords = ", ".join(skill.get('keywords', []))
            
            pdf.set_font('Times', 'B', 10)
            pdf.write(5, f"{category}: ")
            
            pdf.set_font('Times', '', 10)
            pdf.write(5, keywords)
            pdf.ln(6)

    pdf.output(arquivo_saida)
    print(f"PDF Profissional salvo em: {arquivo_saida}")

def teste_fluxo_completo():
    print("\n --- INICIANDO SIMULAÇÃO DO MVP ---")

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

    print("\n LENDO O PDF (resume_agent)...")
    json_inicial = resume_agent.run(curriculo_texto_pdf)
    dict_inicial = json_inicial.content.model_dump()
    imprimir_json("CURRÍCULO EXTRAÍDO DO PDF", json_inicial)

    print("\n ADICIONANDO DADOS DO USUÁRIO (resume_enricher_agent)...")
    prompt_enrich = f"""
    CURRÍCULO ATUAL (JSON):
    {dict_inicial}

    INFORMAÇÕES ADICIONAIS DO USUÁRIO:
    {input_usuario_enrich}
    """
    json_enriquecido = resume_enricher_agent.run(prompt_enrich)
    dict_enriquecido = json_enriquecido.content.model_dump()
    imprimir_json("CURRÍCULO ENRIQUECIDO", json_enriquecido)

    print("\n ADAPTANDO À VAGA (resume_upgrade_agent)...")
    prompt_adaptacao = f"""
    A VAGA É ESTA:
    {descricao_vaga}

    O CURRÍCULO ORIGINAL É ESTE:
    {dict_enriquecido}

    Reescreva o currículo mantendo a verdade, mas destacando pontos que conectem com a vaga.
    """
    json_final = resume_upgrade_agent.run(prompt_adaptacao)
    dict_final = json_final.content.model_dump()
    imprimir_json("CURRÍCULO FINAL (PRONTO PRO ENVIO)", json_final)

    salvar_json_final(dict_final, 'curriculo.json')

    gerar_pdf(dict_final, 'curriculo_completo.pdf')
    

if __name__ == "__main__":
    teste_fluxo_completo()