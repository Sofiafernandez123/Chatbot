import os, json, requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 🔑 Configuración
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

GRAPH_URL = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
HEADERS = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}

# URL del Google Form
FORM_URL = "https://forms.gle/uutX4rXkh1LXqUXe9"


# ✅ Verificación del webhook
@app.get("/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado!")
        return challenge, 200
    else:
        return "Error de verificación", 403


# ✅ Enviar mensaje de texto a WhatsApp
def send_text(to_number: str, text: str):
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    r = requests.post(GRAPH_URL, headers=HEADERS, json=body)
    print("📤 Respuesta de Meta:", r.status_code, r.text)
    return r.json()


# ✅ Webhook para mensajes entrantes
@app.post("/webhook")
def incoming():
    data = request.get_json()
    print("📩 Webhook recibido:", json.dumps(data, indent=2, ensure_ascii=False))

    try:
        entry = (data.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_msisdn = msg["from"]  # 👈 Número del cliente
            text = (msg.get("text") or {}).get("body", "").strip().lower()

            # 👉 Menú inicial
            if text in ["hola", "menu", "opciones", "hi"]:
                menu = (
                    "👋 ¡Hola! Soy el asistente automático de Seguros.\n\n"
                    "Por favor seleccioná una opción:\n"
                    "1️⃣ Seguro Delivery Moto\n"
                    "2️⃣ Seguro Moto\n"
                    "3️⃣ Hablar con un asesor"
                )
                send_text(from_msisdn, menu)

            elif text == "1":
                send_text(from_msisdn,
                          f"🚀 Para avanzar con *Seguro Delivery Moto*, completá este formulario:\n{FORM_URL}")

            elif text == "2":
                send_text(from_msisdn,
                          f"🏍️ Para avanzar con *Seguro Moto*, completá este formulario:\n{FORM_URL}")

            elif text == "3":
                send_text(from_msisdn,
                          "📞 Un asesor se pondrá en contacto con vos en breve. ¡Gracias por confiar en nosotros!")

            else:
                # 👉 Respuesta por defecto si no entiende la opción
                send_text(from_msisdn,
                          "🤔 No entendí tu respuesta.\nEscribí *menu* para ver las opciones disponibles.")

    except Exception as e:
        print("⚠️ Error procesando webhook:", e)

    return "ok", 200


# ✅ Ruta de test
@app.get("/")
def home():
    return "✅ Bot de WhatsApp corriendo y respondiendo"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
