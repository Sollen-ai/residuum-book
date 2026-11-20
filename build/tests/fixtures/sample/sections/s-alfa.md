Esta sección presenta una venta. Véase @sec:s-beta y el @lst:venta.

## Una venta {#sec:venta-sub}

```res {#lst:venta caption="Una venta y su consecuencia" run=run}
module Venta
rule vende() = a() <= b()
```
::: explanation
El listado deriva `b`. Lo usa también @lst:compra.
:::

Texto tras el listado; la @tbl:datos resume.

| a | b |
|---|---|
| 1 | 2 |
: Datos de ejemplo {#tbl:datos}

### Detalle

Más texto.
