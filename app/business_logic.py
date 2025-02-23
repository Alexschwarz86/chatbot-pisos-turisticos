# app/business_logic.py

def handle_intents(conversation_state, analysis_result) -> str:
    """
    Recibe el estado de la conversación y el resultado del análisis NLU.
    Decide qué hacer con las intenciones y produce un texto de respuesta.
    """
    intents = analysis_result.get("intenciones", [])
    idioma = analysis_result.get("idioma", "desconocido")
    
    if not intents:
        # Sin intenciones claras
        return _sin_intencion_respuesta(idioma)
    
    # Si hay múltiples intenciones, las procesamos todas
    responses = []
    for intent in intents:
        text = dispatch_intent(conversation_state, intent, idioma)
        responses.append(text)

    # Podríamos unificar las respuestas en un solo string (o mandar varias)
    final_response = "\n".join(responses)

    return final_response

def dispatch_intent(conversation_state, intent, idioma) -> str:
    """
    Envía la intención a la función adecuada. 
    conversation_state podría usarse para extraer datos del usuario, etc.
    """
    # Ejemplo de "catálogo" de intenciones
    if intent == "informacion_alojamiento":
        return proporcionar_normas_casa(idioma)
    elif intent == "problemas_estancia":
        return gestionar_problema(conversation_state, idioma)
    elif intent == "servicios_adicionales":
        return solicitar_servicio_extra(conversation_state, idioma)
    elif intent == "recomendaciones_personalizadas":
        return dar_recomendaciones(conversation_state, idioma)
    elif intent == "descuentos_promociones":
        return descuentos_promociones(conversation_state, idioma)
    elif intent == "alquilar_mas_dias":
        return gestionar_extension_estancia(conversation_state, idioma)
    elif intent == "solicitar_factura":
        return obtener_factura(conversation_state, idioma)
    # ... Añade más casos

    # Si no coincide
    return f"No sé manejar la intención '{intent}'."

###############################################################################
# Funciones "mock" de ejemplo
###############################################################################
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

def dar_recomendaciones(conversation_state, idioma):
    if idioma == "en":
        return "We recommend visiting the city center and trying local cuisine."
    else:
        return "Te recomendamos visitar el centro de la ciudad y probar la gastronomía local."

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

def descuentos_promociones(descuentos_promociones, idioma):
    if idioma == "en":
        return "I'm sorry,no promotion"
    else:
        return "Lo siento,no hacemos descuento"