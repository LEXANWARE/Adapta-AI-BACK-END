import os
import json
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("ERRO: Cadê a GOOGLE_API_KEY no .env?")
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
