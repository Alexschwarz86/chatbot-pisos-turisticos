# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.database import init_db, get_conversation_state, save_conversation_state
from app.nlu import analyze_message
from app.categorias import recomendaciones  # Asume que 'recomendaciones.py' está en app/categories/

app = FastAPI(title="Chatbot de Ejemplo", version="1.0.0")

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/chat")
def chat_endpoint(chat_request: ChatRequest):
    user_id = chat_request.user_id
    user_message = chat_request.message

    conv_state = get_conversation_state(user_id)
    analysis_result = analyze_message(user_message)
    conv_state.idioma = analysis_result["idioma"]  # Actualizamos idioma detectado

    intenciones = analysis_result["intenciones"]
    
    # Despacho basado en intenciones
    reply = dispatch_intents(conv_state, intenciones, user_message)
    save_conversation_state(conv_state)
    return {"reply": reply}

def dispatch_intents(conv_state, intenciones, user_message):
    if "feedback_positivo" in intenciones:
        return recomendaciones.handle_feedback_positivo(conv_state, user_message)
    if "feedback_negativo" in intenciones:
        return recomendaciones.handle_feedback_negativo(conv_state, user_message)
    if "recomendaciones_personalizadas" in intenciones:
        if "no hay espacio" in user_message.lower():
            return recomendaciones.handle_no_space(conv_state)
        else:
            return recomendaciones.handle_recomendaciones(conv_state, user_message)
    return "Lo siento, no entendí tu petición."