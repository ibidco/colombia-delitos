"""
subir.py
────────────────────────────────────────────────────────────────
Sube el archivo data.json a tu repositorio de GitHub.
Vercel lo detecta y redeploya automáticamente en ~30 segundos.

Uso:
    python subir.py

Configura las 3 variables de la sección CONFIGURACIÓN antes de correr.
────────────────────────────────────────────────────────────────
"""

import json
import base64
import urllib.request
import urllib.error
from datetime import datetime

# ── CONFIGURACIÓN — edita estas 3 líneas ──────────────────────

GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXX"
# Tu token de GitHub. Cómo obtenerlo:
# 1. Ve a github.com → tu foto → Settings
# 2. Developer settings → Personal access tokens → Tokens (classic)
# 3. Generate new token → marca "repo" → Generate
# 4. Copia el token y pégalo aquí (solo se muestra una vez)

GITHUB_USUARIO = "tu-usuario-github"
# Tu nombre de usuario en GitHub (el que aparece en la URL)

GITHUB_REPO = "colombia-delitos"
# El nombre exacto de tu repositorio

# ─────────────────────────────────────────────────────────────
# No edites nada debajo de esta línea
# ─────────────────────────────────────────────────────────────

ARCHIVO_LOCAL  = "data.json"
ARCHIVO_REMOTO = "data.json"   # ruta dentro del repo
API_URL = f"https://api.github.com/repos/{GITHUB_USUARIO}/{GITHUB_REPO}/contents/{ARCHIVO_REMOTO}"


def obtener_sha_actual():
    """
    GitHub requiere el SHA del archivo actual para poder actualizarlo.
    Si el archivo no existe todavía, devuelve None (primera subida).
    """
    req = urllib.request.Request(
        API_URL,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept":        "application/vnd.github.v3+json",
        }
    )
    try:
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read().decode())
        return data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # archivo no existe todavía
        raise


def subir():
    print("=" * 56)
    print("  Subiendo data.json a GitHub")
    print("=" * 56)

    # Leer el archivo local
    print("\n[1/3] Leyendo data.json local...")
    try:
        with open(ARCHIVO_LOCAL, "rb") as f:
            contenido = f.read()
    except FileNotFoundError:
        print(f"  ✗ No se encontró {ARCHIVO_LOCAL}")
        print(f"    Corre primero: python descargar.py")
        return False

    contenido_b64 = base64.b64encode(contenido).decode()
    kb = len(contenido) / 1024
    print(f"  ✓ Archivo leído ({kb:.0f} KB)")

    # Obtener SHA actual (necesario para actualizar)
    print("\n[2/3] Conectando con GitHub...")
    sha = obtener_sha_actual()
    if sha:
        print(f"  ✓ Archivo existente encontrado (SHA: {sha[:8]}…) — se actualizará")
    else:
        print(f"  ✓ Primera subida — se creará el archivo")

    # Preparar el payload
    ahora   = datetime.now().strftime("%d/%m/%Y %H:%M")
    mensaje = f"Actualización datos delitos Colombia — {ahora}"

    payload = {
        "message": mensaje,
        "content": contenido_b64,
    }
    if sha:
        payload["sha"] = sha  # requerido para actualizar

    # Subir
    print("\n[3/3] Subiendo a GitHub...")
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data_bytes,
        method="PUT",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept":        "application/vnd.github.v3+json",
            "Content-Type":  "application/json",
        }
    )

    try:
        response = urllib.request.urlopen(req, timeout=30)
        result   = json.loads(response.read().decode())
        commit   = result.get("commit", {}).get("html_url", "")
        print(f"  ✓ Subido exitosamente")
        print(f"  Commit: {commit}")
        print(f"\n  Vercel detectará el cambio y publicará en ~30 segundos.")
        return True

    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"  ✗ Error HTTP {e.code}: {error}")
        if e.code == 401:
            print("    → El token de GitHub es inválido o expiró.")
        elif e.code == 403:
            print("    → El token no tiene permisos de escritura en el repo.")
        elif e.code == 404:
            print("    → El repositorio no existe o el usuario es incorrecto.")
        return False

    except Exception as e:
        print(f"  ✗ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    # Validación básica antes de correr
    if "XXXXXXX" in GITHUB_TOKEN:
        print("✗ Configura tu GITHUB_TOKEN antes de correr este script.")
        print("  Edita subir.py y reemplaza el token.")
    elif GITHUB_USUARIO == "tu-usuario-github":
        print("✗ Configura tu GITHUB_USUARIO antes de correr este script.")
    else:
        subir()
