import os
import sys
import xml.etree.ElementTree as ET
import requests

def check_manifest():
    url = os.getenv(
        "TARGET_MPD_URL",
        "https://vod-ott.izzigo.tv/out/u/startover/dash/TNT-HD/manifest.mpd?begin=1795017600&end=1795021200"
    )
    
    headers = {
        "Origin": "https://izzigo.tv",
        "Referer": "https://izzigo.tv",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "application/dash+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    # Opcional: configurar proxy en México si se ejecuta fuera del país
    proxy_url = os.getenv("MX_PROXY_URL")
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    try:
        print(f"Consultando URL inicial: {url}")
        response = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            allow_redirects=True,
            timeout=15
        )
        
        print(f"URL final tras redirección: {response.url}")
        print(f"Código de estado HTTP: {response.status_code}")

        if response.status_code != 200:
            print("El servidor no devolvió un manifiesto válido.")
            sys.exit(1)

        # Parsear el XML del manifiesto DASH
        root = ET.fromstring(response.text)
        mpd_type = root.attrib.get("type", "N/A")
        buffer_depth = root.attrib.get("timeShiftBufferDepth", "N/A")
        publish_time = root.attrib.get("publishTime", "N/A")

        print("\n--- Metadatos del Manifiesto MPD ---")
        print(f"Tipo de stream (type): {mpd_type}")
        print(f"Ventana Time-Shift (timeShiftBufferDepth): {buffer_depth}")
        print(f"Hora de publicación (publishTime): {publish_time}")

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión o protocolo: {e}")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"La respuesta no es un XML válido: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_manifest()
