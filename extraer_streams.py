import json
import re
import requests
from playwright.sync_api import sync_playwright
# Importamos el módulo completo para evitar conflictos de nombres de funciones entre versiones
import playwright_stealth

API_URL = "https://api.ppv.is/api/streams"

def obtener_iframes():
    """Obtiene todas las URLs de iframe desde la API manteniendo los parámetros."""
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
                        urls_iframe.append({
                            "name": stream.get("name", "Evento sin nombre"),
                            "url": iframe_url 
                        })
    return urls_iframe

def buscar_m3u8_en_iframe(url_info):
    """Abre el iframe usando técnicas de evasión de detección (Stealth) y captura el m3u8."""
    nombre_evento = url_info["name"]
    url_objetivo = url_info["url"]
    
    print(f"\n[+] Analizando evento: {nombre_evento}")
    print(f"    URL Iframe: {url_objetivo}")

    enlaces_encontrados = []

    with sync_playwright() as p:
        # Lanzamos Chromium pasando argumentos que ocultan el control automatizado
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="es-ES",
            timezone_id="Europe/Madrid"
        )
        
        page = context.new_page()
        
        # !!!! APLICAMOS MODO SIGILOSO EVITANDO ERRORES DE IMPORTACIÓN !!!!
        # Intentamos usar la función de las versiones nuevas, si falla usamos la clásica
        try:
            playwright_stealth.stealth_sync(page)
        except AttributeError:
            playwright_stealth.stealth(page)

        # Escuchamos todas las peticiones de red
        def interceptar_peticion(request):
            if ".m3u8" in request.url.lower():
                if request.url not in enlaces_encontrados:
                    enlaces_encontrados.append(request.url)
                    print(f"    [ENCONTRADO] -> {request.url}")

        page.on("request", interceptar_peticion)

        try:
            # Navegar al iframe
            page.goto(url_objetivo, wait_until="domcontentloaded", timeout=45000)
            
            # Esperamos a que los scripts internos de la web terminen de descifrar
            page.wait_for_timeout(5000)
            
            # Simulamos un clic en el centro para despertar reproductores "Click to Play"
            page.mouse.click(640, 360)
            
            # Damos 10 segundos adicionales para que empiece a reproducir y salte la petición .m3u8
            print("    [*] Esperando transmisión de datos...")
            page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"    [!] Ocurrió un inconveniente durante el análisis: {e}")
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
    
    primer_evento = eventos[0]
    enlaces = buscar_m3u8_en_iframe(primer_evento)
    
    if enlaces:
        print(f"\n[ÉXITO] Se obtuvieron {len(enlaces)} enlace(s) .m3u8.")
    else:
        print("\n[ALERTA] No se detectó ninguna petición .m3u8 en este evento con el método Stealth.")

if __name__ == "__main__":
    main()
