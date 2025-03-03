import os
import json
from dotenv import load_dotenv
from app.database import get_dynamic_state, save_dynamic_state

# 🔹 Cargar variables de entorno
load_dotenv()

def handle_issue_report(numero, user_message):
    """
    Maneja solicitudes de averías o problemas en el piso.
    Extrae el problema y una breve descripción sin preguntar por la ubicación.
    """

    # 🔹 **1️⃣ Obtener estado dinámico del usuario en Supabase**
    conv_state = get_dynamic_state(numero)

    # 🔹 **2️⃣ Revisar si ya tiene la información necesaria**
    problema = conv_state.datos_categoria.get("problema", "No definido")
    descripcion = conv_state.datos_categoria.get("descripcion", "No definido")
    # 🔍 **Debugging: Ver datos en memoria**
    print(f"📌 user_message recibido: {user_message}")
    print(f"📌 Estado actual en memoria: {conv_state.datos_categoria}")

    # 🔹 **3️⃣ Generar el prompt para OpenAI**
    issue_prompt = f"""
    Eres un asistente que gestiona problemas en apartamentos turísticos.
    📌 **Tu tarea es identificar el problema y dar una breve descripción basada en el mensaje del usuario.**

    ⚠️ **Si el usuario menciona que no sabe lo que ocurre, debes registrar "persona no sabe" en la descripción.**

    📌 **Mensaje del usuario**:
    "{user_message}"

    📌 **Estructura esperada en JSON**:
    {{
        "problema": "<Ej: No hay agua caliente / Se ha roto la cafetera / Hay una fuga>",
        "descripcion": "<Breve explicación del problema o 'persona no sabe' si el usuario no lo tiene claro>"
    }}
    """

    # 🔹 **4️⃣ Llamada a OpenAI para procesar el mensaje**
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    issue_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": issue_prompt}],
        max_tokens=150,
        temperature=0
    )

    response_text = issue_response.choices[0].message.content.strip()
    print(f"📌 Respuesta de OpenAI: {response_text}")  # 🔍 Ver la respuesta de OpenAI

    # 🔹 **5️⃣ Validar si la respuesta es JSON**
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        return "❌ Hubo un problema al procesar tu solicitud, intenta de nuevo."

    # 🔹 **6️⃣ Guardar información nueva en `dinamic`**
    if isinstance(result, dict):
        conv_state.datos_categoria["problema"] = result.get("problema", problema)
        conv_state.datos_categoria["descripcion"] = result.get("descripcion", descripcion)
        save_dynamic_state(conv_state.to_dict())  # Guardamos en Supabase

    # 🔹 **7️⃣ Confirmar el reporte**
    return confirm_issue_report(conv_state, numero)


def confirm_issue_report(conv_state, numero):
    """
    Confirma el reporte del problema con la información recopilada.
    """
    problema = conv_state.datos_categoria.get("problema", "No definido")
    descripcion = conv_state.datos_categoria.get("descripcion", "No definido")   
    if problema == "No definido":
        return "❌ Error: No se puede reportar el problema porque falta información."

    return f"✅ Hemos registrado tu reporte: '{problema}'. Detalles adicionales: {descripcion}. Nos pondremos en contacto contigo pronto."

# 🔹 **Ejemplo de uso**
if __name__ == "__main__":
    numero = "644123456"  # Simulación de número de teléfono en lugar de user_id
    user_message = "No sale agua caliente en la ducha, pero no sé por qué."  # Mensaje de ejemplo

    response = handle_issue_report(numero, user_message)
    print(response)