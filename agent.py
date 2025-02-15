import os
import signal
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Carica le variabili d'ambiente
AGENT_ID = "nUnSSapc73VFkrd3Z73U"
API_KEY = "sk_fd2e2174f77c01d53fa54a367676258ae80cc22be1a8c381"

if AGENT_ID is None:
    raise ValueError("La variabile d'ambiente AGENT_ID non è stata impostata.")

# Crea l'istanza del client ElevenLabs
client = ElevenLabs(api_key=API_KEY)


# Inizializza la conversazione con l'agent
conversation = Conversation(
    # Client e ID dell'agent
    client,
    AGENT_ID,
    # Se API_KEY è presente, si assume che sia richiesta l'autenticazione
    requires_auth=bool(API_KEY),
    # Utilizza l'interfaccia audio di default (microfono e altoparlanti di sistema)
    audio_interface=DefaultAudioInterface(),
    # Callback per stampare la risposta dell'agent
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    # Callback per eventuali correzioni nella risposta
    callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
    # Callback per stampare la trascrizione dell'utente
    callback_user_transcript=lambda transcript: print(f"User: {transcript}"),
    # Se desideri visualizzare le misurazioni della latenza, decommenta la seguente riga:
    # callback_latency_measurement=lambda latency: print(f"Latency: {latency}ms"),
)

# Avvia la sessione di conversazione
conversation.start_session()

# Gestore del segnale per una chiusura pulita quando si preme Ctrl+C
signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

# Attendi la fine della sessione e recupera l'ID della conversazione per eventuale debug
conversation_id = conversation.wait_for_session_end()
print(f"Conversation ID: {conversation_id}")
