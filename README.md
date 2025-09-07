# Programa Carnicería

Sistema de punto de venta (POS) para una carnicería. Incluye una versión en consola y una interfaz gráfica sencilla estilo SICAR.

## Uso en consola

```bash
python pos.py
```

Sigue las instrucciones en pantalla para operar el menú.

## Uso con interfaz gráfica

```bash
python pos_gui.py
```

Se abrirá una ventana con pestañas para ventas, inventario y métricas. Requiere un entorno gráfico disponible.

## Integración con balanza

El sistema puede leer automáticamente el peso de una balanza conectada por
puerto serial (`/dev/ttyUSB0`). Si no se detecta una balanza, se solicitará el
peso de forma manual.

## API REST básica

Se incluye un servidor HTTP sencillo para integrar el POS con otras
aplicaciones.

```bash
python api.py
```

Endpoints disponibles:

- `GET /inventory` – Lista de productos con su peso actual.
- `POST /sales` – Registra una venta. Se envía JSON con `product` y `weight`.
- `GET /metrics` – Devuelve ganancias acumuladas y mermas.
