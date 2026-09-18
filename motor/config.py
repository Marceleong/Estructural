"""
Parámetros de práctica — FCV los valida, nunca van quemados en la lógica.

El documento es explícito: constantes físicas fijas (en el catálogo),
parámetros de práctica configurables (aquí). Los marcados VALIDAR CON FCV
son los que el documento deja pendientes.
"""

# ----------------------------------------------------------------------
# E1 — Empalmes
# ----------------------------------------------------------------------

# Longitud comercial de la varilla, en metros. 6 m estándar; 9 y 12 por
# pedido en diámetros mayores. Se confirma con el proveedor.
LONGITUD_COMERCIAL_M = 6.0

# El factor k de traslape (40, 50, 60) viene DEL PLANO. No hay valor por
# defecto a propósito: asumirlo es el error que el documento prohíbe.


# ----------------------------------------------------------------------
# E2 — Ganchos (valores normativos, no de práctica)
# ----------------------------------------------------------------------

# Extensión de gancho por tipo, como múltiplo del diámetro.
GANCHO_EXTENSION_DB = {
    "SISMICO_135": 6,     # 6·db, mínimo 7.5 cm
    "ESTANDAR_90": 12,    # 12·db
    "GANCHO_180": 4,      # 4·db, mínimo 6.5 cm
}
GANCHO_MINIMO_M = {
    "SISMICO_135": 0.075,
    "ESTANDAR_90": 0.0,
    "GANCHO_180": 0.065,
}


# ----------------------------------------------------------------------
# E5 — Desperdicio (los "calculado" salen del despiece, no de aquí)
# ----------------------------------------------------------------------

# Factor de alambre de amarre como fracción del peso del acero.
FACTOR_ALAMBRE = 0.015          # 1.0-1.5%, VALIDAR CON FCV

# Desperdicios de concreto (parámetros, no calculados).
DESPERDICIO_CONCRETO = {
    "PREMEZCLADO": 0.025,       # 2-3%
    "EN_SITIO": 0.04,           # 3-5%
    "LIMPIEZA": 0.065,          # 5-8%, contra terreno
    "GROUT": 0.065,             # 5-8%
}


# ----------------------------------------------------------------------
# E4 — Concreto hecho en sitio
# ----------------------------------------------------------------------

# Sacos de cemento por m³ según resistencia. VALIDAR la dosificación FCV.
SACOS_CEMENTO_POR_M3 = {
    140: 7.0,
    210: 9.0,
    280: 10.5,
}


# ----------------------------------------------------------------------
# Excavación
# ----------------------------------------------------------------------

SOBREEXCAVACION_POR_LADO_M = 0.15
ESPONJAMIENTO = 0.25            # 25% sobre el volumen en banco


RUTA_CATALOGO_ACERO = "datos/acero.csv"
