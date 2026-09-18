"""
Especialización por elemento — empezando por la placa aislada (ficha A2).

El ejemplo trabajado del documento es una placa PA-1, quince pasos, de la
lámina al presupuesto. Este módulo lo reproduce entero y sirve de molde
para los demás elementos: cada uno combina las reglas transversales
(acero, concreto, formaleta) con su geometría propia.

La placa es el mejor primer elemento porque toca casi todo: volumen de
concreto, área de formaleta parcial (solo el perímetro), despiece de acero
con ganchos, empalmes, excavación y desalojo.
"""

import math

from . import config
from .acero import (
    longitud_barra_recta, empalmes, despiece_acero, alambre_de_amarre,
    RESUELTO, CONFLICTO, SIN_EVIDENCIA,
)


def barras_por_sentido(dimension_m, recubrimiento_m, separacion_m):
    """
    n = piso[(dim − 2·recubrimiento) / separación] + 1

    El "+1" es el error clásico que el documento marca en el paso 3: se
    cuentan los espacios, pero las barras son un más.
    """
    libre = dimension_m - 2 * recubrimiento_m
    return math.floor(libre / separacion_m) + 1, libre


def placa_aislada(marca, ancho_m, largo_m, espesor_m,
                  designacion, separacion_m, recubrimiento_m,
                  catalogo, tipo_gancho="ESTANDAR_90", factor_k=None,
                  fc=210, cantidad=1,
                  desperdicio_concreto=None):
    """
    Cuantifica una placa aislada completa — los 15 pasos del ejemplo.

    Reproduce la placa PA-1: 1.20×1.20×0.30, #4 @ 15 cm ambos sentidos,
    gancho 90° de 12·db, recubrimiento 7.5 cm, f'c 210.
    """
    datos = catalogo.buscar(designacion)
    if datos is None:
        return {"estado": SIN_EVIDENCIA,
                "razon": f"barra #{designacion} no está en el catálogo"}

    pasos = []

    # Paso 1 — volumen de concreto
    volumen = ancho_m * largo_m * espesor_m
    pasos.append(("volumen_concreto_m3", round(volumen, 4),
                  f"{ancho_m} × {largo_m} × {espesor_m}"))

    # Paso 2 — área de formaleta (solo el perímetro; el fondo apoya)
    area_formaleta = 2 * (ancho_m + largo_m) * espesor_m
    pasos.append(("area_formaleta_m2", round(area_formaleta, 4),
                  f"2 × ({ancho_m} + {largo_m}) × {espesor_m}"))

    # Paso 3 — barras por sentido (con el +1)
    n_ancho, libre_ancho = barras_por_sentido(ancho_m, recubrimiento_m, separacion_m)
    n_largo, libre_largo = barras_por_sentido(largo_m, recubrimiento_m, separacion_m)
    pasos.append(("barras_sentido_ancho", n_ancho,
                  f"piso({libre_ancho:.3f}/{separacion_m}) + 1"))
    pasos.append(("barras_sentido_largo", n_largo,
                  f"piso({libre_largo:.3f}/{separacion_m}) + 1"))

    # Paso 4 — longitud de cada barra (tramo libre + ganchos)
    #   la barra cruza el ancho útil del sentido perpendicular
    barra_ancho = longitud_barra_recta(
        libre_largo, designacion, catalogo, tipo_gancho, tipo_gancho)
    barra_largo = longitud_barra_recta(
        libre_ancho, designacion, catalogo, tipo_gancho, tipo_gancho)
    if barra_ancho["estado"] != RESUELTO:
        return barra_ancho
    pasos.append(("longitud_barra_m", barra_ancho["longitud_m"],
                  "; ".join(barra_ancho["detalle"])))

    # Paso 5 — longitud total de acero
    #   n_ancho barras que cruzan el largo + n_largo barras que cruzan el ancho
    long_total = (n_ancho * barra_ancho["longitud_m"]
                  + n_largo * barra_largo["longitud_m"])
    pasos.append(("longitud_total_acero_m", round(long_total, 3),
                  f"{n_ancho}×{barra_ancho['longitud_m']} + "
                  f"{n_largo}×{barra_largo['longitud_m']}"))

    # Paso 6 — peso neto
    peso_neto = long_total * datos["peso_kg_m"]
    pasos.append(("peso_neto_acero_kg", round(peso_neto, 2),
                  f"{long_total:.3f} m × {datos['peso_kg_m']} kg/m"))

    # Paso 7 — empalmes (sólo si k viene del plano)
    if factor_k is not None:
        emp = empalmes(barra_ancho["longitud_m"], designacion, catalogo, factor_k)
        pasos.append(("empalmes", emp["empalmes"], emp["razon"]))
    else:
        pasos.append(("empalmes", 0,
                      f"cada barra mide {barra_ancho['longitud_m']:.3f} m < "
                      f"{config.LONGITUD_COMERCIAL_M} m; ninguno"))

    # Pasos 8 y 9 — despiece y desperdicio real
    todos_los_cortes = ([barra_ancho["longitud_m"]] * n_ancho
                        + [barra_largo["longitud_m"]] * n_largo)
    desp = despiece_acero({designacion: todos_los_cortes}, catalogo)
    d = desp[designacion]
    pasos.append(("varillas_a_comprar", d["varillas"],
                  f"optimización de {len(todos_los_cortes)} cortes en "
                  f"varillas de {d['largo_comercial_m']} m"))
    pasos.append(("DESPERDICIO_REAL_pct", d["desperdicio_pct"],
                  f"({d['peso_comprado_kg']} − {d['peso_neto_kg']}) / "
                  f"{d['peso_neto_kg']}"))

    # Paso 10 — alambre
    alambre = alambre_de_amarre(peso_neto)
    pasos.append(("alambre_kg", alambre["kg"], alambre["razon"]))

    # Paso 11 — concreto con desperdicio
    if desperdicio_concreto is None:
        desperdicio_concreto = config.DESPERDICIO_CONCRETO["EN_SITIO"]
    vol_con_desp = volumen * (1 + desperdicio_concreto)
    pasos.append(("concreto_con_desperdicio_m3", round(vol_con_desp, 4),
                  f"{volumen:.4f} × {1+desperdicio_concreto:.2f}"))

    # Paso 12 — cemento en sitio
    sacos_m3 = config.SACOS_CEMENTO_POR_M3.get(fc)
    if sacos_m3:
        sacos_crudo = vol_con_desp * sacos_m3
        sacos = math.ceil(sacos_crudo)
        pasos.append(("cemento_sacos", sacos,
                      f"{vol_con_desp:.4f} × {sacos_m3} sacos/m³ = "
                      f"{sacos_crudo:.2f}, se compra {sacos}"))

    # Paso 13 — excavación
    sob = config.SOBREEXCAVACION_POR_LADO_M
    exc = (ancho_m + 2 * sob) * (largo_m + 2 * sob) * (espesor_m + 0.05)
    pasos.append(("excavacion_m3", round(exc, 3),
                  f"con {sob} m de sobreexcavación por lado"))

    # Paso 14 — sello de limpieza
    sello = (ancho_m + 2 * sob) * (largo_m + 2 * sob) * 0.05
    pasos.append(("sello_limpieza_m3", round(sello, 4),
                  "concreto pobre f'c 140, 5 cm"))

    # Paso 15 — desalojo con esponjamiento
    desalojo = (exc - volumen - sello) * (1 + config.ESPONJAMIENTO)
    pasos.append(("desalojo_m3_sueltos", round(desalojo, 3),
                  f"con {config.ESPONJAMIENTO:.0%} de esponjamiento"))

    # Empaquetar
    valores = {clave: valor for clave, valor, _ in pasos}
    valores = {k: (v * cantidad if k not in
                   ("DESPERDICIO_REAL_pct", "longitud_barra_m") else v)
               for k, v in valores.items()}

    return {
        "estado": RESUELTO,
        "marca": marca,
        "cantidad": cantidad,
        "resumen": valores,
        "pasos": [{"paso": i + 1, "concepto": c, "valor": v, "calculo": calc}
                  for i, (c, v, calc) in enumerate(pasos)],
        "plan_de_corte": d["plan_de_corte"],
        "nota": (f"Desperdicio real de acero {d['desperdicio_pct']}%, no el "
                 f"5% de rutina. Solo se ve haciendo el despiece."),
    }
