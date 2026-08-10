import os
import hashlib
import requests
import urllib3
from bs4 import BeautifulSoup

# Desactivamos el warning por el certificado SSL de FMED
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://www.fmed.uba.ar/index.php/depto/toxico1/grado.htm"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "previous_hash.txt"


def get_page_content():
    response = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        verify=False
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Eliminamos elementos que no forman parte del contenido visible.
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    # Extraemos todo el texto visible.
    text = soup.get_text("\n", strip=True)

    # Normalizamos espacios y saltos de línea.
    text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )

    return text


def calculate_hash(content):
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def send_telegram(message):
    telegram_url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


def main():

    print("Comprobando página...")

    content = get_page_content()
    current_hash = calculate_hash(content)

    previous_hash = None

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            previous_hash = file.read().strip()

# Primera ejecución.
if previous_hash is None:

    with open(STATE_FILE, "w") as file:
        file.write(current_hash)

    print("Primera ejecución. Estado guardado.")

    send_telegram(
        "🧪 PRUEBA DEL BOT\n\n"
        "¡Telegram funciona correctamente! 🚨"
    )

    return

    # Detectamos un cambio.
    if current_hash != previous_hash:

        print("CAMBIO DETECTADO.")

        message = (
            "🚨 CAMBIO DETECTADO EN LA PÁGINA 🚨\n\n"
            "La página de FMED cambió.\n\n"
            f"{URL}"
        )

        send_telegram(message)

        with open(STATE_FILE, "w") as file:
            file.write(current_hash)

        print("Aviso enviado a Telegram.")

    else:

        print("Sin cambios.")


if __name__ == "__main__":
    main()
