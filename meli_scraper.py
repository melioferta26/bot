import requests
from bs4 import BeautifulSoup
import re

def obtener_ofertas_destacadas():
    # URL de la sección de Ofertas de Mercado Libre Argentina
    url = "https://www.mercadolibre.com.ar/ofertas"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    ofertas = []

    # Extraer items en oferta
    items = soup.find_all('div', class_='promotion-item__container')
    
    for item in items[:5]: # Procesa los 5 primeros productos
        try:
            titulo = item.find('p', class_='promotion-item__title').text.strip()
            precio_actual = item.find('span', class_='andes-money-amount__fraction').text.strip()
            
            link_original = item.find('a', class_='promotion-item__link-mask')['href']
            
            # Formateo del enlace con tu tag/id de afiliado de MELI
            # Reemplazar 'TU_TAG_AFILIADO' por el identificador asignado en la Central de Afiliados
            link_afiliado = f"{link_original}?matt_tool=12345678&matt_word=TU_TAG_AFILIADO"

            # Redacción del mensaje
            mensaje = (
                f"🔥 **¡OFERTA DESTACADA EN MERCADO LIBRE!** 🔥\n\n"
                f"📦 **Producto:** {titulo}\n"
                f"💰 **Precio Promocional:** ${precio_actual}\n\n"
                f"⚡ ¡Aprovechá antes de que se agote el stock!\n"
                f"👉 Compra directa acá: {link_afiliado}"
            )
            
            ofertas.append({
                'titulo': titulo,
                'precio': precio_actual,
                'link': link_afiliado,
                'mensaje': mensaje
            })
        except Exception as e:
            continue
            
    return ofertas