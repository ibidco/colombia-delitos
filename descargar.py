"""
descargar.py
────────────────────────────────────────────────────────────────
Descarga todos los datos de Conteo de Víctimas V2 desde
datos.gov.co y genera un archivo data.json listo para el sitio.

Uso:
    python descargar.py

Requiere solo librerías estándar de Python — no hay que instalar nada.
────────────────────────────────────────────────────────────────
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

# ── CONFIGURACIÓN ─────────────────────────────────────────────
SODA_URL   = "https://www.datos.gov.co/resource/4mnf-va5w.json"
PAGE_SIZE  = 50000
THIS_YEAR  = datetime.now().year
MAX_YEAR   = THIS_YEAR - 1          # excluir año actual (incompleto)
OUTPUT     = "data.json"            # archivo que se va a generar


# ── PASO 1: DESCARGAR ─────────────────────────────────────────
def descargar():
    """
    Descarga todos los registros agrupados por grupo_delito y a_o_hechos.
    Usa paginación para manejar datasets grandes.
    """
    todos = []
    offset = 0
    pagina = 1

    while True:
        params = urllib.parse.urlencode({
            "$select": "grupo_delito, a_o_hechos, sum(total_victimas) as total",
            "$group":  "grupo_delito, a_o_hechos",
            "$order":  "a_o_hechos ASC",
            "$limit":  str(PAGE_SIZE),
            "$offset": str(offset),
        })
        url = f"{SODA_URL}?{params}"

        print(f"  Descargando página {pagina}... ({len(todos):,} registros hasta ahora)")

        req      = urllib.request.Request(url, headers={"Accept": "application/json"})
        response = urllib.request.urlopen(req, timeout=30)
        batch    = json.loads(response.read().decode())

        if not batch:
            break

        todos.extend(batch)

        if len(batch) < PAGE_SIZE:
            break  # última página

        offset += PAGE_SIZE
        pagina += 1
        time.sleep(0.3)  # pausa breve para no saturar el servidor

    print(f"  ✓ Total descargado: {len(todos):,} registros")
    return todos


# ── PASO 2: PROCESAR ──────────────────────────────────────────
def procesar(rows):
    """
    Convierte la lista de filas en un dict agrupado:
        {
          "HURTO": { "2010": 45000, "2011": 52000, ... },
          "HOMICIDIO DOLOSO": { ... },
          ...
        }
    Filtra años inválidos y el año actual incompleto.
    """
    mapa = {}

    for r in rows:
        grupo = (r.get("grupo_delito") or "SIN CLASIFICAR").strip()
        try:
            anio = int(r.get("a_o_hechos", 0))
        except (ValueError, TypeError):
            continue
        try:
            total = float(r.get("total", 0))
        except (ValueError, TypeError):
            continue

        # Filtrar años fuera de rango
        if anio < 2000 or anio > MAX_YEAR:
            continue

        if grupo not in mapa:
            mapa[grupo] = {}

        clave = str(anio)
        mapa[grupo][clave] = mapa[grupo].get(clave, 0) + total

    return mapa


# ── PASO 3: ESTRUCTURAR PARA EL SITIO ─────────────────────────
def estructurar(mapa):
    """
    Convierte el mapa en una lista ordenada de mayor a menor total,
    con el formato exacto que espera el index.html.
    """
    resultado = []

    for nombre, por_anio in mapa.items():
        total = sum(por_anio.values())
        if total <= 0:
            continue

        # Encontrar el año peak
        anio_peak  = max(por_anio, key=por_anio.get)
        valor_peak = por_anio[anio_peak]

        # Calcular tendencia (último vs penúltimo año)
        anios_sorted = sorted(por_anio.keys())
        if len(anios_sorted) >= 2:
            ultimo    = por_anio[anios_sorted[-1]]
            penultimo = por_anio[anios_sorted[-2]]
            tendencia = ((ultimo - penultimo) / penultimo * 100) if penultimo else 0
        else:
            tendencia = 0

        resultado.append({
            "nombre":     nombre,
            "total":      total,
            "porAnio":    por_anio,        # {"2010": 1234, "2011": 5678, ...}
            "peak":       anio_peak,
            "peakValor":  valor_peak,
            "tendencia":  round(tendencia, 1),
        })

    # Ordenar de mayor a menor total de víctimas
    resultado.sort(key=lambda x: x["total"], reverse=True)

    return resultado


# ── PASO 4: GUARDAR JSON ──────────────────────────────────────
def guardar(datos):
    """
    Guarda el archivo data.json con metadatos incluidos.
    """
    ahora = datetime.now()

    salida = {
        "meta": {
            "generado":    ahora.isoformat(),
            "generadoStr": ahora.strftime("%d de %B de %Y, %H:%M"),
            "fuente":      SODA_URL,
            "hasta_anio":  MAX_YEAR,
            "categorias":  len(datos),
            "total_victimas": sum(d["total"] for d in datos),
        },
        "datos": datos,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    # Calcular tamaño del archivo
    import os
    kb = os.path.getsize(OUTPUT) / 1024
    print(f"  ✓ Archivo guardado: {OUTPUT} ({kb:.0f} KB)")
    return salida


# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 56)
    print("  Descarga de Datos — Delitos en Colombia")
    print(f"  Años: 2000 → {MAX_YEAR}")
    print("=" * 56)

    print("\n[1/3] Descargando datos del API...")
    rows = descargar()

    print("\n[2/3] Procesando registros...")
    mapa  = procesar(rows)
    datos = estructurar(mapa)
    print(f"  ✓ {len(datos)} categorías de delito encontradas")

    print("\n[3/3] Guardando data.json...")
    salida = guardar(datos)

    print("\n" + "=" * 56)
    print(f"  ✓ Listo. {len(datos)} categorías, {salida['meta']['total_victimas']:,.0f} víctimas totales")
    print(f"  Ahora corre: python subir.py")
    print("=" * 56)
