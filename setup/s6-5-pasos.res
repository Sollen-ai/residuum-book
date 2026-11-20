module Pasos

const tau : PropositionTime

seeded verb A()
seeded verb B()
derived verb shared()
derived verb result()
derived verb ready()

rule fromA(t) = A() @ t <= shared() @ t
rule fromB(t) = B() @ t <= shared() @ t
rule consequence(t) = shared() @ t & ready() @ tau <= result() @ t
rule axiom() = I <= ready() @ tau
