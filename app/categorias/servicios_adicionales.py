import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.database import get_dynamic_state
from app.categorias.servicios.limpiezas import handle_limpieza
from app.categorias.servicios.transporte import handle_transporte
# Cargar variables de entorno
load_dotenv()

# Verificar si la clave API está configurada correctamente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: La API Key de OpenAI no está configurada correctamente.")
client = OpenAI(api_key=api_key)

def categorizar_servicio_adicional(numero, user_message):
    """
    Clasifica el mensaje del usuario en una de las siguientes categorías:
    
    1️⃣ Limpieza
    2️⃣ Transporte (cuando el usuario necesita un vehículo de punto A a B)
    3️⃣ Packs
    4️⃣ Alquiler de Toallas y Sombrillas
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria en Supabase)**
    conv_state = get_dynamic_state(numero)

    # 🔹 **2️⃣ Construcción de memoria híbrida (Supabase + Ventana de tokens)**
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": msg["usuario"]})

            bot_response = msg["bot"]
            if isinstance(bot_response, dict):
                bot_response = json.dumps(bot_response, ensure_ascii=False)  

            historial.append({"role": "assistant", "content": bot_response})

    # 📌 **3️⃣ Generar el prompt para OpenAI**
    classification_prompt = f"""
    Eres un asistente experto en clasificar consultas de usuarios sobre servicios adicionales.  
    📌 **Tu tarea es analizar el mensaje y clasificarlo en una de las siguientes categorías:**  
    
    1️⃣ **Limpieza** - Solicitudes de limpieza extra en el apartamento.  
    2️⃣ **Transporte** - Cuando el usuario necesita transporte de un punto a otro.  
    3️⃣ **Packs** - Preguntas sobre paquetes especiales o servicios adicionales.  
    4️⃣ **Alquiler de Toallas y Sombrillas** - Preguntas sobre alquiler de toallas y sombrillas.  
    
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
        if category_result.get("Categoria") == "Limpieza":
            return handle_limpieza(numero, user_message)
        elif category_result.get("Categoria") == "Transporte":
            return handle_transporte(numero, user_message)
        elif category_result.get("Categoria") == "Packs":
            return handle_packs(numero, user_message)
        elif category_result.get("Categoria") == "Alquiler de Toallas y Sombrillas":
            return handle_alquiler_toallas_sombrillas(numero, user_message)
    except Exception as e:
        print(f"❌ Error en clasificación de categoría: {e}")
        return {"Categoria": "Servicios y Otros"}  # Por defecto
