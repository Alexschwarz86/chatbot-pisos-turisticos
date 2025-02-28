from fastapi import FastAPI
from pydantic import BaseModel
from app.database import get_conversation_state, save_conversation_state
from app.nlu import analyze_message
from app.business_logic import handle_intents  # Usamos la versión centralizada
import json
app = FastAPI(title="Chatbot de Ejemplo", version="1.0.0")

class ChatRequest(BaseModel):
    user_id: str
    message: str
    nombre_apartamento:str

@app.post("/chat")
def chat_endpoint(chat_request: ChatRequest):
    """
    Endpoint que recibe un mensaje del usuario, analiza la intención,
    consulta la memoria y genera una respuesta contextualizada.
    """
    user_id = chat_request.user_id
    user_message = chat_request.message
    nombre_apartamento = chat_request.nombre_apartamento
    
    # 🔹 1️⃣ Recuperamos o creamos el estado de conversación del usuario
    conv_state = get_conversation_state(user_id)

    # 🔹 2️⃣ Analizamos el mensaje con NLU
    analysis_result = analyze_message(user_message, user_id)
    print(f"🔍 analysis_result: {analysis_result}")

    conv_state.idioma = analysis_result["idioma"]  # Actualizamos el idioma detectado

    # 🔹 3️⃣ Procesamos la intención detectada (PASAMOS `conv_state`)
    reply = handle_intents(user_id, analysis_result, user_message, conv_state,nombre_apartamento)

    # 🔹 4️⃣ Guardamos el mensaje en la memoria híbrida (ventana de tokens + Supabase)
    conv_state.historial.append({"usuario": user_message, "bot": reply})

    # 🔹 5️⃣ Mantener solo los últimos 10 mensajes en memoria y Supabase
    conv_state.historial = conv_state.historial[-10:]

    return {"reply": reply}