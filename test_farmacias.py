import csv

from farmacias import ClienteApi, Comuna, Farmacia


def api_falsa(url: str):
    return [
        {"local_id": 10, "comuna_id": 1, "comuna_nombre": "Santiago"},
        {"local_id": 10, "comuna_id": 1, "comuna_nombre": "Santiago"},
        {"local_id": 11, "comuna_id": 2, "comuna_nombre": "Providencia"},
    ]


def test_comuna_elimina_repetidos():
    comunas = Comuna(api=ClienteApi("http://test", api_falsa)).Obtener()
    assert comunas == [{"codigo": 1, "nombre": "Santiago"}, {"codigo": 2, "nombre": "Providencia"}]


def test_busquedas_y_error():
    farmacia = Farmacia(api=ClienteApi("http://test", api_falsa))
    assert farmacia.BuscarPorId(10)["comuna_nombre"] == "Santiago"
    resultado = farmacia.BuscarPorComuna("Santiago")
    assert len(resultado) == 2
    assert resultado[0] == {"codigo": 10, "nombre": "", "direccion": ""}
    assert farmacia.BuscarPorId(99) is None
    assert farmacia.TieneError is True


def test_generar_csv(tmp_path):
    ruta = Farmacia(api=ClienteApi("http://test", api_falsa)).GenerarCSV(tmp_path / "farmacias.csv")
    with ruta.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=";"))
    assert len(filas) == 3