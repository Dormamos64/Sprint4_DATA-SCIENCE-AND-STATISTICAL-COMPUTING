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


st.set_page_config(
    page_title="Inteligência Comercial & CS - TOTVS",
    page_icon="⚡",
    layout="wide"
)


load_dotenv()

def obter_secret(chave, fallback=""):
    
    val = os.environ.get(chave)
    if val:
        return val
    
    try:
        if hasattr(st, "secrets") and chave in st.secrets:
            return st.secrets[chave]
    except Exception:
        pass
    return fallback

env_api_key = obter_secret("GROQ_API_KEY")
env_model_id = obter_secret("GROQ_MODEL_ID", "openai/gpt-oss-20b")

st.sidebar.title("⚙️ Configurações & Filtros")

if env_api_key:
    api_key_final = env_api_key
    st.sidebar.success("⚡ Groq API Key ativa!")
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


PROMPT_EXTRACAO = """
Você é um auditor sênior de inteligência comercial e Customer Success da TOTVS.
Sua tarefa é analisar a transcrição da reunião e extrair métricas profundas sobre a conta e a atuação do vendedor.

Retorne EXCLUSIVAMENTE um objeto JSON válido, sem markdown ou texto adicional fora do JSON, seguindo esta estrutura exata:
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

    caminho_csv = os.path.join(pasta_saida, f"{base_name}_{timestamp}.csv")
    with open(caminho_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(registro.keys()), delimiter='|')
        writer.writeheader()
        writer.writerow(registro)


st.title("⚡ Painel Executivo de Inteligência Comercial - TOTVS")
st.markdown("Plataforma avançada de auditoria de reuniões, análise comportamental e gestão de portfólio via IA.")

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
            with st.spinner("Analisando reunião com Llama 3 via Groq..."):
                dados = extrair_dados_conversa(conteudo_texto, client_ai, modelo_id)
                stats = calcular_percentual_fala(conteudo_texto)
                if dados:
                    salvar_outcomes(dados, stats, arquivo_sel)
                    st.session_state['resultado_unico'] = dados
                    st.session_state['stats_unico'] = stats
                    st.success("Análise finalizada e salva com sucesso!")

    if 'resultado_unico' in st.session_state:
        dados = st.session_state['resultado_unico']
        stats = st.session_state['stats_unico']

        st.markdown("---")
        st.header(f"🏢 Cliente: {dados.get('nome_cliente', 'N/I')}")

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
            st.info(f"📌 **Próxima Ação Recomendada:**\n\n{dados.get('recomendacao_acao')}")

        with col2:
            st.subheader("💡 Feedback e Coaching para o Vendedor")
            st.write(f"👍 **Pontos Fortes:** {dados.get('pontos_fortes_vendedor')}")
            st.warning(f"🛠️ **Sugestões de Melhoria:** {dados.get('sugestoes_melhoria_vendedor')}")

            st.subheader("🗣️ Share of Voice (Tempo de Fala)")
            if stats:
                df_stats = pd.DataFrame(list(stats.items()), columns=['Participante', 'Porcentagem'])
                st.bar_chart(df_stats.set_index('Participante'))


else:
    st.subheader(f"🌐 Visão Executiva Consolidada ({len(nomes_arquivos)} Reuniões Disponíveis)")

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
            st.success("Lote completo processado com sucesso!")

    if 'resultados_lote' in st.session_state:
        res_lote = st.session_state['resultados_lote']
        df_lote = pd.DataFrame(res_lote)

        st.markdown("---")
        st.markdown("### 🎛️ Filtros Avançados do Portfólio")
        
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            filtro_tipo = st.selectbox("Status da Reunião:", ["Todas", "Reuniões Boas (Sucesso)", "Reuniões Ruins (Risco/Insatisfação)"])
        with col_f2:
            filtro_churn = st.selectbox("Filtro de Churn:", ["Todos", "Apenas em Risco (Churn = True)", "Sem Risco (Churn = False)"])
        with col_f3:
            filtro_cross = st.selectbox("Oportunidade de Cross-Sell:", ["Todas", "Com Oportunidade Identificada", "Sem Oportunidade"])

        
        df_filtrado = df_lote.copy()
        
        if filtro_tipo == "Reuniões Boas (Sucesso)":
            df_filtrado = df_filtrado[df_filtrado['classificacao_reuniao'].str.contains("Boa", case=False, na=False)]
        elif filtro_tipo == "Reuniões Ruins (Risco/Insatisfação)":
            df_filtrado = df_filtrado[df_filtrado['classificacao_reuniao'].str.contains("Ruim", case=False, na=False)]
            
        if filtro_churn == "Apenas em Risco (Churn = True)":
            df_filtrado = df_filtrado[df_filtrado['risco_churn'] == True]
        elif filtro_churn == "Sem Risco (Churn = False)":
            df_filtrado = df_filtrado[df_filtrado['risco_churn'] == False]
            
        if filtro_cross == "Com Oportunidade Identificada":
            df_filtrado = df_filtrado[df_filtrado['oportunidade_cross_sell'] != 'Nenhuma']
        elif filtro_cross == "Sem Oportunidade":
            df_filtrado = df_filtrado[df_filtrado['oportunidade_cross_sell'] == 'Nenhuma']

        st.markdown("---")
        
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📊 Reuniões Filtradas", len(df_filtrado))
        m2.metric("🚨 Contas em Risco", len(df_filtrado[df_filtrado['risco_churn'] == True]))
        m3.metric("⭐ Média Health Score", f"{round(df_filtrado['health_score'].mean(), 1)}/100" if not df_filtrado.empty else "0")
        m4.metric("💡 Oportunidades Cross-Sell", len(df_filtrado[df_filtrado['oportunidade_cross_sell'] != 'Nenhuma']))

        st.markdown("---")
        
        
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("🎭 Distribuição de Humor da Conta")
            if 'humor_conta' in df_filtrado.columns and not df_filtrado.empty:
                humor_counts = df_filtrado['humor_conta'].value_counts()
                
                st.bar_chart(humor_counts, color="#ff4b4b")
            else:
                st.info("Sem dados suficientes para exibir o gráfico.")

        with g2:
            st.subheader("🎯 Oportunidades de Cross-Sell Identificadas")
            if 'oportunidade_cross_sell' in df_filtrado.columns and not df_filtrado.empty:
                cross_counts = df_filtrado[df_filtrado['oportunidade_cross_sell'] != 'Nenhuma']['oportunidade_cross_sell'].value_counts()
                if not cross_counts.empty:
                    st.bar_chart(cross_counts, color="#00C853")
                else:
                    st.caption("Nenhuma oportunidade de cross-sell nos filtros atuais.")
            else:
                st.info("Sem dados disponíveis.")

        st.markdown("---")
        
        
        g3, g4 = st.columns(2)
        
        with g3:
            st.subheader("🚨 Proporção de Risco de Churn")
            if 'risco_churn' in df_filtrado.columns and not df_filtrado.empty:
                churn_counts = df_filtrado['risco_churn'].map({True: "Com Risco (True)", False: "Estável (False)"}).value_counts()
                st.bar_chart(churn_counts, color="#FFA726")

        with g4:
            st.subheader("💔 Motivos de Risco / Insatisfação")
            if 'motivo_risco_ou_insatisfacao' in df_filtrado.columns and not df_filtrado.empty:
                motivos_df = df_filtrado[df_filtrado['motivo_risco_ou_insatisfacao'] != 'Nenhum'][['nome_cliente', 'motivo_risco_ou_insatisfacao']]
                if not motivos_df.empty:
                    st.dataframe(motivos_df, use_container_width=True)
                else:
                    st.success("Nenhum motivo de insatisfação detectado nas reuniões filtradas!")

        st.markdown("---")
        st.subheader("📋 Tabela Consolidada do Portfólio")

        colunas_exibicao = ['arquivo', 'nome_cliente', 'classificacao_reuniao', 'health_score', 'humor_conta', 'risco_churn', 'oportunidade_cross_sell', 'sugestoes_melhoria_vendedor']
        cols_existentes = [c for c in colunas_exibicao if c in df_filtrado.columns]
        
        st.dataframe(df_filtrado[cols_existentes], use_container_width=True)

        
        csv_bytes = df_filtrado.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório Consolidado do Portfólio (.CSV)",
            data=csv_bytes,
            file_name="relatorio_consolidado_totvs.csv",
            mime="text/csv"
        )