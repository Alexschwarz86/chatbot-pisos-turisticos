def get_token_window(conv_state, max_messages=10):
    """
    Devuelve los últimos 'max_messages' mensajes en formato de ventana de token.
    """
    return "\n".join([
        f'Usuario: "{msg["usuario"]}"\nBot: "{msg["bot"]}"' 
        for msg in conv_state.historial[-max_messages:]
    ])

def add_message_to_memory(conv_state, user_message, bot_response):
    """
    Agrega un mensaje al historial y lo mantiene limitado a la ventana de tokens.
    """
    conv_state.historial.append({"usuario": user_message, "bot": bot_response})
    conv_state.historial = conv_state.historial[-10:]  # Mantiene solo los últimos 10 mensajes