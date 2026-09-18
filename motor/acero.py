"""
Fichas E1, E2 y E5 — Acero de refuerzo.

El corazón de la disciplina y el argumento más fuerte del documento: el
desperdicio de acero NO es un supuesto, es el resultado de un problema de
optimización de corte que la máquina resuelve y la persona no.

En el ejemplo trabajado, la placa PA-1 da 10.7% de desperdicio real, no
el 5% de rutina. Sobre 30 toneladas eso son 1.7 toneladas que alguien
paga sin verlas.

Tres reglas que se combinan:
  E1 — empalmes: consecuencia geométrica de la longitud contra la varilla
       comercial, no un porcentaje. Y es iterativo: el empalme alarga la
       corrida, que puede pedir otro empalme.
  E2 — ganchos: el desarrollo del aro y de la barra con sus dobleces.
  E5 — despiece: bin packing de los cortes en varillas de 6 m, con el
       desperdicio calculado del resultado.
"""

import math
from collections import defaultdict

from . import config

RESUELTO = "RESUELTO"
CONFLICTO = "CONFLICTO"
SIN_EVIDENCIA = "SIN_EVIDENCIA"


# ----------------------------------------------------------------------
# E2 — Ganchos y desarrollo de barra
# ----------------------------------------------------------------------

def longitud_gancho(designacion, tipo_gancho, catalogo):
    """
    Extensión del gancho, como múltiplo del diámetro con su mínimo.

    Ejemplo trabajado paso 4: gancho de 12·db en #4 = 12 × 0.0127 = 0.1524 m
    por extremo.
    """
    db = catalogo.diametro_m(designacion)
    if db is None:
        return None
    factor = config.GANCHO_EXTENSION_DB.get(tipo_gancho)
    if factor is None:
        return None
    minimo = config.GANCHO_MINIMO_M.get(tipo_gancho, 0.0)
    return max(factor * db, minimo)


def longitud_barra_recta(longitud_libre_m, designacion, catalogo,
                         gancho_inicio=None, gancho_fin=None):
    """
    Longitud desarrollada de una barra recta con ganchos en sus extremos.

    Ejemplo paso 4: 1.05 + 2 × (12·db) = 1.05 + 0.305 = 1.355 m.
    """
    total = float(longitud_libre_m)
    detalle = [f"tramo libre {longitud_libre_m:.4f} m"]

    for extremo, tipo in (("inicio", gancho_inicio), ("fin", gancho_fin)):
        if tipo:
            lg = longitud_gancho(designacion, tipo, catalogo)
            if lg is None:
                return {"estado": SIN_EVIDENCIA,
                        "razon": f"gancho '{tipo}' o barra #{designacion} "
                                 f"desconocido"}
            total += lg
            detalle.append(f"gancho {extremo} {lg:.4f} m")

    return {
        "estado": RESUELTO,
        "longitud_m": round(total, 4),
        "detalle": detalle,
    }


def perimetro_aro(b_m, h_m, recubrimiento_m):
    """P = 2·(b + h) − 8·r. La sección menos el recubrimiento en 4 lados."""
    return 2 * (b_m + h_m) - 8 * recubrimiento_m


def longitud_aro(b_m, h_m, recubrimiento_m, designacion, catalogo,
                 tipo_gancho="SISMICO_135"):
    """
    Desarrollo del aro: perímetro + dos ganchos.

    L_aro = P + 2 × L_gancho
    """
    p = perimetro_aro(b_m, h_m, recubrimiento_m)
    lg = longitud_gancho(designacion, tipo_gancho, catalogo)
    if lg is None:
        return {"estado": SIN_EVIDENCIA, "razon": "gancho o barra desconocido"}
    return {
        "estado": RESUELTO,
        "perimetro_m": round(p, 4),
        "longitud_desarrollada_m": round(p + 2 * lg, 4),
        "razon": f"perímetro {p:.4f} + 2 ganchos de {lg:.4f} m",
    }


# ----------------------------------------------------------------------
# E1 — Empalmes
# ----------------------------------------------------------------------

def empalmes(longitud_requerida_m, designacion, catalogo, factor_k,
             longitud_comercial_m=None):
    """
    Empalmes de una corrida, calculados iterativamente (ficha E1).

    El empalme alarga la corrida, lo que puede exigir otro empalme. Se
    itera hasta converger.

    factor_k viene DEL PLANO (40, 50, 60). No hay valor por defecto: el
    documento prohíbe asumirlo.
    """
    if longitud_comercial_m is None:
        longitud_comercial_m = config.LONGITUD_COMERCIAL_M

    db = catalogo.diametro_m(designacion)
    if db is None:
        return {"estado": SIN_EVIDENCIA,
                "razon": f"barra #{designacion} no está en el catálogo"}

    l_traslape = factor_k * db
    L = float(longitud_requerida_m)

    # Iteración: recalcular n con la longitud ya aumentada hasta converger.
    n_emp = 0
    for _ in range(20):
        nuevo = max(0, math.ceil(L / longitud_comercial_m) - 1)
        l_total = float(longitud_requerida_m) + nuevo * l_traslape
        if nuevo == n_emp:
            break
        n_emp = nuevo
        L = l_total

    l_total = float(longitud_requerida_m) + n_emp * l_traslape

    return {
        "estado": RESUELTO,
        "empalmes": n_emp,
        "longitud_traslape_m": round(l_traslape, 4),
        "longitud_total_m": round(l_total, 4),
        "razon": (f"{longitud_requerida_m:.2f} m contra varilla de "
                  f"{longitud_comercial_m} m -> {n_emp} empalme(s)"
                  + (f", +{n_emp * l_traslape:.3f} m de traslape"
                     if n_emp else " (ninguno)")),
    }


# ----------------------------------------------------------------------
# E5 — Despiece con optimización de corte (bin packing)
# ----------------------------------------------------------------------

def _first_fit_decreasing(cortes, largo_varilla):
    """
    Acomoda los cortes en varillas de largo fijo (first-fit-decreasing).

    Es el greedy que el documento menciona: "un algoritmo greedy ya mejora
    sustancialmente el corte manual". Auditable: se puede leer el plan.
    """
    piezas = sorted(cortes, reverse=True)
    varillas = []   # cada una: lista de cortes que lleva
    restantes = []  # el sobrante de cada varilla

    for pieza in piezas:
        if pieza > largo_varilla + 1e-9:
            # una pieza más larga que la varilla necesita empalme; se parte
            entero = int(pieza // largo_varilla)
            for _ in range(entero):
                varillas.append([largo_varilla])
                restantes.append(0.0)
            resto = pieza - entero * largo_varilla
            if resto > 1e-9:
                varillas.append([resto])
                restantes.append(largo_varilla - resto)
            continue

        colocada = False
        for i in range(len(varillas)):
            if restantes[i] >= pieza - 1e-9:
                varillas[i].append(pieza)
                restantes[i] -= pieza
                colocada = True
                break
        if not colocada:
            varillas.append([pieza])
            restantes.append(largo_varilla - pieza)

    return varillas, restantes


def despiece_acero(cortes_por_diametro, catalogo, longitud_comercial_m=None):
    """
    Despiece completo por diámetro, con el desperdicio calculado.

    cortes_por_diametro: {"4": [1.355, 1.355, ...], "5": [...]}
                         cada lista son las longitudes de corte requeridas.

    Reproduce los pasos 8 y 9 del ejemplo: la optimización y el 10.7%.
    """
    if longitud_comercial_m is None:
        longitud_comercial_m = config.LONGITUD_COMERCIAL_M

    resultado = {}

    for designacion, cortes in cortes_por_diametro.items():
        datos = catalogo.buscar(designacion)
        if datos is None:
            resultado[designacion] = {
                "estado": SIN_EVIDENCIA,
                "razon": f"barra #{designacion} no está en el catálogo",
            }
            continue

        peso_lineal = datos["peso_kg_m"]
        largo_neto = sum(cortes)
        peso_neto = largo_neto * peso_lineal

        varillas, restantes = _first_fit_decreasing(cortes, longitud_comercial_m)
        n_varillas = len(varillas)
        largo_comprado = n_varillas * longitud_comercial_m
        peso_comprado = largo_comprado * peso_lineal

        desperdicio = ((peso_comprado - peso_neto) / peso_neto
                       if peso_neto > 0 else 0.0)

        resultado[designacion] = {
            "estado": RESUELTO,
            "cortes": len(cortes),
            "largo_neto_m": round(largo_neto, 3),
            "peso_neto_kg": round(peso_neto, 2),
            "varillas": n_varillas,
            "largo_comercial_m": longitud_comercial_m,
            "peso_comprado_kg": round(peso_comprado, 2),
            "desperdicio_pct": round(desperdicio * 100, 1),
            "sobrante_total_m": round(
                sum(restantes), 3),
            "plan_de_corte": [
                {"varilla": i + 1,
                 "cortes": [round(c, 3) for c in v],
                 "sobra_m": round(restantes[i], 3)}
                for i, v in enumerate(varillas)
            ],
        }

    return resultado


def alambre_de_amarre(peso_acero_kg, factor=None):
    """Alambre negro #16 como fracción del peso del acero. Ejemplo paso 10."""
    if factor is None:
        factor = config.FACTOR_ALAMBRE
    return {
        "estado": RESUELTO,
        "kg": round(peso_acero_kg * factor, 3),
        "razon": f"{peso_acero_kg:.2f} kg × {factor:.1%}",
    }
