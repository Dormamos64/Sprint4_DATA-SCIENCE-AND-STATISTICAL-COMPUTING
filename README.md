
*PLATAFORMA DE INTELIGÊNCIA EM VENDAS & CUSTOMER SUCCESS - TOTVS

FIAP - Sprint 4 Challenge

===============================================================================



Visão Geral

-------------------------------------------------------------------------------

Esta solução é um protótipo de Data Science e Inteligência Comercial desenvolvido

em Python e Streamlit para automatizar a análise de transcrições de reuniões de 

Vendas e Customer Success (CS) da TOTVS.



O sistema processa reuniões brutas (formatos .txt / .md), extrai indicadores

estratégicos de negócio (Health Score, Risco de Churn, Dores do Cliente, Cross-Sell)

e fornece coaching individualizado para os vendedores com análise de tempo de fala.





Funcionalidades Principais

-------------------------------------------------------------------------------

1. Processamento Individual & em Lote:

   - Análise detalhada de uma única reunião ou lote automatizado de todas as

     transcrições presentes na pasta /transcricoes.



2. Indicadores Comerciais & CS (LLM Extraction):

   - Identificação do Cliente e Participantes.

   - Diagnóstico do Humor da Conta (Empolgado, Satisfeito, Cético, Irritado, Ansioso, Neutro).

   - Cálculo de Health Score (0 a 100) e Alerta Prévio de Churn.

   - Mapeamento de Dores Principais, Concorrentes Mencionados e Oportunidades de Cross-Sell.



3. Coaching de Vendas & Share of Voice:

   - Diagnóstico comportamental com Pontos Fortes e Sugestões Práticas de Melhoria.

   - Cálculo automático da proporção do tempo de fala entre Vendedor e Cliente.



4. Painel Consolidador & Filtros Estratégicos:

   - Dashboard com distribuição de humor e motivos de insatisfação.

   - Filtros de navegação entre Reuniões Boas (Sucesso/Expansão) vs. Ruins (Risco/Insatisfação).



5. Exportação de Outcomes:

   - Geração automática de arquivos estruturados na pasta /outcomes (.csv e .md).

   - Botão para download direto do relatório consolidado em formato CSV.





Estrutura do Projeto

-------------------------------------------------------------------------------

.

├── app.py                   # Aplicação principal do Dashboard em Streamlit

├── requirements.txt         # Dependências do projeto Python

├── .env                     # Variáveis de ambiente e chaves de API (não versionado)

├── .gitignore               # Arquivos e pastas ignorados pelo Git

├── README.txt               # Documentação técnica e guia do projeto

├── transcricoes/            # Pasta com os arquivos brutos de reuniões (.txt e .md)

└── outcomes/                # Pasta onde são salvos os relatórios gerados (.csv e .md)





Requisitos Técnicos

-------------------------------------------------------------------------------

- Python 3.10 ou superior

- Chave de API ativa na Groq Cloud (ou Google AI Studio)





Instalação e Configuração

-------------------------------------------------------------------------------

1. Clonar o repositório e navegar até a pasta raiz:

   cd projeto-totvs-sprint4



2. Criar e ativar um ambiente virtual (recomendado):

   python -m venv venv

   

   # No Windows (PowerShell):

   .\venv\Scripts\Activate.ps1

   

   # No Linux/macOS:

   source venv/bin/activate



3. Instalar as dependências:

   pip install -r requirements.txt



4. Configurar as variáveis de ambiente:

   Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo:



   GROQ_API_KEY=gsk_sua_chave_groq_aqui

   GROQ_MODEL_ID=openai/gpt-oss-20b



   (Nota: Se preferir utilizar o Gemini, configure GEMINI_API_KEY e GEMINI_MODEL_ID).





Como Executar a Aplicação

-------------------------------------------------------------------------------

1. Certifique-se de que existem arquivos de transcrição na pasta `/transcricoes`.



2. Execute o comando do Streamlit no terminal:

   streamlit run app.py



   (Caso ocorra algum problema de caminho no Windows, utilize: python -m streamlit run app.py)



3. O navegador abrirá automaticamente no endereço: `http://localhost:8501`.





Instruções de Uso na Interface

-------------------------------------------------------------------------------

- Modo de Visão "Análise Detalhada (Única)":

  Selecione um arquivo de conversa no menu lateral e clique em "Processar Reunião Selecionada".

  O painel exibirá as métricas do cliente, feedback do vendedor, sugestões e gráfico de fala.



- Modo de Visão "Dashboard do Portfólio (Global)":

  Clique no botão "Processar Lote Completo" para analisar todas as transcrições da pasta.

  Após o processamento, utilize o filtro do menu lateral para alternar entre "Reuniões Boas" 

  e "Reuniões Ruins", visualize a tabela consolidada e faça o download do CSV.





Tecnologias Utilizadas

-------------------------------------------------------------------------------

- Linguagem: Python 3

- Dashboard & Interface: Streamlit

- Manipulação de Dados: Pandas

- Provedor de LLM: Groq Cloud API (Llama 3 / GPT-OSS Models) 

- Gerenciamento de Ambientes: python-dotenv

-------------------------------------------------------------------------------
https://sprint4data-science-and-statistical-computing-o6eabr243shhl7u8.streamlit.app


================================================================
Time
- Felipe Yamaguchi Mesquita	556170
- Gabriel Oliveira Amaral	563872
- Rafael Tavares Santos	563487
- Guilherme Rodrigues de Andrade 565863
- Gusthavo Costa de Melo 561330

Desenvolvido para o Challenge FIAP - Sprint 4

================================----------------=========
