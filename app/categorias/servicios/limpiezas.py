import os
import json
from dotenv import load_dotenv
from datetime import datetime
from app.database import get_dynamic_state, save_dynamic_state

# 🔹 Cargar variables de entorno
load_dotenv()

def handle_limpieza(numero, user_message):
    """
    Maneja solicitudes de limpieza en la estancia.
    Pregunta los datos faltantes y agenda cuando toda la información esté completa.
    """
    # 🔹 **1️⃣ Obtener estado dinámico del usuario en Supabase**
    conv_state = get_dynamic_state(numero)

    # 🔹 **2️⃣ Revisar si ya tiene la información necesaria**
    fecha = conv_state["datos_categoria"].get("fecha", "No definido")
    hora = conv_state["datos_categoria"].get("hora", "No definido")

    # 🔹 **3️⃣ Generar el prompt para OpenAI para verificar si faltan datos**
    info_prompt = f"""
    Eres un asistente de gestión de limpiezas para apartamentos turísticos.
    📌 **Antes de agendar una limpieza, debes asegurarte de que el usuario proporcionó la fecha y la hora.**
    
    - Si ya tiene toda la información, responde con `"respuesta_al_cliente": null`.
    - Si falta algún dato, responde con la pregunta que debe hacer.
    - Interpreta correctamente expresiones como "hoy", "mañana", "el próximo lunes".
    - La hora debe estar en formato 24 horas (HH:MM).

    📌 **Datos actuales en memoria:**  
    - **Fecha:** {fecha}
    - **Hora:** {hora}

    📌 **Mensaje del usuario**:
    "{user_message}"

    📌 **Estructura esperada en JSON**:
    {{
        "fecha": "<fecha o 'No definido'>",
        "hora": "<hora o 'No definido'>",
        "respuesta_al_cliente": "<pregunta al usuario o null>"
    }}
    """
    print("📌 Prompt enviado a OpenAI:\n", info_prompt) 

    # 🔹 **4️⃣ Llamada a OpenAI para procesar el mensaje**
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    info_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": info_prompt}],
        max_tokens=100,
        temperature=0
    )

    response_text = info_response.choices[0].message.content.strip()

    # 🔹 **5️⃣ Validar si la respuesta es JSON**
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        return "❌ Hubo un problema al procesar tu solicitud, intenta de nuevo."

    # 🔹 **6️⃣ Guardar información nueva en `dinamic`**
    if isinstance(result, dict):
        conv_state["datos_categoria"]["fecha"] = result.get("fecha", fecha)
        conv_state["datos_categoria"]["hora"] = result.get("hora", hora)

        save_dynamic_state(conv_state.to_dict())  # Guardamos en Supabase

    # 🔹 **7️⃣ Si falta información, preguntar al usuario**
    if result.get("respuesta_al_cliente") is not None:
        return result["respuesta_al_cliente"]

    # 🔹 **8️⃣ Si ya tiene toda la información, confirmar**
    return f"✅ ¡Limpieza programada para el {result['fecha']} a las {result['hora']}!"
    

# 🔹 **Ejemplo de uso**
if __name__ == "__main__":
    numero = "644123456"  # Simulación de número de teléfono en lugar de user_id
    user_message = "¿Podrían limpiar mi apartamento el próximo lunes a las 10 de la mañana?"  # Mensaje de ejemplo

    response = handle_limpieza(numero, user_message)
    print(response)