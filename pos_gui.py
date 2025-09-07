"""Interfaz gráfica (Tkinter) para el sistema de punto de venta de la carnicería.

Manual de uso:
    Ejecuta el programa con `python pos_gui.py`.
    Se abrirá una ventana con pestañas para Ventas, Inventario y Métricas.
    Requiere un entorno gráfico disponible.
"""

import json
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from scale import get_weight_or_none

from pos import Inventory


class POSApp:
    """Aplicación principal con interfaz gráfica."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("POS Carnicería")
        self.inventory = Inventory()
        self.sales_file = Path("sales.json")
        self.metrics_file = Path("metrics.json")
        self.sales: list[dict] = self._load_json(self.sales_file, [])
        self.merma_log: dict[str, list[float]] = self._load_json(self.metrics_file, {})

        self._create_widgets()

    # ---------------------------
    # Persistencia de datos
    # ---------------------------
    def _load_json(self, path: Path, default):
        if path.exists():
            return json.loads(path.read_text())
        return default

    def _save_sales(self):
        self.sales_file.write_text(json.dumps(self.sales, indent=4))

    def _save_metrics(self):
        self.metrics_file.write_text(json.dumps(self.merma_log, indent=4))

    # ---------------------------
    # Interfaz gráfica
    # ---------------------------
    def _create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.sales_frame = ttk.Frame(notebook)
        self.inventory_frame = ttk.Frame(notebook)
        self.metrics_frame = ttk.Frame(notebook)

        notebook.add(self.sales_frame, text="Ventas")
        notebook.add(self.inventory_frame, text="Inventario")
        notebook.add(self.metrics_frame, text="Métricas")

        # --- Pestaña de Ventas ---
        ttk.Label(self.sales_frame, text="Producto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.product_var = tk.StringVar()
        product_names = list(self.inventory.products.keys())
        self.product_cb = ttk.Combobox(
            self.sales_frame,
            textvariable=self.product_var,
            values=product_names,
            state="readonly",
        )
        self.product_cb.grid(row=0, column=1, padx=5, pady=5)
        if product_names:
            self.product_cb.current(0)

        ttk.Label(self.sales_frame, text="Peso (kg):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.weight_var = tk.StringVar()
        ttk.Entry(self.sales_frame, textvariable=self.weight_var).grid(
            row=1, column=1, padx=5, pady=5
        )
        ttk.Button(
            self.sales_frame, text="Leer balanza", command=self.leer_balanza
        ).grid(row=1, column=2, padx=5, pady=5)

        ttk.Button(
            self.sales_frame, text="Realizar venta", command=self.realizar_venta
        ).grid(row=2, column=0, columnspan=2, pady=10)
        self.sales_result = ttk.Label(self.sales_frame, text="")
        self.sales_result.grid(row=3, column=0, columnspan=2)

        # --- Pestaña de Inventario ---
        self.inventory_tree = ttk.Treeview(
            self.inventory_frame, columns=("precio", "disponible"), show="headings"
        )
        self.inventory_tree.heading("precio", text="Precio/kg")
        self.inventory_tree.heading("disponible", text="Disponible (kg)")
        self.inventory_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self._refresh_inventory()

        # --- Pestaña de Métricas ---
        self.metrics_text = tk.Text(self.metrics_frame, height=15, width=40, state="disabled")
        self.metrics_text.pack(fill="both", expand=True, padx=5, pady=5)
        self._refresh_metrics()

    # ---------------------------
    # Funcionalidad principal
    # ---------------------------
    def realizar_venta(self):
        product_name = self.product_var.get()
        weight_str = self.weight_var.get()
        try:
            weight = float(weight_str)
        except ValueError:
            messagebox.showerror("Error", "Peso inválido.")
            return

        product = self.inventory.products.get(product_name)
        if not product:
            messagebox.showerror("Error", "Producto inexistente.")
            return
        if weight <= 0 or weight > product.current_weight:
            messagebox.showerror("Error", "Peso fuera de rango.")
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

        self.sales_result.config(
            text=f"Venta: {product.name}, {weight:.2f} kg, $ {total:.2f}"
        )
        self.weight_var.set("")
        self._refresh_inventory()
        self._refresh_metrics()

    def leer_balanza(self):
        """Obtiene el peso desde la balanza y lo coloca en el campo."""
        weight = get_weight_or_none()
        if weight is None:
            messagebox.showwarning(
                "Balanza", "No se pudo leer la balanza. Ingresa el peso manualmente."
            )
        else:
            self.weight_var.set(f"{weight:.3f}")

    def _refresh_inventory(self):
        self.inventory_tree.delete(*self.inventory_tree.get_children())
        for product in self.inventory.products.values():
            self.inventory_tree.insert(
                "", "end", values=(f"$ {product.price_per_kg:.2f}", f"{product.current_weight:.2f}")
            )
        self.product_cb["values"] = list(self.inventory.products.keys())
        if self.inventory.products:
            self.product_cb.current(0)

    def _refresh_metrics(self):
        self.metrics_text.config(state="normal")
        self.metrics_text.delete("1.0", tk.END)
        ganancias = sum(s["total_price"] for s in self.sales)
        for product in self.inventory.products.values():
            sold = product.initial_weight - product.current_weight
            merma = product.initial_weight - sold
            self.metrics_text.insert(
                tk.END,
                f"{product.name}: vendido {sold:.2f} kg, merma {merma:.2f} kg\n",
            )
        self.metrics_text.insert(tk.END, f"Ganancia total: $ {ganancias:.2f}\n")
        self.metrics_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()