import os
import json
from openai import OpenAI  # Cliente OpenAI
from dotenv import load_dotenv
from app.database import get_conversation_state, save_conversation_state

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 🔹 **Plantilla del prompt con memoria híbrida**
PROMPT_TEMPLATE = """
Eres un asistente que clasifica un mensaje de usuario en una o varias de las siguientes categorías:

📌 **CATEGORÍAS DISPONIBLES:**
1️⃣ informacion_alojamiento - Preguntas sobre características (wifi, toallas, normas, ubicación, etc.)
2️⃣ problemas_estancia - Reportes de problemas o averías en la estancia
3️⃣ servicios_adicionales - Solicitud de servicios extra (limpieza, toallas, comida, etc.)
4️⃣ recomendaciones_personalizadas - Preguntas sobre turismo, comida y actividades en la zona
5️⃣ alquilar_mas_dias - Peticiones para extender la estancia
6️⃣ descuentos_promociones - Preguntas sobre ofertas y descuentos

🔹 **Si el mensaje no encaja en ninguna categoría, usa "indeterminado".**
🔹 **Devuelve SIEMPRE un JSON con esta estructura exacta (sin texto adicional):**
json
{
  "idioma": "<código_idioma>",
  "intenciones": ["<una_o_mas_categorias>"],
  "confidence": <número entre 0 y 1>,
  "original_text": "<mensaje original>"
}
Historial de conversación reciente:
{historial}

 Mensaje actual del usuario:
“{mensaje_usuario}”
"""

def analyze_message(user_message: str, user_id: str) -> dict:
    """
    Usa OpenAI para clasificar un mensaje, teniendo en cuenta el historial reciente.
    """

    # 🔹 1️⃣ Recuperar estado del usuario desde Supabase
    conv_state = get_conversation_state(user_id)

    # 🔹 2️⃣ Construir historial de conversación en formato OpenAI
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": msg["usuario"]})
            historial.append({"role": "assistant", "content": msg["bot"] if isinstance(msg["bot"], str) else json.dumps(msg["bot"], ensure_ascii=False)})

    # 🔹 3️⃣ Construir el prompt con historial y mensaje del usuario
    final_prompt = PROMPT_TEMPLATE.replace("{historial}", json.dumps(historial, ensure_ascii=False)).replace("{mensaje_usuario}", user_message)

    # 🔹 4️⃣ Llamada a la API de OpenAI
    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Eres un experto en clasificación de intenciones."},
            {"role": "user", "content": final_prompt}
        ],
        max_tokens=200,
        temperature=0
    )

    response_text = completion.choices[0].message.content.strip()
    print("📌 Respuesta completa de OpenAI:", response_text)

    # 🔹 5️⃣ Primero limpiamos las backticks (si existen):
    # Por ejemplo, podemos usar un simple replace (o una expresión regular).
    if response_text.startswith("```json"):
        response_text = response_text[7:].strip()  # Elimina ```json
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()  # Elimina ```
    
    # Ahora que 'response_text' está limpio, lo parseamos:
    try:
        result = json.loads(response_text)
        print("📌 Respuesta procesada como JSON:", result)
        
        if not isinstance(result, dict) or "idioma" not in result or "intenciones" not in result:
            raise ValueError("Respuesta inválida de OpenAI: faltan campos obligatorios")

        # Si la lista de intenciones está vacía, forzamos 'indeterminado'
        if not result["intenciones"]:
            result["intenciones"] = ["indeterminado"]

    except json.JSONDecodeError:
        print("❌ Error al convertir la respuesta de OpenAI en JSON")
        result = {
            "idioma": "desconocido",
            "intenciones": ["indeterminado"],
            "confidence": 0.0,
            "original_text": user_message
        }
    except Exception as e:
        print(f"❌ Error inesperado en OpenAI: {e}")
        result = {
            "idioma": "desconocido",
            "intenciones": ["indeterminado"],
            "confidence": 0.0,
            "original_text": user_message
        }
    # 🔹 6️⃣ Guardar historial correctamente en Supabase
    try:
        conv_state.historial.append({"usuario": user_message, "bot": result})  # Guardamos dict, no string
        conv_state.historial = conv_state.historial[-10:]  # Limitamos historial a 10 mensajes
        save_conversation_state(conv_state)
    except Exception as e:
        print(f"❌ Error al guardar historial en Supabase: {e}")

    return result