"""Punto de entrada de ejemplo y manejo de errores de la evaluación."""

from farmacias import ApiError, Farmacia


def main() -> None:
    farmacias = Farmacia()
    try:
        datos = farmacias.Obtener()
        print(f"Farmacias recibidas: {len(datos)}")
        farmacias.GenerarCSV("farmacias.csv")
        print("Archivo farmacias.csv generado correctamente.")
    except ApiError as error:
        print(f"Error de API: {error}")
    except OSError as error:
        print(f"Error de archivo: {error}")


if __name__ == "__main__":
    main()