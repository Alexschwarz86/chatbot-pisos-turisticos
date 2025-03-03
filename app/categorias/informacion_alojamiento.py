import os
import json
from dotenv import load_dotenv
from app.database import get_dynamic_state, save_dynamic_state
from openai import OpenAI
from openai import OpenAI
from app.categorias.tipo_informacion.handle_instalaciones import handle_apartment_info
from app.categorias.tipo_informacion.handle_normas import handle_normas_info
from app.categorias.tipo_informacion.handle_penalizaciones import handle_penalizacion_info
# Cargar variables de entorno
# 🔹 Cargar variables de entorno
load_dotenv()

# 🔹 Verificar si la clave API está configurada correctamente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: La API Key de OpenAI no está configurada correctamente.")
client = OpenAI(api_key=api_key)


def categorizar_pregunta_informacion(numero, user_message,nombre_apartamento):
    """
    Clasifica el mensaje del usuario en una de las siguientes categorías:

    1️⃣ **Instalaciones** - Preguntas sobre servicios del apartamento (ej. "¿Tienen WiFi?")
    2️⃣ **Normas** - Preguntas sobre reglas de convivencia (ej. "¿A qué hora no se puede hacer ruido?")
    3️⃣ **Penalizaciones** - Preguntas sobre consecuencias de ciertas acciones (ej. "¿Qué pasa si pierdo las llaves?")
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria en Supabase)**
    conv_state = get_dynamic_state(numero)

    # 🔹 **2️⃣ Construcción de memoria híbrida (Supabase + Ventana de tokens)**
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": msg["usuario"]})

            # Convertir bot a string si es un diccionario
            bot_response = msg["bot"]
            if isinstance(bot_response, dict):
                bot_response = json.dumps(bot_response, ensure_ascii=False)  

            historial.append({"role": "assistant", "content": bot_response})

    # 📌 **3️⃣ Generar el prompt para OpenAI**
    classification_prompt = f"""
    Eres un asistente experto en clasificar preguntas de usuarios sobre su estancia en un apartamento turístico.  
    📌 **Tu tarea es analizar el mensaje y clasificarlo en una de las siguientes categorías:**  

    1️⃣ **Instalaciones** - Preguntas sobre servicios y comodidades del apartamento (ej. "¿Tienen WiFi?", "¿Hay secador de pelo?").  
    2️⃣ **Normas** - Preguntas sobre reglas y comportamiento dentro del apartamento (ej. "¿A qué hora hay que hacer silencio?").  
    3️⃣ **Penalizaciones** - Preguntas sobre consecuencias de ciertas acciones (ej. "¿Cuánto cuesta perder las llaves?").  

    📌 **Reglas importantes:**  
    🔹 **Usa solo las categorías indicadas.**  
    🔹 **Si el mensaje no encaja exactamente en una categoría, elige la más cercana.**  

    📌 **Historial de conversación reciente:**  
    {json.dumps(historial, ensure_ascii=False, indent=2)}

    📌 **Mensaje del usuario:**  
    "{user_message}"  

    🔹 **Devuelve SIEMPRE un JSON puro con esta estructura exacta (sin texto adicional, sin backticks):**  
    {{
      "Categoria": "<nombre de la categoría>"
    }}
    """

    # 🔹 **4️⃣ Llamada a OpenAI**
    try:
        classification_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": classification_prompt}],
            max_tokens=50,
            temperature=0
        )
        
        response_text = classification_response.choices[0].message.content.strip()
        category_result = json.loads(response_text)

        print("📌 Respuesta de OpenAI para clasificación:", category_result)

        # 🔹 **5️⃣ Redirigir la consulta a la función correspondiente**
        if category_result.get("Categoria") == "Instalaciones":
            return handle_apartment_info(numero, user_message,nombre_apartamento)
        elif category_result.get("Categoria") == "Normas":
            return handle_normas_info(numero, user_message,nombre_apartamento)
        elif category_result.get("Categoria") == "Penalizaciones":
            return handle_penalizacion_info(numero, user_message,nombre_apartamento)
    except Exception as e:
        print(f"❌ Error en clasificación de categoría: {e}")
        return {"Categoria": "No clasificado"}  # Por defecto