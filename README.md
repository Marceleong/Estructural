# Módulo Estructural — Guía

Cuantifica elementos estructurales siguiendo el documento "Casos
estructurales típicos FCV", y está validado contra su ejemplo trabajado:
la placa de fundación PA-1, quince pasos, de la lámina al presupuesto.

El argumento más fuerte de la disciplina, y lo que este motor demuestra:
**el desperdicio de acero no es un supuesto, es el resultado de un problema
de corte.** La placa PA-1 da 10.7% real, no el 5% de rutina. Sobre 30
toneladas, esa diferencia son 1.7 toneladas que alguien paga sin verlas.

---

## Instalar

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

El motor no usa ninguna librería externa: solo Python de fábrica. `pytest`
es lo único que se instala, y es para correr las pruebas.

---

## Correr las pruebas

```
python3 -m pytest tests/ -q
```

Debe decir `30 passed`. Incluye los 15 pasos del ejemplo trabajado.

---

## El ejemplo trabajado

```
python3 placa.py
```

Reproduce la placa PA-1. El resultado que importa está en el paso del
desperdicio:

```
  10. DESPERDICIO_REAL_pct    10.7  ◄── EL HALLAZGO
      (23.86 − 21.55) / 21.55
```

Y el plan de corte que lo produce:

```
  PLAN DE CORTE (varillas de 6 m)
    Varilla 1: 1.355 + 1.355 + 1.355 + 1.355   sobra 0.58 m
    ...
```

---

## Las cinco reglas transversales

En estructural, como en arquitectónico, las reglas de medición pesan más
que cualquier elemento individual:

| Ficha | Qué resuelve | Dónde |
|---|---|---|
| E1 | Empalmes: consecuencia geométrica, iterativa, no un porcentaje | `motor/acero.py` |
| E2 | Aros y ganchos: desarrollo con dobleces | `motor/acero.py` |
| E5 | Despiece de acero con optimización de corte (bin packing) | `motor/acero.py` |
| — | Precedencia con trazabilidad de qué fuente ganó | `motor/precedencia.py` |
| A2+ | Especialización por elemento (placa, y molde para los demás) | `motor/elementos.py` |

---

## Constantes físicas contra parámetros de práctica

El documento separa dos clases de valores, y el motor las respeta:

- **Constantes físicas** (peso del acero por diámetro, densidad 7850): van
  en `datos/acero.csv`, son fijas, no se tocan. Salen calculadas del
  documento.

- **Parámetros de práctica** (desperdicios, dosificaciones, factor de
  alambre): van en `motor/config.py`, FCV los valida, nunca quemados en la
  lógica.

Y una tercera categoría que el documento subraya: el **factor k de
traslape** (40, 50, 60·db) viene **DEL PLANO**, no del catálogo ni de la
config. No hay valor por defecto a propósito: asumirlo es el error que el
documento prohíbe.

---

## Lo que hace a propósito

**Calcula el desperdicio, no lo asume.** Del despiece real optimizado. Es
el punto más fuerte que un motor ofrece sobre una hoja de cálculo: un
problema de corte que la máquina resuelve en segundos y la persona no
resuelve nunca.

**El empalme es geométrico, no un porcentaje.** Una viga de 5.80 m no
lleva empalme; una de 6.20 lleva uno. El motor lo determina de la longitud
contra la varilla comercial, y de forma iterativa: el empalme alarga la
corrida, que puede pedir otro.

**Guarda de dónde salió cada dato.** Cuando dos fuentes se contradicen,
gana la de mayor precedencia y se registra cuál ganó y contra qué. Nunca
se promedia: un refuerzo promediado no existe en ningún plano. Es lo que
permite auditar el presupuesto, no solo el número final.

**Puede decir "no sé".** Un diámetro fuera del catálogo, una fuente
desconocida, un gancho no especificado: se reportan, no se inventan.

**Respeta el "+1" de las barras.** El error clásico del paso 3: se cuentan
los espacios entre barras, pero las barras son uno más.

---

## Estructura

```
estructural/
├── README.md
├── requirements.txt
├── placa.py                  ← el ejemplo trabajado, placa PA-1
├── motor/
│   ├── config.py             ← parámetros de práctica (edita aquí)
│   ├── catalogo.py           ← constantes físicas del acero
│   ├── acero.py              ← fichas E1, E2, E5
│   ├── elementos.py          ← especialización por elemento (placa)
│   └── precedencia.py        ← trazabilidad de qué fuente ganó
├── datos/
│   └── acero.csv             ← tabla de conversión del acero (del documento)
└── tests/
    └── test_motor.py         ← los 15 pasos + empalmes, despiece, precedencia
```

---

## Conectarse con el pipeline

El motor recibe **los datos del cuadro del elemento** —dimensiones,
refuerzo, separación, recubrimiento— ya leídos, y produce el presupuesto.
La lectura del plano (el cuadro de placas, el cuadro de columnas, la
etiqueta PA-1) la hace el pipeline del compañero.

Según el documento de brecha, estructural es la disciplina que "todavía no
identifica": sus elementos se nombran con etiquetas (P-1, V-1, C-1), y ese
es el trabajo que la desbloquea. Ese paso —leer la etiqueta— es del
pipeline. Este motor es lo que va después: una vez que se sabe que hay una
placa PA-1 con tales datos, la cuantifica entera.

Dos exigencias del contrato: las dimensiones llegan **en metros**, y si un
dato del cuadro no se leyó, llega **ausente** — el motor entonces se
abstiene en vez de suponer.

---

## Las decisiones que le tocan a FCV

Listadas en `motor/config.py` con su valor propuesto:

| Qué | Por qué importa |
|---|---|
| Desperdicios de concreto por tipo | Parámetro, no calculado |
| Factor de alambre de amarre | 1.0–1.5% del peso del acero |
| Dosificación (sacos de cemento por m³) | Cambia el costo del concreto en sitio |
| Longitud comercial de varilla | 6 m estándar; 9 y 12 por pedido |

Y una que no es de config sino de lectura: **el factor k de traslape
siempre viene del plano**. El motor lo exige, no lo asume.
```
