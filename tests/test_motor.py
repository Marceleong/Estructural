"""
Pruebas del motor estructural.

La prueba de aceptación es el ejemplo trabajado del documento: la placa de
fundación PA-1, quince pasos, de la lámina al presupuesto. El hallazgo
central que hay que reproducir es el paso 9: el desperdicio real de acero
es 10.7%, no el 5% de rutina.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import (
    CatalogoAcero, placa_aislada, barras_por_sentido,
    longitud_gancho, longitud_barra_recta, longitud_aro,
    empalmes, despiece_acero, alambre_de_amarre,
    resolver_dato, Trazabilidad,
    RESUELTO, CONFLICTO, SIN_EVIDENCIA,
)

BASE = Path(__file__).resolve().parent.parent
TOL = 0.01


def cat():
    return CatalogoAcero.desde_carpeta(BASE)


# ======================================================================
# El catálogo — constantes físicas del documento
# ======================================================================

def test_peso_lineal_del_acero():
    """Constantes físicas de la tabla de conversión (densidad 7850)."""
    c = cat()
    assert abs(c.peso_lineal("4") - 0.994) < 0.001
    assert abs(c.peso_lineal("5") - 1.554) < 0.001
    assert abs(c.buscar("8")["peso_varilla_6m_kg"] - 23.87) < 0.01


# ======================================================================
# PRUEBA DE ACEPTACION — placa PA-1, los 15 pasos
# ======================================================================

def placa():
    return placa_aislada(
        "PA-1", 1.20, 1.20, 0.30, "4", 0.15, 0.075, cat(),
        tipo_gancho="ESTANDAR_90", fc=210,
        desperdicio_concreto=0.03)


def test_paso1_volumen():
    r = placa()["resumen"]
    assert abs(r["volumen_concreto_m3"] - 0.432) < TOL


def test_paso2_formaleta_solo_el_perimetro():
    r = placa()["resumen"]
    assert abs(r["area_formaleta_m2"] - 1.44) < TOL


def test_paso3_barras_con_el_mas_uno():
    """El '+1' es el error clásico que el documento marca."""
    n, libre = barras_por_sentido(1.20, 0.075, 0.15)
    assert n == 8
    assert abs(libre - 1.05) < TOL


def test_paso4_longitud_barra_con_ganchos():
    """1.05 + 2 × (12·db en #4) = 1.05 + 0.305 = 1.355 m."""
    r = longitud_barra_recta(1.05, "4", cat(),
                             gancho_inicio="ESTANDAR_90",
                             gancho_fin="ESTANDAR_90")
    assert abs(r["longitud_m"] - 1.355) < 0.001


def test_paso4_gancho_12db():
    g = longitud_gancho("4", "ESTANDAR_90", cat())
    assert abs(g - 12 * 0.0127) < 0.001


def test_paso5_longitud_total():
    r = placa()["resumen"]
    assert abs(r["longitud_total_acero_m"] - 21.68) < 0.05


def test_paso6_peso_neto():
    r = placa()["resumen"]
    assert abs(r["peso_neto_acero_kg"] - 21.55) < 0.1


def test_paso7_sin_empalmes():
    """1.355 m < 6.00 m: ninguna barra requiere traslape."""
    r = placa()["resumen"]
    assert r["empalmes"] == 0


def test_paso8_varillas():
    r = placa()["resumen"]
    assert r["varillas_a_comprar"] == 4


def test_paso9_desperdicio_real_es_10_7():
    """
    EL HALLAZGO CENTRAL. El desperdicio real es 10.7%, no el 5% de rutina.
    Solo se ve haciendo el despiece. Sobre 30 t, la diferencia son 1.7 t.
    """
    r = placa()["resumen"]
    assert abs(r["DESPERDICIO_REAL_pct"] - 10.7) < 0.2


def test_paso10_alambre():
    r = placa()["resumen"]
    assert abs(r["alambre_kg"] - 0.32) < 0.02


def test_paso11_concreto_con_desperdicio():
    r = placa()["resumen"]
    assert abs(r["concreto_con_desperdicio_m3"] - 0.445) < 0.001


def test_paso13_excavacion():
    r = placa()["resumen"]
    assert abs(r["excavacion_m3"] - 0.79) < 0.02


def test_paso14_sello_limpieza():
    r = placa()["resumen"]
    assert abs(r["sello_limpieza_m3"] - 0.113) < 0.002


def test_paso15_desalojo_con_esponjamiento():
    r = placa()["resumen"]
    assert abs(r["desalojo_m3_sueltos"] - 0.31) < 0.02


# ======================================================================
# E1 — Empalmes (consecuencia geométrica, no porcentaje)
# ======================================================================

def test_viga_corta_no_lleva_empalme():
    """Una viga de 5.80 m no lleva ningún empalme (ejemplo del documento)."""
    r = empalmes(5.80, "5", cat(), factor_k=50)
    assert r["empalmes"] == 0


def test_viga_larga_lleva_empalme():
    """Una de 6.20 m lleva uno; con 50·db en #5 son 0.79 m adicionales."""
    r = empalmes(6.20, "5", cat(), factor_k=50)
    assert r["empalmes"] == 1
    # 50 × 0.01588 = 0.794 m
    assert abs(r["longitud_traslape_m"] - 0.794) < 0.002


def test_empalme_es_iterativo():
    """
    Una corrida muy larga: los empalmes la alargan y pueden pedir otro.
    El cálculo tiene que converger, no quedarse corto.
    """
    r = empalmes(17.0, "6", cat(), factor_k=50)
    # 17 m en varillas de 6 -> al menos 2 empalmes; el traslape agrega ~1 m
    assert r["empalmes"] >= 2
    assert r["longitud_total_m"] > 17.0


# ======================================================================
# E2 — Ganchos y aros
# ======================================================================

def test_gancho_sismico_respeta_minimo():
    """6·db en #3 = 0.057 m, por debajo del mínimo de 7.5 cm: gana el mínimo."""
    g = longitud_gancho("3", "SISMICO_135", cat())
    assert abs(g - 0.075) < 0.001


def test_aro_desarrollo():
    """Perímetro + dos ganchos sísmicos."""
    r = longitud_aro(0.30, 0.30, 0.04, "3", cat())
    # P = 2×(0.30+0.30) − 8×0.04 = 1.20 − 0.32 = 0.88
    assert abs(r["perimetro_m"] - 0.88) < TOL


# ======================================================================
# E5 — Despiece con optimización de corte
# ======================================================================

def test_despiece_calcula_el_desperdicio():
    """16 cortes de 1.355 en varillas de 6: 4 caben por varilla, 4 varillas."""
    cortes = {"4": [1.355] * 16}
    r = despiece_acero(cortes, cat())
    assert r["4"]["varillas"] == 4
    assert abs(r["4"]["desperdicio_pct"] - 10.7) < 0.3


def test_optimizacion_mejora_el_corte_ingenuo():
    """
    Cortes que combinados llenan mejor la varilla. La optimización debe
    usar menos varillas que una por corte.
    """
    cortes = {"5": [2.0, 2.0, 2.0, 4.0, 4.0]}   # 14 m netos
    r = despiece_acero(cortes, cat())
    # first-fit: 4+2, 4+2, 2 -> 3 varillas (no 5)
    assert r["5"]["varillas"] == 3


def test_barra_mas_larga_que_la_varilla_se_parte():
    cortes = {"6": [8.5]}   # más de 6 m
    r = despiece_acero(cortes, cat())
    assert r["6"]["varillas"] == 2


def test_diametro_fuera_de_catalogo_abstiene():
    r = despiece_acero({"99": [1.0, 2.0]}, cat())
    assert r["99"]["estado"] == SIN_EVIDENCIA


# ======================================================================
# Precedencia con trazabilidad
# ======================================================================

def test_gana_la_fuente_de_mayor_precedencia():
    r = resolver_dato("factor_k", [
        {"fuente": "NOTA_GENERAL", "valor": 50},
        {"fuente": "DETALLE", "valor": 60},
    ])
    assert r["valor"] == 60
    assert r["fuente_ganadora"] == "DETALLE"
    assert r["hubo_desacuerdo"]


def test_fuentes_que_coinciden_no_son_conflicto():
    r = resolver_dato("fc", [
        {"fuente": "NOTA_GENERAL", "valor": 210},
        {"fuente": "CUADRO", "valor": 210},
    ])
    assert r["estado"] == RESUELTO
    assert not r["hubo_desacuerdo"]


def test_especificacion_escrita_gana_a_todo():
    """En estructural, la especificación escrita manda casi siempre."""
    r = resolver_dato("recubrimiento", [
        {"fuente": "PLANTA", "valor": 0.05},
        {"fuente": "CUADRO", "valor": 0.075},
        {"fuente": "ESPECIFICACION_ESCRITA", "valor": 0.04},
    ])
    assert r["valor"] == 0.04
    assert len(r["fuentes_descartadas"]) == 2


def test_trazabilidad_guarda_los_conflictos():
    t = Trazabilidad("PA-1")
    t.resolver("factor_k", [
        {"fuente": "NOTA_GENERAL", "valor": 50},
        {"fuente": "DETALLE", "valor": 60}])
    t.resolver("fc", [{"fuente": "CUADRO", "valor": 210}])

    rep = t.reporte()
    assert "factor_k" in rep["conflictos"]
    assert "fc" not in rep["conflictos"]
    assert not rep["todos_resueltos"]


def test_sin_fuentes_abstiene():
    r = resolver_dato("algo", [])
    assert r["estado"] == SIN_EVIDENCIA
