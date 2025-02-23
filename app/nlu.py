
import os
import json
from openai import OpenAI  # <-- En lugar de import openai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# Creamos el cliente con la API Key
client = OpenAI(api_key=api_key)

PROMPT_TEMPLATE = """
Eres un asistente que clasifica un mensaje de usuario en una o varias de las siguientes categorías:

CATEGORÍAS:
CATEGORÍAS:

1) informacion_alojamiento
   - Preguntas sobre características generales (wifi, sábanas, toallas incluidas, capacidad, ubicación, etc.)
   - Preguntas sobre reglas de la casa (fumar, mascotas, horarios de ruido)

2) problemas_estancia
   - El usuario reporta un problema o avería (aire acondicionado dañado, fuga de agua, puerta bloqueada)

3) servicios_adicionales
   - Solicitud de servicios extra (limpieza, cambio de sábanas/toallas, lavandería, comida, etc.)

4) recomendaciones_personalizadas
   - Preguntas sobre qué visitar, dónde comer, turismo local

5) alquilar_mas_dias
   - Peticiones de extender la estancia, añadir más días

6) descuentos_promociones
   - Preguntas sobre rebajas, cupones, descuentos, etc.

Por favor, devuelve SIEMPRE un JSON con esta estructura exacta (sin texto adicional):

{
  "idioma": "<código_idioma_principal>",
  "intenciones": ["<una_o_mas_de_las_categorias_de_la_lista_anterior>"],
  "confidence": <número entre 0 y 1>,
  "original_text": "<mensaje original>"
}

Si no reconoces ninguna categoría, usa ["indeterminado"] en "intenciones".

EJEMPLOS:

Ejemplo 1:
Mensaje: "¿Dónde puedo ver las normas de la casa?"
{
  "idioma": "es",
  "intenciones": ["informacion_alojamiento"],
  "confidence": 0.9,
  "original_text": "¿Dónde puedo ver las normas de la casa?"
}

Ejemplo 2:
Mensaje: "I need fresh towels and I'd like to extend my stay"
{
  "idioma": "en",
  "intenciones": ["servicios_adicionales", "alquilar_mas_dias"],
  "confidence": 0.85,
  "original_text": "I need fresh towels and I'd like to extend my stay"
}

AHORA, clasifica este mensaje:

"{mensaje_usuario}"
"""

def analyze_message(user_message: str) -> dict:
    """
    Llamamos a la API usando client.chat.completions.create(...)
    y parseamos la respuesta en JSON.
    """
    # Sustituimos el placeholder {mensaje_usuario}
    final_prompt = PROMPT_TEMPLATE.replace("{mensaje_usuario}", user_message)

    # Llamada al endpoint 'chat.completions'
    completion = client.chat.completions.create(
        # Puedes usar "gpt-3.5-turbo", "gpt-4", etc. 
        model="gpt-4-turbo",
        # Parche para almacenar la conversación (si tu SDK lo admite)
        store=True,  
        messages=[
            {"role": "system", "content": "Eres un experto en clasificación de intenciones."},
            {"role": "user", "content": final_prompt}
        ],
        max_tokens=200,
        temperature=0
    )

    # La respuesta la obtienes en completion.choices[0].message["content"]
    response_text = completion.choices[0].message.content.strip()

    print("GPT responded with:", response_text)

    # Parseo de JSON (suponiendo que GPT devuelva un JSON válido)
    result = json.loads(response_text)

    # Validaciones mínimas
    if "idioma" not in result:
        result["idioma"] = "desconocido"
    if "intenciones" not in result:
        result["intenciones"] = []
    if "confidence" not in result:
        result["confidence"] = 0.5

    result["original_text"] = user_message
    return result