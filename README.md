# El lenguaje de programación Residuum

Libro sobre [Residuum](https://github.com/Sollen-ai/residuum), un lenguaje de
programación lógica con tipos. Autores: Jesús Antonio Sesma Espinoza y Claude
(Anthropic).

**Descargar:** [PDF](https://github.com/Sollen-ai/residuum-book/releases/latest/download/residuum.pdf)
· [folleto para imprimir](https://github.com/Sollen-ai/residuum-book/releases/latest/download/residuum-booklet.pdf)
· [texto plano](https://github.com/Sollen-ai/residuum-book/releases/latest/download/residuum.txt)
· [todas las ediciones](https://github.com/Sollen-ai/residuum-book/releases)

## Qué versión de Residuum describe

Cada edición describe Residuum en un commit fijo, no su estado actual. La
portada, el colofón y la etiqueta de la edición nombran ese commit:

| Edición | Etiqueta | Residuum |
|---|---|---|
| es-1.0 | `es-1.0-residuum-d4d2282` | [`d4d2282`](https://github.com/Sollen-ai/residuum/tree/d4d2282c3b7868d84579c8f09f0c3172bf1bdb76) |

Los commits posteriores de Residuum pueden diferir de lo que dice el libro.
`./book staleness` compara el commit fijado con otra revisión y lista las
secciones que citan ficheros cambiados.

## Cómo se construye

Las afirmaciones del libro proceden del repositorio de Residuum en el commit
fijado. Cada listado es un programa que el build ejecuta con el launcher de
Residuum; la salida impresa es la salida real, comparada con una copia en
`expected/`. El build también comprueba referencias, citas y las reglas de
lenguaje llano de `guidelines/`.

- `spine.yaml`: índice y encargo de cada sección (alcance, evidencias, listados).
- `sections/`: el texto, un fichero por sección; `setup/` y `expected/`, los
  módulos ocultos y las salidas fijadas de los listados; `bib/`, la bibliografía.
- `build/`: la herramienta de build (`build/README.md`).
- `AGENTS.md` y `HANDOFF.md`: reglas de trabajo y estado del proyecto.

Para construirlo hace falta una copia de Residuum junto a esta (`../residuum`,
o la ruta en `RESIDUUM_REPO`), con su launcher y sus límites de memoria; el PDF
necesita el entorno virtual:

```sh
python3 -m venv .venv && .venv/bin/pip install -r build/requirements.txt
./book build --all        # out/index.html, residuum.pdf, residuum-booklet.pdf, residuum.txt
```

La sección 6.5 cita además el estudio `residuum-diagrams` (commit `ac4727f`),
que todavía no es público; sus cifras se marcan en el texto con su clase de
afirmación.

## Licencia

- El texto del libro, sus figuras y sus listados: [CC BY 4.0](LICENSE)
  ([resumen](https://creativecommons.org/licenses/by/4.0/deed.es)).
- Los fragmentos citados del repositorio de Residuum, incluida su referencia
  del lenguaje (apéndice C): licencia MIT de Residuum.
- La herramienta de build (`build/`): [MIT](build/LICENSE).

---

*English:* a Spanish-language book on the Residuum logic programming
language. Each edition describes Residuum at one pinned commit, named on the
title page and in the release tag. Text CC BY 4.0; build tool MIT.
