import os
import json
from openai import OpenAI  # Cliente OpenAI
from dotenv import load_dotenv
from app.database import save_dynamic_state, get_dynamic_state

# Cargar variables de entorno
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 🔹 **Plantilla del prompt con memoria híbrida**
PROMPT_TEMPLATE = """
Eres un asistente que clasifica mensajes en función de su intención.  
📌 **Tu tarea clasificar el mensaje del cliente con la categoría que encaje más**.  
NO clasifiques mensajes individualmente. Siempre analiza el contexto previo antes de decidir la categoría.  

## 📌 **CATEGORÍAS DISPONIBLES**:
1️⃣ **informacion_alojamiento** - Preguntas sobre características del alojamiento (wifi, toallas, normas, penalizaciones, ubicación, etc.)  
2️⃣ **averia_estancia** - Reportes de problemas o averías en la estancia  
3️⃣ **servicios_adicionales** - Cuando la persona pregunta sobre servicios limpieza, toallas, tranporte privado(Si la persona te pregunte si le pueden ir a buscar o llevar algun lugar).  
4️⃣ **recomendaciones_personalizadas** - Preguntas sobre turismo, comida y actividades en la zona  
5️⃣ **alquilar_mas_dias** - Peticiones para extender la estancia  
6️⃣ **descuentos_promociones** - Preguntas sobre ofertas y descuentos  

🔹 **Si el mensaje no encaja en ninguna categoría, usa "indeterminado".**

🔹 **Reglas importantes**:
- **Nunca clasifiques mensajes de forma aislada.** Siempre analiza el historial previo.  
- **Si el usuario responde a una pregunta del bot, NO cambies la categoría.**  
- **Si el usuario dice "sí", "no" o da más detalles, asume que está respondiendo al mensaje anterior.**  
- **Si el usuario cambia completamente de tema, entonces sí puedes cambiar la categoría.**  

📌 **Historial de conversación reciente (incluyendo memoria de Supabase):**  
{historial}

📌 **Mensaje actual del usuario:**  
"{mensaje_usuario}"  

🔹 **Devuelve SIEMPRE un JSON puro con esta estructura exacta (sin texto adicional, sin explicaciones, sin backticks):**  
json
{{
  "idioma": "Idioma en el que te envía el mensaje el cliente, ejemplo: es",
  "intenciones": ["La categoría que has clasificado ejemplo: informacion_alojamiento"],
  "confidence": <número entre 0 y 1>,
  "original_text": "{mensaje_usuario}"
}}
"""

def analyze_message(user_message: str, numero: str) -> dict:
    # 🔹 1️⃣ Recuperar estado del usuario desde Supabase
    conv_state = get_dynamic_state(numero)

    # 🔹 2️⃣ Construir historial de conversación en formato OpenAI (últimos 10 mensajes)
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": msg["usuario"]})
            historial.append({"role": "assistant", "content": msg["bot"] if isinstance(msg["bot"], str) else json.dumps(msg["bot"], ensure_ascii=False)})

    print(f"📌 Estado de idioma antes del prompt: {conv_state.idioma}")
    print("📌 Historial enviado a OpenAI:", json.dumps(historial, indent=2, ensure_ascii=False))
    print("📌 Prompt enviado a OpenAI:\n", PROMPT_TEMPLATE)
    # ✅ Asegurar que `datos_categoria` sea un diccionario antes de acceder a `.get()`
    if not isinstance(conv_state.datos_categoria, dict):
        try:
            conv_state.datos_categoria = json.loads(conv_state.datos_categoria)
        except (json.JSONDecodeError, TypeError):
            conv_state.datos_categoria = {}  # ✅ Si hay error, inicializarlo como dict vacío

    # ✅ Generar `final_prompt` de manera segura
    final_prompt = PROMPT_TEMPLATE \
        .replace("{idioma}", conv_state.idioma if isinstance(conv_state.idioma, str) and conv_state.idioma else "desconocido") \
        .replace("{tipo_comida}", conv_state.datos_categoria.get("tipo_cocina", "No definido")) \
        .replace("{budget}", conv_state.datos_categoria.get("budget", "No definido")) \
        .replace("{categoria_activa}", conv_state.categoria_activa if isinstance(conv_state.categoria_activa, str) else "desconocido") \
        .replace("{historial}", json.dumps(historial, ensure_ascii=False, indent=2)) \
        .replace("{mensaje_usuario}", user_message)

    # 🔹 4️⃣ Llamada a la API de OpenAI
    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente que clasifica mensajes en función de su intención. Tu tarea es clasificar el mensaje del cliente con la categoría que encaje más. NO clasifiques mensajes individualmente. Siempre analiza el contexto previo antes de decidir la categoría."},
            {"role": "user", "content": final_prompt}
        ],
        max_tokens=200,
        temperature=0
    )

    response_text = completion.choices[0].message.content.strip()
    print("📌 Respuesta completa de OpenAI:", response_text)

    # 🔹 5️⃣ Primero limpiamos las backticks (si existen)
    if response_text.startswith("```json"):
        response_text = response_text[7:].strip()  # Elimina ```json
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()  # Elimina ```

    # 🔹 6️⃣ Intentar parsear la respuesta de OpenAI como JSON
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

    # 🔹 7️⃣ Guardar historial correctamente en Supabase
    try:
        conv_state.historial.append({"usuario": user_message, "bot": result})  # Guardamos dict, no string
        conv_state.historial = conv_state.historial[-10:]  # Limitamos historial a 10 mensajes
        save_dynamic_state(conv_state.to_dict())  # Guardar en `dinamic`
        print("✅ Historial guardado correctamente en `dinamic` desde nlu.py")
    except Exception as e:
        print(f"❌ Error al guardar historial en Supabase: {e}")

    return result