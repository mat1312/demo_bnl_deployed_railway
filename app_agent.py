import streamlit as st
import streamlit.components.v1 as components

# Configura la pagina Streamlit
st.set_page_config(page_title="Conversational Agent", layout="wide")

st.title("Agent Conversazionale - ElevenLabs")
st.write("Interagisci con l'agent direttamente dal frontend!")

# HTML del widget fornito da ElevenLabs
widget_html = """
<elevenlabs-convai agent-id="nUnSSapc73VFkrd3Z73U"></elevenlabs-convai>
<script src="https://elevenlabs.io/convai-widget/index.js" async type="text/javascript"></script>
"""

# Incorpora il widget nella pagina Streamlit
components.html(widget_html, height=600, scrolling=True)
