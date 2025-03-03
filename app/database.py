from supabase import create_client, Client
import os
import json
from datetime import datetime
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
from datetime import datetime
import json

class ConversationState:
    def __init__(self, numero_telefono, categoria_activa="recomendaciones_restaurantes", data=None):
        self.numero_telefono = numero_telefono
        self.categoria_activa = categoria_activa

        # 🔹 Manejo de datos adicionales
        self.last_message = data.get("last_message", "") if data else ""
        self.checkout_date = data.get("checkout_date") if data else None
        self.is_closed = data.get("is_closed", False) if data else False
        self.idioma = data.get("idioma", "es") if data else "es"
        self.created_at = data["created_at"] if data and "created_at" in data else datetime.utcnow().isoformat()

        # 🔹 Historial seguro (Manejo correcto de listas y JSON)
        self.historial = []
        if data and "historial" in data:
            if isinstance(data["historial"], str):
                try:
                    self.historial = json.loads(data["historial"])
                except (json.JSONDecodeError, TypeError):
                    self.historial = []
            elif isinstance(data["historial"], list):
                self.historial = data["historial"]
            else:
                self.historial = []

        # 🔹 Manejo seguro de datos de categorías
        self.datos_categoria = {}
        if data:
            raw_datos_categoria = data.get("datos_categoria", "{}")
            if isinstance(raw_datos_categoria, str):
                try:
                    self.datos_categoria = json.loads(raw_datos_categoria)
                except (json.JSONDecodeError, TypeError):
                    self.datos_categoria = {}
            elif isinstance(raw_datos_categoria, dict):
                self.datos_categoria = raw_datos_categoria
            else:
                self.datos_categoria = {}
        else:
            print("⚠️ `datos_categoria` no encontrado en Supabase, asignando `{}`")
            self.datos_categoria = {}

    def to_dict(self):
        """Convierte el objeto en un diccionario para guardarlo en la base de datos."""
        return {
            "numero_telefono": self.numero_telefono,
            "categoria_activa": self.categoria_activa,
            "last_message": self.last_message,
            "checkout_date": self.checkout_date,
            "is_closed": self.is_closed,
            "historial": json.dumps(self.historial, ensure_ascii=False) if isinstance(self.historial, list) else "[]",
            "datos_categoria": json.dumps(self.datos_categoria, ensure_ascii=False) if isinstance(self.datos_categoria, dict) else "{}",
            "idioma": self.idioma,
            "created_at": self.created_at
        }
###############################################################################
# Función para obtener el estado de conversación desde Supabase
###############################################################################
def get_dynamic_state(numero_telefono: str) -> ConversationState:
    """
    Obtiene solo los datos dinámicos del usuario desde `dinamicos`.
    Si no existe, lo crea con valores predeterminados.
    """
    response = supabase.table("dinamicos").select("*").eq("numero_telefono", numero_telefono).execute()
    
    if response.data:
        data = response.data[0]
        print(f"📌 Usuario {numero_telefono} encontrado en `dinamicos`. Datos cargados.")

        # 🔹 Asegurar que historial sea una lista válida
        if "historial" in data:
            if isinstance(data["historial"], str):
                try:
                    data["historial"] = json.loads(data["historial"])  # Convertir de JSON a lista
                except json.JSONDecodeError:
                    print(f"⚠️ Error al convertir historial de {numero_telefono}, inicializando lista vacía.")
                    data["historial"] = []
            elif not isinstance(data["historial"], list):
                data["historial"] = []  # Si no es lista, forzar lista vacía
        
        else:
            data["historial"] = []  # Si no existe la clave, inicializar con lista vacía

        # 🔹 Asegurar que `datos_categoria` sea un diccionario válido
        if "datos_categoria" in data:
            if isinstance(data["datos_categoria"], str):
                try:
                    data["datos_categoria"] = json.loads(data["datos_categoria"])  # Convertir de JSON a dict
                except json.JSONDecodeError:
                    print(f"⚠️ Error al convertir `datos_categoria` de {numero_telefono}, inicializando diccionario vacío.")
                    data["datos_categoria"] = {}
            elif not isinstance(data["datos_categoria"], dict):
                data["datos_categoria"] = {}  # Si no es dict, forzar a dict vacío

        else:
            data["datos_categoria"] = {}  # Si no existe la clave, inicializar con dict vacío

        return ConversationState(numero_telefono, data=data)  # ✅ Devuelve un objeto correctamente
    
    # 🔹 Si el usuario no existe, creamos una nueva entrada
    print(f"⚠️ Usuario {numero_telefono} no tiene datos dinámicos. Creando nuevo estado...")
    new_state = ConversationState(numero_telefono)

    # Guardar en Supabase
    save_dynamic_state(new_state.to_dict())

    return new_state
###############################################################################
# Función para obtener el estado estático basado en el número de teléfono
###############################################################################

def get_user_static_state(numero_telefono: str):
    """
    Obtiene los datos estáticos del usuario en función de su número de teléfono.
    """
    response = supabase.table("estaticos").select("*").eq("numero_telefono", numero_telefono).execute()
    
    if response.data:
        data = response.data[0]
        print(f"📌 Usuario con teléfono {numero_telefono} encontrado en `estaticos`. Datos cargados.")
        return data
    else:
        print(f"⚠️ Usuario con teléfono {numero_telefono} no encontrado en `estaticos`.")
        return None

###############################################################################
# Función para guardar el estado de conversación en Supabase
###############################################################################

def save_dynamic_state(state):
    """
    Guarda solo los datos dinámicos del usuario en `conversaciones`.
    """
    try:
        # ✅ Acceder a los atributos de `ConversationState` correctamente
        conversation_data = {
            "categoria_activa": state.categoria_activa,  # ❌ state["categoria_activa"] → ✅ state.categoria_activa
            "historial": json.dumps(state.historial, ensure_ascii=False),  # ❌ state["historial"] → ✅ state.historial
            "datos_categoria": json.dumps(state.datos_categoria, ensure_ascii=False),  # ❌ state["datos_categoria"] → ✅ state.datos_categoria
            "is_closed": state.is_closed  # ❌ state["is_closed"] → ✅ state.is_closed
        }

        print(f"📌 Guardando datos dinámicos en `conversaciones` para usuario con teléfono {state.numero_telefono}...")

        response = supabase.table("dinamicos").update(conversation_data).eq("numero_telefono", state.numero_telefono).execute()
        
        if response.data:
            print(f"✅ Conversación guardada correctamente en `conversaciones` para usuario con teléfono {state.numero_telefono}.")
            return response.data  # ✅ Devolvemos los datos guardados
        
        return None  # 🚨 En caso de que no haya datos en la respuesta

    except Exception as e:
        print(f"❌ Error en `save_dynamic_state`: {e}")
        return None  # 🚨 Si hay un error, retornamos `None`
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

def obtener_historial_usuario(numero_telefono: str):
    """
    Obtiene el estado de conversación del usuario y construye su historial reciente.
    """
    conv_state = get_dynamic_state(numero_telefono)
    
    historial = "\n".join([
        f'Usuario: "{msg["usuario"]}"\nBot: "{msg["bot"]}"' 
        for msg in conv_state["historial"][-10:]
    ])

    return conv_state, historial