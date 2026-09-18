"""
Precedencia de especificaciones, con trazabilidad.

La fila propia de la tabla estructural: "trazabilidad de qué fuente ganó
cada dato". El documento la ordena así, de menor a mayor:

    notas generales < planta < cuadro del elemento < detalle específico
    < especificación técnica escrita

Cuando dos fuentes se contradicen, gana la de mayor precedencia, y se
GUARDA cuál ganó y contra qué. Nunca se promedia: un dato de refuerzo
promediado no existe en ningún plano.

Esto es lo que permite auditar un presupuesto: no solo el número final,
sino de dónde salió y qué otras fuentes decían otra cosa.
"""

from .acero import RESUELTO, CONFLICTO, SIN_EVIDENCIA


# Orden de precedencia, de menor a mayor (índice mayor = manda).
PRECEDENCIA = [
    "NOTA_GENERAL",
    "PLANTA",
    "CUADRO",
    "DETALLE",
    "ESPECIFICACION_ESCRITA",
]


def _rango(fuente):
    f = str(fuente).strip().upper()
    return PRECEDENCIA.index(f) if f in PRECEDENCIA else -1


def resolver_dato(nombre, candidatos):
    """
    Resuelve un dato entre varias fuentes que pueden discrepar.

    candidatos: [{"fuente", "valor"}], por ejemplo
        [{"fuente": "NOTA_GENERAL", "valor": 50},
         {"fuente": "DETALLE", "valor": 60}]

    Devuelve el valor que gana, la fuente, y el registro completo de qué
    decía cada una — la trazabilidad que el documento exige.
    """
    if not candidatos:
        return {"estado": SIN_EVIDENCIA, "dato": nombre,
                "razon": "ninguna fuente aporta este dato"}

    validos = [c for c in candidatos if _rango(c["fuente"]) >= 0]
    if not validos:
        return {"estado": SIN_EVIDENCIA, "dato": nombre,
                "razon": "ninguna fuente reconocida"}

    ganador = max(validos, key=lambda c: _rango(c["fuente"]))

    # ¿hubo desacuerdo real entre las fuentes?
    valores_distintos = {str(c["valor"]) for c in validos}
    hubo_conflicto = len(valores_distintos) > 1

    perdedores = [c for c in validos if c is not ganador]

    return {
        "estado": CONFLICTO if hubo_conflicto else RESUELTO,
        "dato": nombre,
        "valor": ganador["valor"],
        "fuente_ganadora": ganador["fuente"],
        "hubo_desacuerdo": hubo_conflicto,
        "fuentes_descartadas": [
            {"fuente": p["fuente"], "valor": p["valor"],
             "razon": f"menor precedencia que {ganador['fuente']}"}
            for p in perdedores
        ],
        "razon": (
            f"gana {ganador['fuente']} = {ganador['valor']}"
            + (f"; discrepaba con {[p['valor'] for p in perdedores]}"
               if hubo_conflicto else "; todas coinciden")
        ),
    }


class Trazabilidad:
    """
    Acumula la resolución de todos los datos de un elemento, para poder
    auditar de dónde salió cada uno.
    """

    def __init__(self, elemento):
        self.elemento = elemento
        self.datos = {}

    def resolver(self, nombre, candidatos):
        r = resolver_dato(nombre, candidatos)
        self.datos[nombre] = r
        return r.get("valor")

    def conflictos(self):
        """Los datos donde las fuentes discrepaban: lo que hay que revisar."""
        return {k: v for k, v in self.datos.items() if v.get("hubo_desacuerdo")}

    def reporte(self):
        return {
            "elemento": self.elemento,
            "datos": self.datos,
            "conflictos": list(self.conflictos()),
            "todos_resueltos": not self.conflictos(),
        }
