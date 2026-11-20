@Sec:s-alfa empieza; aquí sigue la @sec:venta-sub.

## Compra

```res {#lst:compra caption="Una compra con preparación oculta" run=query setup=decls}
rule compra() = c() <= d()
```
::: explanation
La preparación `decls` declara el módulo.
:::

![Esquema de la compra](compra.svg){#fig:esquema}

La @fig:esquema muestra el esquema.
