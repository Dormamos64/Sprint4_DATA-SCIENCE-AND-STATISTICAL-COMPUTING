import os
import glob
import json
import csv
import re
import time
from datetime import datetime
import streamlit as st
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Inteligência Comercial & CS - TOTVS (Groq)",
    page_icon="⚡",
    layout="wide"
)

# ==============================================================================
# INICIALIZAÇÃO DA API GROQ
# ==============================================================================
load_dotenv()
env_api_key = os.environ.get("GROQ_API_KEY")
env_model_id = os.environ.get("GROQ_MODEL_ID") or "llama-3.3-70b-versatile"

st.sidebar.title("⚙️ Configurações & Filtros")

if env_api_key:
    api_key_final = env_api_key
    st.sidebar.success("⚡ Groq API Key ativa via .env")
else:
    api_key_final = st.sidebar.text_input("Insira sua GROQ_API_KEY:", type="password")

modelo_id = st.sidebar.text_input("Modelo Groq:", value=env_model_id)

@st.cache_resource
def get_groq_client(api_key: str):
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Erro ao inicializar cliente Groq: {e}")
        return None

client_ai = get_groq_client(api_key_final)

# ==============================================================================
# PROMPT DE EXTRAÇÃO
# ==============================================================================
PROMPT_EXTRACAO = """
Você é um auditor sênior de inteligência comercial e Customer Success da TOTVS.
Sua tarefa é analisar a transcrição da reunião e extrair métricas profundas sobre a conta e a atuação do vendedor.

Retorne EXCLUSIVAMENTE um objeto JSON válido, sem qualquer markdown ou texto adicional fora do JSON, seguindo esta estrutura exata:
{
    "nome_cliente": "Nome da empresa cliente",
    "participantes": [{"nome": "Nome", "papel": "vendedor ou cliente"}],
    "humor_conta": "Irritado, Empolgado, Cético, Satisfeito, Ansioso ou Neutro",
    "sentimento_geral": "Positivo, Neutro ou Negativo",
    "risco_churn": true ou false,
    "motivo_risco_ou_insatisfacao": "Explicação clara do motivo se houver risco/insatisfação, ou 'Nenhum' se reunião for boa",
    "classificacao_reuniao": "Boa (Sucesso/Expansão) ou Ruim (Risco/Insatisfação)",
    "health_score": 85,
    "produtos_atuais": ["Lista de produtos"],
    "concorrentes_mencionados": ["Lista de concorrentes"],
    "oportunidade_cross_sell": "Produto TOTVS sugerido ou 'Nenhuma'",
    "dores_principais": "Resumo das dores do cliente",
    "budget_mencionado": "Valor ou 'Não citado'",
    "confianca_no_vendedor": true ou false,
    "pontos_fortes_vendedor": "O que o vendedor fez de bom",
    "sugestoes_melhoria_vendedor": "Dicas práticas de onde o vendedor deve melhorar a abordagem",
    "recomendacao_acao": "Próxima ação comercial/CS imediata"
}
"""

# ==============================================================================
# FUNÇÕES DE PROCESSAMENTO
# ==============================================================================
def calcular_percentual_fala(texto_conversa: str) -> dict:
    padrao_orador = r"^(?P<nome>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)(?:\s\[\d{2}:\d{2}:\d{2}\])?:\s"
    blocos = re.split(padrao_orador, texto_conversa, flags=re.MULTILINE)
    
    if len(blocos) < 3:
        return {}

    falas_por_pessoa = {}
    for i in range(1, len(blocos), 2):
        nome = blocos[i].strip()
        texto = blocos[i+1].strip()
        num_palavras = len(texto.split())
        falas_por_pessoa[nome] = falas_por_pessoa.get(nome, 0) + num_palavras

    total_palavras = sum(falas_por_pessoa.values())
    if total_palavras == 0: 
        return {}

    return {nome: round((qtd / total_palavras) * 100, 1) for nome, qtd in falas_por_pessoa.items()}

def extrair_dados_conversa(texto_conversa: str, client: Groq, model_id: str) -> dict:
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": PROMPT_EXTRACAO},
                {"role": "user", "content": f"Transcrição da reunião:\n\n{texto_conversa}"}
            ],
            model=model_id,
            response_format={"type": "json_object"},
            temperature=0.2
        )
        resposta_texto = chat_completion.choices[0].message.content
        return json.loads(resposta_texto)
    except Exception as e:
        st.error(f"Erro ao consultar Groq API: {e}")
        return {}

def salvar_outcomes(dados: dict, stats: dict, nome_arquivo_origem: str):
    pasta_saida = "outcomes"
    os.makedirs(pasta_saida, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(nome_arquivo_origem)[0]
    
    registro = dados.copy()
    registro['arquivo_origem'] = nome_arquivo_origem
    registro['percentual_fala_estimado'] = ", ".join([f"{n}: {p}%" for n, p in stats.items()])
    
    for k in ['produtos_atuais', 'concorrentes_mencionados']:
        if isinstance(registro.get(k), list):
            registro[k] = ", ".join(map(str, registro[k]))

    if 'participantes' in registro and isinstance(registro['participantes'], list):
        registro['participantes_detalhados'] = ", ".join([f"{p.get('nome')} ({p.get('papel')})" for p in registro['participantes']])
        del registro['participantes']

    # Salva CSV
    caminho_csv = os.path.join(pasta_saida, f"{base_name}_{timestamp}.csv")
    with open(caminho_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(registro.keys()), delimiter='|')
        writer.writeheader()
        writer.writerow(registro)

    # Salva Markdown
    caminho_md = os.path.join(pasta_saida, f"{base_name}_{timestamp}.md")
    with open(caminho_md, 'w', encoding='utf-8') as f:
        f.write(f"# Diagnóstico de Reunião - {dados.get('nome_cliente', 'Cliente')}\n\n")
        for k, v in registro.items():
            f.write(f"- **{k}**: {v}\n")

# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
st.title("⚡ Painel Executivo de Inteligência Comercial - TOTVS (Groq)")
st.markdown("Análise quantitativa e qualitativa de reuniões com modelos Llama 3 via Groq Cloud.")

arquivos_locais = sorted(glob.glob("transcricoes/*.txt") + glob.glob("transcricoes/*.md"))
nomes_arquivos = [os.path.basename(f) for f in arquivos_locais]

st.sidebar.markdown("---")
opcao_fonte = st.sidebar.radio("Modo de Visão:", ["Análise Detalhada (Única)", "Dashboard do Portfólio (Global)"])

if opcao_fonte == "Análise Detalhada (Única)":
    if nomes_arquivos:
        arquivo_sel = st.sidebar.selectbox("Escolha uma transcrição:", nomes_arquivos)
        caminho_completo = os.path.join("transcricoes", arquivo_sel)
        with open(caminho_completo, "r", encoding="utf-8") as f:
            conteudo_texto = f.read()
    else:
        conteudo_texto = ""

    if st.button("🚀 Processar Reunião Selecionada", type="primary"):
        if not client_ai:
            st.error("Configure sua GROQ_API_KEY para continuar.")
        elif not conteudo_texto:
            st.error("Arquivo vazio.")
        else:
            with st.spinner("Analisando transcrição com Groq (Llama 3.3)..."):
                dados = extrair_dados_conversa(conteudo_texto, client_ai, modelo_id)
                stats = calcular_percentual_fala(conteudo_texto)
                if dados:
                    salvar_outcomes(dados, stats, arquivo_sel)
                    st.session_state['resultado_unico'] = dados
                    st.session_state['stats_unico'] = stats
                    st.success("Análise finalizada ultra-rápida! Resultados salvos na pasta `outcomes/`.")

    if 'resultado_unico' in st.session_state:
        dados = st.session_state['resultado_unico']
        stats = st.session_state['stats_unico']

        st.markdown("---")
        st.header(f"🏢 Cliente: {dados.get('nome_cliente', 'N/I')}")

        # KPIs Rápidos
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Classificação", dados.get('classificacao_reuniao', 'N/I'))
        k2.metric("Health Score", f"{dados.get('health_score', 0)}/100")
        k3.metric("Humor da Conta", dados.get('humor_conta', 'N/I'))
        k4.metric("Risco Churn", "🚨 SIM" if dados.get('risco_churn') else "✅ NÃO")
        k5.metric("Confiança Vendedor", "Sim" if dados.get('confianca_no_vendedor') else "Não")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 Diagnóstico Comercial & Motivos")
            st.write(f"**Motivo Risco/Insatisfação:** {dados.get('motivo_risco_ou_insatisfacao')}")
            st.write(f"**Dores Principais:** {dados.get('dores_principais')}")
            st.write(f"**Produtos Atuais:** {dados.get('produtos_atuais')}")
            st.write(f"**Concorrentes Mencionados:** {dados.get('concorrentes_mencionados')}")
            st.write(f"**Oportunidade Cross-Sell:** {dados.get('oportunidade_cross_sell')}")

            st.info(f"📌 **Recomendação de Próxima Ação:**\n\n{dados.get('recomendacao_acao')}")

        with col2:
            st.subheader("💡 Feedback para o Vendedor (Onde Melhorar)")
            st.write(f"👍 **Pontos Fortes:** {dados.get('pontos_fortes_vendedor')}")
            st.warning(f"🛠️ **Sugestões de Melhoria:** {dados.get('sugestoes_melhoria_vendedor')}")

            st.subheader("🗣️ Tempo de Fala por Participante (% Share of Voice)")
            if stats:
                df_stats = pd.DataFrame(list(stats.items()), columns=['Participante', 'Porcentagem'])
                st.bar_chart(df_stats.set_index('Participante'))

else:
    # DASHBOARD GLOBAL DO PORTFÓLIO
    st.subheader(f"🌐 Análise de Portfólio ({len(nomes_arquivos)} Reuniões Disponíveis)")

    if st.button("🔄 Processar / Atualizar Lote Completo", type="primary"):
        if not client_ai:
            st.error("Configure sua GROQ_API_KEY para continuar.")
        else:
            resultados_lote = []
            progresso = st.progress(0)
            
            for idx, arq in enumerate(nomes_arquivos):
                caminho = os.path.join("transcricoes", arq)
                with open(caminho, "r", encoding="utf-8") as f:
                    txt = f.read()
                
                res = extrair_dados_conversa(txt, client_ai, modelo_id)
                st_fala = calcular_percentual_fala(txt)
                
                if res:
                    res['arquivo'] = arq
                    res['percentual_fala'] = st_fala
                    resultados_lote.append(res)
                    salvar_outcomes(res, st_fala, arq)
                
                progresso.progress((idx + 1) / len(nomes_arquivos))

            st.session_state['resultados_lote'] = resultados_lote
            st.success("Lote completo processado com velocidade incrível!")

    if 'resultados_lote' in st.session_state:
        res_lote = st.session_state['resultados_lote']
        df_lote = pd.DataFrame(res_lote)

        st.markdown("---")
        st.header("📈 Indicadores Consolidados do Portfólio")

        # Filtro no Sidebar
        filtro_tipo = st.sidebar.selectbox("🔍 Filtrar Reuniões:", ["Todas", "Reuniões Boas (Sucesso)", "Reuniões Ruins (Risco/Insatisfação)"])
        
        df_filtrado = df_lote.copy()
        if filtro_tipo == "Reuniões Boas (Sucesso)":
            df_filtrado = df_filtrado[df_filtrado['classificacao_reuniao'].str.contains("Boa", case=False, na=False)]
        elif filtro_tipo == "Reuniões Ruins (Risco/Insatisfação)":
            df_filtrado = df_filtrado[df_filtrado['classificacao_reuniao'].str.contains("Ruim", case=False, na=False)]

        # Métricas Globais
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Reuniões Exibidas", len(df_filtrado))
        m2.metric("Contas em Risco de Churn", len(df_filtrado[df_filtrado['risco_churn'] == True]))
        m3.metric("Média de Health Score", f"{round(df_filtrado['health_score'].mean(), 1)}/100" if not df_filtrado.empty else "0")
        m4.metric("Oportunidades Cross-Sell", len(df_filtrado[df_filtrado['oportunidade_cross_sell'] != 'Nenhuma']))

        st.markdown("---")
        c_graf1, c_graf2 = st.columns(2)

        with c_graf1:
            st.subheader("🎭 Distribuição do Humor da Conta")
            if 'humor_conta' in df_filtrado.columns and not df_filtrado.empty:
                humor_counts = df_filtrado['humor_conta'].value_counts()
                st.bar_chart(humor_counts)

        with c_graf2:
            st.subheader("💔 Motivos de Risco / Insatisfação")
            if 'motivo_risco_ou_insatisfacao' in df_filtrado.columns and not df_filtrado.empty:
                motivos_df = df_filtrado[df_filtrado['motivo_risco_ou_insatisfacao'] != 'Nenhum'][['nome_cliente', 'motivo_risco_ou_insatisfacao']]
                st.dataframe(motivos_df, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Tabela Consolidada com Exportação para CSV")

        colunas_exibicao = ['arquivo', 'nome_cliente', 'classificacao_reuniao', 'health_score', 'humor_conta', 'risco_churn', 'motivo_risco_ou_insatisfacao', 'sugestoes_melhoria_vendedor']
        cols_existentes = [c for c in colunas_exibicao if c in df_filtrado.columns]
        
        st.dataframe(df_filtrado[cols_existentes], use_container_width=True)

        csv_bytes = df_filtrado.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório Consolidado (.CSV)",
            data=csv_bytes,
            file_name="relatorio_consolidado_totvs.csv",
            mime="text/csv"
        )