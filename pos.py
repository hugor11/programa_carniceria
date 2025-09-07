"""Sistema de Punto de Venta (POS) para una carnicería.

Manual de uso:
    Ejecuta el programa con `python pos.py`.
    Utiliza el menú para realizar ventas, revisar el inventario y ver métricas.
    Los datos se almacenan en archivos JSON para persistir la información entre sesiones.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# ----------------------------
# Modelos de datos
# ----------------------------

@dataclass
class Product:
    """Representa un producto con precio por kilo y control de peso."""
    name: str
    price_per_kg: float
    initial_weight: float
    current_weight: float

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            price_per_kg=data["price_per_kg"],
            initial_weight=data["initial_weight"],
            current_weight=data.get("current_weight", data["initial_weight"]),
        )


class Inventory:
    """Gestiona los productos disponibles."""
    def __init__(self, file_path: str = "inventory.json"):
        self.file_path = Path(file_path)
        self.products: dict[str, Product] = {}
        self.load()

    def load(self):
        if self.file_path.exists():
            data = json.loads(self.file_path.read_text())
            for item in data:
                product = Product.from_dict(item)
                self.products[product.name] = product
        else:
            # Inventario inicial por defecto
            self.products = {
                "Bistec de res": Product("Bistec de res", 250.0, 10.0, 10.0),
                "Chuleta de cerdo": Product("Chuleta de cerdo", 180.0, 8.0, 8.0),
            }
            self.save()

    def save(self):
        data = [p.to_dict() for p in self.products.values()]
        self.file_path.write_text(json.dumps(data, indent=4))

    def list_products(self):
        for idx, product in enumerate(self.products.values(), start=1):
            print(
                f"{idx}. {product.name} ($ {product.price_per_kg:.2f}/kg, "
                f"{product.current_weight:.2f} kg disponibles)"
            )

    def get_product_by_index(self, index: int) -> Product | None:
        try:
            return list(self.products.values())[index - 1]
        except IndexError:
            return None


class POS:
    """Controla el flujo principal del sistema de ventas."""
    def __init__(self):
        self.inventory = Inventory()
        self.sales_file = Path("sales.json")
        self.metrics_file = Path("metrics.json")
        self.sales: list[dict] = self._load_json(self.sales_file, [])
        self.merma_log: dict[str, list[float]] = self._load_json(self.metrics_file, {})

    def _load_json(self, path: Path, default):
        if path.exists():
            return json.loads(path.read_text())
        return default

    def _save_sales(self):
        self.sales_file.write_text(json.dumps(self.sales, indent=4))

    def _save_metrics(self):
        self.metrics_file.write_text(json.dumps(self.merma_log, indent=4))

    # ----------------------
    # Funciones del sistema
    # ----------------------

    def realizar_venta(self):
        if not self.inventory.products:
            print("No hay productos disponibles.")
            return

        print("Productos disponibles:")
        self.inventory.list_products()
        try:
            choice = int(input("Elige el producto: "))
        except ValueError:
            print("Opción inválida.")
            return

        product = self.inventory.get_product_by_index(choice)
        if not product:
            print("Producto inexistente.")
            return

        try:
            weight = float(input("Ingresa el peso en kg: "))
        except ValueError:
            print("Peso inválido.")
            return

        if weight <= 0 or weight > product.current_weight:
            print("Peso fuera de rango.")
            return

        total = weight * product.price_per_kg
        product.current_weight -= weight
        self.inventory.save()

        merma = product.initial_weight - (product.initial_weight - product.current_weight)
        self.merma_log.setdefault(product.name, []).append(merma)
        self._save_metrics()

        sale_record = {
            "product": product.name,
            "weight": weight,
            "total_price": total,
            "merma_after_sale": merma,
            "timestamp": datetime.now().isoformat(),
        }
        self.sales.append(sale_record)
        self._save_sales()

        print("\nVenta realizada:")
        print(f"- Producto: {product.name}")
        print(f"- Peso: {weight:.2f} kg")
        print(f"- Total: $ {total:.2f}")
        print(f"- Merma actual del producto: {merma:.2f} kg\n")

    def ver_inventario(self):
        print("\nInventario actual:")
        self.inventory.list_products()
        print()

    def ver_metricas(self):
        print("\nMétricas:")
        ganancias = sum(s["total_price"] for s in self.sales)
        for product in self.inventory.products.values():
            sold = product.initial_weight - product.current_weight
            merma = product.initial_weight - sold
            print(
                f"- {product.name}: vendido {sold:.2f} kg, merma {merma:.2f} kg"
            )
        print(f"Ganancia total: $ {ganancias:.2f}\n")

    def menu(self):
        options = {
            "1": self.realizar_venta,
            "2": self.ver_inventario,
            "3": self.ver_metricas,
            "4": exit,
        }
        while True:
            print("Menú:")
            print("1. Realizar Venta")
            print("2. Ver Inventario")
            print("3. Ver Métricas")
            print("4. Salir")
            choice = input("Elige una opción (1-4): ").strip()
            action = options.get(choice)
            if action:
                action()
            else:
                print("Opción inválida. Intenta de nuevo.\n")


if __name__ == "__main__":
    POS().menu()
