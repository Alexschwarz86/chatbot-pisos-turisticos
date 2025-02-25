import json
from openai import OpenAI
from app.database import query_restaurantes, save_conversation_state, get_conversation_state
import os

# Cargar la API Key de OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def handle_recomendaciones(user_id, user_message):
    """
    Maneja solicitudes de recomendación de restaurantes utilizando memoria híbrida.
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria a Largo Plazo - Supabase)**
    conv_state = get_conversation_state(user_id)

    # 🔹 **2️⃣ Construcción de memoria híbrida (Supabase + Ventana de tokens)**
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": str(msg["usuario"])})  # ✅ Asegurar que sea string
            bot_response = msg["bot"]
            if isinstance(bot_response, dict):  # ✅ Si es un JSON, convertirlo a string
                bot_response = json.dumps(bot_response, ensure_ascii=False)  
            historial.append({"role": "assistant", "content": str(bot_response)})  # ✅ Asegurar string

    # 📌 **Verificación de información faltante**
    info_prompt = f"""
Eres un asistente especializado en recomendaciones de restaurantes.  
Tu tarea es analizar el mensaje del usuario y verificar si falta información esencial.  
Siempre revisa si el usuario ha proporcionado estos datos:
- Tipo de comida preferido (italiana, japonesa, mexicana, etc.).
- Presupuesto (barato, medio, caro).

📌 **Si falta al menos uno de estos datos, genera preguntas claras en el idioma del usuario.**  
📌 **Si ya están completos, devuelve exactamente este JSON vacío: `{{}}`.**  

📌 **Datos actuales en memoria:**  
- Tipo de comida: {conv_state.datos_categoria.get("tipo_cocina", "No definido")}
- Presupuesto: {conv_state.datos_categoria.get("budget", "No definido")}

📌 **Conversación Reciente (Ventana de Tokens)**:
{json.dumps(historial, ensure_ascii=False, indent=2)}

📌 **Mensaje del usuario**:
"{user_message}"
"""

    info_response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": info_prompt}],
    max_tokens=100,
    temperature=0
)
    

    response_text = info_response.choices[0].message.content.strip()

# 📌 **Si OpenAI devuelve `{}`, devolver un mensaje personalizado**
    if response_text == "{}":
      return "Ya tengo toda la información necesaria. Te mostraré los mejores restaurantes en breve."

    return response_text  # Devolver la respuesta normal si no es un JSON vacío