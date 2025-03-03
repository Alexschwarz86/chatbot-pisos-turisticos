import json
from datetime import datetime

class ConversationState:
    def __init__(self, numero_telefono, categoria_activa="recomendaciones_restaurantes", data=None):
        self.numero_telefono = numero_telefono
        self.categoria_activa = categoria_activa
        self.historial = data.get("historial", []) if data else []
        self.datos_categoria = data.get("datos_categoria", {}) if data else {}
        self.is_closed = data.get("is_closed", False) if data else False
        self.idioma = data.get("idioma", "es") if data else "es"
        self.created_at = data["created_at"] if data and "created_at" in data else datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "numero_telefono": self.numero_telefono,
            "categoria_activa": self.categoria_activa,
            "historial": json.dumps(self.historial, ensure_ascii=False),
            "datos_categoria": json.dumps(self.datos_categoria, ensure_ascii=False),
            "is_closed": self.is_closed,
            "idioma": self.idioma,
            "created_at": self.created_at
        }