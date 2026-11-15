"""Clases del backend para consultar farmacias de turno."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _cargar_env() -> None:
    """Carga pares simples KEY=VALUE sin agregar una dependencia externa."""
    archivo_env = Path(__file__).with_name(".env")
    if not archivo_env.exists():
        return
    for linea in archivo_env.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"'))


_cargar_env()


class ApiError(Exception):
    """Error producido al cargar datos desde la API."""


@dataclass
class Error:
    MessageError: str = ""
    TieneError: bool = False


class ClienteApi:
    """Cliente pequeño y reemplazable para no acoplar las clases a urllib."""

    def __init__(self, base_url: str, transport: Callable[[str], Any] | None = None):
        self.base_url = base_url.rstrip("/")
        self.transport = transport or self._solicitar

    @staticmethod
    def _solicitar(url: str) -> Any:
        request = Request(
            url,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://midas.minsal.cl/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise ApiError(f"No fue posible consultar la API: {exc}") from exc

    def obtener(self, recurso: str, **parametros: str) -> Any:
        consulta = urlencode({k: v for k, v in parametros.items() if v})
        url = f"{self.base_url}/{recurso.lstrip('/')}"
        if consulta:
            url = f"{url}?{consulta}"
        return self.transport(url)


def _lista_de_respuesta(respuesta: Any) -> list[dict[str, Any]]:
    """Acepta listas directas y las envolturas habituales de APIs JSON."""
    if isinstance(respuesta, list):
        return [item for item in respuesta if isinstance(item, dict)]
    if isinstance(respuesta, dict):
        for clave in ("data", "results", "result", "comunas", "farmacias"):
            if clave in respuesta:
                return _lista_de_respuesta(respuesta[clave])
    return []


class Comuna(Error):
    def __init__(self, codigo: int | None = None, nombre: str = "", api: ClienteApi | None = None):
        super().__init__()
        self.Codigo = codigo
        self.Nombre = nombre
        self._api = api or ClienteApi(os.getenv("API_BASE_URL", "https://midas.minsal.cl/farmacia_v2/WS"))

    def _cargar(self) -> list[dict[str, Any]]:
        respuesta = self._api.obtener("getLocalesTurnos.php")
        comunas: list[dict[str, Any]] = []
        vistos: set[tuple[Any, str]] = set()
        for item in _lista_de_respuesta(respuesta):
            codigo = item.get("comuna_id", item.get("codigo", item.get("id", item.get("Codigo"))))
            nombre = str(item.get("comuna_nombre", item.get("nombre", item.get("Nombre", "")))).strip()
            clave = (codigo, nombre.casefold())
            if nombre and clave not in vistos:
                vistos.add(clave)
                comunas.append({"codigo": codigo, "nombre": nombre})
        return comunas

    def Cargar(self) -> list[dict[str, Any]]:
        return self._cargar()

    def Obtener(self) -> list[dict[str, Any]]:
        return self.Cargar()


class Farmacia(Error):
    CAMPOS = (
        "Id", "NombreLocal", "Comuna", "Localidad", "Direccion",
        "HoraApertura", "HoraCierre", "Telefono", "DiaFuncionamiento",
    )

    def __init__(self, api: ClienteApi | None = None, **datos: Any):
        super().__init__()
        self._api = api or ClienteApi(os.getenv("API_BASE_URL", "https://midas.minsal.cl/farmacia_v2/WS"))
        for campo in self.CAMPOS:
            setattr(self, campo, datos.get(campo, datos.get(campo.lower(), "")))

    @staticmethod
    def _limpiar_texto(valor: Any) -> Any:
        if not isinstance(valor, str):
            return valor
        return " ".join(valor.replace("\x00", "").split())

    def _cargar(self) -> list[dict[str, Any]]:
        respuesta = self._api.obtener("getLocalesTurnos.php")
        return [
            {clave: self._limpiar_texto(valor) for clave, valor in farmacia.items()}
            for farmacia in _lista_de_respuesta(respuesta)
        ]

    def Cargar(self) -> list[dict[str, Any]]:
        return self._cargar()

    def Obtener(self) -> list[dict[str, Any]]:
        return self.Cargar()

    def BuscarPorId(self, codigo: int | str) -> dict[str, Any] | None:
        farmacia = next((f for f in self.Cargar() if str(f.get("local_id", f.get("id", f.get("Id", "")))) == str(codigo)), None)
        if farmacia is None:
            self.TieneError = True
            self.MessageError = "No se encontró una farmacia con ese código."
        else:
            self.TieneError = False
            self.MessageError = ""
        return farmacia

    def BuscarPorComuna(self, comuna: str | int) -> list[dict[str, Any]]:
        encontradas = [
            farmacia for farmacia in self.Cargar()
            if str(farmacia.get("comuna_nombre", farmacia.get("comuna", farmacia.get("Comuna", "")))).casefold() == str(comuna).casefold()
            or str(farmacia.get("comuna_id", "")) == str(comuna)
        ]
        if not encontradas:
            self.TieneError = True
            self.MessageError = "No se encontraron farmacias para esa comuna."
        else:
            self.TieneError = False
            self.MessageError = ""
        return [
            {
                "codigo": farmacia.get("local_id", farmacia.get("id", farmacia.get("Id", ""))),
                "nombre": farmacia.get("local_nombre", farmacia.get("nombre_local", farmacia.get("NombreLocal", ""))),
                "direccion": farmacia.get("local_direccion", farmacia.get("direccion", farmacia.get("Direccion", ""))),
            }
            for farmacia in encontradas
        ]

    def GenerarCSV(self, nombre_archivo: str) -> Path:
        farmacias = self.Cargar()
        ruta = Path(nombre_archivo)
        if not ruta.is_absolute():
            ruta = Path(os.getenv("CSV_PATH", ".")) / ruta
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            campos = list(farmacias[0].keys()) if farmacias else list(self.CAMPOS)
            escritor = csv.DictWriter(archivo, fieldnames=campos, delimiter=";", extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(farmacias)
        return ruta