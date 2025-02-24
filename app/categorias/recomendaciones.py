# app/categorias/recomendaciones.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.database import query_restaurantes, save_conversation_state

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def handle_recomendaciones(conv_state, user_message):
    """
    Procesa la solicitud de recomendaciones de restaurantes, asegurando que todos los datos necesarios estén presentes.
    Si faltan datos, se pregunta al usuario. Si ya hay datos suficientes, se consulta la BD y se genera una respuesta.
    """

    # Construcción del prompt para clasificar el mensaje
    classification_prompt = f"""
Eres un asistente que clasifica el siguiente mensaje en una de las siguientes categorías y extrae datos específicos en el caso de "Restaurantes y Comida".

Categorías:
1. Actividades y Ocio: Actividades recreativas, excursiones, deportes, experiencias culturales o de ocio.
2. Restaurantes y Comida: Lugares para comer o cenar. Devuelve un JSON con esta estructura EXACTA:
   {{
      "Categoria": "Restaurantes y Comida",
      "tipo_comida": "<tipo de comida>",
      "butget": "<rango de precio: 'barato', 'medio' o 'caro', o vacío si no se menciona>"
   }}
3. Transporte y Movilidad: Servicios de transporte, alquiler de vehículos o movilidad urbana.
4. Eventos y Entretenimiento: Conciertos, festivales, obras de teatro, shows o eventos similares.
5. Servicios y Otros: Otros servicios que no encajan en las categorías anteriores.

Analiza el siguiente mensaje y devuelve únicamente el JSON indicado:
"{user_message}"
    """

    # Llamada a OpenAI para clasificar el mensaje
    classification_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un experto en clasificación. Devuelve solo el JSON sin texto adicional."},
            {"role": "user", "content": classification_prompt}
        ],
        max_tokens=100,
        temperature=0
    )

    print("GPT Response:", classification_response)

    try:
        # Extraer JSON de la respuesta
        classification_json = json.loads(classification_response.choices[0].message.content.strip())
        print("🔍 JSON Devuelto por GPT:", classification_json)
    except Exception as e:
        print("⚠️ Error al procesar JSON:", e)
        print("⚠️ Respuesta bruta de OpenAI:", classification_response.choices[0].message.content.strip())  #
        return "No pude procesar la clasificación del mensaje. Por favor, inténtalo de nuevo."

    # Verificamos que la categoría sea "Restaurantes y Comida"
    if classification_json.get("Categoria", "").lower() != "restaurantes y comida":
        return "El mensaje no pertenece a la categoría 'Restaurantes y Comida'."

    # Extraemos los datos clasificados
    tipo_comida = classification_json.get("tipo_comida", "").strip()
    butget = classification_json.get("butget", "").strip()

    # Preguntar por datos faltantes
    if not tipo_comida or not butget:
        if not tipo_comida:
            return "¿Tienes algún restaurante en particular en mente?"
        if not butget:
            return "¿Qué rango de precio prefieres? (barato, medio, caro)"
        
    
    # Actualizamos el estado del usuario
    conv_state.tipo_recomendacion = "Restaurantes y Comida"
    conv_state.tipo_cocina = tipo_comida
    conv_state.budget = butget

    # Consultamos la base de datos simulada
    results = query_restaurantes(conv_state.tipo_cocina, conv_state.budget)
    if not results:
        return "No encontré opciones con esos criterios. ¿Quieres cambiar alguna preferencia?"

    # Seleccionamos las tres mejores opciones
    top_three = results[:3]

    # Formateamos la respuesta para OpenAI
    options_text = "\n".join([
        f"{idx+1}. {r['nombre']} (Cocina: {r['tipo_cocina']}, Precio: {r['budget']})"
        for idx, r in enumerate(top_three)
    ])

    return generar_respuesta_personalizada(conv_state.idioma, options_text)

def generar_respuesta_personalizada(idioma, opciones_texto):
    """
    Genera una respuesta de recomendación personalizada en el idioma detectado.
    """
    prompt = f"""
Eres un asistente que siempre responde en {idioma}.
El usuario busca un restaurante. Aquí tienes las mejores opciones basadas en sus preferencias:

{opciones_texto}

Por favor, escribe una respuesta amigable y natural recomendando estas opciones.
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente de recomendaciones personalizado y debes responder en el idioma indicado."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

# Manejo de si no hay espacio en el restaurante recomendado
def handle_no_space(conv_state):
    exclude = conv_state.last_recommendation_id
    results = query_restaurantes(conv_state.tipo_cocina, conv_state.budget, exclude)
    if not results:
        return "Lo siento, no tengo más opciones con esos criterios."
    new_rec = results[0]
    conv_state.last_recommendation_id = new_rec["id"]
    save_conversation_state(conv_state)
    return generar_respuesta_personalizada(conv_state.idioma, new_rec)

# Manejo del feedback del usuario
def handle_feedback_positivo(conv_state, user_message):
    conv_state.feedback.append({"restaurant_id": conv_state.last_recommendation_id, "comment": "positivo"})
    save_conversation_state(conv_state)
    return "¡Me alegra mucho saber que te gustó la recomendación!"

def handle_feedback_negativo(conv_state, user_message):
    conv_state.feedback.append({"restaurant_id": conv_state.last_recommendation_id, "comment": "negativo"})
    save_conversation_state(conv_state)
    return "Lamento que no haya sido de tu agrado. Puedo buscarte otra opción si quieres."