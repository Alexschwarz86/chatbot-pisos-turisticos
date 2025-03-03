import os
import json
from dotenv import load_dotenv
from app.database import get_dynamic_state, save_dynamic_state,supabase
# 🔹 Cargar variables de entorno
load_dotenv()

def handle_normas_info(numero, user_message, nombre_apartamento):
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
 
    info_prompt = f"""
📌 Eres un asistente de apartamentos turísticos especializado en responder preguntas sobre normas de convivencia de la forma más natural y humana posible.

Reglas clave:
🔹 Siempre responde en un tono amigable y cercano, sin sonar robótico ni demasiado formal.
🔹 Usa la lógica para interpretar normas aunque no estén explícitas.
🔹 Si la norma no está mencionada, responde con sentido común.
🔹 Si una norma es estricta, explícalo con suavidad y ofreciendo alternativas si es posible.

📌 Normas conocidas del apartamento:
	•	❌ No se puede hacer ruido a partir de las 10 PM hasta las 8 AM, no hacer fiestas
    •	❌No se puede fumar
    •	❌No mascotas
    •	❌Solo huesoedes registrados
    •	❌Al salir del check out hay que sacar la basura
	•	⚠️ El resto de normas no están especificadas, usa sentido común para responder.

📌 Ejemplo de respuestas esperadas:
Usuario: “¿Puedo poner música alta por la noche?”
Respuesta: “Lo mejor es mantener el volumen bajo a partir de las 9 PM para no molestar a los vecinos. Si quieres disfrutar de música, te recomendaría usar auriculares. 😊”

Usuario: “¿Se pueden traer invitados?”
Respuesta: “No hay una norma específica sobre esto, pero lo ideal es mantener un ambiente tranquilo y respetar la privacidad de los demás huéspedes. Si planeas traer a alguien, intenta que no sea un grupo grande y evita ruidos molestos.”

Usuario: “¿Puedo fumar dentro del apartamento?”
Respuesta: “No tengo información sobre una norma específica, pero en la mayoría de apartamentos turísticos no está permitido fumar en interiores. Puedes revisar si hay una zona habilitada para fumadores o preguntar a la recepción. 😊”

📌 Mensaje del usuario:
“{user_message}”

🔹 Genera una respuesta breve, clara y humana. Si no tienes suficiente información, responde con tacto y sin inventar reglas.
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
