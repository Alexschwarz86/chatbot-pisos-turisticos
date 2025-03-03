import os
import json
from datetime import datetime
from app.database import get_dynamic_state, save_dynamic_state
from openai import OpenAI

# Cargar la API Key de OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def handle_transporte(numero, user_message):
    """
    Maneja solicitudes de transporte privado registrando origen, destino, día y hora en memoria híbrida.
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria en Supabase)**
    conv_state = get_dynamic_state(numero)

    # 🔹 **2️⃣ Construcción de memoria híbrida**
    historial = []
    for msg in conv_state.historial[-10:]:  
        if isinstance(msg, dict) and "usuario" in msg and "bot" in msg:
            historial.append({"role": "user", "content": str(msg["usuario"])})  
            bot_response = msg["bot"]
            if isinstance(bot_response, dict):  
                bot_response = json.dumps(bot_response, ensure_ascii=False)  
            historial.append({"role": "assistant", "content": str(bot_response)})  

    # 📌 **3️⃣ Generar el prompt para OpenAI**
    info_prompt = f"""
Eres un asistente especializado en gestionar solicitudes de transporte privado.  
📌 **Tu objetivo es asegurar que el usuario proporciona toda la información necesaria antes de registrar su solicitud.**  
📌 **Si falta algún dato, pregunta hasta obtenerlo.**  

### **🔹 Reglas de Inferencia Automática**  
✅ **Si el usuario dice "¿Me pueden recoger en X lugar?"**, asume que el destino es **Calafell** (pero confirma).  
✅ **Si el usuario dice "¿Me pueden llevar a X lugar?"**, asume que el origen es **Calafell** (pero confirma).  
✅ **Si el usuario menciona un punto de referencia importante (ej: "PortAventura")**, asume que **sale de Calafell** (pero confirma).  
✅ **Si el usuario menciona tanto el origen como el destino, solo confirma los datos.**  
✅ **Si falta información, pregunta solo por lo que falta.**  

📌 **Datos actuales en memoria:**  
- **Origen:** {conv_state.datos_categoria.get("origen", "No definido")}
- **Destino:** {conv_state.datos_categoria.get("destino", "No definido")}
- **Día:** {conv_state.datos_categoria.get("dia", "No definido")}
- **Hora:** {conv_state.datos_categoria.get("hora", "No definido")}

📌 **Conversación Reciente (Ventana de Tokens)**:
{json.dumps(historial, ensure_ascii=False, indent=2)}

📌 **Mensaje del usuario**:
"{user_message}"

📌 **Estructura de respuesta esperada**:
{{
    "origen": "<ciudad de origen o 'No definido'>",
    "destino": "<ciudad de destino o 'No definido'>",
    "dia": "<día del viaje o 'No definido'>",
    "hora": "<hora del viaje o 'No definido'>",
    "respuesta_al_cliente": "<pregunta para el usuario o null si ya tienes todo>"
}}
"""
    # 🔹 **4️⃣ Llamada a OpenAI**
    info_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": info_prompt}],
        max_tokens=100,
        temperature=0
    )

    print("📌 Prompt enviado a OpenAI:\n", info_prompt)
    response_text = info_response.choices[0].message.content.strip()
    print("📌 Respuesta completa de OpenAI:", response_text)

    # 🔹 **5️⃣ Eliminar backticks antes de parsear JSON**
    if response_text.startswith("```json"):
        response_text = response_text[7:].strip()  
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()  

    # 🔹 **6️⃣ Validar si la respuesta es realmente un JSON**
    try:
        result = json.loads(response_text)  
    except json.JSONDecodeError:
        print("❌ OpenAI no devolvió un JSON válido. Usando respuesta normal.")
        return response_text  

    # 🔹 **7️⃣ Guardar la información en memoria híbrida**
    if isinstance(result, dict):  
        conv_state.datos_categoria["origen"] = result.get("origen", conv_state.datos_categoria.get("origen", "No definido"))
        conv_state.datos_categoria["destino"] = result.get("destino", conv_state.datos_categoria.get("destino", "No definido"))
        conv_state.datos_categoria["dia"] = result.get("dia", conv_state.datos_categoria.get("dia", "No definido"))
        conv_state.datos_categoria["hora"] = result.get("hora", conv_state.datos_categoria.get("hora", "No definido"))

        # 📌 Debugging: Verificar actualización correcta
        print("📌 datos_categoria actualizado antes de guardar:", json.dumps(conv_state.datos_categoria, indent=4, ensure_ascii=False))

        # Guardamos la nueva información en Supabase
        # ✅ Asegurar que 'conversation_data' es un diccionario antes de serializar
        conversation_data = conv_state.to_dict()

# ✅ Serializar correctamente a JSON
        try:
            print("📌 Datos que se van a guardar en Supabase:", json.dumps(conversation_data, indent=4, ensure_ascii=False))
        except TypeError as e:
         print(f"❌ Error al serializar datos para Supabase: {e}")
        
        save_dynamic_state(conv_state.to_dict())
    else:
        print("⚠️ La respuesta de OpenAI no contiene datos válidos para actualizar `datos_categoria`.")

    # 🔹 **8️⃣ Si `"respuesta_al_cliente"` es `null`, significa que ya tiene toda la información**
    if result.get("respuesta_al_cliente") is None:
        print("✅ Solicitud de transporte registrada correctamente.")
        return "Tu solicitud de transporte ha sido registrada. Contactaremos contigo para confirmarla."

    # 🔹 **9️⃣ Si falta información, devolver la pregunta al usuario**
    return result["respuesta_al_cliente"]