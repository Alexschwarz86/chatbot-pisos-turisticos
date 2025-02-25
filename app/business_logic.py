from app.categorias import recomendaciones  # Asegúrate de que el módulo esté en app/categorias/
from app.database import get_conversation_state, save_conversation_state

def handle_intents(user_id, analysis_result, user_message) -> str:
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
        text = dispatch_intent(conversation_state, intent, user_message, idioma)
        responses.append(text)

    # 🔹 **3️⃣ Guardar conversación actualizada en Supabase**
    save_conversation_state(conversation_state)

    return "\n".join([str(resp) if isinstance(resp, dict) else resp for resp in responses])

def dispatch_intent(conversation_state, intent, user_message, idioma) -> str:
    """
    Redirige cada intención a su respectiva función de manejo.
    """

    if intent == "informacion_alojamiento":
        return proporcionar_normas_casa(idioma)

    elif intent == "problemas_estancia":
        return gestionar_problema(conversation_state, idioma)

    elif intent == "servicios_adicionales":
        return solicitar_servicio_extra(conversation_state, idioma)

    elif intent == "recomendaciones_personalizadas":
        # Si detectamos que no hay espacio en la reserva, llamamos a otra función
        if "no hay espacio" in user_message.lower():
            return recomendaciones.handle_no_space(conversation_state)
        else:
            return recomendaciones.categorizar_recomendacion(conversation_state.user_id, user_message)

    elif intent == "descuentos_promociones":
        return descuentos_promociones(idioma)

    elif intent == "alquilar_mas_dias":
        return gestionar_extension_estancia(idioma)

    elif intent == "solicitar_factura":
        return obtener_factura(idioma)

    else:
        return f"No sé manejar la intención '{intent}'."

# 📌 **Funciones auxiliares para otras intenciones**
def proporcionar_normas_casa(idioma):
    return {
        "en": "Our house rules: No smoking, no loud noises after 10PM...",
        "es": "Las normas de la casa son: No fumar, no hacer ruido después de las 22h..."
    }.get(idioma, "Las normas de la casa son: No fumar, no hacer ruido después de las 22h...")

def gestionar_problema(conversation_state, idioma):
    return {
        "en": "Please describe the issue in your room, we'll send assistance.",
        "es": "Por favor describe el problema de tu habitación, enviaremos asistencia."
    }.get(idioma, "Por favor describe el problema de tu habitación, enviaremos asistencia.")

def solicitar_servicio_extra(conversation_state, idioma):
    return {
        "en": "We can provide extra cleaning or towels. Let us know what you need!",
        "es": "Podemos ofrecer limpieza adicional o toallas extra. ¡Indícanos qué necesitas!"
    }.get(idioma, "Podemos ofrecer limpieza adicional o toallas extra. ¡Indícanos qué necesitas!")

def descuentos_promociones(idioma):
    return {
        "en": "I'm sorry, we do not offer promotions.",
        "es": "Lo siento, no hacemos descuentos."
    }.get(idioma, "Lo siento, no hacemos descuentos.")

def gestionar_extension_estancia(idioma):
    return {
        "en": "You can extend your stay. Please check availability with reception.",
        "es": "Puedes ampliar tu estancia. Por favor revisa disponibilidad con recepción."
    }.get(idioma, "Puedes ampliar tu estancia. Por favor revisa disponibilidad con recepción.")

def obtener_factura(idioma):
    return {
        "en": "Your invoice will be sent to your email. Please provide your details.",
        "es": "Tu factura será enviada a tu correo electrónico. Por favor, facilita tus datos."
    }.get(idioma, "Tu factura será enviada a tu correo electrónico. Por favor, facilita tus datos.")

def _sin_intencion_respuesta(idioma):
    return {
        "en": "I'm sorry, I didn't quite catch that. Can you rephrase?",
        "es": "Lo siento, no te he entendido. ¿Podrías reformular tu pregunta?"
    }.get(idioma, "Lo siento, no te he entendido. ¿Podrías reformular tu pregunta?")