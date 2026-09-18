"""
Catálogo del acero de refuerzo.

CONSTANTES FÍSICAS: peso del acero por diámetro, densidad 7850 kg/m³.
Fijas, del documento, van en el CSV y no se tocan.

El factor k de traslape y la longitud comercial vienen DEL PLANO, no del
catálogo: el documento insiste en "nunca asumir".
"""

import csv
from pathlib import Path


class CatalogoAcero:
    def __init__(self, ruta):
        self.barras = {}
        with open(ruta, newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                d = fila["designacion"].strip().lstrip("#")
                self.barras[d] = {
                    "diametro_mm": float(fila["diametro_mm"]),
                    "diametro_m": float(fila["diametro_mm"]) / 1000.0,
                    "area_cm2": float(fila["area_cm2"]),
                    "peso_kg_m": float(fila["peso_kg_m"]),
                    "peso_varilla_6m_kg": float(fila["peso_varilla_6m_kg"]),
                }

    def buscar(self, designacion):
        return self.barras.get(str(designacion).strip().lstrip("#"))

    def peso_lineal(self, designacion):
        d = self.buscar(designacion)
        return d["peso_kg_m"] if d else None

    def diametro_m(self, designacion):
        d = self.buscar(designacion)
        return d["diametro_m"] if d else None

    @classmethod
    def desde_carpeta(cls, carpeta="."):
        return cls(Path(carpeta) / "datos" / "acero.csv")
