# app/database.py
from datetime import datetime, timedelta

###############################################################################
# Ejemplo: usaremos un diccionario en memoria como "BD" de ejemplo
# En producción, reemplazar con una BD real (Postgres, Supabase, etc.)
###############################################################################
FAKE_DB = {}  # clave: user_id, valor: un dict con campos de estado

###############################################################################
# Clase simple para representar el estado de conversación
###############################################################################
class ConversationState:
    def __init__(self, user_id):
        self.user_id = user_id
        self.last_message = ""
        self.last_response = ""
        self.checkout_date = None  # Si lo supiéramos
        self.is_closed = False

def init_db():
    """
    Inicializa la conexión a la BD real, si la hubiera.
    En este ejemplo, no hacemos nada.
    """
    pass

def get_conversation_state(user_id: str) -> ConversationState:
    """
    Retorna el estado de conversación para un user_id.
    Si no existe, lo crea.
    """
    if user_id not in FAKE_DB:
        FAKE_DB[user_id] = ConversationState(user_id)
    return FAKE_DB[user_id]

def save_conversation_state(state: ConversationState):
    """
    Guarda el estado en nuestra FAKE_DB.
    En un entorno real, haríamos un INSERT/UPDATE en la base de datos.
    """
    FAKE_DB[state.user_id] = state

def close_conversation_if_expired(state: ConversationState) -> ConversationState:
    """
    Simulamos que la conversación se cierra 1 día después del checkout_date.
    Si no se ha definido checkout_date, no expiramos.
    """
    if state.checkout_date:
        expire_time = state.checkout_date + timedelta(days=1)
        if datetime.utcnow() > expire_time:
            state.is_closed = True
    return state