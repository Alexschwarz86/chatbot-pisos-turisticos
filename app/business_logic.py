from app.database import get_conversation_state, save_conversation_state
from app.categorias.recomendaciones import categorizar_recomendacion
from app.categorias.manejo_limpieza import handle_cleaning_request 
from app.categorias.averia_estancia import handle_issue_report
from app.categorias.informacion_alojamiento import handle_apartment_info
def handle_intents(user_id, analysis_result, user_message, conv_state, nombre_apartamento) -> str:
    """
    Recibe el ID de usuario, el resultado del análisis NLU y el mensaje original.
    Gestiona la intención detectada y devuelve la respuesta adecuada.
    """

    # 🔹 **1️⃣ Obtener estado del usuario (Memoria a Largo Plazo - Supabase)**
    conversation_state = get_conversation_state(user_id)

    intenciones = analysis_result.get("intenciones", [])
    idioma = analysis_result.get("idioma", "es")  # Si no hay idioma detectado, asumimos español
    
    if not intenciones:
        return _sin_intencion_respuesta(idioma)

    responses = []
    
    # 🔹 **2️⃣ Procesar cada intención detectada**
    for intent in intenciones:
        text = dispatch_intent(conversation_state, intent, user_message, idioma, nombre_apartamento)  # ✅ Ahora se pasa correctamente
        responses.append(text)

    # 🔹 **3️⃣ Guardar conversación actualizada en Supabase**
    save_conversation_state(conversation_state)

    return "\n".join([str(resp) if isinstance(resp, dict) else resp for resp in responses])

def dispatch_intent(conversation_state, intent, user_message, idioma,nombre_apartamento) -> str:
    """
    Redirige cada intención a su respectiva función de manejo.
    """

    # 🔹 Asegurar que idioma tenga un valor válido
    idioma = idioma if idioma in ["es", "en"] else "es"

    if intent == "informacion_alojamiento":
        return handle_apartment_info(conversation_state.user_id, user_message, nombre_apartamento)  # ✅ Corrección

    elif intent == "averia_estancia":
        return handle_issue_report(conversation_state.user_id, user_message)

    elif intent == "servicios_adicionales":
        return handle_cleaning_request(conversation_state,user_message)

    elif intent == "recomendaciones_personalizadas":
     return categorizar_recomendacion(conversation_state.user_id, user_message)

    elif intent == "descuentos_promociones":
        return descuentos_promociones(idioma)

    elif intent == "alquilar_mas_dias":
        return gestionar_extension_estancia(idioma)

    elif intent == "solicitar_factura":
        return obtener_factura(idioma)

    else:
        return _sin_intencion_respuesta(idioma)


# 📌 **Funciones auxiliares para otras intenciones**
def proporcionar_normas_casa(idioma):
    return {
        "en": "Our house rules: No smoking, no loud noises after 10PM...",
        "es": "Las normas de la casa son: No fumar, no hacer ruido después de las 22h..."
    }.get(idioma)

def gestionar_problema(conversation_state, idioma):
    return {
        "en": "Please describe the issue in your room, we'll send assistance.",
        "es": "Por favor describe el problema de tu habitación, enviaremos asistencia."
    }.get(idioma)

def solicitar_servicio_extra(conversation_state, idioma):
    return {
        "en": "We can provide extra cleaning or towels. Let us know what you need!",
        "es": "Podemos ofrecer limpieza adicional o toallas extra. ¡Indícanos qué necesitas!"
    }.get(idioma)

def descuentos_promociones(idioma):
    return {
        "en": "I'm sorry, we do not offer promotions.",
        "es": "Lo siento, no hacemos descuentos."
    }.get(idioma)

def gestionar_extension_estancia(idioma):
    return {
        "en": "You can extend your stay. Please check availability with reception.",
        "es": "Puedes ampliar tu estancia. Por favor revisa disponibilidad con recepción."
    }.get(idioma)

def obtener_factura(idioma):
    return {
        "en": "Your invoice will be sent to your email. Please provide your details.",
        "es": "Tu factura será enviada a tu correo electrónico. Por favor, facilita tus datos."
    }.get(idioma)

def _sin_intencion_respuesta(idioma):
    return {
        "en": "I'm sorry, I didn't quite catch that. Can you rephrase?",
        "es": "Lo siento, no te he entendido. ¿Podrías reformular tu pregunta?"
    }.get(idioma)