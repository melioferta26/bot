import os
import requests
from bs4 import BeautifulSoup
import tweepy
from database import log_event, increment_stat

# Credenciales Telegram & Afiliado
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AFFILIATE_TAG = os.getenv('AFFILIATE_TAG', 'ofermeli')

# Credenciales X (Twitter)
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET')

# URLs de Categorías Solicitadas
CATEGORIES = [
    {
        "name": "⚡ Oferta Relámpago",
        "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA779357-1&promotion_type=lightning"
    },
    {
        "name": "💥 Precio Imbatible",
        "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA1321205-1&deal_ids=MLA1321205"
    },
    {
        "name": "🏷️ Liquidación",
        "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA916439-1"
    },
    {
        "name": "💰 Menos de $20.000",
        "url": "https://www.mercadolibre.com.ar/ofertas?container_id=MLA779357-1&price=0.0-20000.0"
    }
]

def clean_url(url):
    """Limpia la URL y le adjunta el tag de afiliado."""
    base_url = url.split('?')[0].split('#')[0]
    return f"{base_url}?mattool={AFFILIATE_TAG}"

def fetch_product_from_category(cat_info):
    """Accede a una URL de categoría y extrae una publicación concreta de producto."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(cat_info['url'], headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscar enlaces que apunten directamente a publicaciones de producto (/p/MLA o /MLA-)
        candidates = soup.find_all('a', href=True)
        for a in candidates:
            href = a['href']
            
            # Filtros de exclusión (evitar supermercado, navegación, categorías generales)
            if any(forbidden in href for forbidden in ['/addresses/', '/navigation/', '/gz/web/', '/login', '/supermercado', 'categories']):
                continue
            
            # Formato de publicación de producto individual
            if ('/p/MLA' in href or '/MLA-' in href) and href.startswith('https://'):
                # Intentar obtener el título del producto
                title = a.get_text(strip=True)
                if not title or len(title) < 5 or "Enviar a" in title:
                    # Si la etiqueta a no tiene el texto, buscar dentro del contenedor o atributo alt/title
                    img = a.find('img')
                    if img and img.get('alt'):
                        title = img['alt']
                    else:
                        title = "Producto en Oferta"
                
                aff_link = clean_url(href)
                return {
                    "category": cat_info['name'],
                    "title": title[:60] + "..." if len(title) > 60 else title,
                    "url": aff_link,
                    "raw_url": href
                }
    except Exception as e:
        print(f"Error procesando {cat_info['name']}: {e}")
    return None

def send_telegram_msg(products):
    """Envía un resumen de las ofertas a Telegram."""
    msg = "🔥 **¡MEJORES OFERTAS DESTACADAS EN MERCADO LIBRE!** 🔥\n\n"
    for p in products:
        msg += f"{p['category']}\n📦 {p['title']}\n👉 [Comprar acá]({p['url']})\n\n"
    
    msg += "⚡ ¡Aprovechá las promociones antes de que se agoten!"
    
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': msg,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }
    res = requests.post(tg_url, json=payload, timeout=10)
    return res.status_code == 200

def post_to_x(products):
    """Publica las ofertas recopiladas en X (Twitter)."""
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        print("Faltan credenciales de X/Twitter")
        return False
        
    try:
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET
        )
        
        tweet_text = "🔥 ¡NUEVAS OFERTAS DESTACADAS EN MERCADO LIBRE! 🔥\n\n"
        for p in products[:3]: # Se limita a 3 para no superar los 280 caracteres
            tweet_text += f"{p['category']}: {p['url']}\n"
            
        tweet_text += "\n#Ofertas #MercadoLibre #Descuentos"
        
        response = client.create_tweet(text=tweet_text)
        return bool(response.data)
    except Exception as e:
        print(f"Error publicando en X: {e}")
        return False

def run_bot_job():
    increment_stat('run')
    found_products = []
    
    # 1. Scraping por cada sección
    for cat in CATEGORIES:
        product = fetch_product_from_category(cat)
        if product:
            found_products.append(product)
            
    if not found_products:
        log_event('WARNING', 'No se pudieron extraer productos válidos de las categorías.')
        increment_stat('fail')
        return False

    # 2. Enviar a Telegram
    tg_success = send_telegram_msg(found_products)
    
    # 3. Publicar en X (Twitter)
    x_success = post_to_x(found_products)

    # 4. Registrar en BD y métricas
    sample_prod = found_products[0]
    if tg_success or x_success:
        status_msg = f"Enviado correctamente (TG: {tg_success}, X: {x_success}) - {len(found_products)} productos."
        log_event('SUCCESS', status_msg, sample_prod['title'], sample_prod['raw_url'], sample_prod['url'])
        increment_stat('success')
        return True
    else:
        log_event('ERROR', 'Fallo al publicar en Telegram y X', sample_prod['title'], sample_prod['raw_url'], sample_prod['url'])
        increment_stat('fail')
        return False