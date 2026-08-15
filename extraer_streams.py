import json
import re
import requests
from playwright.sync_api import sync_playwright

API_URL = "https://api.ppv.is/api/streams"

def obtener_iframes():
    """Obtiene todas las URLs de iframe desde la API."""
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return []

    urls_iframe = []
    
    # Recorrer la estructura del JSON entregado
    if "streams" in data:
        for categoria in data["streams"]:
            if "streams" in categoria:
                for stream in categoria["streams"]:
                    iframe_url = stream.get("iframe")
                    if iframe_url:
                        # OPCIONAL: Si necesitas recortar antes del '?', descomenta la línea de abajo:
                        # iframe_url = iframe_url.split('?')[0]
                        
                        urls_iframe.append({
                            "name": stream.get("name", "Evento sin nombre"),
                            "url": iframe_url
                        })
    return urls_iframe

def buscar_m3u8_en_iframe(url_info):
    """Abre el iframe en un navegador invisible y captura el enlace .m3u8."""
    nombre_evento = url_info["name"]
    url_objetivo = url_info["url"]
    
    print(f"\n[+] Analizando evento: {nombre_evento}")
    print(f"    URL Iframe: {url_objetivo}")

    enlaces_encontrados = []

    with sync_playwright() as p:
        # Lanzar navegador en modo invisible
        browser = p.chromium.launch(headless=True)
        # Configurar un User-Agent común para evitar bloqueos básicos
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Función interna que se activa con cada petición de red que hace la página
        def interceptar_peticion(request):
            if ".m3u8" in request.url:
                if request.url not in enlaces_encontrados:
                    enlaces_encontrados.append(request.url)
                    print(f"    [ENCONTRADO] -> {request.url}")

        # Registrar el "escuchador" de peticiones de red
        page.on("request", interceptar_peticion)

        try:
            # Ir a la página y esperar hasta 30 segundos a que carguen las conexiones de red
            page.goto(url_objetivo, wait_until="networkidle", timeout=30000)
            # Esperar 5 segundos extra en la pantalla por si el reproductor tarda en arrancar
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"    [!] Tiempo de espera agotado o error al cargar el iframe: {e}")
        finally:
            browser.close()
            
    return enlaces_encontrados

def main():
    print("Iniciando la extracción de transmisiones...")
    eventos = obtener_iframes()
    
    if not eventos:
        print("No se encontraron eventos activos en la API.")
        return

    print(f"Se encontraron {len(eventos)} eventos para procesar.")
    
    # Procesar cada iframe (puedes limitar esto si son demasiados)
    for evento in eventos:
        buscar_m3u8_en_iframe(evento)

if __name__ == "__main__":
    main()
