La expresividad mide qué ideas puede escribir un programador sin rodeos.
Un lenguaje expresivo dice mucho con poco código.

## El criterio en Residuum

<!-- covers: 1 -->
Residuum escribe reglas, eventos y experimentos. La @sec:s-uno presenta las
reglas.

```res {#lst:criterio caption="Un módulo mínimo" run=none}
module Criterio
```
::: explanation
El módulo no declara nada todavía.
:::

```prolog {#lst:contraste caption="Una cláusula de Prolog" run=none}
venta(X) :- pago(X).
```
::: explanation
Prolog escribe la conclusión a la izquierda de `:-`.
:::

## Detalle

<!-- covers: 1.1 -->
El primer detalle trata los tipos.

<!-- covers: 1.2 -->
El segundo detalle trata los tiempos.

Una lista resuelve las enumeraciones:

- uno, dos, tres, cuatro y cinco elementos caben en un punto, sin falta de lista;
- otro punto.

## Veredicto

Según este criterio, Residuum ofrece un desempeño medio: expresa reglas y
eventos, pero no funciones de orden superior.
