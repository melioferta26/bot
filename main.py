import os
import time
from meli_scraper import obtener_ofertas_destacadas
from publishers.telegram_bot import publicar_en_telegram
from publishers.twitter_bot import publicar_en_x

# Carga de credenciales desde variables de entorno por seguridad
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

def ejecutar_bot():
    print("Iniciando búsqueda de ofertas...")
    ofertas = obtener_ofertas_destacadas()
    
    for oferta in ofertas:
        print(f"Publicando: {oferta['titulo']}")
        
        # 1. Publicar en Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            publicar_en_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, oferta['mensaje'])
            
        # 2. Publicar en X (Twitter)
        if TWITTER_API_KEY:
            publicar_en_x(
                TWITTER_API_KEY, TWITTER_API_SECRET, 
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, 
                oferta['mensaje']
            )
            
        # Pausa para no saturar los feeds/APIs
        time.sleep(300) # Espera 5 minutos entre publicaciones

if __name__ == "__main__":
    ejecutar_bot()