import json
import re
import requests
from bs4 import BeautifulSoup


def obtener_ofertas_destacadas():
  url = "https://www.mercadolibre.com.ar/ofertas"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "es-AR,es;q=0.9",
  }

  response = requests.get(url, headers=headers)
  if response.status_code != 200:
    print(f"Error al acceder a Mercado Libre: Status {response.status_code}")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  ofertas = []
  TAG_AFILIADO = "ofermeli"  # Tu tag configurado

  # Estrategia 1: Extraer datos del JSON-LD incrustado (más estable)
  scripts = soup.find_all("script", type="application/ld+json")
  for script in scripts:
    if not script.string:
      continue
    try:
      data = json.loads(script.string)
      items = []

      # Si es una ItemList o un catálogo
      if isinstance(data, dict) and "itemListElement" in data:
        items = data["itemListElement"]
      elif isinstance(data, list):
        items = data

      for elem in items:
        prod = elem.get("item", elem) if isinstance(elem, dict) else {}
        titulo = prod.get("name")
        link_original = prod.get("url")

        # Extraer precio si existe
        offers = prod.get("offers", {})
        precio_actual = None
        if isinstance(offers, dict):
          precio_actual = offers.get("price")
        elif isinstance(offers, list) and len(offers) > 0:
          precio_actual = offers[0].get("price")

        if titulo and link_original:
          link_afiliado = (
              f"{link_original}?matt_tool=12345678&matt_word={TAG_AFILIADO}"
          )
          precio_str = f"${precio_actual}" if precio_actual else "Consultar"

          mensaje = (
              f"🔥 **¡OFERTA DESTACADA EN MERCADO LIBRE!** 🔥\n\n"
              f"📦 **Producto:** {titulo}\n"
              f"💰 **Precio Promocional:** {precio_str}\n\n"
              f"⚡ ¡Aprovechá antes de que se agote el stock!\n"
              f"👉 Compra directa acá: {link_afiliado}"
          )

          ofertas.append({
              "titulo": titulo,
              "precio": precio_str,
              "link": link_afiliado,
              "mensaje": mensaje,
          })

          if len(ofertas) >= 5:
            break
    except Exception as e:
      continue

    if ofertas:
      break

  # Estrategia 2: Respaldo por búsqueda de hipervínculos si el JSON-LD no tiene ofertas
  if not ofertas:
    links = soup.find_all(
        "a", href=re.compile(r"https://www\.mercadolibre\.com\.ar/")
    )
    vistos = set()
    for a in links:
      href = a.get("href", "")
      titulo = a.get_text(strip=True)
      if (
          "/p/MLA" in href or "promotions" in href or "ofertas" in href
      ) and len(titulo) > 15:
        if href in vistos:
          continue
        vistos.add(href)

        link_afiliado = f"{href}?matt_tool=12345678&matt_word={TAG_AFILIADO}"
        mensaje = (
            f"🔥 **¡OFERTA DESTACADA EN MERCADO LIBRE!** 🔥\n\n"
            f"📦 **Producto:** {titulo}\n\n"
            f"⚡ ¡Aprovechá la promoción del día!\n"
            f"👉 Compra directa acá: {link_afiliado}"
        )
        ofertas.append({
            "titulo": titulo,
            "precio": "Ver en sitio",
            "link": link_afiliado,
            "mensaje": mensaje,
        })
        if len(ofertas) >= 5:
          break

  print(f"Se encontraron {len(ofertas)} ofertas.")
  return ofertas
