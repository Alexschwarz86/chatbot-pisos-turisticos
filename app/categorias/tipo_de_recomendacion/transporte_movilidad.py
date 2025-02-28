import os
import json
from datetime import datetime
from app.database import get_conversation_state, save_conversation_state
from openai import OpenAI

# Cargar la API Key de OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def handle_transporte(user_id, user_message):
    """
    Maneja solicitudes de transporte utilizando solo GPT-4 sin APIs externas.
    """

    # 🔹 **1️⃣ Obtener estado del usuario**
    conv_state = get_conversation_state(user_id)

    # 🔹 **2️⃣ Construcción de memoria híbrida**
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": str(msg["usuario"])})
            bot_response = msg["bot"]
            if isinstance(bot_response, dict):  
                bot_response = json.dumps(bot_response, ensure_ascii=False)  
            historial.append({"role": "assistant", "content": str(bot_response)})

    # 📌 **3️⃣ Generar el prompt para OpenAI**
    info_prompt = f"""
    📌 **Objetivo**: Ayudar al usuario a encontrar la mejor opción de transporte entre ciudades como Calafell, Barcelona, Tarragona, Sitges, etc.

    **Reglas Clave**:
    1. Usa **Rodalies de Cataluña (trenes)**, **buses interurbanos** y **taxis** como opciones principales.
    2. Proporciona **horarios aproximados** y **precios orientativos** si el usuario los solicita. 
   - Si no tienes datos exactos, indica que son estimaciones basadas en información común.
    3. **Si el trayecto es específico**, intenta dar la ruta más sencilla en el transporte disponible (indicando origen y destino).
    4. **Si no se especifica origen**, asume **Calafell** como punto de partida.
    5. Al **recomendar un transporte**, facilita la **web de referencia** solo si aún no se ha dado antes al usuario.
    6. **Responde únicamente** a la pregunta formulada, sin añadir más detalles de los que se te piden.
    7. Sé conciso, **humano** y **cortés**, pero **no des información innecesaria**.

    ## **Ejemplos de respuesta esperada**:
    - “Para ir de Calafell a Barcelona, puedes tomar el Rodalies R2 Sud cada 30 minutos por ~4,60€. Si prefieres bus, MonBus ofrece varias salidas al día.”
    - “Para un taxi entre Tarragona y Salou, el precio ronda los 20-25€.”
    - “El tren de Sitges a Calafell tarda unos 25-30 minutos y cuesta alrededor de 3,90€.”


    📌 **Datos actuales en memoria:**  
    - **Origen:** {conv_state.datos_categoria.get("origen", "No definido")}
    - **Destino:** {conv_state.datos_categoria.get("destino", "No definido")}
    - **Tipo de transporte preferido:** {conv_state.datos_categoria.get("transporte", "No definido")}

    📌 **Conversación Reciente (Ventana de Tokens)**:
    {json.dumps(historial, ensure_ascii=False, indent=2)}

    📌 **Mensaje del usuario**:
    "{user_message}"

    📌 **Estructura de respuesta esperada**:
    {{
        "origen": "<ciudad de origen o 'No definido'>",
        "destino": "<ciudad de destino o 'No definido'>",
        "transporte": "<tipo de transporte preferido o 'No definido'>",
        "respuesta_al_cliente": "<respuesta con la mejor opción de transporte>"
    }}
    """

    # 🔹 **4️⃣ Llamada a OpenAI**
    info_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": info_prompt}],
        max_tokens=200,
        temperature=0
    )

    print("📌 Prompt enviado a OpenAI:\n", info_prompt)
    response_text = info_response.choices[0].message.content.strip()
    print("📌 Respuesta completa de OpenAI:", response_text)

    # 🔹 **5️⃣ Eliminar backticks antes de parsear JSON**
    if response_text.startswith("```json"):
        response_text = response_text[7:].strip()
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()

    # 🔹 **6️⃣ Validar si la respuesta es realmente un JSON**
    try:
        result = json.loads(response_text)  
    except json.JSONDecodeError:
        print("❌ OpenAI no devolvió un JSON válido. Usando respuesta normal.")
        return response_text  

    # 🔹 **7️⃣ Actualizar y guardar la información en memoria**
    if isinstance(result, dict):  
        conv_state.datos_categoria["origen"] = result.get("origen", conv_state.datos_categoria.get("origen", "No definido"))
        conv_state.datos_categoria["destino"] = result.get("destino", conv_state.datos_categoria.get("destino", "No definido"))
        conv_state.datos_categoria["transporte"] = result.get("transporte", conv_state.datos_categoria.get("transporte", "No definido"))

        # 📌 Debugging: Verificar actualización correcta
        print("📌 datos_categoria actualizado antes de guardar:", json.dumps(conv_state.datos_categoria, indent=4, ensure_ascii=False))

        # Guardamos la nueva información en Supabase
        save_conversation_state(conv_state)
    else:
        print("⚠️ La respuesta de OpenAI no contiene datos válidos para actualizar `datos_categoria`.")

    # 🔹 **8️⃣ Responder al usuario con la mejor opción de transporte**
    return result["respuesta_al_cliente"]