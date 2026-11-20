Un préstamo con declaraciones ocultas.

```res {#lst:prestamo caption="Un préstamo" run=run setup=prestamo}
rule lending(person, object, t) =
    requests(person, object) @ t & available(object) @ t <= lent(person, object) @ t

experiment anaBorrows {
    seeds { requests(ana, book) @ tau, available(book) @ tau, }
    query residual lent(ana, book) @ tau
}
```
::: explanation
La regla deriva `lent` de las dos semillas.
:::

El @lst:roto usa un verbo sin declarar.

```res {#lst:roto caption="Un verbo sin declarar" run=expect-error setup=prestamo}
rule keeping(person, object, t) =
    requests(person, object) @ t <= keeps(person, object) @ t
```
::: explanation
Residuum rechaza `keeps`, que no está declarado.
:::
