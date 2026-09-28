import os
from meli_scraper import obtener_ofertas_destacadas
from publishers.telegram_bot import publicar_en_telegram
from publishers.twitter_bot import publicar_en_x

def ejecutar_bot():
    print("Iniciando búsqueda de ofertas...")
    ofertas = obtener_ofertas_destacadas()
    
    for oferta in ofertas:
        print(f"Publicando: {oferta['titulo']}")
        
        # 1. Publicar en Telegram
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if bot_token and chat_id:
            publicar_en_telegram(bot_token, chat_id, oferta['mensaje'])
            
        # 2. Publicar en X (Twitter)
        api_key = os.getenv("TWITTER_API_KEY")
        if api_key:
            publicar_en_x(
                api_key, 
                os.getenv("TWITTER_API_SECRET"), 
                os.getenv("TWITTER_ACCESS_TOKEN"), 
                os.getenv("TWITTER_ACCESS_SECRET"), 
                oferta['mensaje']
            )

if __name__ == "__main__":
    ejecutar_bot()