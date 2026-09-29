import os
import requests
from bs4 import BeautifulSoup
from database import log_event, increment_stat

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AFFILIATE_TAG = os.getenv('AFFILIATE_TAG', 'tu_tag_afiliado')

def run_bot_job():
    increment_stat('run')
    try:
        # 1. Scraping Mercado Libre
        url = "https://www.mercadolibre.com.ar/ofertas"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Filtrar enlaces descartando geolocalización o navegación interna
        candidate_links = soup.find_all('a', href=True)
        valid_product = None

        for link in candidate_links:
            href = link['href']
            # Filtro anti-bug (evita /addresses/, /navigation/, etc.)
            if '/addresses/' in href or '/navigation/' in href or '/gz/web/' in href or '/login' in href:
                continue
            
            # Buscar patrones válidos de ofertas / productos de Mercado Libre
            if ('/MLA-' in href or '/p/MLA' in href or 'ofertas' in href) and href.startswith('https://'):
                title = link.get_text(strip=True) or "Oferta Destacada"
                if len(title) > 3 and "Enviar a" not in title:
                    valid_product = {'title': title, 'url': href}
                    break

        if not valid_product:
            log_event('WARNING', 'No se encontró ninguna oferta válida en el scraping.')
            increment_stat('fail')
            return False

        # 2. Construir Link de Afiliado
        prod_url = valid_product['url']
        affiliate_url = f"{prod_url}?mattool={AFFILIATE_TAG}" if '?' not in prod_url else f"{prod_url}&mattool={AFFILIATE_TAG}"
        prod_title = valid_product['title']

        # 3. Formatear y Enviar a Telegram
        msg = (
            f"🔥 **¡OFERTA DESTACADA EN MERCADO LIBRE!** 🔥\n\n"
            f"📦 **Producto:** {prod_title}\n\n"
            f"⚡ ¡Aprovechá la promoción del día!\n"
            f"👉 **Compra directa acá:** {affiliate_url}"
        )

        tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': msg,
            'parse_mode': 'Markdown'
        }
        tg_res = requests.post(tg_url, json=payload, timeout=10)

        if tg_res.status_code == 200:
            log_event('SUCCESS', 'Mensaje enviado a Telegram correctamente', prod_title, prod_url, affiliate_url)
            increment_stat('success')
            return True
        else:
            log_event('ERROR', f'Error enviando a Telegram: {tg_res.text}', prod_title, prod_url, affiliate_url)
            increment_stat('fail')
            return False

    except Exception as e:
        log_event('ERROR', f'Error inesperado en ejecución: {str(e)}')
        increment_stat('fail')
        return False