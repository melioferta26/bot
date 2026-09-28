import requests

def publicar_en_telegram(bot_token, chat_id, texto):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()