import os
import csv
import glob
import time
import random
import re
import urllib.parse
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # 1 dia de cache para /static (iconos, manifest, sw.js)

CARPETA_CONTENIDO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contenido")

# =========================================================================
# NOMBRE AUTOMATICO (solo se usa si dejas la columna "nombre" vacia en el CSV)
# =========================================================================
def nombre_automatico(url):
    # Intenta adivinar un nombre a partir del archivo. Puede salir raro si
    # el nombre del archivo tenia tildes o ñ (se suelen perder al subir a
    # Dropbox) -- si ves un nombre feo en pantalla, lo mas facil es abrir
    # el CSV y escribir vos el nombre en la columna "nombre".
    filename = urllib.parse.unquote(url.split('/')[-1].split('?')[0])
    nombre = re.sub(r'\.(mp4|webm)$', '', filename, flags=re.IGNORECASE)
    basura = [
        r'-Official-Music-Video.*', r'-Official-Video.*', r'-Director-s-Cut.*',
        r'-HD-UPGRADE.*', r'-4K-Upgrade.*', r'-4K-Film-Restored.*',
        r'-EPISODIO-COMPLETO.*', r'-EPISODO-COMPLETO.*', r'-Extended.*',
        r'-SFW.*', r'-2006', r'-2007', r'-Live.*',
        r'-[a-zA-Z0-9\-_]{11}$', r'_[a-zA-Z0-9\-_]{11}$'
    ]
    for b in basura:
        nombre = re.sub(b, '', nombre, flags=re.IGNORECASE)
    nombre = nombre.replace('-', ' ').replace('_', ' ').strip()
    return nombre or "Undone TV"

def parsear_duracion(valor):
    # Acepta segundos ("227") o formato reloj ("3:47" / "1:02:05").
    valor = str(valor).strip()
    if ":" in valor:
        total = 0
        for parte in valor.split(":"):
            total = total * 60 + int(parte)
        return total
    return int(float(valor))

def _relleno_de_emergencia():
    # Solo se usa si una categoria entera queda vacia (archivo borrado o
    # todas las filas mal escritas). Undone TV nunca se debe caer del todo
    # por un error de edicion -- mejor mostrar esto un rato que romper el sitio.
    return {
        "url": "https://www.dropbox.com/scl/fi/qjovx52w5fyy5j3y131jo/Radiohead-Blipvert-Everything-In-Its-Right-Place-1.mp4?rlkey=hjfkklro3l7uhwkqgdffmxfr2&st=c5mvkfop&raw=1",
        "duracion": 15, "es_blip": True, "nombre": "Undone TV",
    }

def cargar_categoria(archivo, es_blip=False, respaldo=None):
    """Lee un archivo CSV de la carpeta contenido/ y arma la lista de videos.
    Cualquier fila con datos invalidos se salta (con un aviso en el log) en
    vez de romper el sitio entero. Si el archivo queda vacio y se paso una
    lista de 'respaldo' (una categoria parecida), se usa esa mientras tanto
    en vez de mostrar siempre lo mismo."""
    ruta = os.path.join(CARPETA_CONTENIDO, archivo)
    items = []
    if not os.path.exists(ruta):
        print(f"[UndoneTV] AVISO: no se encontro contenido/{archivo}")
    else:
        with open(ruta, newline="", encoding="utf-8") as f:
            for num_fila, fila in enumerate(csv.DictReader(f), start=2):
                url = (fila.get("url") or "").strip()
                if not url:
                    continue
                try:
                    duracion = parsear_duracion(fila.get("duracion", ""))
                    if duracion <= 0:
                        raise ValueError
                except (ValueError, TypeError):
                    print(f"[UndoneTV] AVISO: fila {num_fila} de {archivo} tiene una duracion invalida, se omitio esa fila.")
                    continue
                nombre = (fila.get("nombre") or "").strip() or nombre_automatico(url)
                item = {"url": url, "duracion": duracion, "nombre": nombre}
                if es_blip:
                    item["es_blip"] = True
                items.append(item)
    if not items and respaldo:
        print(f"[UndoneTV] AVISO: '{archivo}' esta vacio, se usa contenido de una categoria parecida mientras tanto.")
        return list(respaldo)
    if not items:
        print(f"[UndoneTV] AVISO: '{archivo}' quedo sin contenido valido, se usa un relleno temporal.")
        items = [_relleno_de_emergencia()]
    return items

# =========================================================================
# CREDITOS: viven en creditos.txt, separados de este archivo de codigo.
# La primera linea del archivo es el encabezado en negrita; cada linea
# siguiente se muestra como su propio renglon en la caja de creditos.
# =========================================================================
def cargar_creditos():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "creditos.txt")
    try:
        with open(ruta, encoding="utf-8") as f:
            lineas = [linea.strip() for linea in f if linea.strip()]
    except (FileNotFoundError, OSError):
        lineas = []
    return lineas if lineas else ["CREDITOS DE TRANSMISION:"]

CREDITOS_LINEAS = cargar_creditos()

# =========================================================================
# CONTENIDO: cada categoria vive en su propio archivo CSV dentro de la
# carpeta contenido/. Para agregar o quitar videos NO hace falta tocar este
# archivo .py -- se edita el .csv correspondiente. Guia completa con un
# ejemplo por categoria en GUIA_DE_CONTENIDO.md
# =========================================================================
BLIPS_REGULARES    = cargar_categoria("blips_regulares.csv", es_blip=True)
BLIPS_UNDONE       = cargar_categoria("blips_undone.csv", es_blip=True)
MUSICALES_NORMALES = cargar_categoria("musicales_normales.csv")
MUSICALES_OSCUROS  = cargar_categoria("musicales_oscuros.csv")
ROCK_CLASICO_PRE89 = cargar_categoria("rock_clasico_pre89.csv")
BLOQUE_A           = cargar_categoria("bloque_a.csv")
BLOQUE_B           = cargar_categoria("bloque_b.csv")
BLOQUE_C           = cargar_categoria("bloque_c.csv")
BLOQUE_E           = cargar_categoria("bloque_e.csv", respaldo=BLOQUE_A)
CORTOS             = cargar_categoria("cortos.csv")
PILOTOS            = cargar_categoria("pilotos.csv", respaldo=CORTOS)
def nombre_de_serie(archivo):
    # Deriva el nombre del programa a partir del nombre del archivo:
    # series_tres_acordes.csv -> "Tres Acordes"
    base = archivo[len("series_"):] if archivo.startswith("series_") else archivo
    base = base[:-4] if base.lower().endswith(".csv") else base
    return base.replace("_", " ").replace("-", " ").strip().title() or "Serie"

def cargar_serie(archivo):
    """Como cargar_categoria, pero ademas lee 'temporada' y 'capitulo' (si
    faltan, asume temporada 1 y capitulos en el orden del archivo) y siempre
    ordena los episodios por temporada y capitulo -- asi salen al aire en
    orden, como un canal de verdad, sin importar en que orden estan las
    filas en el CSV."""
    ruta = os.path.join(CARPETA_CONTENIDO, archivo)
    nombre_show = nombre_de_serie(archivo)
    items = []
    if not os.path.exists(ruta):
        print(f"[UndoneTV] AVISO: no se encontro contenido/{archivo}")
        return items
    with open(ruta, newline="", encoding="utf-8") as f:
        for num_fila, fila in enumerate(csv.DictReader(f), start=2):
            url = (fila.get("url") or "").strip()
            if not url:
                continue
            try:
                duracion = parsear_duracion(fila.get("duracion", ""))
                if duracion <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                print(f"[UndoneTV] AVISO: fila {num_fila} de {archivo} tiene una duracion invalida, se omitio esa fila.")
                continue
            try:
                temporada = int(str(fila.get("temporada") or "1").strip())
            except ValueError:
                temporada = 1
            try:
                capitulo = int(str(fila.get("capitulo") or "").strip())
            except ValueError:
                capitulo = len(items) + 1
            nombre_capitulo = (fila.get("nombre") or "").strip() or nombre_automatico(url)
            items.append({
                "url": url, "duracion": duracion,
                "nombre": f"{nombre_show} T{temporada}E{capitulo}",
                "nombre_capitulo": nombre_capitulo,
                "temporada": temporada, "capitulo": capitulo,
            })
    items.sort(key=lambda i: (i["temporada"], i["capitulo"]))
    if not items:
        print(f"[UndoneTV] AVISO: '{archivo}' quedo sin capitulos validos.")
    return items

def cargar_series():
    # Busca automaticamente CUALQUIER archivo que empiece con "series_"
    # dentro de contenido/ y lo suma como una serie mas a la rotacion.
    # Para agregar una serie nueva no hace falta tocar este archivo: alcanza
    # con crear un CSV llamado series_lo-que-sea.csv (columnas: url,
    # duracion, capitulo, temporada, nombre) y subirlo a la carpeta
    # contenido/.
    patron = os.path.join(CARPETA_CONTENIDO, "series_*.csv")
    archivos = sorted(glob.glob(patron))
    listas = [cargar_serie(os.path.basename(ruta)) for ruta in archivos]
    listas = [l for l in listas if l]  # descarta series sin ningun capitulo valido
    return listas if listas else [[_relleno_de_emergencia()]]

SERIES = cargar_series()

# =========================================================================
# LÓGICA DE PROGRAMACIÓN COMPLETA (MÁQUINA DE ESTADOS)
# =========================================================================
CACHE_PARRILLA = {"inicio_semana_utc": None, "datos": []}

def calcular_num_blips(hora, dia):
    # Días entre semana (Lunes=0, Martes=1, Miércoles=2, Jueves=3, Domingo noche=6)
    if dia in [0, 1, 2, 3, 6]:
        if hora == 21: return 2
        elif hora == 22: return 3
        elif hora == 23: return 4
        elif hora == 0: return 5
        elif hora == 1: return 6
        elif hora == 2: return 7
        elif hora == 3: return 8
        elif hora == 4: return 9
    
    # Fines de semana o fuera del horario progresivo
    if 20 <= hora <= 21: return 2
    elif 22 <= hora <= 23: return 3
    elif 0 <= hora <= 2: return 4
    elif 3 <= hora <= 5: return 5
    return 1

def crear_ciclo(lista_original, rng):
    """Entrega 'el siguiente' item de una lista sin repetir ninguno antes de
    haber pasado por todos. Al completar una vuelta, se vuelve a barajar
    (en vez de repetir siempre el mismo orden) y se evita que el ultimo
    item de una vuelta quede pegado con el primero de la vuelta siguiente."""
    baraja = list(lista_original)
    rng.shuffle(baraja)
    estado = {"i": 0, "anterior": None}
    def siguiente():
        if estado["i"] >= len(baraja):
            nueva = list(lista_original)
            rng.shuffle(nueva)
            if len(nueva) > 1 and nueva[0] is estado["anterior"]:
                nueva[0], nueva[1] = nueva[1], nueva[0]
            baraja[:] = nueva
            estado["i"] = 0
        item = baraja[estado["i"]]
        estado["i"] += 1
        estado["anterior"] = item
        return item
    return siguiente

def generar_parrilla_semanal(inicio_semana_utc):
    rng = random.Random(inicio_semana_utc)
    parrilla = []
    t = inicio_semana_utc
    fin_semana = inicio_semana_utc + 604800

    # ZONA HORARIA VENEZOLANA ASEGURADA (UTC-4 = -14400 segundos)
    OFFSET_VET = -14400

    def hora_vet(ts): return ((ts + OFFSET_VET) % 86400) // 3600
    def dia_semana(ts): return time.gmtime(ts + OFFSET_VET).tm_wday

    # Ciclos: cada uno entrega "el siguiente" sin repetir contenido antes de
    # agotar la lista completa, y se reordena solo al completar una vuelta
    # (en vez de repetir siempre la misma secuencia toda la semana).
    ciclo_blips_r = crear_ciclo(BLIPS_REGULARES, rng)
    ciclo_blips_u = crear_ciclo(BLIPS_UNDONE, rng)
    ciclo_mus_normales = crear_ciclo(MUSICALES_NORMALES, rng)
    ciclo_mus_oscuros = crear_ciclo(MUSICALES_OSCUROS, rng)
    ciclo_rock_manana = crear_ciclo(ROCK_CLASICO_PRE89, rng)
    ciclo_rock_noche = crear_ciclo(ROCK_CLASICO_PRE89, rng)
    ciclo_viernes = crear_ciclo(BLOQUE_A + BLOQUE_C, rng)
    ciclo_bloque_c_indie = crear_ciclo(BLOQUE_C, rng)
    ciclo_bloque_e = crear_ciclo(BLOQUE_E, rng)
    ciclo_pilotos = crear_ciclo(PILOTOS, rng)
    ciclo_cortos = crear_ciclo(CORTOS, rng)

    # Bloque A y B del evento del sabado: se agotan una vez y recien ahi
    # avanza la etapa siguiente (no son un loop largo, son un tramo fijo
    # dentro de la noche), asi que estos si usan indice simple.
    bloque_a = list(BLOQUE_A); rng.shuffle(bloque_a); idx_a = 0
    bloque_b = list(BLOQUE_B); rng.shuffle(bloque_b); idx_b = 0

    # Cada serie mantiene su PROPIO contador de capitulo, independiente del
    # de las demas series, para que cada una salga siempre en orden
    # (T1E1, T1E2, T1E3...) como un canal de verdad -- nunca salteada ni
    # desordenada, sin importar cuantas veces le toque a otra serie primero.
    series = SERIES
    idx_por_serie = [0] * len(series)
    idx_cual_serie = 0
    def obtener_serie():
        nonlocal idx_cual_serie
        j = idx_cual_serie % len(series)
        lista = series[j]
        i = idx_por_serie[j] % len(lista)
        idx_por_serie[j] += 1
        idx_cual_serie += 1
        return lista[i]

    etapa_sabado_noche = 0
    etapa_domingo = 0

    # ------------------------------------------------------------
    # CORTOS: todas las noches de 7pm a 6am salen entre 3 y 6 (nunca mas de
    # los que realmente existan en cortos.csv, y sin repetir ninguno hasta
    # agotar la lista). Se calculan "horarios" parejos dentro de la ventana
    # de esa noche para que queden repartidos, no todos juntos. Si no hay
    # NINGUN corto cargado, esto simplemente no hace nada y la programacion
    # sigue como si no existiera esta seccion.
    # ------------------------------------------------------------
    id_noche_actual = None
    checkpoints_cortos_noche = []

    def es_finde_extendido(dia, hora):
        # El gran finde especial: viernes 6pm a lunes 6am de la semana
        # siguiente. Fuera de esto, dia de semana normal (pero variado).
        return (dia == 4 and hora >= 18) or dia == 5 or dia == 6 or (dia == 0 and hora < 6)

    while t < fin_semana:
        hora = hora_vet(t)
        dia = dia_semana(t)

        def add_blips():
            nonlocal t, hora
            num = calcular_num_blips(hora, dia)
            for i in range(num):
                if i == num - 1 and rng.random() <= 0.4:
                    blip = ciclo_blips_u()
                else:
                    blip = ciclo_blips_r()
                parrilla.append(blip)
                t += blip["duracion"]
                hora = hora_vet(t)

        def add_serie_o_corto():
            nonlocal t, hora
            add_blips()
            serie = obtener_serie()
            parrilla.append(serie)
            t += serie["duracion"]
            hora = hora_vet(t)

        # ------------------------------------------------------------
        # CORTOS GARANTIZADOS: se revisa PRIMERO, antes que cualquier otro
        # bloque del dia, para que aparezcan todas las noches sin importar
        # que otra cosa este sonando (finde especial o dia normal).
        # ------------------------------------------------------------
        en_ventana_cortos = hora >= 19 or hora < 6
        if en_ventana_cortos:
            id_noche = (t + OFFSET_VET - 19 * 3600) // 86400
            if id_noche != id_noche_actual:
                id_noche_actual = id_noche
                disponibles = len(CORTOS)
                objetivo = min(rng.randint(3, 6), disponibles) if disponibles else 0
                horas_restantes_ventana = (6 - hora) % 24
                if objetivo > 0 and horas_restantes_ventana > 0:
                    duracion_ventana = horas_restantes_ventana * 3600
                    checkpoints_cortos_noche = sorted(
                        t + int((i + rng.random()) * duracion_ventana / objetivo)
                        for i in range(objetivo)
                    )
                else:
                    checkpoints_cortos_noche = []

            if checkpoints_cortos_noche and t >= checkpoints_cortos_noche[0]:
                checkpoints_cortos_noche.pop(0)
                add_blips()
                corto = ciclo_cortos()
                parrilla.append(corto)
                t += corto["duracion"]
                continue
        else:
            id_noche_actual = None

        # ------------------------------------------------------------
        # VIERNES 6 PM a SÁBADO 6 AM: Puro Rock Alternativo e Indie
        # ------------------------------------------------------------
        if (dia == 4 and hora >= 18) or (dia == 5 and hora < 6):
            add_blips()
            tema = ciclo_viernes()
            parrilla.append(tema)
            t += tema["duracion"]
            continue

        # ------------------------------------------------------------
        # SÁBADO DESDE LAS 6 AM: Rock Clásico
        # ------------------------------------------------------------
        if dia == 5 and 6 <= hora < 18:
            add_blips()
            tema = ciclo_rock_manana()
            parrilla.append(tema)
            t += tema["duracion"]
            continue

        # ------------------------------------------------------------
        # SÁBADO EVENTO 6 PM (Alt -> Serie -> Clasico -> Serie -> Emo -> Normal)
        # ------------------------------------------------------------
        if dia == 5 and hora >= 18:
            if etapa_sabado_noche == 0:
                if idx_a < len(bloque_a):
                    add_blips()
                    tema = bloque_a[idx_a]
                    idx_a += 1
                    parrilla.append(tema)
                    t += tema["duracion"]
                    continue
                else: etapa_sabado_noche = 1

            if etapa_sabado_noche == 1:
                add_serie_o_corto()
                etapa_sabado_noche = 2
                continue

            if etapa_sabado_noche == 2:
                add_blips()
                tema = ciclo_rock_noche()
                parrilla.append(tema)
                t += tema["duracion"]
                etapa_sabado_noche = 3
                continue

            if etapa_sabado_noche == 3:
                add_serie_o_corto()
                etapa_sabado_noche = 4
                continue

            if etapa_sabado_noche == 4:
                if idx_b < len(bloque_b):
                    add_blips()
                    tema = bloque_b[idx_b]
                    idx_b += 1
                    parrilla.append(tema)
                    t += tema["duracion"]
                    continue
                else: etapa_sabado_noche = 5

        # ------------------------------------------------------------
        # DOMINGO 00:00: Isle unto Thyself + Momento Indie
        # ------------------------------------------------------------
        if dia == 6 and 0 <= hora < 9:
            if etapa_domingo == 0:
                # Busca la cancion "Isle unto Thyself" por su archivo (no por
                # el nombre en pantalla, que se puede editar libremente sin
                # romper esto). Si no la encuentra, usa cualquier cancion de
                # Bloque C en su lugar para no cortar la emision.
                isle = next((item for item in BLOQUE_C if "isle-unto-thyself" in item["url"].lower()), None) or ciclo_bloque_c_indie()
                parrilla.append(isle)
                t += isle["duracion"]
                etapa_domingo = 1
                continue
            elif etapa_domingo == 1:
                num_blips_indie = rng.randint(4, 7)
                for _ in range(num_blips_indie):
                    blip = ciclo_blips_r() if rng.random() > 0.4 else ciclo_blips_u()
                    parrilla.append(blip)
                    t += blip["duracion"]

                tema = ciclo_bloque_c_indie()
                parrilla.append(tema)
                t += tema["duracion"]
                continue

        # ------------------------------------------------------------
        # DOMINGO 9 AM a 10 AM: Rock Clásico
        # ------------------------------------------------------------
        if dia == 6 and hora == 9:
            add_blips()
            tema = ciclo_rock_manana()
            parrilla.append(tema)
            t += tema["duracion"]
            continue

        # ------------------------------------------------------------
        # EL RESTO DE LA SEMANA (fuera de los bloques de arriba):
        # rotacion de musica variada + series/cortos, siempre presente
        # todos los dias. Durante el finde extendido (viernes 6pm a lunes
        # 6am) se suma ademas una chance de pilotos, para que esos huecos
        # tambien se sientan parte del evento grande y no una vuelta brusca
        # a la rutina.
        # ------------------------------------------------------------
        add_blips()
        for _ in range(3):
            es_noche = (hora >= 20 or hora < 6)
            if es_noche and rng.random() < 0.6:
                tema = ciclo_mus_oscuros()
            else:
                tema = ciclo_mus_normales()
            parrilla.append(tema)
            t += tema["duracion"]
            hora = hora_vet(t)
            dia = dia_semana(t)

        if es_finde_extendido(dia, hora) and rng.random() < 0.2:
            add_blips()
            tema = ciclo_pilotos()
            parrilla.append(tema)
            t += tema["duracion"]
        else:
            add_serie_o_corto()

    return parrilla

def obtener_programacion_actual():
    timestamp_actual = int(time.time())
    inicio_semana_utc = (timestamp_actual // 604800) * 604800
    if CACHE_PARRILLA["inicio_semana_utc"] != inicio_semana_utc:
        CACHE_PARRILLA["datos"] = generar_parrilla_semanal(inicio_semana_utc)
        CACHE_PARRILLA["inicio_semana_utc"] = inicio_semana_utc
    segundos_desde_inicio = timestamp_actual - inicio_semana_utc
    tiempo_acumulado = 0
    datos = CACHE_PARRILLA["datos"]
    for i, item in enumerate(datos):
        if segundos_desde_inicio < tiempo_acumulado + item["duracion"]:
            segundo_dentro = segundos_desde_inicio - tiempo_acumulado
            tiempo_restante = item["duracion"] - segundo_dentro
            
            titulo_actual_display = "Intermedio / Comerciales"
            for j in range(i, -1, -1):
                if not datos[j].get("es_blip"):
                    titulo_actual_display = datos[j]["nombre"]
                    break
            
            titulo_siguiente_display = "..."
            for j in range(i + 1, len(datos) + i + 1):
                idx = j % len(datos)
                if not datos[idx].get("es_blip"):
                    titulo_siguiente_display = datos[idx]["nombre"]
                    break
            return item["url"], segundo_dentro, tiempo_restante, titulo_actual_display, titulo_siguiente_display
        tiempo_acumulado += item["duracion"]
    return datos[0]["url"], 0, datos[0]["duracion"], datos[0]["nombre"], datos[1]["nombre"]

# =========================================================================
# RUTAS DE FLASK (CON INTERFAZ COMPLETA)
# =========================================================================
ESPECTADORES_ACTIVOS = {}

def obtener_preview_actual():
    # Modo de prueba: un loop simple e independiente de contenido/borrador.csv,
    # totalmente separado de la grilla en vivo. Nadie mas que quien tenga la
    # clave de vista previa ve esto.
    items = cargar_categoria("borrador.csv")
    duracion_total = sum(i["duracion"] for i in items)
    if duracion_total <= 0:
        items = [_relleno_de_emergencia()]
        duracion_total = items[0]["duracion"]
    pos = time.time() % duracion_total
    acumulado = 0
    for i, item in enumerate(items):
        if acumulado + item["duracion"] > pos:
            segundo_inicio = int(pos - acumulado)
            tiempo_restante = int(item["duracion"] - segundo_inicio)
            siguiente = items[(i + 1) % len(items)]
            return item["url"], segundo_inicio, tiempo_restante, item["nombre"], siguiente["nombre"]
        acumulado += item["duracion"]
    item = items[0]
    return item["url"], 0, item["duracion"], item["nombre"], item["nombre"]

def clave_preview_valida(clave):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_clave.txt")
    try:
        with open(ruta, encoding="utf-8") as f:
            secreta = f.read().strip()
    except (FileNotFoundError, OSError):
        return False
    return bool(clave) and bool(secreta) and clave == secreta

@app.route("/")
def home():
    es_preview = clave_preview_valida(request.args.get('preview'))
    clave_actual = request.args.get('preview', '') if es_preview else ''
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Undone TV</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="preconnect" href="https://www.dropbox.com">
        <link rel="dns-prefetch" href="https://www.dropbox.com">
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">

        <!-- ==== Ajustes para instalar como app (PWA) ==== -->
        <link rel="manifest" href="/static/manifest.json">
        <meta name="theme-color" content="#1a0524">
        <link rel="apple-touch-icon" href="/static/icon-192.png">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Undone TV">
        <!-- ================================================ -->

        <!-- Icono de la pestaña del navegador. Para cambiarlo, reemplaza
             static/favicon.png por tu propia imagen (cuadrada, PNG) con
             EXACTAMENTE ese mismo nombre de archivo. -->
        <link rel="icon" type="image/png" href="/static/favicon.png">

        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { background-color: #0d0212; color: #d900ff; font-family: 'Press Start 2P', monospace; font-size: 10px; padding: 10px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .ie-window { background-color: #1a0524; width: 100%; max-width: 850px; border: 3px solid; border-color: #3b0e4d #0d0212 #0d0212 #3b0e4d; padding: 3px; box-shadow: 0px 0px 10px rgba(217, 0, 255, 0.2); }
            .ie-titlebar { background: linear-gradient(90deg, #4b0082, #1a0524); color: #fff; padding: 6px 10px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0d0212; font-size: 9px; }
            .ie-title-controls span { display: inline-block; width: 16px; height: 16px; background-color: #21082e; border: 2px solid; border-color: #4b1763 #0d0212 #0d0212 #4b1763; text-align: center; line-height: 12px; cursor: pointer; color: #d900ff; margin-left: 2px;}
            .ie-menubar, .ie-toolbar, .ie-addressbar, .ie-statusbar { background-color: #21082e; color: #b18ec4; border-bottom: 2px solid #0d0212; padding: 6px; display: flex; gap: 15px; align-items: center; }
            .ie-menubar span:hover { color: #d900ff; cursor: pointer; }
            .tool-btn { display: flex; align-items: center; gap: 4px; cursor: pointer; color: #d900ff;}
            .tool-btn:hover { text-shadow: 0 0 5px #d900ff; }
            .ie-addressbar { border-bottom: 3px double #0d0212; gap: 8px;}
            .address-input { flex-grow: 1; background-color: #0d0212; border: 2px solid; border-color: #000 #3b0e4d #3b0e4d #000; color: #d900ff; padding: 4px 8px; font-family: 'Press Start 2P', monospace; font-size: 9px; }
            .page-content { background-color: #0d0212; padding: 20px 15px; text-align: center; border: 2px solid; border-color: #000 #21082e #21082e #000; }
            h1 { font-size: 24px; color: #d900ff; text-shadow: 0 0 10px rgba(217,0,255,0.8); margin-bottom: 8px; letter-spacing: 2px; }
            .subtitle { color: #8e5ca8; font-size: 8px; margin-bottom: 15px; line-height: 1.6; }
            .ws-link { display: inline-block; background-color: #12031a; color: #00ff66; text-decoration: none; padding: 8px 12px; border: 2px dashed #00ff66; font-size: 8px; margin-bottom: 20px; transition: 0.2s; }
            .ws-link:hover { background-color: #00ff66; color: #000; }
            .video-container { position: relative; width: 100%; max-width: 854px; margin: 0 auto; aspect-ratio: 16/9; background-color: #000; border: 3px solid; border-color: #000 #3b0e4d #3b0e4d #000;}
            video { width: 100%; height: 100%; object-fit: contain; pointer-events: none; }
            .tv-guide { margin-top: 15px; background-color: #1a0524; border: 2px solid #3b0e4d; padding: 10px; text-align: left; font-size: 8px; color: #b18ec4; max-width: 680px; margin-left: auto; margin-right: auto; }
            .tv-guide span { color: #d900ff; }
            .tv-guide .next { margin-top: 5px; color: #6a4085; }
            .viewers-box { margin-top: 10px; color: #00ff66; font-size: 8px; }
            .fs-button { margin-top: 15px; background-color: #21082e; color: #d900ff; border: 3px solid; border-color: #4b1763 #0d0212 #0d0212 #4b1763; padding: 12px 24px; cursor: pointer; font-family: 'Press Start 2P', monospace; font-size: 10px; }
            .fs-button:active { border-color: #0d0212 #4b1763 #4b1763 #0d0212; }
            .creditos-box { margin-top: 25px; padding: 10px; font-size: 7px; color: #6a4085; border-top: 1px dashed #3b0e4d; text-align: left; line-height: 1.8;}
            .creditos-box span { color: #b18ec4; }
            .ie-statusbar { font-size: 8px; justify-content: space-between; border-top: 2px solid #3b0e4d; border-bottom: none;}
        </style>
    </head>
    <body>
        <div class="ie-window">
            <div class="ie-titlebar">
                <div class="ie-title-text">Undone TV - Microsoft Internet Explorer</div>
                <div class="ie-title-controls"><span>_</span><span>[]</span><span>X</span></div>
            </div>
            <div class="ie-menubar"><span>File</span><span>Edit</span><span>View</span><span>Go</span><span>Favorites</span><span>Help</span></div>
            <div class="ie-toolbar"><div class="tool-btn">&lt; Back</div><div class="tool-btn">Forward &gt;</div><div class="tool-btn">(X) Stop</div><div class="tool-btn">(*) Refresh</div><div class="tool-btn">[H] Home</div></div>
            <div class="ie-addressbar"><span>Address</span><input type="text" class="address-input" value="https://randomtv.onrender.com" readonly></div>
            {% if es_preview %}
            <div style="background: repeating-linear-gradient(45deg, #000, #000 10px, #ffcc00 10px, #ffcc00 20px); text-align: center; padding: 6px;">
                <span style="background:#000; color:#ffcc00; padding: 3px 10px; font-family: 'Press Start 2P', monospace; font-size: 8px; letter-spacing: 1px;">MODO PRUEBA -- SOLO VOS VES ESTO</span>
            </div>
            {% endif %}
            <div class="page-content">
                <h1>UNDONE TV</h1>
                <div class="subtitle">Blips, Musica Y Series Web 24/7</div>
                <a href="https://whatsapp.com/channel/0029VbCPqAa30LKHSrllFa1z" target="_blank" class="ws-link">[ CLIC AQUI PARA NOTICIAS DEL CANAL ]</a>
                <div class="video-container" id="video-wrapper">
                    <div id="reproductor-caja" style="width:100%; height:100%;">
                        <video id="tv-player" preload="none" autoplay muted playsinline disablePictureInPicture controlsList="nodownload nofullscreen noremoteplayback"></video>
                    </div>
                </div>
                <div class="tv-guide"><div>AHORA: <span id="txt-actual">Cargando...</span></div><div class="next">A CONTINUACION: <span id="txt-siguiente">...</span></div></div>
                <div class="viewers-box">[ ESPECTADORES EN LINEA: <span id="num-viewers">1</span> ]</div>
                <button id="btn-audio" class="fs-button" onclick="conectarCanal()">[ SINTONIZAR AUDIO ]</button>
                <div class="creditos-box"><span>{{ lineas_creditos[0] }}</span>{% for linea in lineas_creditos[1:] %}<br>{{ linea }}{% endfor %}</div>
            </div>
            <div class="ie-statusbar"><span>Done</span><span>[e] Internet zone</span></div>
        </div>
        <script>
            var ES_PREVIEW = {{ 'true' if es_preview else 'false' }};
            var CLAVE_PREVIEW = {{ clave_actual|tojson }};
            var URL_INFO = ES_PREVIEW ? ('/api/preview_info?clave=' + encodeURIComponent(CLAVE_PREVIEW)) : '/api/live_info';
            var caja = document.getElementById('reproductor-caja');
            var wrapper = document.getElementById('video-wrapper');
            var btnAudio = document.getElementById('btn-audio');
            var txtActual = document.getElementById('txt-actual');
            var txtSiguiente = document.getElementById('txt-siguiente');
            var txtViewers = document.getElementById('num-viewers');
            var temporizador;
            var player;
            var reintentos = 0;
            // Margen de seguridad: si un video real dura un poco mas de lo que
            // dice su duracion declarada, esto evita que se corte de golpe.
            // El video igual se corta si se pasa MUCHO mas alla de este margen
            // (por si se llega a trabar), pero en el caso normal quien manda
            // es el final natural del video (onended), no este timer.
            var MARGEN_SEGUNDOS = 12;

            function crearReproductorLimpio() {
                if (player) { player.removeAttribute('src'); player.load(); }
                caja.innerHTML = '<video id="tv-player" preload="none" autoplay playsinline disablePictureInPicture controlsList="nodownload nofullscreen noremoteplayback"></video>';
                player = document.getElementById('tv-player');
                player.onended = function() { sincronizarCanal(); };
                player.onerror = function() { console.log("Error de red. Reintentando..."); setTimeout(sincronizarCanal, 3000); };
                if (btnAudio.innerText.indexOf('AUDIO') !== -1) player.muted = true;
                else player.muted = false;
            }

            function sincronizarCanal() {
                var t_recibido = Date.now();
                fetch(URL_INFO)
                    .then(function(respuesta) { return respuesta.json(); })
                    .then(function(datos) {
                        reintentos = 0;
                        crearReproductorLimpio();
                        txtActual.innerText = datos.titulo_actual;
                        txtSiguiente.innerText = datos.titulo_siguiente;
                        setTimeout(function() {
                            // Se compensa el tiempo real que paso desde que
                            // el servidor contesto (red + preparar el video)
                            // para arrancar en la posicion correcta sin
                            // importar cuanto tarde tu conexion o tu celular.
                            // Asi, entres cuando entres, ves lo mismo que
                            // todos los demas estan viendo en vivo.
                            var transcurrido = (Date.now() - t_recibido) / 1000;
                            player.src = datos.video_url + "#t=" + (datos.segundo_inicio + transcurrido);
                            var playPromise = player.play();
                            if (playPromise !== undefined) playPromise.catch(function(err) { console.log("Alineando Stream..."); });
                        }, 1000);
                        clearTimeout(temporizador);
                        temporizador = setTimeout(sincronizarCanal, (datos.tiempo_restante + MARGEN_SEGUNDOS) * 1000);
                    })
                    .catch(function(error) { reintentos++; if (reintentos < 5) setTimeout(sincronizarCanal, 4000); });
            }

            function conectarCanal() {
                if (player) { player.muted = false; player.play().catch(function(e){}); }
                btnAudio.innerText = "[ PANTALLA COMPLETA ]";
                if (!document.fullscreenElement) {
                    if (wrapper.requestFullscreen) wrapper.requestFullscreen().catch(function(){});
                    else if (wrapper.webkitRequestFullscreen) wrapper.webkitRequestFullscreen();
                } else document.exitFullscreen();
            }

            var clientId = localStorage.getItem('undonetv_id');
            if (!clientId) { clientId = Math.random().toString(36).substring(2); localStorage.setItem('undonetv_id', clientId); }
            if (!ES_PREVIEW) {
                setInterval(function() {
                    fetch('/api/ping?id=' + clientId).then(res => res.json()).then(data => { txtViewers.innerText = data.espectadores; }).catch(e => console.log(e));
                }, 60000);
            } else {
                txtViewers.innerText = "modo prueba";
            }
            sincronizarCanal();

            // ==== Registro del service worker (necesario para poder instalar la app) ====
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('/static/sw.js').catch(function(err) {
                        console.log('No se pudo registrar el service worker:', err);
                    });
                });
            }
        </script>
    </body>
    </html>
    """, lineas_creditos=CREDITOS_LINEAS, es_preview=es_preview, clave_actual=clave_actual)

@app.route("/api/preview_info")
def api_preview_info():
    if not clave_preview_valida(request.args.get('clave')):
        return jsonify({"error": "no autorizado"}), 403
    video_url, segundo_inicio, tiempo_restante, titulo_actual, titulo_siguiente = obtener_preview_actual()
    return jsonify({
        "video_url": video_url,
        "segundo_inicio": segundo_inicio,
        "tiempo_restante": tiempo_restante,
        "titulo_actual": titulo_actual,
        "titulo_siguiente": titulo_siguiente
    })

@app.route("/api/live_info")
def api_live_info():
    video_url, segundo_inicio, tiempo_restante, titulo_actual, titulo_siguiente = obtener_programacion_actual()
    return jsonify({
        "video_url": video_url,
        "segundo_inicio": segundo_inicio,
        "tiempo_restante": tiempo_restante,
        "titulo_actual": titulo_actual,
        "titulo_siguiente": titulo_siguiente
    })

@app.route("/api/ping")
def api_ping():
    client_id = request.args.get('id')
    if not client_id:
        client_id = request.headers.get('X-Forwarded-For', request.remote_addr)
    now = time.time()
    ESPECTADORES_ACTIVOS[client_id] = now
    activas = [k for k, v in ESPECTADORES_ACTIVOS.items() if now - v < 70]
    for k in list(ESPECTADORES_ACTIVOS.keys()):
        if k not in activas:
            del ESPECTADORES_ACTIVOS[k]
    return jsonify({"espectadores": max(1, len(ESPECTADORES_ACTIVOS))})

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)

