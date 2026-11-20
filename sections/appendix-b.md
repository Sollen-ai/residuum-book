Este apéndice sigue un caso jurídico de principio a fin. Parte de unas
normas sobre la compraventa, las codifica en Residuum y obtiene sus
respuestas con las cuatro órdenes de la CLI. Cada salida es la que produce el
build con el commit fijado.

El caso usa dos fixtures del repositorio:

- `examples/legal/case_monotonic_formal.res`, el expediente monotónico. Es la
  referencia inline de `LegalMonotonicCase`, congelada en el tag `v1`
  (`docs/legal-monotonic-v1.md`).
- `examples/legal/case_sale_defaults_formal.res`, una fixture separada que
  escribe la misma compraventa con defaults.

Los listados de este apéndice ocultan el bloque de declaraciones y reglas de
cada fixture como setup, copiado sin cambios. Sólo muestran los experimentos.
@Sec:s6.13 hizo un recorrido parecido con un módulo pequeño. Aquí el módulo es
el del caso de referencia.

## El texto jurídico

<!-- covers: 1 -->

Las fixtures no citan un artículo de un código. Sus reglas y sus comentarios
fijan, en cambio, un contenido normativo preciso. Este apéndice lo resume en
cinco normas. La redacción es del libro; cada norma remite a la regla que la
codifica.

1. **Permiso.** Una compraventa permite al vendedor transmitir la cosa al
   comprador, con cualquiera de los dos paquetes de reciprocidad
   (`reciprocalTransferPermission`).
2. **Deber simple.** Con el paquete simple (`Plain`), la compraventa obliga
   al vendedor a transmitir la cosa (`plainTransferObligation`).
3. **Deber con reserva.** Con el paquete de reserva (`Retention`), ese deber
   nace sólo cuando el comprador paga el precio al vendedor
   (`paidRetentionObligation`).
4. **Relación de hacer.** Toda obligación crea, en el instante siguiente, una
   relación de hacer entre deudor y beneficiario (`obligationCreatesRelation`).
5. **Transmisión.** Un acto de transmisión realizado pasa la cosa al
   destinatario, que adquiere su titularidad (`transferOccurrence`,
   `transferTitle` y `historicalTransferEffect`).

Los comentarios añaden tres precisiones de lectura. La primera separa el
índice del expediente de la vigencia. `tau` indexa lo observado, mientras que
`oldDate` y `newDate` son fechas simbólicas de vigencia. La segunda separa la
evidencia de la norma. `~Act` es evidencia explícita de que un acto no
ocurrió; nunca nace de la ausencia de `Act`. La tercera separa la norma de su
ejecución. Una obligación queda en Known, y su efecto se ejecuta sólo después
y sólo si se pide.

El caso concreto es siempre el mismo. Juan vende un coche a Pedro por un
precio, con autoridad privada y vigencia `oldDate`. Los escenarios cambian el
paquete y la evidencia del pago.

El expediente contiene más normas que estas cinco. Deriva cumplimientos y
violaciones, crea leyes a partir de un poder legislativo y anula normas
inferiores por autoridad superior. Sus 16 experimentos recorren esas normas.
Este apéndice sigue sólo la compraventa y una transmisión cumplida.

Las normas también tienen límites declarados. Un comentario de la fixture
advierte que las reglas de reciprocidad no afirman ningún `Act` de
transmisión ni ejecutan el estado. Una transmisión automática por ley
requeriría su propia regla explícita. En este expediente, `give` sólo se
deriva de una transmisión ya ocurrida.

## Su codificación

<!-- covers: 2 -->

La codificación empieza por el vocabulario. Cada norma necesita verbos tipados
para sus hechos de entrada y para sus conclusiones.

```res {#lst:appendix-b-verbos caption="Los verbos de entrada del expediente" run=include include=residuum@d4d2282:examples/legal/case_monotonic_formal.res#L97-L116}
```
::: explanation
El extracto declara los verbos `seeded` del expediente. Los verbos de
conducta y de norma llevan un identificador `Fact` y los participantes.
También llevan una autoridad y una vigencia. `sale` reúne en un solo evento
los nueve datos de la compraventa. `reciprocity` aporta el paquete como dato positivo, y
`paymentFor` liga el documento de pago a la venta.
:::

@Lst:appendix-b-verbos muestra tres decisiones de la codificación. La primera
es que la autoridad y la vigencia son argumentos ordinarios. Así se conservan
en cada evento derivado y en su provenance. La segunda es que el paquete de
reciprocidad entra como dato, no como elección del motor. La tercera es que
el pago tiene dos piezas: `paymentFor` dice que un documento corresponde a la
venta, y un `Act` acredita que el pago ocurrió.

Las normas 2 y 3 son dos reglas con el mismo antecedente de partida. Las dos
concluyen la misma obligación. @Lst:s2-11-cabeceras, en la evaluación de la
legibilidad, ya mostró las tres reglas de reciprocidad juntas.

```res {#lst:appendix-b-reglas caption="Las dos fuentes del deber de transmitir" run=include include=residuum@d4d2282:examples/legal/case_monotonic_formal.res#L218-L228}
```
::: explanation
Las dos reglas concluyen la misma obligación del vendedor de transmitir la
cosa al comprador. La primera exige el paquete `Plain`. La segunda
exige el paquete `Retention`, un documento de pago y el `Act` de pago del
comprador al vendedor. Los parámetros `paymentAuthority` y `paymentEffective`
guardan la autoridad y la vigencia del pago sin igualarlas a las de la venta.
:::

La flecha `<=` se lee «implica»: las condiciones van a la izquierda y la
conclusión a la derecha (@sec:s5.1). Cada parámetro toma su tipo de las firmas
de los verbos (@sec:s4.1). Las normas 4 y 5 son reglas puente entre las
conclusiones jurídicas y los efectos.

```res {#lst:appendix-b-puentes caption="Las reglas puente hacia los efectos" run=include include=residuum@d4d2282:examples/legal/case_monotonic_formal.res#L185-L201}
```
::: explanation
`obligationCreatesRelation` deriva el efecto `do` en `after t` a partir de
una obligación. `historicalTransferEffect` deriva el efecto `give` a partir
de una transmisión. `filedObligation` convierte una obligación presentada desde
fuera en la misma conclusión `obligation` que producen las reglas.
:::

Los efectos tienen sus propios verbos. Un verbo `effect` declara, después de
`=>`, qué campos del estado cambia (@sec:s7.4).

```res {#lst:appendix-b-efectos-decl caption="Los verbos de efecto del expediente" run=include include=residuum@d4d2282:examples/legal/case_monotonic_formal.res#L146-L167}
```
::: explanation
`give` quita la cosa de los activos del sujeto y la añade a los del
destinatario. `do` añade un record `Relation` a las obligaciones del deudor y
a los derechos del beneficiario. El campo `mode` vale `Doing`. Ambos verbos
llegan a los conjuntos a través del campo `patrimony` de cada persona.
:::

La relación de hacer es un dato del estado, no una polaridad de `Act`. El
comentario del extracto lo dice: `do` y `notDo` constituyen relaciones de
hacer y de abstenerse, pero no son evidencia de una conducta histórica. Los
tipos sostienen esa separación. `Relation` es una entidad con campos, y su
campo `thing` es opcional (@sec:s4.2).

## Cierre

<!-- covers: 3 -->

La primera pregunta es qué se sigue de cada expediente. La responde el cierre
(@sec:s6.3). @Lst:appendix-b-cierre reproduce tres experimentos de la
fixture. Los tres tienen la misma venta y cambian el paquete o el pago.

```res {#lst:appendix-b-cierre caption="El cierre de tres expedientes de compraventa" run=run setup=appendix-b-expediente}
experiment plainWithoutPayment {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Plain) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}

experiment retentionWithoutPayment {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}

experiment retentionPaid {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
        paymentFor(saleCase, pricePayment) @ tau,
        Act(pricePayment, pedro, pay, price, juan, private, newDate) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}
```
::: explanation
Los tres experimentos están copiados de la fixture. Con `Plain`, el cierre
contiene el permiso, la obligación y el efecto `do` en `after(tau)`. Con
`Retention` y sin pago, sólo contiene el permiso. Con `Retention` y el pago,
vuelve a contener la obligación y el efecto. La línea `Horn` dice si el
objetivo declarado está en el cierre.
:::

La salida sigue las normas una por una. El permiso aparece en los tres
expedientes, porque la norma 1 vale con cualquier paquete. La obligación
aparece con `Plain` y con `Retention` pagada. El efecto `do` aparece donde
aparece la obligación, en el instante siguiente.

El expediente sin pago merece atención. El cierre no contiene la obligación,
pero tampoco contiene `~obligation`. Residuum no tiene negación por fallo: la
falta de una prueba no produce evidencia en contra (@sec:s1.5). La respuesta
es sólo que la obligación no se deriva de estos hechos.

La norma 3 pide un pago concreto: del comprador, por el precio y al vendedor.
La fixture comprueba esa exigencia con tres variantes del pago.

```res {#lst:appendix-b-pagos caption="Tres variantes de la evidencia del pago" run=run setup=appendix-b-expediente}
experiment retentionNegativePayment {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
        paymentFor(saleCase, pricePayment) @ tau,
        ~Act(pricePayment, pedro, pay, price, juan, private, newDate) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}

experiment retentionPaidAndNegative {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
        paymentFor(saleCase, pricePayment) @ tau,
        Act(pricePayment, pedro, pay, price, juan, private, newDate) @ tau,
        ~Act(pricePayment, pedro, pay, price, juan, private, newDate) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}

experiment retentionWrongPayment {
    // El documento refiere a la venta, pero el destinatario del pago no es
    // el vendedor. Esa evidencia no satisface la condición compartida.
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
        paymentFor(saleCase, pricePayment) @ tau,
        Act(pricePayment, pedro, pay, price, pedro, private, newDate) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}
```
::: explanation
Los tres experimentos están copiados de la fixture. Con sólo evidencia
negativa del pago, la obligación no se deriva. Con evidencia positiva y
negativa del mismo pago, la obligación se deriva y la regla
`conflictingActEvidence` añade `inconsistent`. Con un pago cuyo destinatario
es Pedro, la obligación tampoco se deriva.
:::

Cada variante enseña algo distinto:

- **Evidencia negativa.** `~Act` no cumple la condición positiva de la regla.
  Tampoco produce `~obligation`, porque ninguna regla lo concluye.
- **Evidencia opuesta.** El acto y su negación conviven en Known. La
  obligación se deriva igual, y una regla ordinaria marca el conflicto con
  `inconsistent`. Nada se borra y nada explota.
- **Pago mal dirigido.** El documento corresponde a la venta, pero el acto no
  va al vendedor. El matching exige que coincidan todos los argumentos
  compartidos, así que la regla no se aplica.

El cierre guarda también por qué vale cada evento. La orden `explain` lo
muestra. @Lst:appendix-b-justificacion usa el experimento `bothReciprocities`
de la fixture, que aporta los dos paquetes a la vez.

```res {#lst:appendix-b-justificacion caption="Dos justificaciones de la misma obligación" run=explain setup=appendix-b-expediente}
experiment bothReciprocities {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Plain) @ tau,
        reciprocity(saleCase, Retention) @ tau,
        paymentFor(saleCase, pricePayment) @ tau,
        Act(pricePayment, pedro, pay, price, juan, private, newDate) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}
```
::: explanation
La obligación tiene dos justificaciones. Una viene de
`plainTransferObligation`, con la venta y el paquete simple. La otra viene de
`paidRetentionObligation`, con la venta, la reserva, el documento y el acto
de pago. Cada justificación lleva su sustitución completa, su sello
`derivedAt` y sus antecedentes numerados.
:::

Ningún paquete derrota aquí al otro. El comentario de la fixture lo dice: las
reglas acumulan consecuencias y pruebas, y esa selección corresponde a los
defaults. Es la conducta que @sec:s1.5 contrasta con Catala. Cada
justificación conserva la sustitución de todos los parámetros. Así se ve, por
ejemplo, que el pago tiene vigencia `newDate` y la venta `oldDate`.

## Requisitos residuales

<!-- covers: 4 -->

La segunda pregunta es la inversa: qué falta para la obligación en el
expediente con reserva y sin pago. La responde una consulta residual
(@sec:s6.8). Sin más datos, el expediente excede el fragmento de esa
búsqueda, como muestra @lst:appendix-b-sin-ambito.

```res {#lst:appendix-b-sin-ambito caption="Una consulta residual sin ámbito sobre el expediente" run=expect-error cmd=query setup=appendix-b-expediente}
experiment retentionUnscoped {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}
```
::: explanation
La búsqueda parte de la obligación y examina las reglas que la concluyen. La
cabeza de `plainTransferObligation` no menciona `saleId`, que sólo aparece en
el cuerpo. La búsqueda no enumera dominios para fijarlo, así que se detiene
con un error en lugar de dar una respuesta parcial.
:::

El error no es un fallo del caso. Las reglas de la compraventa usan datos que
la obligación no menciona:

- el identificador de la venta;
- el precio y el permiso;
- para la reserva, el documento de pago y su autoridad y vigencia.

La búsqueda sólo admite parámetros fijados por la cabeza o por un binding
explícito. No prueba valores entre las constantes del módulo, aunque aquí
sólo haya una venta posible.

La solución es declarar un ámbito y fijar esos parámetros con `with`. Un
binding es una restricción de la búsqueda, no evidencia (@sec:s4.7).

```res {#lst:appendix-b-requisito caption="Lo que falta para el deber de transmitir" run=query setup=appendix-b-expediente}
experiment retentionWithoutPayment {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        reciprocity(saleCase, Retention) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
    using rules { plainTransferObligation, paidRetentionObligation }
    with {
        rule plainTransferObligation.saleId = saleCase,
        rule plainTransferObligation.priceObject = price,
        rule plainTransferObligation.permit = saleTransferPermission,
        rule paidRetentionObligation.saleId = saleCase,
        rule paidRetentionObligation.priceObject = price,
        rule paidRetentionObligation.permit = saleTransferPermission,
        rule paidRetentionObligation.payment = pricePayment,
        rule paidRetentionObligation.paymentAuthority = private,
        rule paidRetentionObligation.paymentEffective = newDate,
    }
}
```
::: explanation
El ámbito contiene las dos reglas de @lst:appendix-b-reglas. Los bindings
fijan la venta, el precio, el permiso y los datos del pago. El requisito une
dos alternativas con `∨`. Una es el paquete simple. La otra es el producto
`⊗` del documento de pago y del acto de pago de Pedro a Juan.
:::

El requisito tiene dos ramas, y las dos son correctas en este programa:

- **El pago.** Con el documento y el acto de pago, la regla de reserva
  concluye la obligación. Es la respuesta que espera quien lee la norma 3.
- **El paquete simple.** Con `reciprocity(saleCase, Plain)`, la regla simple
  también la concluye. El expediente monotónico admite los dos paquetes a la
  vez, como mostró @lst:appendix-b-justificacion.

Cada rama es una hipótesis, no un hecho. Ninguna entra en Known, y cada una
se certifica por replay antes de publicarse. La consulta no elige entre ramas
ni las ordena. La segunda rama muestra un límite del modelo monotónico: nada
impide aportar un paquete que contradiga el pacto de reserva. Esa exclusión
es tarea de la capa de defaults.

Las dos ramas se pueden contrastar con el cierre. La rama del pago contiene
los dos seeds que el experimento `retentionPaid` añadía en
@lst:appendix-b-cierre, y allí el cierre derivó la obligación. La rama del
paquete simple corresponde a `bothReciprocities` en
@lst:appendix-b-justificacion. El requisito y el cierre cuentan así la misma
historia desde los dos extremos.

La respuesta vale para el ámbito declarado. La regla `filedObligation`, por
ejemplo, quedó fuera. Una obligación presentada desde fuera sería una tercera
explicación que esta consulta no examina.

## Defaults

<!-- covers: 5 -->

La fixture `case_sale_defaults_formal.res` reescribe la compraventa para que
el paquete sea una conclusión y no un dato. El verbo `selectedReciprocity` es
`derived`. Dos reglas lo concluyen desde la venta, y dos defaults deciden cuál
se aplica (@sec:s6.9).

```res {#lst:appendix-b-defaults-decl caption="Los defaults de la compraventa" run=include include=residuum@d4d2282:examples/legal/case_sale_defaults_formal.res#L130-L141}
```
::: explanation
`NormalSale` aplica por defecto la regla `normalSale`, que elige el paquete
simple. Lo bloquea un pacto de reserva. `RetentionSale` declara la regla
`retentionSale` como excepción a `NormalSale` cuando consta ese pacto. Los
dos registros, bloqueo y derrota, son distintos para el evaluador.
:::

@Lst:appendix-b-defaults ejecuta dos experimentos de esa fixture. El setup
oculto contiene sus declaraciones, sus reglas y sus defaults, sin cambios.

```res {#lst:appendix-b-defaults caption="La selección del paquete con y sin reserva" run=run setup=appendix-b-defaults}
experiment noRetention {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
    }
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}

experiment retentionUnpaid {
    seeds {
        sale(saleCase, juan, car, pedro, price, saleTransferDuty, saleTransferPermission, private, oldDate) @ tau,
        retentionAgreed(saleCase) @ tau,
    }
    // No se deriva la obligación; tampoco se afirma ~obligation.
    query residual obligation(saleTransferDuty, juan, transfer, car, pedro, private, oldDate) @ tau
}
```
::: explanation
Sin pacto de reserva, `NormalSale` se selecciona y el cierre contiene
`selectedReciprocity(saleCase, Plain)` y la obligación. Con el pacto,
`NormalSale` queda bloqueado por `retentionAgreed(saleCase)` y se selecciona
`RetentionSale`. El cierre contiene entonces el paquete de reserva y el
permiso, pero no la obligación, porque falta el pago.
:::

La salida dice cómo se hizo la selección. El contexto es el cierre de las
reglas obligatorias. El alcance del bloqueo es `RuleLambda`. La consistencia
queda `NotChecked`. Cada default informa su aplicabilidad, la evidencia que lo
bloquea y la sustitución que la encontró.

El contexto cambia de tamaño entre los dos experimentos. Sin pacto, el cierre
obligatorio tiene un evento: la venta. Con el pacto, tiene dos. Ese cierre se
calcula antes de elegir, sólo con las reglas que no dependen de un default.
Después, el runner cierra de nuevo con la lambda elegida. La selección se
hace una vez y no se revisa con lo que ese segundo cierre deriva.

Esta fixture resuelve el límite de la sección anterior. Con el pacto de
reserva, el paquete simple ya no se puede obtener: el default que lo elegía
está bloqueado. El precio es que la consulta residual ya no se admite. Las
consultas residuales y FOUR rechazan los módulos con defaults
(@lst:s2-2-sin-defaults). En la fixture, las líneas `query residual` sólo
declaran el objetivo que `run` comprueba.

## FOUR

<!-- covers: 6 -->

El cierre sólo recorre las reglas hacia delante. Una consulta FOUR pregunta,
en cambio, qué se sigue en todos los modelos de cuatro valores. Así capta la
contraposición (@sec:s6.10). En el caso, la norma 5 dice que una transmisión
da la titularidad al destinatario. ¿Qué se sigue si consta que Pedro no es
titular del coche por ese acto?

```res {#lst:appendix-b-four caption="La norma de titularidad leída hacia atrás" run=query setup=appendix-b-expediente}
experiment notOwner {
    premises { ~owns(pedro, car, transferAct, private, newDate) @ tau, }
    query fourFusion ~transferred(transferAct, juan, car, pedro, private, newDate) @ tau
    using rules { transferTitle }
    with {
        rule transferTitle.act = transferAct,
        rule transferTitle.subject = juan,
        rule transferTitle.object = car,
        rule transferTitle.recipient = pedro,
        rule transferTitle.authority = private,
        rule transferTitle.effective = newDate,
        rule transferTitle.t = tau,
    }
}
```
::: explanation
La premisa es evidencia explícita de que Pedro no es titular del coche por el
acto `transferAct`. El ámbito contiene sólo `transferTitle`, con todos sus
parámetros fijados. Horn no deriva el objetivo. FOUR sí: en todo modelo de la
teoría, la transmisión de Juan a Pedro tiene evidencia en contra.
:::

La respuesta FOUR es la contraposición de la norma 5. Si la transmisión
implica la titularidad, la evidencia contra la titularidad es evidencia contra
la transmisión. El cierre no obtiene esa conclusión, y Horn responde `false`.

La consulta usa `premises`, no `seeds`: son hipótesis lógicas. El ámbito es
obligatorio, porque `transferTitle` tiene parámetros. La salida lo marca con
`explicit scope`. Con un ámbito, un `true` vale para todo el módulo; un
`false` sólo diría que esas instancias no bastan (@sec:s6.10).

La salida da dos comprobaciones del mismo resultado. La primera enumera las
16 interpretaciones de los dos átomos del ámbito y encuentra 3 modelos; el
objetivo vale en todos. La segunda calcula el modelo mínimo FOUR y le asigna
al objetivo el valor `T`. Las dos coinciden.

La lectura jurídica exige cuidado. La consulta no dice que el acto no ocurrió
en la historia del caso. Dice que, si se admite la premisa, la norma 5 obliga
a admitir evidencia contra la transmisión. La premisa es una hipótesis lógica, y
la conclusión vale sólo bajo ella.

## Efectos

<!-- covers: 7 -->

Las conclusiones jurídicas quedan en Known. La orden `execute` va un paso más
allá: aplica los efectos derivados a un estado inicial (@sec:s7.4). El estado
se declara en el experimento. Como el `give` jurídico recorre
`subject.patrimony.assets`, el estado necesita referencias a dos patrimonios.

```res {#lst:appendix-b-efectos caption="Una transmisión cumplida y sus efectos sobre el patrimonio" run=execute setup=appendix-b-expediente}
const juanPatrimony : Patrimony
const pedroPatrimony : Patrimony

experiment fulfilledTransfer {
    seeds {
        obligationFiled(transferDuty, juan, transfer, car, pedro, private, oldDate) @ tau,
        Act(transferAct, juan, transfer, car, pedro, private, newDate) @ tau,
    }
    state @ tau {
        juan.patrimony = juanPatrimony,
        pedro.patrimony = pedroPatrimony,
        juanPatrimony.assets = {car},
        pedroPatrimony.assets = {},
        juanPatrimony.obligations = {},
        pedroPatrimony.rights = {},
    }
    query residual owns(pedro, car, transferAct, private, newDate) @ tau
}
```
::: explanation
El experimento adapta `fulfilledTransfer` de la fixture: conserva la
obligación presentada y el acto de transmisión. Declara además un estado con
dos clases de campos: referencias a un patrimonio y conjuntos. El cierre deriva el cumplimiento,
la titularidad y los efectos `do` y `give` en `after(tau)`. La ejecución
mueve el coche al patrimonio de Pedro y registra la relación de hacer en los
dos patrimonios.
:::

La salida tiene dos partes. La primera es el cierre, igual que con `run`.
Contiene el cumplimiento de la obligación, la titularidad de Pedro por dos
causas y los dos efectos. La segunda es la ejecución. Los dos efectos ocurren
en el mismo instante, pero no chocan: uno cambia activos y el otro relaciones.
La salida imprime cada record `Relation` en la forma interna de Rust.

La ejecución sigue el orden de `after` (@sec:s7.4). El estado inicial está en
`tau`. Los dos efectos tienen instante de entrada `after(tau)`, así que se
aplican en un solo paso de `tau` a `after(tau)`. El estado final muestra el
coche en los activos de Pedro. También muestra la misma relación de hacer en
las obligaciones de Juan y en los derechos de Pedro.

La ejecución no vuelve al cierre. El nuevo estado no produce un `Act` ni
ninguna otra conclusión. El comentario de la fixture lo exige: `do` crea una
relación de hacer, pero no es evidencia de una conducta histórica.

## Lo que muestra el caso

El caso pasa por todas las capas, pero no las combina en una sola consulta.
El recorrido deja estos resultados:

- El cierre aplica las normas tal como están escritas y guarda cada
  justificación, con autoridad y vigencia.
- La consulta residual encuentra lo que falta sólo con ámbito y bindings. Sin
  ellos, el expediente excede su fragmento.
- Los defaults excluyen el paquete contrario, pero entonces el módulo ya no
  admite consultas residuales ni FOUR.
- FOUR obtiene la contraposición que el cierre no da, dentro de un ámbito
  explícito.
- La ejecución cambia el estado y nunca vuelve a la lógica.

El caso tampoco cubre todo el lenguaje. El expediente no declara Programs
ni verbos asociados, así que no usa la consulta residual activa
(@sec:s5.6). Su grafo de verbos es acíclico, y por eso el runner lo acepta
(@sec:s4.9). Ningún tiempo derivado pasa de `after(tau)`.

Ninguna de estas respuestas valora el caso en derecho. Las fixtures codifican
unas normas elegidas, y el motor dice qué se sigue de ellas. @Sec:s8.2 discute
qué enseña este tipo de modelado.
