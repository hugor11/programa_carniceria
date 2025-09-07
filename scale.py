"""Integración básica con balanza para el POS de carnicería.

El módulo intenta leer el peso desde un dispositivo serial conectado a
`/dev/ttyUSB0`. Si la lectura falla, se recurre a pedir manualmente el
peso al usuario. De esta forma se permite trabajar con o sin balanza.
"""

from __future__ import annotations

from typing import Optional


def _read_serial_weight(port: str = "/dev/ttyUSB0", baudrate: int = 9600) -> float:
    """Intenta obtener el peso de una balanza conectada por puerto serial.

    Se utiliza pyserial si está disponible. En caso de cualquier error se
    genera ``RuntimeError`` para que el llamador pueda manejar la
    situación.
    """

    try:
        import serial  # type: ignore

        ser = serial.Serial(port, baudrate=baudrate, timeout=1)
        line = ser.readline().decode().strip()
        ser.close()
        return float(line)
    except Exception as exc:  # pragma: no cover - dependiente de hardware
        raise RuntimeError("No se pudo leer la balanza") from exc


def get_weight_cli(prompt: str = "Ingresa el peso en kg: ") -> float:
    """Obtiene el peso usando la balanza si es posible.

    Si la balanza no está disponible se solicita el peso manualmente al
    usuario mediante ``input``. La función se asegura de regresar un float
    válido.
    """

    try:
        return _read_serial_weight()
    except RuntimeError:
        while True:
            try:
                return float(input(prompt))
            except ValueError:
                print("Peso inválido.")


def get_weight_or_none() -> Optional[float]:
    """Devuelve el peso de la balanza o ``None`` si no es posible leerlo.

    Esta versión es útil para interfaces gráficas donde no es posible
    solicitar input manual directamente.
    """

    try:
        return _read_serial_weight()
    except RuntimeError:
        return None
