# Hecho por @b2b3
# Primero hacer:
#  python -m venv scraper-env    
#  source scraper-env/bin/activate
#  pip install beautifulsoup4 requests googlesearch-python
#  python scraper.py
import csv
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
from requests.exceptions import HTTPError
import os
from collections import Counter
import re

def analizar_palabras_clave(texto, top_n=10):
    # Eliminar signos de puntuación y convertir a minúsculas
    texto = re.sub(r'[^\w\s]', '', texto.lower())
    palabras = texto.split()
    # Filtrar palabras comunes (puedes ampliar esta lista)
    palabras_comunes = set(['el', 'la', 'los', 'las', 'de', 'en', 'y', 'a', 'que', 'con', 'del', 'se', 'por', 'para', 'un', 'una', 'es'])
    palabras_filtradas = [p for p in palabras if p not in palabras_comunes and len(p) > 3]
    contador = Counter(palabras_filtradas)
    return [p[0] for p in contador.most_common(top_n)]

def guardar_resultados(resultados, nombre_base):
    with open(f"{nombre_base}.csv", mode='w', encoding='utf-8', newline='') as archivo_csv:
        fieldnames = ["query", "url", "texto", "palabras_clave"]
        writer = csv.DictWriter(archivo_csv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultados)
    with open(f"{nombre_base}.txt", mode='w', encoding='utf-8') as archivo_txt:
        for res in resultados:
            archivo_txt.write(f"QUERY: {res['query']}\nURL: {res['url']}\nPALABRAS CLAVE: {', '.join(res['palabras_clave'])}\nTEXTO:\n{res['texto']}\n\n{'-'*80}\n")

def cargar_resultados_parciales(nombre_base):
    try:
        with open(f"{nombre_base}.csv", mode='r', encoding='utf-8') as archivo_csv:
            reader = csv.DictReader(archivo_csv)
            return list(reader)
    except FileNotFoundError:
        return []

def guardar_estado(opcion, queries, query_actual, url_actual, resultados, nombre_base):
    estado = {
        'opcion': opcion,
        'queries': queries,
        'query_actual': query_actual,
        'url_actual': url_actual,
        'resultados': resultados
    }
    with open(f"estado_{nombre_base}.json", mode='w', encoding='utf-8') as f:
        json.dump(estado, f)

def cargar_estado(nombre_base):
    try:
        with open(f"estado_{nombre_base}.json", mode='r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def procesar_url(query, url, resultados_parciales):
    # Verificar si esta URL ya fue procesada
    for res in resultados_parciales:
        if res['url'] == url:
            print("")
            print(f"↩️  URL ya procesada anteriormente: {url}")
            return None
    print("")
    print(f"🌐 Procesando: {url}")
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Eliminar elementos no deseados
        for element in soup(["script", "style", "noscript", "iframe", "nav", "footer"]):
            element.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())[:5000]
        palabras_clave = analizar_palabras_clave(text)
        
        resultado = {
            "query": query,
            "url": url,
            "texto": text,
            "palabras_clave": palabras_clave
        }
        
        time.sleep(3)  # Espera para evitar bloqueos
        return resultado
        
    except HTTPError as http_err:
        if response.status_code == 429:
            print("")
            print(f"⚠️  Demasiadas peticiones (429) en {url}. Guardando resultados parciales...")
            raise
        else:
            print("")
            print(f"❌ HTTP error con {url}: {http_err}")
    except Exception as e:
        print("")
        print(f"❌ Error con {url}: {e}")
    return None

def scraper_generico(queries, num_results, nombre_base, resultados_parciales=None):
    if resultados_parciales is None:
        resultados_parciales = []
    
    # Convertir a lista si es necesario (para compatibilidad con carga de CSV)
    if resultados_parciales and isinstance(resultados_parciales[0], dict):
        urls_procesadas = {res['url'] for res in resultados_parciales}
    else:
        urls_procesadas = set()
    
    resultados = resultados_parciales.copy()
    
    try:
        for query_idx, query in enumerate(queries):
            print("")
            print(f"\n🔍 Buscando: {query}")
            
            # Obtener resultados de búsqueda
            urls_busqueda = list(search(query, num_results=num_results, lang="es"))
            
            for url_idx, url in enumerate(urls_busqueda):
                if url in urls_procesadas:
                    print("")
                    print(f"↩️  Saltando URL ya procesada: {url}")
                    continue
                    
                try:
                    resultado = procesar_url(query, url, resultados)
                    if resultado:
                        resultados.append(resultado)
                        urls_procesadas.add(url)
                        
                        # Guardar estado cada 5 URLs
                        if (url_idx + 1) % 5 == 0:
                            guardar_resultados(resultados, f"{nombre_base}_parciales")
                            print(f"💾 Checkpoint guardado (Query {query_idx+1}/{len(queries)}, URL {url_idx+1}/{len(urls_busqueda)})")
                            
                except Exception as e:
                    guardar_resultados(resultados, f"{nombre_base}_parciales")
                    print(f"⚠️  Error grave. Resultados guardados. Error: {e}")
                    return resultados
                    
            # Guardar después de cada query completa
            guardar_resultados(resultados, f"{nombre_base}_parciales")
            print(f"✅ Query completada: {query}")
            
    except KeyboardInterrupt:
        print("\n⏹  Scraping interrumpido por el usuario. Guardando resultados...")
        guardar_resultados(resultados, f"{nombre_base}_parciales")
        return resultados
    except Exception as e:
        print(f"\n⚠️  Error inesperado: {e}. Guardando resultados parciales...")
        guardar_resultados(resultados, f"{nombre_base}_parciales")
        return resultados
    
    return resultados

# Las funciones específicas (hacking, marketing, programador_web) se simplifican usando scraper_generico
def scraper_hacking(num_results=10):
    print("1. Scraper Hacking - Buscando paginas vulnerables")
    queries = [
        'inurl:"wp-admin" intitle:"login"',
        'inurl:"wp-login.php" "Lost your password?"',
        'inurl:"wp-admin" intext:"password" "form"',
        'inurl:"wp-admin" intext:"username" "form"',
        '"sql injection" inurl:"wp-admin"',
        '"injection" inurl:"wp-login.php"'
    ]
    
    # Cargar resultados parciales si existen
    resultados_parciales = cargar_resultados_parciales("resultados_hacking_parciales")
    if resultados_parciales:
        print(f"🔍 Continuando desde {len(resultados_parciales)} resultados previos")
    
    return scraper_generico(queries, num_results, "resultados_hacking", resultados_parciales)

# (Las otras funciones scraper_marketing y scraper_programador_web se modificarían de forma similar)

if __name__ == "__main__":
    import json
    print("")
    print("Hola! Elige que scraper ejecutar:")
    print("")
    print("1 - Scraper hacking (busqueda de paginas vulnerables)")
    print("2 - Scraper marketing (busqueda de webs para marketing)")
    print("3 - Scraper programación (busqueda de webs y perfiles de programadores)")
    print("")
    opcion = input("Introduce 1, 2 o 3 y pulsa Enter: ").strip()

    num_results = 10

    try:
        if opcion == "1":
            hacking_results = scraper_hacking(num_results=num_results)
            guardar_resultados(hacking_results, "resultados_hacking")
            print("")
            print("✅ Scraper hacking completado. Archivos guardados como resultados_hacking.csv y .txt")
            
        elif opcion == "2":
            print("Introduce las queries que quieres scrapear para marketing.")
            print("Puedes introducir varias queries separadas por comas (',').")
            user_input = input("Queries: ").strip()
            queries = [q.strip() for q in user_input.split(",") if q.strip()]
            if not queries:
                print("No has introducido ninguna query válida. Usando queries predeterminadas...")
                queries = [
                    "agencias inmobiliarias en Holanda",
                    "agencias inmobiliarias en Madrid",
                    "alquiler vacacional en Barcelona",
                    "inversores en Holanda",
                    "filetype:pdf presupuesto agencia inmobiliaria",
                    "intitle:\"Contacto\" agencia inmobiliaria"
                ]
            
            resultados_parciales = cargar_resultados_parciales("resultados_marketing_parciales")
            marketing_results = scraper_generico(queries, num_results, "resultados_marketing", resultados_parciales)
            guardar_resultados(marketing_results, "resultados_marketing")
            print("")
            print("✅ Scraper marketing completado. Archivos guardados como resultados_marketing.csv y .txt")
            
        elif opcion == "3":
            print("")
            print("Introduce las queries que quieres scrapear para programador web.")
            print("Puedes introducir varias queries separadas por comas (',').")
            user_input = input("Queries: ").strip()
            queries = [q.strip() for q in user_input.split(",") if q.strip()]
            if not queries:
                print("No has introducido ninguna query válida. Usando queries predeterminadas...")
                queries = [
                    "portafolio programador web",
                    "desarrollador web freelance",
                    "programador web Barcelona",
                    "programador web Madrid",
                    "contratar programador web",
                    "perfil LinkedIn programador web"
                ]
            
            resultados_parciales = cargar_resultados_parciales("resultados_programador_web_parciales")
            progweb_results = scraper_generico(queries, num_results, "resultados_programador_web", resultados_parciales)
            guardar_resultados(progweb_results, "resultados_programador_web")
            print("")
            print("✅ Scraper programador web completado. Archivos guardados como resultados_programador_web.csv y .txt")
            
        else:
            print("")
            print("Opcion no valida. Por favor ejecuta el script de nuevo y elige 1, 2 o 3.")
            
    except Exception as e:
        print("")
        print(f"\n⚠️  Error inesperado en el main: {e}")
        print("Intenta continuar más tarde con los resultados parciales guardados.")