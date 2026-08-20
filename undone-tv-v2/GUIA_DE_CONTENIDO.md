# Guía para agregar contenido a Undone TV

Ya no hace falta tocar `app.py` para agregar o quitar videos. Cada categoría vive en su propio archivo dentro de la carpeta `contenido/`, y son archivos `.csv` — básicamente una tabla como la de Excel, pero en texto plano. Para agregar un video, agregás una fila. Nada más.

---

## La receta universal (aplica a las 13 categorías)

Todos los archivos tienen las mismas 3 columnas:

| Columna | Obligatoria | Qué va ahí |
|---|---|---|
| `url` | Sí | El link **directo** de Dropbox del video |
| `duracion` | Sí | Cuánto dura el video |
| `nombre` | No | Lo que se muestra en pantalla ("AHORA:") |

### 1. Conseguir la `url` correcta
Tiene que ser un link de descarga directa de Dropbox — es decir, que termine en `raw=1`. Si copiás el link para compartir normal de Dropbox, va a terminar en `dl=0`; cambiá esa parte por `raw=1`, o revisá que el que copiás ya diga `raw=1` al final (así son todos los que ya están cargados).

### 2. Escribir la `duracion`
Podés escribirla como `minutos:segundos` (por ejemplo `3:47`) o como `horas:minutos:segundos` para algo más largo (`1:02:05`). También aceptás solo segundos (`227`) si preferís.

**Para saber cuánto dura tu video:** arrastrá el archivo de video a una pestaña nueva de Chrome (se abre solo con un reproductor) y mirá el contador de abajo.

**Si no estás segura/o del número exacto, redondeá hacia ARRIBA, no hacia abajo.** El sistema ya tiene 12 segundos de margen y prioriza que el video termine solo antes de cambiar — pero ese margen es para errores chicos. Si la duración que escribís es bastante más corta que el video real, se va a cortar antes de tiempo. Si es un poco más larga, no pasa nada.

### 3. Escribir el `nombre` (opcional)
Es lo que va a decir "AHORA: ..." en pantalla mientras se reproduce. Si lo dejás vacío, el sistema intenta adivinarlo a partir del nombre del archivo — pero esto puede salir raro si el archivo tenía tildes o "ñ" (se pierden fácil al subir a Dropbox). Lo más prolijo es escribirlo vos mismo.

### Ejemplo de fila completa
```
https://www.dropbox.com/scl/fi/abc123.../Cancion-Nueva.mp4?rlkey=xyz&raw=1,3:20,Mi Banda Favorita
```

---

## Cómo editar un archivo CSV en GitHub

1. Entrá a tu repositorio en github.com y abrí la carpeta `contenido`.
2. Hacé clic en el archivo de la categoría que querés editar (por ejemplo `bloque_a.csv`).
3. Arriba a la derecha, hacé clic en el ícono de lápiz (Edit).
4. GitHub te muestra una tabla (no texto raro) — hacé clic en la última fila y presioná Enter para agregar una fila nueva, o usá el botón "+" si lo ves.
5. Completá `url`, `duracion` y `nombre` en su columna.
6. Abajo, escribí un mensaje corto (ej: "agrego cancion nueva") y hacé clic en **Commit changes**.
7. Render redeploya solo en 1-3 minutos.

Para borrar un video: borrás toda su fila de la misma manera.

---

## Las 13 categorías, una por una

### 🔵 Blips (los cortitos entre videos)

**`blips_regulares.csv`** — los blips normales, se usan todo el tiempo entre segmentos (más seguidos de madrugada, menos de día).
```
https://www.dropbox.com/scl/fi/qjovx52w5fyy5j3y131jo/Radiohead-Blipvert-Everything-In-Its-Right-Place-1.mp4?rlkey=hjfkklro3l7uhwkqgdffmxfr2&st=c5mvkfop&raw=1,0:15,Radiohead
```

**`blips_undone.csv`** — blips especiales/más raros. Hay 40% de chance de que uno de estos reemplace al último blip de cada tanda.
```
https://www.dropbox.com/scl/fi/7z8oqu2gwpva54c5q3kvh/Undone-TV-Blip-2.mp4?rlkey=j51tsqezhkptnohp4j7cdcmrc&st=95hzo1hd&raw=1,0:13,Undone
```

### 🎵 Música (rotación general)

**`musicales_normales.csv`** — la rotación de música por defecto, la que más se usa día a día.
```
https://www.dropbox.com/scl/fi/4uxfiahxfa1mc0f277stp/Anyone-Can-Play-Guitar.mp4?rlkey=6dgnran1x5fefz6k5pnrtdl1x&st=s21cg3dr&raw=1,3:47,Anyone
```

**`musicales_oscuros.csv`** — música más oscura/movida. De noche (8pm a 6am) hay 60% de chance de que salga una de estas en vez de una "normal".
```
https://www.dropbox.com/scl/fi/1tlz3pn5j5eh46h4jyct3/Crazy-Food.mp4?rlkey=f2fsqiygyr3c6pqb2vwnw53zz&st=823udng3&raw=1,2:43,Crazy
```

### 🎸 Bloques especiales de fin de semana

**`rock_clasico_pre89.csv`** — rock clásico. Ocupa TODO el sábado a la mañana (6am-6pm) hasta agotarse, vuelve a aparecer el sábado a la noche (como tercera etapa del evento) y de nuevo el domingo de 9 a 10am.
```
https://www.dropbox.com/scl/fi/xcp6rnv8rhjvcue5b0fqc/The-Ramones-Surfin-Bird-12-28-1978-Winterland-Official-B2N0EeIV2aQ.webm?rlkey=tj033bnqd7lcomogenvx3xczd&st=mht448us&raw=1,2:35,The Ramones
```

**`bloque_a.csv`** — primera etapa del evento del sábado a la noche (desde las 6pm). También forma parte del bloque de rock alternativo del viernes 9pm a sábado 6am (junto con Bloque C).
```
https://www.dropbox.com/scl/fi/38uz1n2e58vevzoyzy0ti/Buddy-Holly.mp4?rlkey=eqs0t3hdr1j5tpmjjfvy8k7q4&st=fkwmqe2r&raw=1,4:02,Buddy
```

**`bloque_b.csv`** — última etapa del evento del sábado a la noche.
```
https://www.dropbox.com/scl/fi/zh9ecm7oq4m9po5cw4k47/Green-Day-Jesus-Of-Suburbia-Official-Music-Video-4K-Upgrade-fZFmaMbkUD4.webm?rlkey=1a1hpohzet7t5fwfxv7yvrp26&st=fo5u7zj5&raw=1,11:48,Green Day
```

**`bloque_c.csv`** — la otra mitad del bloque del viernes a la noche (junto con Bloque A), y además es de donde sale el segmento especial del domingo a la madrugada ("Isle unto Thyself" + momento indie). **Importante:** no borres la fila de "Isle-unto-Thyself" — si la borrás, el sistema simplemente usa la primera canción de este mismo archivo en su lugar, así que no se rompe nada, pero ese segmento deja de sonar la canción pensada para él.
```
https://www.dropbox.com/scl/fi/ve8xgwx57oxvu82c31rlm/Tally-Hall-Welcome-To-Tally-Hall-SwToedwyhoE.webm?rlkey=noqmvuqgobjj773uv5vacm81l&st=rwrt5i4l&raw=1,3:33,Tally Hall
```

**`bloque_e.csv`** — ⚠️ **este archivo existe pero ahora mismo no se usa en ningún momento de la programación** (ya era así en tu código original, no es algo que haya cambiado yo). Tiene 5 canciones cargadas que nunca salen al aire. Lo dejé funcionando por si en algún momento querés que forme parte de algún horario — avisame y lo conectamos.
```
https://www.dropbox.com/scl/fi/tarhcsuswwsjxqqszue4j/VARIATIONS-ON-A-CLOUD-by-MUSIC-VIDEO-jUc6vVCh5vQ.webm?rlkey=c7vprkogd37u1gn6cg27qfki3&st=9uw044j3&raw=1,3:11,VARIATIONS
```

### 📺 Series y cortos

**`cortos.csv`** — cortos animados. Entre 11pm y 3am hay 50% de chance (máximo una vez por día) de que salga uno de estos en vez de un capítulo de serie.
```
https://www.dropbox.com/scl/fi/zs797lomer9rk0ovw8d4q/Mime-And-Dash-SFW.webm?rlkey=mkcxzbhob4uldurszcp5khjy7&st=4ike8rnf&raw=1,2:52,Mime And Dash
```

**`series_tres_acordes.csv`**, **`series_proyecto_perchi.csv`**, **`series_alejo_y_valentina.csv`** — las 3 series rotan entre sí cada vez que le toca a "serie" en la programación (de madrugada y en el evento del sábado). Cada una en su propio archivo, incluso si son capítulos de la misma serie.
```
https://www.dropbox.com/scl/fi/tg1xe9w2hsaser42rexpo/Tres-Acordes-T01E01-Afortunada-Desdicha-Q2K3KvkUMpM.webm?rlkey=e39evjyzpczh9pr0uzxxco19x&st=hpfp4zlh&raw=1,5:45,Tres Acordes
```

---

## Cambiar el ícono de la página (favicon)

El ícono que aparece en la pestaña del navegador es el archivo `static/favicon.png`. Para cambiarlo:
1. Preparate tu propia imagen, **cuadrada** (por ejemplo 512x512), en formato PNG.
2. Anda a `static/favicon.png` en tu repositorio de GitHub.
3. Add file → Upload files → arrastrá tu imagen nueva con el **mismo nombre exacto** `favicon.png`.
4. Commit changes.

Eso es todo — no hace falta tocar nada más, ni el `app.py`, ni el manifest.

Si en cambio querés cambiar el ícono que aparece cuando alguien instala Undone TV como app en su celular, son los archivos `static/icon-192.png` y `static/icon-512.png` — mismo procedimiento, mismo nombre de archivo.

---

## Si algo sale mal

- **Una fila con datos mal escritos** (por ejemplo, la duración no es un número ni un mm:ss válido) se salta sola — el sitio sigue funcionando normal, esa fila simplemente no se usa.
- **Si vaciás sin querer un archivo entero de categoría**, el sitio tampoco se rompe: usa un contenido de relleno temporal hasta que vuelvas a cargar algo ahí.
- **Si un video no reproduce**, lo más común es que el link no termine en `raw=1`, o que el archivo se haya movido/borrado de Dropbox.
