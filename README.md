# Conexion API de farmacias

Proyecto en Python que consulta el servicio de farmacias de turno del
Ministerio de Salud de Chile (MINSAL), permite buscar farmacias y comunas, y
exporta los resultados a un archivo CSV.

## ¿Qué hace el proyecto?

La aplicación se organiza en tres responsabilidades principales:

- `ClienteApi` construye las URL, envía solicitudes HTTP y convierte las
  respuestas JSON. Usa `urllib` de la biblioteca estándar y un tiempo máximo de
  espera de 15 segundos.
- `Comuna` obtiene las comunas asociadas a las farmacias y elimina los
  registros repetidos. Cada comuna se devuelve con su código y nombre.
- `Farmacia` obtiene los locales de turno, limpia sus textos y permite buscar
  por código de local o por comuna.

La respuesta de la API puede ser una lista directa o estar dentro de las
propiedades `data`, `results`, `result`, `comunas` o `farmacias`. Esto permite
trabajar con distintas formas de respuesta del servicio.

## Funcionalidades de `Farmacia`

### Obtener todas las farmacias

```python
from farmacias import Farmacia

farmacias = Farmacia().Obtener()
```

Devuelve una lista de diccionarios con los datos disponibles de cada local.
También se puede usar `Cargar()`, que realiza la misma operación.

### Buscar por código

```python
farmacia = Farmacia()
resultado = farmacia.BuscarPorId(123)
```

Devuelve el diccionario de la farmacia encontrada o `None` si no existe.
Cuando no encuentra el código, `TieneError` queda en `True` y
`MessageError` contiene el mensaje correspondiente.

### Buscar por comuna

```python
farmacia = Farmacia()
resultados = farmacia.BuscarPorComuna("Santiago")
```

La búsqueda acepta el nombre o el código de la comuna. Devuelve una lista
resumida con el código, nombre y dirección de cada local encontrado. Si no hay
resultados, se informa mediante `TieneError` y `MessageError`.

### Generar un CSV

```python
ruta = Farmacia().GenerarCSV("farmacias.csv")
```

Genera un archivo CSV codificado en UTF-8, separado por punto y coma (`;`).
Crea automáticamente la carpeta de destino si no existe. Las columnas se
obtienen de los datos recibidos; si la API no devuelve farmacias, usa los
campos definidos por la clase.

## Punto de entrada

`main.py` ejecuta el flujo principal:

1. Crea una instancia de `Farmacia`.
2. Consulta todas las farmacias de turno.
3. Muestra en consola cuántos registros recibió.
4. Genera el archivo `farmacias.csv`.
5. Informa errores de API o de escritura de archivos sin detenerse con un
   traceback innecesario para el usuario.

## Configuración

El proyecto carga automáticamente un archivo `.env` ubicado en la raíz.
Puedes copiar `.env.example` como `.env`:

```powershell
Copy-Item .env.example .env
```

Variables disponibles:

| Variable | Descripción | Valor predeterminado |
| --- | --- | --- |
| `API_BASE_URL` | URL base del servicio de farmacias | `https://midas.minsal.cl/farmacia_v2/WS` |
| `CSV_PATH` | Carpeta donde se guardan las rutas relativas del CSV | `.` |

Ejemplo:

```env
API_BASE_URL=https://midas.minsal.cl/farmacia_v2/WS
CSV_PATH=salida
```

Cuando `CSV_PATH=salida`, la ejecución de `main.py` genera el archivo en
`salida/farmacias.csv`.

## Instalación y uso

Requiere Python 3.10 o posterior.

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Pruebas

Las pruebas usan un cliente API falso, por lo que no dependen de Internet ni
del estado del servicio externo:

```powershell
pytest -q
```

Se comprueba que:

- las comunas repetidas se eliminan;
- las búsquedas por código y comuna funcionan;
- los errores se registran correctamente;
- el CSV se genera con sus filas y columnas.

## Estructura

```text
.
├── farmacias.py       # Cliente API y clases del dominio
├── main.py            # Ejecución principal
├── test_farmacias.py  # Pruebas automatizadas
├── farmacias.csv      # Datos de entrada de ejemplo
├── .env.example       # Plantilla de configuración
└── requirements.txt   # Dependencias de desarrollo
```
