Este libro describe Residuum, un lenguaje de programación lógica con tipos.
Sigue el plan de la serie a la que pertenece: primero presenta el lenguaje,
después lo evalúa con doce criterios y al final expone su teoría y su
práctica. Este prefacio dice para quién es el libro, qué cubre y cuál es la
aportación central del lenguaje.

## Para quién es este libro

<!-- covers: 1 -->

El libro se dirige a lectores con formación en lenguajes de programación o en
lógica. Supone que el lector ha programado antes y que lee sin esfuerzo una
regla lógica escrita con variables. No supone que conozca Residuum, Rust ni
la teoría de los retículos residuados. Los ejemplos jurídicos no exigen
formación en derecho: cada sección explica el caso que usa.

## Qué cubre

<!-- covers: 2 -->

El libro describe Residuum tal como está en un commit fijado del repositorio.
El colofón indica ese commit. Cada afirmación sobre el lenguaje procede de
ese estado del código y de su documentación. El libro cubre:

- la sintaxis y los tipos;
- las reglas y los Programs;
- la semántica del cierre y de las consultas;
- la ejecución acotada y los efectos.

El libro deja fuera tres cosas:

- los cambios posteriores al commit fijado;
- las capacidades que el commit no tiene, salvo para decir que faltan;
- el trabajo futuro que la documentación de Residuum no marca como pendiente.

Otros lenguajes aparecen sólo como contraste. La historia del proyecto ocupa
@sec:s1.2. La referencia del lenguaje del repositorio se incluye como
@sec:appendix-c.

## La aportación central

<!-- covers: 3 -->

**El problema.** Un programa lógico suele responder qué se sigue de lo que ya
se sabe. En Residuum, esa respuesta es el cierre de Known bajo las reglas
(@sec:s6.3). Muchas preguntas piden lo contrario: qué falta para llegar a un
objetivo. Un abogado no pregunta sólo si un contrato produce una entrega.
Pregunta qué hecho falta para que la produzca.

**El mecanismo.** Residuum responde con la consulta residual. Su respuesta es
un requisito residual: una fórmula de seeds que, añadida como hipótesis a
Known, basta para derivar el objetivo. La fórmula une con `⊗` los seeds de una
misma explicación y con `∨` las explicaciones alternativas. Cada explicación
lleva una prueba finita. Antes de publicarla, el replay la recorre hacia
delante con el mismo matching que usa el cierre. Un candidato que no pasa el
replay se descarta. Las hipótesis nunca entran en Known (@sec:s6.8).

**La garantía.** La auditoría del núcleo monotónico clasifica la garantía T10
como **THEOREM** condicional. Si la consulta devuelve un requisito `H`, el
objetivo pertenece al cierre de Known más las hojas de `H`. La garantía es de
suficiencia: lo propuesto basta. No es de completitud: la consulta no promete
encontrar toda explicación posible (@sec:s6.8, @sec:s2.12).

**Los límites.** El contrato de la consulta tiene fronteras declaradas:

- sólo admite objetivos ground, cuyos parámetros fije la cabeza de cada regla;
  no enumera dominios (@sec:s6.8);
- no elige explicaciones mínimas ni preferidas (@sec:s6.8);
- rechaza los módulos con defaults (@sec:s6.9);
- T10 trata las reglas como cláusulas aisladas, así que no vale para el
  cierre de un Program con activaciones; una consulta residual activa cubre
  ese caso, si el cierre termina (@sec:s5.6, @sec:s6.8);
- una búsqueda que agota sus límites devuelve un error, nunca un resultado
  parcial (@sec:s6.11).

@Sec:s8.1 sitúa esta aportación entre las fortalezas y las limitaciones del
lenguaje.

## Cómo leer el libro

<!-- covers: 4 -->

La serie fija un orden: los criterios van antes de la teoría. La Parte 2
evalúa Residuum antes de que las Partes 3 a 6 expongan su sintaxis, sus tipos
y su semántica. Cada veredicto remite a la sección que lo fundamenta. El libro
admite dos recorridos.

**El recorrido de referencia** sigue el orden del índice:

1. la Parte 1 presenta el paradigma, el diseño y los criterios (@sec:p1);
2. la Parte 2 aplica los doce criterios (@sec:p2);
3. las Partes 3 a 6 exponen la sintaxis, los tipos, las reglas y la semántica
   (@sec:p3, @sec:p4, @sec:p5, @sec:p6);
4. las Partes 7 a 9 tratan la pragmática y el balance (@sec:p7, @sec:p8,
   @sec:p9).

**El recorrido guiado** empieza en @sec:s1.7. Esa sección escribe un módulo
pequeño, lo ejecuta y lee su salida, incluida una consulta residual. Desde
allí, el lector puede ir a la residuación (@sec:s6.8) y al caso jurídico
completo (@sec:appendix-b). Después puede volver a los criterios.

## Convenciones

<!-- covers: 5 -->

**Clases de afirmación.** El libro conserva las clases que usan los
documentos de Residuum, en inglés, como ellos:

- **THEOREM**: un argumento general con sus hipótesis explícitas; no
  significa que el código Rust esté verificado formalmente;
- **MODEL RESULT**: la enumeración exhaustiva de una familia finita de
  modelos;
- **EXPERIMENTAL OBSERVATION**: lo que muestran APIs, tests y fixtures
  concretos;
- **IMPLEMENTED + TESTED**: una capacidad implementada y cubierta por tests;
- **IMPLEMENTED + LIMITED**: una capacidad implementada que necesita
  restricciones, precondiciones o una API distinta;
- **NOT IMPLEMENTED**: una capacidad que el commit no tiene.

El libro atribuye cada clase al documento que la asigna. Un calificativo como
«condicional» forma parte de la clase. @Sec:s6.2 explica cómo separan los
documentos los teoremas de los resultados en modelos.

**Listados.** Cada listado es un módulo completo de Residuum, o un fragmento
con un módulo oculto que lo completa. El build lo ejecuta con el launcher del
commit fijado, bajo sus límites de memoria y de tiempo. La salida que el libro
muestra es la salida real de esa ejecución. El build la compara con una copia
guardada y falla si cambia. Ningún resultado se escribió a mano.

**Explicaciones.** Cada listado lleva una explicación breve de lo que el
lector debe observar. El build reúne esas explicaciones en
@sec:appendix-a, en el orden de los listados.

## Cómo se hizo este libro

Los autores son Jesús Antonio Sesma Espinoza y Claude, de Anthropic. Jesús
Antonio Sesma Espinoza definió el plan del libro y revisa el texto. El texto
se escribió con Claude, a partir del repositorio de Residuum en el commit
fijado. Un índice comentado fija el alcance de cada sección. El build
comprueba cada listado, cada referencia y las reglas de lenguaje llano.
