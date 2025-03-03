import os
import json
from datetime import datetime
from app.database import get_dynamic_state, save_dynamic_state
from openai import OpenAI

# Cargar la API Key de OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def handle_actividades_ocio(numero_telefono, user_message):
    """
    Maneja solicitudes de recomendación de actividades de ocio utilizando memoria dinámica.
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria Dinámica - Supabase)**
    conv_state = get_dynamic_state(numero_telefono)

    # 🔹 **2️⃣ Construcción de memoria híbrida (Supabase + Ventana de tokens)**
    historial = []
    for msg in conv_state["historial"][-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": str(msg["usuario"])})  # ✅ Asegurar que sea string
            bot_response = msg["bot"]
            if isinstance(bot_response, dict):  # ✅ Si es un JSON, convertirlo a string
                bot_response = json.dumps(bot_response, ensure_ascii=False)  
            historial.append({"role": "assistant", "content": str(bot_response)})  # ✅ Asegurar string

    # 📌 **3️⃣ Generar el prompt para OpenAI**
    info_prompt = f"""
    Eres un asistente especializado en recomendaciones de actividades de ocio.  
    📌 **Todas las actividades recomendadas deben ser en Segur de Calafell, Calafell, Cunit o Comarruga.**  
    📌 **Si el usuario menciona otra ciudad, infórmale que solo puedes recomendar en esa zona.**  

    Tu tarea es analizar el mensaje del usuario y verificar si ya tiene todos los datos necesarios.  
    📌 **Reglas Clave:**
    🔹 **Si ya tiene el día y el tipo de grupo, devuelve un JSON con `"respuesta_al_cliente": null`.**  
    🔹 **Si falta algún dato, devuelve un JSON con `"respuesta_al_cliente"` conteniendo la pregunta necesaria.**  
    🔹 **NO devuelvas texto plano, siempre responde en formato JSON sin backticks.**  

    📌 **Estructura de respuesta esperada:**
    {{
        "dia": "<día o 'No definido'>",
        "tipo_grupo": "<familia / amigos / pareja o 'No definido'>",
        "mas_informacion": "<información extra o 'No definido'>",
        "respuesta_al_cliente": "<pregunta para el usuario o null>"
    }}

    📌 **Datos actuales en memoria:**  
    - **Día de la actividad:** {conv_state["datos_categoria"].get("dia", "No definido")}
    - **Tipo de grupo:** {conv_state["datos_categoria"].get("tipo_grupo", "No definido")}
    - **Información adicional:** {conv_state["datos_categoria"].get("mas_informacion", "No definido")}

    📌 **Conversación Reciente (Ventana de Tokens)**:
    {json.dumps(historial, ensure_ascii=False, indent=2)}

    📌 **Mensaje del usuario**:
    "{user_message}"
    """

    # 🔹 **4️⃣ Llamada a OpenAI**
    info_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": info_prompt}],
        max_tokens=100,
        temperature=0
    )

    print("📌 Prompt enviado a OpenAI:\n", info_prompt)
    response_text = info_response.choices[0].message.content.strip()
    print("📌 Respuesta completa de OpenAI:", response_text)

    # 🔹 **5️⃣ Eliminar backticks antes de parsear JSON**
    if response_text.startswith("```json"):
        response_text = response_text[7:].strip()  # Elimina ```json
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()  # Elimina ```

    # 🔹 **6️⃣ Validar si la respuesta es realmente un JSON**
    try:
        result = json.loads(response_text)  # Intentar parsear JSON
    except json.JSONDecodeError:
        print("❌ OpenAI no devolvió un JSON válido. Usando respuesta normal.")
        return response_text  # Devolver texto plano si OpenAI falló

    # 🔹 **7️⃣ Actualizar y guardar la información en `dinamic`**
    if isinstance(result, dict):  # Verificar que result sea un diccionario
        conv_state["datos_categoria"]["dia"] = result.get("dia", conv_state["datos_categoria"].get("dia", "No definido"))
        conv_state["datos_categoria"]["tipo_grupo"] = result.get("tipo_grupo", conv_state["datos_categoria"].get("tipo_grupo", "No definido"))
        conv_state["datos_categoria"]["mas_informacion"] = result.get("mas_informacion", conv_state["datos_categoria"].get("mas_informacion", "No definido"))

        # 📌 Debugging: Verificar si se actualiza correctamente
        print("📌 datos_categoria actualizado antes de guardar:", json.dumps(conv_state["datos_categoria"], indent=4, ensure_ascii=False))

        # Guardamos la nueva información en Supabase
        save_dynamic_state(conv_state.to_dict())
    else:
        print("⚠️ La respuesta de OpenAI no contiene datos válidos para actualizar `datos_categoria`.")

    # 🔹 **8️⃣ Si `"respuesta_al_cliente"` es `null`, significa que ya tiene toda la información**
    if result.get("respuesta_al_cliente") is None:
        print("✅ Ya tiene toda la información necesaria, no se hacen más preguntas.")
        return "Ya tengo toda la información necesaria. Te mostraré las mejores actividades en breve."

    # 🔹 **9️⃣ Si falta información, devolver la pregunta al usuario**
    return result["respuesta_al_cliente"]