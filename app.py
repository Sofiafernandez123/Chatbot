import os, json, requests
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI  # IA opcional

load_dotenv()
app = Flask(__name__)

# 🔑 Configuración
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GRAPH_URL = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
HEADERS = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}

# Cliente OpenAI (opcional)
client = OpenAI(api_key=OPENAI_API_KEY)

# Estados por usuario
user_states = {}


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


# ✅ Generar respuesta IA (opcional)
def ai_response(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sos un asistente útil y simpático."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ Error en IA:", e)
        return "Lo siento, hubo un error con el asistente de IA."


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
            from_msisdn = msg["from"]  # 👈 SIEMPRE respondemos a quien escribió
            text = (msg.get("text") or {}).get("body", "").strip().lower()

            # 👉 Menú inicial
            if text in ["hola", "menu", "opciones", "hi"]:
                menu = (
                    "👋 Hola, soy el asistente automático.\n"
                    "Elegí una opción:\n\n"
                    "1️⃣ Seguro Delivery Moto\n"
                    "2️⃣ Seguro Moto\n"
                    "3️⃣ Hablar con un asesor"
                )
                send_text(from_msisdn, menu)

            elif text == "1":
                send_text(from_msisdn,
                          "🚀 Para darte más info sobre *Seguro Delivery Moto* necesito:\n"
                          "- Marca\n- Modelo\n- Año\n- Código Postal")

            elif text == "2":
                send_text(from_msisdn,
                          "🏍️ Para darte más info sobre *Seguro Moto* necesito:\n"
                          "- Marca\n- Modelo\n- Año\n- Código Postal")

            elif text == "3":
                send_text(from_msisdn,
                          "📞 En unos minutos un asesor se va a contactar con vos.")

            else:
                # 👉 Si no coincide con opciones → IA
                respuesta = ai_response(text)
                send_text(from_msisdn, respuesta)

    except Exception as e:
        print("⚠️ Error procesando webhook:", e)

    return "ok", 200


# ✅ Ruta de test
@app.get("/")
def home():
    return "✅ Bot de WhatsApp corriendo y respondiendo"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
