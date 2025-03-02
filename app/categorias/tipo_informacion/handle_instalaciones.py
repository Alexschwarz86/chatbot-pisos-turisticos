import os
import json
from dotenv import load_dotenv
from app.database import get_conversation_state, save_conversation_state, supabase

# 🔹 Cargar variables de entorno
load_dotenv()

def handle_apartment_info(user_id, user_message, nombre_apartamento):
    """
    Recupera la información del apartamento directamente desde Supabase 
    y responde con los detalles solicitados de las instalaciones.
    """

    # 🔹 **1️⃣ Recuperar datos del apartamento desde Supabase**
    response = supabase.table("apartamentos").select("instalaciones").eq("nombre", nombre_apartamento).execute()
    
    if not response.data:
        return f"❌ No hemos encontrado información sobre el apartamento '{nombre_apartamento}' en nuestra base de datos."

    # 🔹 **2️⃣ Extraer las instalaciones del apartamento**
    instalaciones = response.data[0].get("instalaciones", {})
    if not instalaciones:
        return f"❌ No hay detalles de las instalaciones disponibles para el apartamento '{nombre_apartamento}'."

    # 🔹 **3️⃣ Generar el prompt para OpenAI**
    info_prompt = f"""
   Eres un asistente de apartamentos turísticos.  
📌 **Responde SOLO con información del apartamento basada en la pregunta del usuario.**  
📌 **Usa exclusivamente los datos del JSON de instalaciones proporcionado.**  
📌 **Si la información no está en el JSON, responde que no tienes datos sobre eso.**  
📌 **NO inventes información ni asumas nada.**  

🔹 **Apartamento asignado:** {nombre_apartamento}  
🔹 **Lista de instalaciones del apartamento:**  

El siguiente JSON contiene TODAS las instalaciones disponibles en el apartamento. Usa esta información para responder la pregunta del usuario. Si la instalación no está en la lista, responde que no está disponible.

📌 **Instalaciones del apartamento en JSON:**  
{json.dumps(instalaciones, ensure_ascii=False, indent=2)}

🔹 **Pregunta del usuario:**  
"{user_message}"

🔹 **Ejemplo de respuesta esperada:**  
- Usuario: "¿Hay secador de pelo?"  
- Respuesta: "Sí, este apartamento dispone de secador de pelo en el baño."  
- Usuario: "¿Tiene piscina?"  
- Respuesta: "No, este apartamento no dispone de piscina."  

🔹 **IMPORTANTE:** Devuelve una respuesta directa y breve sin explicaciones adicionales.
"""
    print(f"Open ia respuestaaaaaaa:{info_prompt}")
    # 🔹 **4️⃣ Llamada a OpenAI para generar la respuesta**
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": info_prompt}],
        max_tokens=200,
        temperature=0
    )

    response_text = response.choices[0].message.content.strip()
    print(f"📌 Respuesta generada por OpenAI: {response_text}")

    return response_text

# 🔹 **Ejemplo de uso**
if __name__ == "__main__":
    user_id = "44"  # ID de ejemplo
    nombre_apartamento = "Apartamento Sol"  # Nombre del apartamento asignado
    user_message = "¿El apartamento tiene aire acondicionado y WiFi?"  # Pregunta de ejemplo

    response = handle_apartment_info(user_id, user_message, nombre_apartamento)
    print(response)