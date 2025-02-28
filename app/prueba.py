import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 🔹 Cargar variables de entorno
load_dotenv()

# 🔹 Leer credenciales desde el `.env`
creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if not creds_json:
    raise ValueError("❌ ERROR: No se encontraron las credenciales en el archivo .env.")

try:
    creds_dict = json.loads(creds_json)
    print("✅ Credenciales cargadas correctamente.")  # 🔍 Debugging
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
except json.JSONDecodeError:
    raise ValueError("❌ ERROR: La clave JSON en .env no es válida.")

# 🔹 Conectar con la API de Google Calendar
service = build("calendar", "v3", credentials=credentials)

# 🔹 ID del calendario de limpieza
calendar_id = "7e39956991ef4d1663604ae62672beb62304e0438798fa09c3431f4c62bd4209@group.calendar.google.com"

# 🔹 Obtener los eventos del calendario específico
try:
    events_result = service.events().list(calendarId=calendar_id).execute()
    events = events_result.get("items", [])

    # 🔹 Mostrar los eventos existentes
    print(f"✅ Eventos en el calendario ({calendar_id}):")
    if not events:
        print("📌 No hay eventos programados.")
    else:
        for event in events:
            print(f"  - {event['summary']} | {event.get('start', {}).get('dateTime', 'Fecha no disponible')}")

except Exception as e:
    print(f"❌ Error al obtener eventos: {e}")