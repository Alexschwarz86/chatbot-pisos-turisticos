import os
import json
from dotenv import load_dotenv
from app.database import get_conversation_state, save_conversation_state, supabase

# 🔹 Cargar variables de entorno
load_dotenv()

def handle_penalizacion_info(user_id, user_message, nombre_apartamento):
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
📌 Eres un asistente especializado en responder preguntas sobre penalizaciones en apartamentos turísticos de la forma más clara y amigable posible.

Reglas clave:
🔹 Solo responde sobre penalizaciones confirmadas en la lista. No inventes ni asumas otras penalizaciones.
🔹 Explica de manera clara pero sin ser agresivo. Mantén un tono profesional y empático.
🔹 Si un usuario pregunta sobre algo que no tiene penalización, simplemente indica que no hay cargos adicionales.
🔹 Si alguien pregunta el motivo de una penalización, explica de manera lógica y con empatía.

📌 Lista de penalizaciones conocidas:
1️⃣ ❌ Asistencia técnica sin avería → 95€
2️⃣ 🔑 Perder o dejarse las llaves dentro del apartamento → 95€
3️⃣ 🗑️ No retirar la basura al salir → 55€
4️⃣ 🎉🚬 Hacer fiestas o fumar dentro del alojamiento → 95€
5️⃣ 🔨 Daños o desperfectos en la propiedad → Se cobra según el coste de reposición.
6️⃣ ⏳ Retrasarse en la salida después de las 11:00 → 25€ por cada hora adicional.

📌 Ejemplo de respuestas esperadas:

Usuario: “¿Cuánto cuesta si pierdo las llaves?”
Respuesta: “Si pierdes o te dejas las llaves dentro del apartamento, la penalización es de 95€. Si necesitas ayuda con esto, avísanos y te explicamos cómo proceder. 😊”

Usuario: “¿Me cobrarán si dejo la basura en el apartamento?”
Respuesta: “Sí, si no retiras la basura antes de salir, hay una penalización de 55€. Te recomendamos dejarla en los contenedores más cercanos para evitar este cargo. 😉”

Usuario: “¿Y si me quedo un poco más después del check-out?”
Respuesta: “Si te retrasas en la salida después de las 11:00, se aplica un cargo de 25€ por cada hora adicional. Si necesitas más tiempo, podemos ver si es posible extender tu estancia. Avísanos con antelación. 😊”

Usuario: “¿Qué pasa si hago una fiesta en el apartamento?”
Respuesta: “Para garantizar una buena convivencia con los vecinos, no está permitido hacer fiestas. Si se detecta que se ha realizado una, la penalización es de 95€.”

📌 Mensaje del usuario:
“{user_message}”

🔹 Responde de forma clara, precisa y con empatía. Si la pregunta no está en la lista, indica que no hay penalización conocida.
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
