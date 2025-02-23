# app/main.py

from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional

from app.database import init_db, get_conversation_state, save_conversation_state, close_conversation_if_expired
from app.nlu import analyze_message
from app.business_logic import handle_intents
from app.nlu import PROMPT_TEMPLATE
###############################################################################
# 1) Definimos un modelo Pydantic para la petición de chat
###############################################################################
class ChatRequest(BaseModel):
    user_id: str
    message: str

###############################################################################
# 2) Creamos la aplicación FastAPI
###############################################################################
app = FastAPI(
    title="Chatbot de Ejemplo",
    version="1.0.0"
)

###############################################################################
# 3) Al iniciar la app, inicializamos la base de datos
###############################################################################
@app.on_event("startup")
def startup_event():
    init_db()

###############################################################################
# 4) Creamos un endpoint /chat para recibir el mensaje del usuario
###############################################################################
@app.post("/chat")
def chat_endpoint(chat_request: ChatRequest):
    """
    Endpoint para procesar un mensaje de chat. 
    Recibe un JSON con 'user_id' y 'message'.
    """

    # Extraemos información
    user_id = chat_request.user_id
    user_message = chat_request.message

    # 1. Recuperamos el estado de conversación desde la BD (o creamos uno si no existe)
    conversation_state = get_conversation_state(user_id)

    # 2. Revisamos si la conversación debe cerrarse (por checkout + 1 día, etc.)
    conversation_state = close_conversation_if_expired(conversation_state)

    if conversation_state.is_closed:
        # Si la conversación está cerrada, respondemos acorde
        return {
            "reply": "La conversación ha expirado. Si necesitas ayuda, por favor inicia una nueva."
        }

    # 3. Analizamos el mensaje con la capa NLU
    analysis_result = analyze_message(user_message)
    # Ejemplo de analysis_result esperado:
    # {
    #   "idioma": "es",
    #   "intenciones": ["servicios_adicionales", "checkout"],
    #   "confidence": 0.95,
    #   "original_text": "..."
    # }

    # 4. Llamamos a la lógica de negocio, para obtener la respuesta final
    response_text = handle_intents(conversation_state, analysis_result)

    # 5. Guardamos el nuevo estado en la BD (último mensaje, última respuesta, etc.)
    conversation_state.last_message = user_message
    conversation_state.last_response = response_text
    save_conversation_state(conversation_state)

    # 6. Devolvemos la respuesta en JSON
    return {"reply": response_text}