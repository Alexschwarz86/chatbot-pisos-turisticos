import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.database import get_conversation_state
from app.categorias.tipo_de_recomendacion import recomendaciones_restaurantes
# Cargar variables de entorno
load_dotenv()

# Verificar si la clave API está configurada correctamente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: La API Key de OpenAI no está configurada correctamente.")
client = OpenAI(api_key=api_key)

def categorizar_recomendacion(user_id, user_message):
    """
    Clasifica el mensaje del usuario en una de las siguientes categorías:
    
    1️⃣ Actividades y Ocio
    2️⃣ Restaurantes y Comida
    3️⃣ Transporte y Movilidad
    4️⃣ Eventos y Entretenimiento
    5️⃣ Servicios y Otros
    """

    # 🔹 **Obtener estado del usuario**
    conv_state = get_conversation_state(user_id)

    # 🔹 **Construir historial de conversación en formato compatible con OpenAI**
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": msg["usuario"]})
            
            # Si "bot" es un diccionario, convertirlo a string antes de enviarlo a OpenAI
            bot_response = msg["bot"]
            if isinstance(bot_response, dict):
                bot_response = json.dumps(bot_response, ensure_ascii=False)  

            historial.append({"role": "assistant", "content": bot_response})

    # 🔹 **Prompt para la clasificación de categorías**
    classification_prompt = [
        {"role": "system", "content": "Eres un clasificador de mensajes experto en categorizar consultas de usuarios en función de su contenido."},
    ]

    if historial:
        classification_prompt += historial[-10:]  # Agregar solo los últimos 10 mensajes
    
    classification_prompt.append(
        {"role": "user", "content": f"Clasifica este mensaje en una de las siguientes categorías:\n\n"
                                    "1️⃣ Actividades y Ocio\n"
                                    "2️⃣ Restaurantes y Comida\n"
                                    "3️⃣ Transporte y Movilidad\n"
                                    "4️⃣ Eventos y Entretenimiento\n"
                                    "5️⃣ Servicios y Otros\n\n"
                                    "Responde con un JSON:\n"
                                    "{\n   \"Categoria\": \"<nombre de la categoría>\"\n}\n\n"
                                    f"📌 **Mensaje del usuario:**\n\"{user_message}\""}
    )

    # 🔹 **Llamada a la API de OpenAI**
    try:
        classification_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=classification_prompt,
            max_tokens=50,
            temperature=0
        )

        response_text = classification_response.choices[0].message.content.strip()
        print("📌 Respuesta de OpenAI:", response_text)

        # 🔹 **Convertir la respuesta a JSON**
        result = json.loads(response_text)
        if not isinstance(result, dict) or "Categoria" not in result:
            raise ValueError("La respuesta de OpenAI no tiene una estructura válida.")
    
    except json.JSONDecodeError:
        print("❌ Error al convertir la respuesta de OpenAI en JSON")
        result = {"Categoria": "indeterminado"}
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        result = {"Categoria": "indeterminado"}

    if result["Categoria"] == "Restaurantes y Comida":
        return recomendaciones_restaurantes.handle_recomendaciones(user_id, user_message)
    
    return f"Tu mensaje se ha clasificado en la categoría '{result['Categoria']}'."  # Respuesta general si no es comida