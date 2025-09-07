"""API REST básica para el POS de la carnicería.

La API permite consultar el inventario, registrar ventas y obtener
métricas de ganancias y mermas. Se implementa usando únicamente la
biblioteca estándar de Python.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from pos import POS


class POSHandler(BaseHTTPRequestHandler):
    pos = POS()

    def _json_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self) -> None:  # pragma: no cover - interacción http
        if self.path == "/inventory":
            data = [p.to_dict() for p in self.pos.inventory.products.values()]
            self._json_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/metrics":
            ganancias = sum(s["total_price"] for s in self.pos.sales)
            payload = {"ganancias": ganancias, "mermas": self.pos.merma_log}
            self._json_headers()
            self.wfile.write(json.dumps(payload).encode())
        else:
            self._json_headers(404)
            self.wfile.write(b"{}")

    def do_POST(self) -> None:  # pragma: no cover - interacción http
        if self.path == "/sales":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw or b"{}")
            product_name = data.get("product")
            weight = data.get("weight")
            product = self.pos.inventory.products.get(product_name)
            if not product or not isinstance(weight, (int, float)):
                self._json_headers(400)
                self.wfile.write(b"{}")
                return
            if weight <= 0 or weight > product.current_weight:
                self._json_headers(400)
                self.wfile.write(b"{}")
                return

            total = weight * product.price_per_kg
            product.current_weight -= weight
            self.pos.inventory.save()

            merma = product.initial_weight - (product.initial_weight - product.current_weight)
            self.pos.merma_log.setdefault(product.name, []).append(merma)
            self.pos._save_metrics()

            sale_record = {
                "product": product.name,
                "weight": weight,
                "total_price": total,
            }
            self.pos.sales.append(sale_record)
            self.pos._save_sales()

            self._json_headers(201)
            self.wfile.write(json.dumps(sale_record).encode())
        else:
            self._json_headers(404)
            self.wfile.write(b"{}")


def run(server_class=HTTPServer, handler_class=POSHandler, port: int = 8000) -> None:
    server_address = ("0.0.0.0", port)
    httpd = server_class(server_address, handler_class)
    print(f"Sirviendo API en el puerto {port}")
    httpd.serve_forever()


if __name__ == "__main__":  # pragma: no cover - punto de entrada
    run()
