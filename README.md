# AdaptaAi

**AdaptaAi** é um serviço web que utiliza agentes inteligentes para adaptar currículos de forma personalizada para vagas de emprego específicas, aumentando a compatibilidade com requisitos técnicos, comportamentais e sistemas de triagem automática (ATS).

## 🎯 Objetivo do Projeto

O objetivo do AdaptaAi é ajudar candidatos a:

* Ajustar seus currículos de acordo com descrições de vagas reais
* Evidenciar competências e experiências mais relevantes para cada oportunidade
* Melhorar a taxa de aprovação em sistemas de recrutamento automatizados (ATS)
* Economizar tempo no processo de candidatura a múltiplas vagas
* Não adicionar informações falsas ou incorretas sobre o candidato

## 🚀 Funcionalidades Principais

* Upload e análise de currículos (PDF, DOCX)
* Análise automática da descrição da vaga
* Reescrita inteligente do currículo com foco na vaga alvo
* Sugestões de melhorias em linguagem, palavras-chave e estrutura
* Geração de versões múltiplas de um mesmo currículo
* Histórico de currículos adaptados por vaga

## 🧠 Inteligência Artificial

O AdaptaAi utiliza agentes inteligentes baseados em modelos de linguagem para:

* Compreender requisitos técnicos e comportamentais das vagas
* Identificar lacunas entre o currículo e a descrição da vaga
* Reescrever trechos mantendo coerência, clareza e veracidade
* Otimizar o conteúdo para leitura humana e sistemas ATS

## 🛠️ Tecnologias e Frameworks Sugeridos

### Frontend

* **React**
* **TypeScript**
* **Tailwind CSS**
* **Vite**

### Backend
* **Python** com **FastAPI** (alternativa)

### Inteligência Artificial

* **Gemini API** ou modelos LLM compatíveis
* **LangSmith**  para observabilidade
* **Agno** para estruturar fluxo e ferramentas dos agentes

### Banco de Dados

* **PostgreSQL**
* **MongoDB**

### Infraestrutura

* **Docker**
* **AWS**, **GCP** ou **Vercel**
* **CI/CD** com GitHub Actions

## 🔒 Considerações de Segurança e Privacidade

* Criptografia de dados sensíveis
* Exclusão automática de currículos após período definido
* Conformidade com LGPD
* Autenticação via OAuth ou JWT