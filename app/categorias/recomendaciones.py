import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.database import get_conversation_state
from app.categorias.tipo_de_recomendacion.recomendaciones_restaurantes import handle_recomendaciones 
from app.categorias.tipo_de_recomendacion.actividades_ocio import handle_actividades_ocio
from app.categorias.tipo_de_recomendacion.transporte_movilidad import handle_transporte
# Cargar variables de entorno
load_dotenv()

# Verificar si la clave API está configurada correctamente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: La API Key de OpenAI no está configurada correctamente.")
client = OpenAI(api_key=api_key)


def categorizar_recomendacion(user_id, user_message,nombre_apartamento):
    """
    Clasifica el mensaje del usuario en una de las siguientes categorías:
    
    1️⃣ Actividades y Ocio
    2️⃣ Restaurantes y Comida
    3️⃣ Transporte y Movilidad
    4️⃣ Eventos y Entretenimiento
    5️⃣ Servicios y Otros
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria en Supabase)**
    conv_state = get_conversation_state(user_id)

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
    Eres un asistente experto en clasificar consultas de usuarios en función de su contenido.  
    📌 **Tu tarea es analizar el mensaje y clasificarlo en una de las siguientes categorías:**  

    1️⃣ **Actividades y Ocio** - Lugares para visitar, tours, excursiones.  
    2️⃣ **Restaurantes y Comida** - Opciones para comer, tipos de cocina, precios.  
    3️⃣ **Transporte y Movilidad** - Cómo moverse por la zona, transporte público.  
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
        if category_result.get("Categoria") == "Restaurantes y Comida":
            return handle_recomendaciones(user_id, user_message)
        elif category_result.get("Categoria") == "Actividades y Ocio":
            return handle_actividades_ocio(user_id, user_message)
        elif category_result.get("Categoria") == "Transporte y Movilidad":
            return handle_transporte(user_id, user_message,nombre_apartamento)
    except Exception as e:
        print(f"❌ Error en clasificación de categoría: {e}")
        return {"Categoria": "Servicios y Otros"}  # Por defecto