from supabase import create_client, Client
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificar si las credenciales están configuradas correctamente
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ ERROR: Las variables de entorno SUPABASE_URL y SUPABASE_KEY no están configuradas correctamente.")

# Crear la conexión a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

###############################################################################
# Clase para representar el estado de conversación
###############################################################################
class ConversationState:
    def __init__(self, user_id, categoria_activa="recomendaciones_restaurantes", data=None):
        self.user_id = user_id
        self.categoria_activa = categoria_activa  # Se inicializa correctamente

        # 🔹 Manejo de datos adicionales
        self.last_message = data.get("last_message", "") if data else ""
        self.last_response = data.get("last_response", "") if data else ""
        self.checkout_date = data.get("checkout_date") if data else None
        self.is_closed = data.get("is_closed", False) if data else False
        self.idioma = data.get("idioma", "es") if data else "es"
        self.created_at = data["created_at"] if data and "created_at" in data else datetime.utcnow().isoformat()

        # 🔹 Historial seguro (Manejo correcto de listas y JSON)
        if data and "historial" in data:
            if isinstance(data["historial"], str):  # Si es una cadena JSON, la cargamos
                try:
                    self.historial = json.loads(data["historial"])
                except (json.JSONDecodeError, TypeError):
                    self.historial = []  # Si hay un error, asignamos una lista vacía
            elif isinstance(data["historial"], list):  # Si ya es una lista, la asignamos directamente
                self.historial = data["historial"]
            else:
                self.historial = []  # Si es cualquier otra cosa, aseguramos una lista vacía
        else:
            self.historial = []  # Si no hay historial, inicializamos con una lista vacía

        # 🔹 Manejo seguro de datos de categorías (Evitar errores en JSON)
        if data and "datos_categoria" in data:
            if isinstance(data["datos_categoria"], str):  # Si es una cadena JSON, la cargamos
                try:
                    self.datos_categoria = json.loads(data["datos_categoria"])
                except (json.JSONDecodeError, TypeError):
                    self.datos_categoria = {}  # Si hay error, asignamos diccionario vacío
            elif isinstance(data["datos_categoria"], dict):  # Si ya es un diccionario, lo usamos directamente
                self.datos_categoria = data["datos_categoria"]
            else:
                self.datos_categoria = {}  # Si es cualquier otra cosa, aseguramos un diccionario vacío
        else:
            self.datos_categoria = {}  # Si no hay datos de categoría, inicializamos vacío

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "categoria_activa": self.categoria_activa,  # Se guarda correctamente
            "last_message": self.last_message,
            "last_response": self.last_response,
            "checkout_date": self.checkout_date,
            "is_closed": self.is_closed,
            "historial": json.dumps(self.historial) if isinstance(self.historial, list) else "[]",
            "datos_categoria": json.dumps(self.datos_categoria) if isinstance(self.datos_categoria, dict) else "{}",
            "idioma": self.idioma,
            "created_at": self.created_at
        }
###############################################################################
# Función para obtener el estado de conversación desde Supabase
###############################################################################

def get_conversation_state(user_id: str):
    """
    Recupera el estado de conversación desde Supabase o lo crea si no existe.
    """
   
    response = supabase.table("conversation_state").select("*").eq("user_id", user_id).execute()
    print("📌 Respuesta de Supabase:", response.data)
    
    if response.data:
        data = response.data[0]
        print("📌 Usuario encontrado en Supabase. Datos cargados:", data)

        # ✅ Pasamos `data` directamente a `ConversationState`
        return ConversationState(user_id=data["user_id"], data=data)
    
    # ⚠️ Si no existe en Supabase, creamos un nuevo estado para el usuario
    print(f"⚠️ Usuario {user_id} no encontrado en Supabase. Creando nuevo estado...")
    new_state = ConversationState(user_id)  # Creamos una nueva instancia con valores predeterminados
    save_conversation_state(new_state)  # Guardamos en Supabase antes de retornarlo
    return new_state  # Devolvemos el nuevo estadonuevo estado

###############################################################################
# Función para guardar el estado de conversación en Supabase
###############################################################################
def save_conversation_state(state: ConversationState):
    """
    Guarda o actualiza el estado de conversación en Supabase.
    """
    try:
        # 🔹 Limpieza del historial
        historial_limpio = []
        for msg in state.historial:
            if isinstance(msg, dict):  # Asegurar que sea un diccionario
                usuario = msg.get("usuario", "")
                bot = msg.get("bot", "")

                # 🔹 Evitar JSON dentro de JSON en "bot"
                if isinstance(bot, str):
                    try:
                        bot_json = json.loads(bot)
                        if isinstance(bot_json, dict):
                            bot = bot_json  # Convertimos el string JSON en diccionario
                    except json.JSONDecodeError:
                        pass  # Si no es JSON, lo dejamos como string

                historial_limpio.append({"usuario": usuario, "bot": bot})

        # 🔹 Convertimos todo a JSON serializable antes de enviarlo a Supabase
        data = {
            "user_id": state.user_id,
            "categoria_activa": state.categoria_activa,
            "historial": historial_limpio,
            "last_message": state.last_message,
            "last_response": state.last_response,
            "checkout_date": state.checkout_date,
            "is_closed": state.is_closed,
            "idioma": state.idioma,
            "created_at": state.created_at
        }

        # 🔹 DEBUG: Ver qué se está enviando a Supabase
        print("📌 Datos que se intentan guardar en Supabase:", json.dumps(data, indent=4))

        # 🔹 Guardar en Supabase
        response = supabase.table("conversation_state").upsert(data).execute()

        # 🔹 Verificar respuesta de Supabase
        if response.data:
            print(f"✅ Estado guardado en Supabase para el usuario {state.user_id}")
        else:
            print(f"❌ Error al guardar en Supabase. Respuesta: {response}")

    except Exception as e:
        print(f"❌ Error inesperado en save_conversation_state: {str(e)}")
###############################################################################
# Función para cerrar conversación si ha expirado
###############################################################################
def close_conversation_if_expired(state: ConversationState) -> ConversationState:
    """
    Cierra la conversación si ha pasado 1 día después del checkout.
    """
    if state.checkout_date:
        expire_time = datetime.fromisoformat(state.checkout_date) + timedelta(days=1)
        if datetime.utcnow() > expire_time:
            state.is_closed = True
            save_conversation_state(state)  # Guardamos el estado actualizado en Supabase
    return state

###############################################################################
# Base de datos simulada de restaurantes
###############################################################################
RESTAURANTES_FAKE = [
    {"id": 1, "nombre": "Mamma Mia", "tipo_cocina": "italiano", "budget": "barato"},
    {"id": 2, "nombre": "La Tagliatella", "tipo_cocina": "italiano", "budget": "medio"},
    {"id": 3, "nombre": "Sushi Lowcost", "tipo_cocina": "japones", "budget": "barato"},
    {"id": 4, "nombre": "Kyoto Deluxe", "tipo_cocina": "japones", "budget": "caro"},
]

def query_restaurantes(tipo_cocina=None, budget=None, exclude_id=None):
    return [
        r for r in RESTAURANTES_FAKE
        if (not tipo_cocina or r["tipo_cocina"] == tipo_cocina)
        and (not budget or r["budget"] == budget)
        and (exclude_id is None or r["id"] != exclude_id)
    ]

def obtener_historial_usuario(user_id: str):
    """
    Obtiene el estado de conversación del usuario y construye su historial reciente.
    """
    conv_state = get_conversation_state(user_id)
    
    historial = "\n".join([
        f'Usuario: "{msg["usuario"]}"\nBot: "{msg["bot"]}"' 
        for msg in conv_state.historial[-10:]
    ])

    return conv_state, historial