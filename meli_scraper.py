import requests
from bs4 import BeautifulSoup

def obtener_ofertas_destacadas():
    url = "https://www.mercadolibre.com.ar/ofertas"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error al acceder a Mercado Libre: Status {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    ofertas = []

    # Intento 1: Clases habituales de items en oferta
    items = soup.find_all('div', class_='promotion-item__container')
    
    # Intento 2: Si no encuentra con la clase anterior, busca en la grilla principal
    if not items:
        items = soup.select('.promotions-item, .promotion-item, li.promotion-item')

    for item in items[:5]:
        try:
            titulo_elem = item.find('p', class_='promotion-item__title') or item.find('h2') or item.find('p')
            precio_elem = item.find('span', class_='andes-money-amount__fraction')
            link_elem = item.find('a', href=True)

            if not (titulo_elem and precio_elem and link_elem):
                continue

            titulo = titulo_elem.text.strip()
            precio_actual = precio_elem.text.strip()
            link_original = link_elem['href']
            
            # Reemplazar 'TU_TAG_AFILIADO' por tu identificador de afiliado
            TAG_AFILIADO = "ofermeli" 
            link_afiliado = f"{link_original}?matt_tool=12345678&matt_word={TAG_AFILIADO}"

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
            print(f"Error procesando un item: {e}")
            continue
            
    print(f"Se encontraron {len(ofertas)} ofertas.")
    return ofertas
