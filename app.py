import os
import streamlit as st
import requests
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain import PromptTemplate, LLMChain
import streamlit.components.v1 as components

# Carica le variabili d'ambiente dal file .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("La variabile OPENAI_API_KEY non è stata caricata correttamente.")
    st.stop()

elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
if not elevenlabs_api_key:
    st.error("La variabile ELEVENLABS_API_KEY non è stata caricata correttamente.")
    st.stop()

# Imposta il percorso del vector DB persistente
persist_directory = "vectordb"
if not os.path.exists(persist_directory):
    st.error("Il vector DB non è stato trovato. Esegui prima l'ingestione con 'ingest.py'.")
    st.stop()

# Carica il vector DB abilitando la deserializzazione per file pickle
embeddings = OpenAIEmbeddings()
vector_store = FAISS.load_local(persist_directory, embeddings, allow_dangerous_deserialization=True)

# Inizializza il modello LLM e la catena di RetrievalQA (con ritorno dei documenti sorgente)
llm = ChatOpenAI(temperature=0.1, model="gpt-4o-mini")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(),
    return_source_documents=True
)

# Funzioni per recuperare la conversazione da ElevenLabs
def get_last_conversation(agent_id, api_key):
    url = "https://api.elevenlabs.io/v1/convai/conversations"
    headers = {"xi-api-key": api_key}
    params = {"agent_id": agent_id, "page_size": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
         st.error(f"Errore nel recuperare le conversazioni: {response.status_code}")
         return None
    data = response.json()
    conversations = data.get("conversations", [])
    if not conversations:
         st.info("Nessuna conversazione trovata.")
         return None
    return conversations[0].get("conversation_id")

def get_conversation_details(conversation_id, api_key):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
         st.error(f"Errore nel recuperare i dettagli della conversazione: {response.status_code}")
         return None
    return response.json()

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Assistente per Mutui e Finanziamenti", layout="wide")
st.title("Assistente per Mutui e Finanziamenti")


# ---------------------------------------------
# SEZIONE: Q&A tramite LangChain e OpenAI
# ---------------------------------------------
st.subheader("Fai una domanda su mutui, finanziamenti, ecc.")
user_input = st.text_input("Inserisci la tua domanda qui")
if st.button("Invia") and user_input:
    with st.spinner("Generazione della risposta..."):
        result = qa_chain.invoke(user_input)
        if isinstance(result, dict) and "result" in result:
            answer = result["result"]
            source_docs = result.get("source_documents", [])
    st.markdown(f"**Q:** {user_input}")
    st.markdown(f"**A:** {answer}")
    if source_docs:
        st.markdown("**Fonti:**")
        sources_dict = {}
        for doc in source_docs:
            metadata = doc.metadata
            if "source" in metadata:
                source = metadata["source"].replace("\\", "/")
                page = metadata.get("page", None)
                line = metadata.get("start_index", None)
                if source in sources_dict:
                    sources_dict[source].append((page, line))
                else:
                    sources_dict[source] = [(page, line)]
        for source, occurrences in sources_dict.items():
            file_name = os.path.basename(source)
            occ_list = []
            for occ in occurrences:
                p, l = occ
                occ_str = ""
                if p is not None and p != 0:
                    occ_str += f"pagina {p}"
                if l is not None and l != 0:
                    occ_str += f", riga {l}" if occ_str else f"riga {l}"
                if occ_str:
                    occ_list.append(occ_str)
            occ_text = " - ".join(occ_list) if occ_list else ""
            if occ_text:
                st.markdown(f"- [{file_name} ({occ_text})]({source})")
            else:
                st.markdown(f"- [{file_name}]({source})")
    else:
        st.markdown("*Nessuna fonte disponibile.*")

# ---------------------------------------------
# SEZIONE: Agent Conversazionale ElevenLabs (embed essenziale)
# ---------------------------------------------
st.subheader("Agent Conversazionale ElevenLabs")
# Script HTML essenziale per l'embedding del widget
minimal_widget_html = """
<div>
  <elevenlabs-convai agent-id="nUnSSapc73VFkrd3Z73U"></elevenlabs-convai>
</div>
<script src="https://elevenlabs.io/convai-widget/index.js" async></script>
"""
components.html(minimal_widget_html, height=600)


# ---------------------------------------------
# SEZIONE: Transcript e Estrazione Contatti (in alto)
# ---------------------------------------------
st.subheader("Transcript e Estrazione Contatti")

col1, col2 = st.columns(2)

with col1:
    if st.button("Recupera conversazione"):
        with st.spinner("Recupero conversazione..."):
             agent_id = "nUnSSapc73VFkrd3Z73U"
             conv_id = get_last_conversation(agent_id, elevenlabs_api_key)
             if conv_id:
                 details = get_conversation_details(conv_id, elevenlabs_api_key)
                 if details:
                     transcript = details.get("transcript", [])
                     st.session_state["transcript"] = transcript  # Salva il transcript in sessione
                     if transcript:
                         st.markdown("#### Transcript")
                         for msg in transcript:
                             role = msg.get("role", "unknown")
                             time_in_call_secs = msg.get("time_in_call_secs", "")
                             message = msg.get("message", "")
                             st.markdown(f"**{role.capitalize()} [{time_in_call_secs}s]:** {message}")
                     else:
                         st.info("Nessun transcript disponibile")
             else:
                 st.error("Nessuna conversazione trovata")

with col2:
    if st.button("Estrai contatti"):
        transcript = st.session_state.get("transcript", [])
        if transcript:
            # Filtra solo i messaggi dell'utente
            user_messages = [msg.get("message", "") for msg in transcript if msg.get("role", "").lower() == "user"]
            transcript_text = "\n".join(user_messages)
            if transcript_text.strip():
                prompt_template = """
Analizza la seguente trascrizione di una conversazione tra un utente e un agente virtuale.
Estrai, se presenti, l'indirizzo email e il numero di telefono dell'utente.
Rispondi nel seguente formato:
Email: <indirizzo email>
Telefono: <numero di telefono>
Se non trovi alcun dato, indica "Non trovato".
Se vedi qualche termine simile a "chiocciola" si tratta di un'email e cambiala con il carattere "@".

Trascrizione:
{transcript}
"""
                template = PromptTemplate(input_variables=["transcript"], template=prompt_template)
                contact_chain = LLMChain(llm=llm, prompt=template)
                with st.spinner("Analizzando la trascrizione per estrarre contatti..."):
                    contact_info = contact_chain.run(transcript=transcript_text)
                st.markdown("#### Contatti estratti")
                st.markdown(contact_info)
            else:
                st.info("Nessun messaggio utente trovato per l'analisi dei contatti.")
        else:
            st.info("Nessuna trascrizione disponibile per l'analisi dei contatti.")
