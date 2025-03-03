from fastapi import FastAPI
from pydantic import BaseModel
from app.database import get_dynamic_state,save_dynamic_state
from openai import OpenAI
from app.nlu import analyze_message
from app.business_logic import handle_intents  # Usamos la versión centralizada
import json

app = FastAPI(title="Chatbot de Ejemplo", version="1.0.0")

class ChatRequest(BaseModel):
    numero_telefono: str
    message: str
    nombre_apartamento: str

@app.post("/chat")
def chat_endpoint(chat_request: ChatRequest):
    """
    Endpoint que recibe un mensaje del usuario, analiza la intención,
    consulta la memoria y genera una respuesta contextualizada.
    """
    numero_telefono = chat_request.numero_telefono
    user_message = chat_request.message
    nombre_apartamento = chat_request.nombre_apartamento

    # 🔹 1️⃣ Recuperamos o creamos el estado de conversación del usuario
    conv_state = get_dynamic_state(numero_telefono)

    # 🔹 2️⃣ Analizamos el mensaje con NLU
    analysis_result = analyze_message(user_message, numero_telefono)
    print(f"🔍 analysis_result: {analysis_result}")

    conv_state.idioma = analysis_result["idioma"]  # ✅ Ahora accedemos correctamente al atributo

    # 🔹 3️⃣ Procesamos la intención detectada
    reply = handle_intents(numero_telefono, analysis_result, user_message, conv_state, nombre_apartamento)

    # 🔹 **4️⃣ Validar y convertir `historial` en una lista antes de `append()`**
    # 🔹 5️⃣ Asegurar que historial sea una lista antes de agregar el mensaje
    if isinstance(conv_state.historial, str):
       try:
        conv_state.historial = json.loads(conv_state.historial)  # Convertir a lista si es string
       except json.JSONDecodeError:
        conv_state.historial = []  # Si hay error, inicializar como lista vacía
    elif not isinstance(conv_state.historial, list):
       conv_state.historial = []  # Si no es lista, inicializar como lista vacía

    # 🔹 **5️⃣ Guardar el mensaje en el historial**
    conv_state.historial.append({"usuario": user_message, "bot": reply})

    # 🔹 6️⃣ Mantener solo los últimos 10 mensajes en memoria y Supabase
    conv_state.historial = conv_state.historial[-10:]

    # 🔹 7️⃣ Guardar la conversación en Supabase
    save_dynamic_state(conv_state)  # ✅ Convertimos el objeto a diccionario antes de guardar

    return {"reply": reply}