# Plantilla de las secciones de la Parte 2

Every Part 2 section (`s2.1` … `s2.12`, `verdict: required` in `spine.yaml`)
follows this shape. The build's template check enforces the parts marked
**checked**. The template comes from the series pattern (`AGENTS.md`, rule 6);
the twelve criteria and their order are fixed by the spine.

````markdown
<!-- section: s2.N -->

Definición genérica del criterio, sin hablar de Residuum.
Dos o tres párrafos: qué mide el criterio en cualquier lenguaje.

## El criterio en Residuum
<!-- covers: 1 -->
Qué significa el criterio para Residuum, desde la evidencia de la sección.
Si la sección tiene `subsections` en el spine, cada una es un `##` propio,
con el título del spine y sus anclas `covers`.

```res {#lst:... caption="..." run=query}
...
```
::: explanation
...
:::

```catala {#lst:... caption="..." run=none}
...
```
::: explanation
...
:::

## Veredicto
Según este criterio, Residuum ofrece un desempeño <alto|medio|bajo|...>: <razón en una oración>.
````

## Checked

1. **Order.** The section opens with the generic definition, before any
   mention of Residuum's constructs. The first `##` heading comes after it.
2. **Listings.** At least one `res` listing and at least one contrast listing
   in another language (fence language other than `res`, `run=none`). The
   contrast language is one the series compares against: Haskell, Catala,
   Prolog, Datalog or another named in the section's evidence or cited
   literature. Contrast code is quoted or cited, never invented as the
   behaviour of a real system without a source.
3. **Verdict.** The last heading is `## Veredicto`. Its last sentence starts
   with `Según este criterio, Residuum` (the Spanish form of the series'
   "Under this criterion, Residuum performs ...").
4. **Covers.** Every `covers` item of the section (and of each subsection)
   has its `<!-- covers: n -->` anchor; subsection items are numbered
   `<subsection>.<item>`, from 1, in spine order.

## Not checked, but required

- The verdict follows from the section's own evidence; it introduces no new
  claim.
- Limitations are stated plainly, with the repo's claim class where its docs
  give one (THEOREM, MODEL RESULT, EXPERIMENTAL OBSERVATION,
  IMPLEMENTED + TESTED, NOT IMPLEMENTED).
- Criterion names are spelled as in `terms.txt`.
