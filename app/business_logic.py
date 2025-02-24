from app.categorias import recomendaciones  # Asegúrate de que el módulo esté en app/categorias/

def handle_intents(conversation_state, analysis_result, user_message) -> str:
    """
    Recibe el estado de la conversación, el resultado del análisis NLU y el mensaje original,
    y decide qué hacer según las intenciones detectadas.
    """
    intenciones = analysis_result.get("intenciones", [])
    idioma = analysis_result.get("idioma", "desconocido")
    
    if not intenciones:
        return _sin_intencion_respuesta(idioma)
    
    responses = []
    # Recorrer cada intención detectada y despacharla
    for intent in intenciones:
        text = dispatch_intent(conversation_state, intent, user_message, idioma)
        responses.append(text)
    
    final_response = "\n".join(responses)
    return final_response

def dispatch_intent(conversation_state, intent, user_message, idioma) -> str:
    """
    Envía la intención a la función adecuada. 
    Se pasa el mensaje del usuario para poder tomar decisiones en funciones específicas (por ejemplo, recomendaciones).
    """
    if intent == "informacion_alojamiento":
        return proporcionar_normas_casa(idioma)
    elif intent == "problemas_estancia":
        return gestionar_problema(conversation_state, idioma)
    elif intent == "servicios_adicionales":
        return solicitar_servicio_extra(conversation_state, idioma)
    elif intent == "recomendaciones_personalizadas":
        # Aquí, según el contenido de user_message, decidimos qué función llamar
        if "no hay espacio" in user_message.lower():
            return recomendaciones.handle_no_space(conversation_state)
        else:
            return recomendaciones.handle_recomendaciones(conversation_state, user_message)
    elif intent == "descuentos_promociones":
        return descuentos_promociones(conversation_state, idioma)
    elif intent == "alquilar_mas_dias":
        return gestionar_extension_estancia(conversation_state, idioma)
    elif intent == "solicitar_factura":
        return obtener_factura(conversation_state, idioma)
    else:
        return f"No sé manejar la intención '{intent}'."

# Funciones "mock" de ejemplo para otras intenciones
def proporcionar_normas_casa(idioma):
    if idioma == "en":
        return "Our house rules: No smoking, no loud noises after 10PM..."
    else:
        return "Las normas de la casa son: No fumar, no hacer ruido después de las 22h..."

def gestionar_problema(conversation_state, idioma):
    if idioma == "en":
        return "Please describe the issue in your room, we'll send assistance."
    else:
        return "Por favor describe el problema de tu habitación, enviaremos asistencia."

def solicitar_servicio_extra(conversation_state, idioma):
    if idioma == "en":
        return "We can provide extra cleaning or towels. Let us know what you need!"
    else:
        return "Podemos ofrecer limpieza adicional o toallas extra. ¡Indícanos qué necesitas!"

def descuentos_promociones(conversation_state, idioma):
    if idioma == "en":
        return "I'm sorry, we do not offer promotions."
    else:
        return "Lo siento, no hacemos descuento."

def gestionar_extension_estancia(conversation_state, idioma):
    if idioma == "en":
        return "You can extend your stay. Please check availability with reception."
    else:
        return "Puedes ampliar tu estancia. Por favor revisa disponibilidad con recepción."

def obtener_factura(conversation_state, idioma):
    if idioma == "en":
        return "Your invoice will be sent to your email. Please provide your details."
    else:
        return "Tu factura será enviada a tu correo electrónico. Por favor, facilita tus datos."

def _sin_intencion_respuesta(idioma):
    if idioma == "en":
        return "I'm sorry, I didn't quite catch that. Can you rephrase?"
    else:
        return "Lo siento, no te he entendido. ¿Podrías reformular tu pregunta?"