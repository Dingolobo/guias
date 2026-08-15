import json
import re
import requests
from playwright.sync_api import sync_playwright

API_URL = "https://api.ppv.is/api/streams"

def obtener_iframes():
    """Obtiene todas las URLs de iframe desde la API manteniendo los tokens necesarios."""
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return []

    urls_iframe = []
    
    if "streams" in data:
        for categoria in data["streams"]:
            if "streams" in categoria:
                for stream in categoria["streams"]:
                    iframe_url = stream.get("iframe")
                    if iframe_url:
                        # MANTENEMOS LA URL COMPLETA para que el reproductor tenga sus credenciales (como gid=...)
                        urls_iframe.append({
                            "name": stream.get("name", "Evento sin nombre"),
                            "url": iframe_url 
                        })
    return urls_iframe

def buscar_m3u8_en_iframe(url_info):
    """Abre el iframe con tokens, simula interacción y captura el enlace .m3u8."""
    nombre_evento = url_info["name"]
    url_objetivo = url_info["url"]
    
    print(f"\n[+] Analizando evento: {nombre_evento}")
    print(f"    URL Iframe (Con Parámetros): {url_objetivo}")

    enlaces_encontrados = []

    with sync_playwright() as p:
        # Iniciamos Chromium invisible
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Interceptamos las peticiones de red buscando el archivo .m3u8
        def interceptar_peticion(request):
            if ".m3u8" in request.url:
                if request.url not in enlaces_encontrados:
                    enlaces_encontrados.append(request.url)
                    print(f"    [ENCONTRADO] -> {request.url}")

        page.on("request", interceptar_peticion)

        try:
            # Ir a la página y esperar que cargue la estructura básica
            page.goto(url_objetivo, wait_until="domcontentloaded", timeout=30000)
            
            # Forzar una interacción física (Hacer clic en el centro de la pantalla)
            # Esto activa reproductores que requieren un clic del usuario para empezar a transmitir
            page.mouse.click(640, 360) 
            
            # Esperar 8 segundos a que se disparen las conexiones de video tras el clic
            page.wait_for_timeout(8000)
            
        except Exception as e:
            print(f"    [!] Error durante el análisis del iframe: {e}")
        finally:
            browser.close()
            
    return enlaces_encontrados

def main():
    print("Iniciando la extracción de transmisiones...")
    eventos = obtener_iframes()
    
    if not eventos:
        print("No se encontraron eventos activos en la API.")
        return

    print(f"Se detectaron {len(eventos)} eventos en total.")
    print("--- MODO DE PRUEBA: Procesando únicamente el primer stream encontrado ---")
    
    # Tomamos el primer evento de la lista
    primer_evento = eventos[0]
    enlaces = buscar_m3u8_en_iframe(primer_evento)
    
    if enlaces:
        print(f"\n[ÉXITO] Se obtuvieron {len(enlaces)} enlace(s) .m3u8.")
    else:
        print("\n[ALERTA] No se detectó ninguna petición .m3u8 en este evento.")

if __name__ == "__main__":
    main()
