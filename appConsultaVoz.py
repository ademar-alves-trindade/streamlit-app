import os
import tempfile
from gtts import gTTS
import speech_recognition as sr
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
import pandas as pd

# Configuração da chave API do OpenAI
os.environ["OPENAI_API_KEY"] = "sk-proj-c3Jervsv7SJkPenqdKtvT3BlbkFJjvcR8YKtPLfmtjsWuafT"

# Conectando ao banco de dados SQLite
db = SQLDatabase.from_uri("sqlite:///vendas.db")

# Configurando o modelo de linguagem
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# Criando a cadeia de consulta SQL
sql_db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, verbose=True)

# Função para gravar áudio do microfone
def gravar_audio(duracao=4):
    reconhecedor = sr.Recognizer()
    with sr.Microphone() as fonte:
        st.write("Ajustando o ruído ambiente...")
        reconhecedor.adjust_for_ambient_noise(fonte, duration=1)
        st.write(f"Gravando por {duracao} segundos...")
        audio_gravado = reconhecedor.listen(fonte, timeout=duracao)
        st.write("Gravação concluída.")
    return audio_gravado

# Função para converter áudio em texto
def audio_para_texto(audio):
    reconhecedor = sr.Recognizer()
    try:
        st.write("Reconhecendo o texto...")
        texto = reconhecedor.recognize_google(audio, language="pt-BR")
        st.write("Texto reconhecido:", texto)
    except sr.UnknownValueError:
        texto = "O Google Speech Recognition não conseguiu entender o áudio."
        st.write(texto)
    except sr.RequestError:
        texto = "Não foi possível solicitar os resultados do serviço de reconhecimento de fala do Google."
        st.write(texto)
    return texto

# Função para converter texto em voz e tocar o áudio
def texto_para_fala(texto):
    tts = gTTS(texto, lang='pt-br')
    buffer_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(buffer_audio.name)
    st.audio(buffer_audio.name)
    return buffer_audio.name

# Função para fazer consulta SQL e gerar áudio com a resposta
def realizar_consulta(pergunta_usuario):
    resultado = sql_db_chain.invoke(pergunta_usuario)
    texto_resultado = resultado['result']
    
    # Verificar se o resultado é uma tabela (pode ser lista de dicionários) e converter para DataFrame
    if isinstance(texto_resultado, list) and isinstance(texto_resultado[0], dict):
        df = pd.DataFrame(texto_resultado)
        st.table(df)
    else:
        st.write("Resultado:", texto_resultado)
    
    # Gerar áudio usando gTTS
    caminho_audio = texto_para_fala(str(texto_resultado))
    
    return texto_resultado, caminho_audio

# Interface do usuário com Streamlit
def main():
    st.set_page_config(page_title="Consulta SQL com IA 📊")
    st.header("Consulta SQL com IA 📊")

    st.write("Faça uma pergunta sobre o banco de dados:")

    # Sidebar com perguntas pré-estabelecidas
    st.sidebar.title("Perguntas pré-definidas")
    opcoes = ["Qual é o total de vendas do dia 19/08/2024?", 
              "Qual o produto mais vendido no último mês?",
              "Quais são os valores das vendas feitas pelo vendedor chico?",
              "Que dia foi vendido o canivete zebu?",
              "Quanto a loja vendeu para o cliente pedro alexandre da silva?",
              "Qual é quantidade de barra rosca 3/4 vendidas na loja?",
              "Distribuição dos custos e preços de venda dos produtos",
              "Qual é o produto que mais vendeu na loja?",
              "Quais clientes compraram mais de R$ 1000?"]
    pergunta_selecionada = st.sidebar.radio("Escolha uma pergunta:", opcoes)

    # Campo de input para perguntas personalizadas com preenchimento automático
    pergunta_usuario = st.text_input("Digite sua pergunta:", value=pergunta_selecionada if pergunta_selecionada else "", placeholder='Após digitar a pergunta, pressione enter')

    if st.button("Fazer Consulta por Voz"):
        st.write("Gravando...")
        audio_gravado = gravar_audio()
        pergunta_usuario = audio_para_texto(audio_gravado)
    
    if pergunta_usuario:
        resultado, caminho_audio = realizar_consulta(pergunta_usuario)
    
if __name__ == "__main__":
    main()
