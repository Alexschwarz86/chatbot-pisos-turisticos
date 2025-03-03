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

class ConversationState:
    def __init__(self, numero_telefono, categoria_activa="recomendaciones_restaurantes", data=None):
        self.numero_telefono = numero_telefono
        self.categoria_activa = categoria_activa
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
            "is_closed": self.is_closed,
            "idioma": self.idioma,
            "created_at": self.created_at,
            "historial": json.dumps(self.historial, ensure_ascii=False) if isinstance(self.historial, list) else "[]",
            "datos_categoria": json.dumps(self.datos_categoria, ensure_ascii=False) if isinstance(self.datos_categoria, dict) else "{}"
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
    
    if response.data and len(response.data) > 0:
        data = response.data[0]
        print(f"📌 Usuario {numero_telefono} encontrado en `dinamicos`. Datos cargados.")

        # 🔹 Convertir historial a lista si es un string JSON
        if isinstance(data.get("historial"), str):
            try:
                data["historial"] = json.loads(data["historial"])
            except json.JSONDecodeError:
                data["historial"] = []
        elif not isinstance(data.get("historial"), list):
            data["historial"] = []

        return ConversationState(numero_telefono, data=data)  

    # 🔹 Si el usuario no existe, creamos una nueva entrada **pero solo si es necesario**
    print(f"⚠️ Usuario {numero_telefono} no tiene datos dinámicos. Creando nuevo estado...")
    new_state = ConversationState(numero_telefono)

    # **Solo guardamos si el usuario NO existe**
    save_dynamic_state(new_state)

    return new_state

###############################################################################
# Función para guardar el estado de conversación en Supabase
###############################################################################

def save_dynamic_state(state):
    """
    Guarda solo los datos dinámicos del usuario en `dinamicos`.
    """
    try:
        if isinstance(state, ConversationState):  
            state = state.to_dict()  # ✅ Convertir a diccionario solo si es necesario

        print("📌 Estado antes de guardar en Supabase:", json.dumps(state, indent=4, ensure_ascii=False))

        response = supabase.table("dinamicos").upsert(state).execute()

        if response.data:
            print(f"✅ Conversación guardada correctamente en `dinamicos` para usuario con teléfono {state['numero_telefono']}.")
            return True
        else:
            print(f"❌ No se guardaron datos en Supabase.")
            return False

    except Exception as e:
        print(f"❌ Error en `save_dynamic_state`: {e}")
        return False

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
    restaurantes = [
        r for r in RESTAURANTES_FAKE
        if (not tipo_cocina or r["tipo_cocina"] == tipo_cocina)
        and (not budget or r["budget"] == budget)
    ]
    
    if exclude_id is not None:
        restaurantes = [r for r in restaurantes if r["id"] != exclude_id]

    return restaurantes

###############################################################################
# Función para obtener el historial del usuario
###############################################################################

def obtener_historial_usuario(numero_telefono: str):
    """
    Obtiene el estado de conversación del usuario y construye su historial reciente.
    """
    conv_state = get_dynamic_state(numero_telefono)
    
    historial = "\n".join([
        f'Usuario: "{msg["usuario"]}"\nBot: "{msg["bot"]}"' 
        for msg in conv_state.historial[-10:]  # ✅ Usar `conv_state.historial`, no `conv_state["historial"]`
    ])

    return conv_state, historial