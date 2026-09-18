#!/usr/bin/env python3
"""
Cuantifica una placa de fundación, de la lámina al presupuesto.

Uso:
    python3 placa.py          # corre el ejemplo trabajado: placa PA-1

Reproduce los 15 pasos del documento de casos estructurales. El resultado
que importa está en el paso 9: el desperdicio real de acero.
"""

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from motor import CatalogoAcero, placa_aislada, RESUELTO


def main():
    cat = CatalogoAcero.desde_carpeta(BASE)
    r = placa_aislada("PA-1", 1.20, 1.20, 0.30, "4", 0.15, 0.075, cat,
                      tipo_gancho="ESTANDAR_90", fc=210,
                      desperdicio_concreto=0.03)

    if r["estado"] != RESUELTO:
        print(f"\n  [{r['estado']}] {r['razon']}\n")
        return

    print()
    print("=" * 70)
    print(f"  Placa de fundación {r['marca']} — 1.20 × 1.20 × 0.30 m")
    print("=" * 70)
    print(f"  #4 @ 15 cm ambos sentidos · gancho 90° · f'c 210 · recub. 7.5 cm")
    print()

    for p in r["pasos"]:
        destacar = "  ◄── EL HALLAZGO" if "DESPERDICIO" in p["concepto"] else ""
        print(f"  {p['paso']:>2}. {p['concepto']:<28} {str(p['valor']):>10}"
              f"{destacar}")
        print(f"      {p['calculo']}")

    print()
    print(f"  PLAN DE CORTE (varillas de 6 m)")
    for v in r["plan_de_corte"]:
        cortes = " + ".join(f"{c}" for c in v["cortes"])
        print(f"    Varilla {v['varilla']}: {cortes}   sobra {v['sobra_m']} m")

    print()
    print(f"  {r['nota']}")
    print()
    print("  El desperdicio de acero no es un supuesto: es el resultado de un")
    print("  problema de corte que la máquina resuelve y la persona no. Sobre")
    print("  30 toneladas, la diferencia entre 10.7% y 5% son 1.7 toneladas.")
    print()


if __name__ == "__main__":
    main()
