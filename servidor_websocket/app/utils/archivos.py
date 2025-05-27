import json
import os
import csv
import logging

# 💥 Añade esto al principio para ver errores en consola/log
logging.basicConfig(level=logging.INFO)

HISTORIAL_FILE = "datos/clientes_historial.json"
GRUPOS_FILE = "datos/grupos.json"
FRASES_FILE = "datos/frases.json"
USUARIOS_FILE = "datos/usuarios.json"

logger = logging.getLogger("archivos_csv")
logger.setLevel(logging.INFO)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_historial(historial):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4)

def cargar_grupos():
    if os.path.exists(GRUPOS_FILE):
        with open(GRUPOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_grupos(grupos):
    with open(GRUPOS_FILE, "w", encoding="utf-8") as f:
        json.dump(grupos, f, indent=4)

def cargar_frases():
    if os.path.exists(FRASES_FILE):
        with open(FRASES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_frases(frases):
    with open(FRASES_FILE, "w", encoding="utf-8") as f:
        json.dump(frases, f, indent=4, ensure_ascii=False)

def cargar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4)

import csv
import logging

logger = logging.getLogger("acciones")

def importar_grupos_csv(ruta_csv):
    logger.info(f"📥 [CSV] Leyendo archivo: {ruta_csv}")
    nuevos_grupos = {}

    with open(ruta_csv, "r", encoding="utf-8") as f:
        lector = csv.reader(f)
        for i, fila in enumerate(lector, 1):
            logger.info(f"➡️  Línea {i}: {fila}")
            if not fila or not fila[0].strip():
                raise ValueError(f"❌ Línea {i}: nombre del grupo vacío.")

            nombre_grupo = fila[0].strip()
            nombre_grupo_lower = nombre_grupo.lower()

            if nombre_grupo_lower in [g.lower() for g in nuevos_grupos]:
                raise ValueError(f"❌ Línea {i}: el grupo '{nombre_grupo}' ya fue definido antes en este CSV.")

            miembros = [m.strip() for m in fila[1:] if m.strip()]
            vistos = set()
            miembros_limpios = []

            for m in miembros:
                if m.lower() in vistos:
                    raise ValueError(f"❌ Línea {i}: el usuario '{m}' está repetido dentro del grupo '{nombre_grupo}'.")
                vistos.add(m.lower())
                miembros_limpios.append(m)

            nuevos_grupos[nombre_grupo] = miembros_limpios

    logger.info(f"📂 [CSV] Nuevos grupos encontrados: {list(nuevos_grupos.keys())}")
    from app.utils.archivos import cargar_grupos, guardar_grupos
    actuales = cargar_grupos()
    actuales_lower = {g.lower(): g for g in actuales}
    logger.info(f"📁 [CSV] Grupos actuales ya en sistema: {list(actuales_lower.keys())}")

    conflictos = [g for g in nuevos_grupos if g.lower() in actuales_lower]
    if conflictos:
        logger.warning(f"🚫 [CSV] Conflictos detectados: {conflictos}")
        raise ValueError(f"❌ Ya existen grupos con estos nombres (ignorando mayúsculas): {', '.join(conflictos)}")

    actuales.update(nuevos_grupos)
    guardar_grupos(actuales)
    logger.info(f"✅ [CSV] Se han importado correctamente: {list(nuevos_grupos.keys())}")
    return f"✅ Se importaron correctamente {len(nuevos_grupos)} grupos desde el CSV."
