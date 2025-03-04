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
    def __init__(self, numero_telefono, categoria_activa="recomendaciones_restaurantes", is_closed=False, idioma="es", created_at=None, historial=None, datos_categoria=None, data=None):
        self.numero_telefono = numero_telefono
        self.categoria_activa = categoria_activa
        self.is_closed = is_closed if data is None else data.get("is_closed", False)
        self.idioma = idioma if data is None else data.get("idioma", "es")
        self.created_at = created_at if created_at else (data["created_at"] if data and "created_at" in data else datetime.utcnow().isoformat())

        # Manejo seguro del historial
        self.historial = historial if isinstance(historial, list) else []
        if data and "historial" in data:
            try:
                self.historial = json.loads(data["historial"]) if isinstance(data["historial"], str) else data["historial"]
            except (json.JSONDecodeError, TypeError):
                self.historial = []

        # Manejo seguro de `datos_categoria`
        self.datos_categoria = datos_categoria if isinstance(datos_categoria, dict) else {}
        if data and "datos_categoria" in data:
            try:
                self.datos_categoria = json.loads(data["datos_categoria"]) if isinstance(data["datos_categoria"], str) else data["datos_categoria"]
            except (json.JSONDecodeError, TypeError):
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
    Guarda o actualiza el estado del usuario en `dinamicos` en Supabase.
    """
    try:
        if not isinstance(state, ConversationState):
            print("⚠️ `save_dynamic_state` recibió un diccionario en lugar de un `ConversationState`. Convirtiendo...")
            print("📌 Diccionario recibido antes de conversión:", json.dumps(state, indent=4, ensure_ascii=False))

            if isinstance(state, dict):
                expected_keys = {"numero_telefono", "categoria_activa", "is_closed", "idioma", "created_at", "historial", "datos_categoria"}
                received_keys = set(state.keys())

                print(f"📌 Claves esperadas: {expected_keys}")
                print(f"📌 Claves recibidas: {received_keys}")

                # Si hay claves extra, eliminarlas antes de la conversión
                extra_keys = received_keys - expected_keys
                if extra_keys:
                    print(f"⚠️ Eliminando claves inesperadas: {extra_keys}")
                    for key in extra_keys:
                        del state[key]

                # ✅ Asegurar que `historial` sea una lista
                if isinstance(state.get("historial"), str):
                    try:
                        state["historial"] = json.loads(state["historial"])
                    except json.JSONDecodeError:
                        state["historial"] = []  # Si falla, dejarlo vacío

                # ✅ Asegurar que `datos_categoria` sea un diccionario
                if isinstance(state.get("datos_categoria"), str):
                    try:
                        state["datos_categoria"] = json.loads(state["datos_categoria"])
                    except json.JSONDecodeError:
                        state["datos_categoria"] = {}  # Si falla, dejarlo vacío

                state = ConversationState(**state)  # Ahora debe convertirse sin error

        # 📌 Continuar con el guardado en Supabase
        print(f"📌 Guardando datos en `dinamicos` para usuario {state.numero_telefono}...")

        response = supabase.table("dinamicos").upsert(state.to_dict(), on_conflict=["numero_telefono"]).execute()

        if response.data:
            print(f"✅ Datos actualizados correctamente en `dinamicos` para usuario {state.numero_telefono}.")
            return True

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