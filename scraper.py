import os
import requests
from bs4 import BeautifulSoup
import tweepy
from database import log_event, increment_stat

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AFFILIATE_TAG = os.getenv('AFFILIATE_TAG', 'ofermeli')

X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET')

CATEGORIES = [
    {"name": "⚡ Oferta Relámpago", "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA779357-1&promotion_type=lightning"},
    {"name": "💥 Precio Imbatible", "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA1321205-1&deal_ids=MLA1321205"},
    {"name": "🏷️ Liquidación", "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA916439-1"},
    {"name": "💰 Menos de $20.000", "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA779357-1&price=0.0-20000.0"}
]

def clean_url(url):
    base_url = url.split('?')[0].split('#')[0]
    return f"{base_url}?mattool={AFFILIATE_TAG}"

def fetch_product_from_category(cat_info):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(cat_info['url'], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        candidates = soup.find_all('a', href=True)
        for a in candidates:
            href = a['href']
            if any(forbidden in href for forbidden in ['/addresses/', '/navigation/', '/gz/web/', '/login', '/supermercado', 'categories']):
                continue
            
            if ('/p/MLA' in href or '/MLA-' in href) and href.startswith('https://'):
                title = a.get_text(strip=True)
                if not title or len(title) < 5 or "Enviar a" in title:
                    img = a.find('img')
                    title = img['alt'] if (img and img.get('alt')) else "Producto en Oferta"
                
                return {
                    "category": cat_info['name'],
                    "title": title[:60] + "..." if len(title) > 60 else title,
                    "url": clean_url(href),
                    "raw_url": href
                }
    except Exception as e:
        print(f"Error procesando {cat_info['name']}: {e}")
    return None

def send_telegram_msg(products):
    msg = "🔥 ¡MEJORES OFERTAS DESTACADAS EN MERCADO LIBRE! 🔥\n\n"
    for p in products:
        msg += f"{p['category']}\n📦 {p['title']}\n👉 {p['url']}\n\n"
    msg += "⚡ ¡Aprovechá las promociones antes de que se agoten!"
    
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': msg,
        'disable_web_page_preview': True
    }
    try:
        res = requests.post(tg_url, json=payload, timeout=10)
        return res.status_code == 200, msg, None
    except Exception as e:
        return False, msg, str(e)

def post_to_x(products):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        return False, "", "Faltan credenciales de X en las variables de entorno."
        
    try:
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET
        )
        
        tweet_text = "🔥 ¡NUEVAS OFERTAS EN MERCADO LIBRE! 🔥\n\n"
        for p in products[:3]:
            tweet_text += f"{p['category']}: {p['url']}\n"
        tweet_text += "\n#Ofertas #MercadoLibre"
        
        response = client.create_tweet(text=tweet_text)
        return bool(response.data), tweet_text, None
    except Exception as e:
        return False, "", str(e)

def run_bot_job():
    increment_stat('run')
    found_products = []
    
    for cat in CATEGORIES:
        product = fetch_product_from_category(cat)
        if product:
            found_products.append(product)
            
    if not found_products:
        log_event('ERROR', 'No se encontraron ofertas en Mercado Libre', 'Sin productos', '', '')
        increment_stat('fail')
        return False

    # Intentar envíos
    tg_ok, tg_msg, tg_err = send_telegram_msg(found_products)
    x_ok, x_msg, x_err = post_to_x(found_products)

    # Evaluación de estado estricto
    all_success = tg_ok and x_ok
    status_label = 'SUCCESS' if all_success else 'ERROR'

    # Construcción de detalles y red de fallos
    network_status = f"Telegram: {'OK' if tg_ok else 'FALLO (' + str(tg_err) + ')'} | X: {'OK' if x_ok else 'FALLO (' + str(x_err) + ')'}"
    message_content = tg_msg if tg_msg else x_msg

    sample_prod = found_products[0]
    log_event(status_label, message_content, network_status, sample_prod['raw_url'], sample_prod['url'])

    if all_success:
        increment_stat('success')
        return True
    else:
        increment_stat('fail')
        return False