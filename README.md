# Evaluación 3 POO

Implementación en Python de las clases `Error`, `Comuna` y `Farmacia`.

## Ejecución

```powershell
python -m pip install -r requirements.txt
pytest -q
python -m pytest -q
python main.py
```

La URL base y la ruta de salida del CSV se configuran en `.env`. Por defecto se usa el servicio de farmacias de turno del MINSAL:

```powershell
$env:API_BASE_URL = "https://tu-api.example"
python main.py
```

La implementación usa `getComunas.php` y `getLocalesTurnos.php`. Las respuestas pueden ser listas directas o estar dentro de `data`, `results`, `comunas` o `farmacias`.