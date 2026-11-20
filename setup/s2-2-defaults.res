module Defaults

entity Fact
entity Package
const Plain : Package
const Retention : Package
const saleCase : Fact
const tau : PropositionTime

seeded verb sale(id : Fact)
seeded verb retentionAgreed(sale : Fact)
derived verb selected(sale : Fact, package : Package)

rule normalSale(saleId, t) = sale(saleId) @ t <= selected(saleId, Plain) @ t
rule retentionSale(saleId, t) = sale(saleId) @ t <= selected(saleId, Retention) @ t

default NormalSale =
    supernormal normalSale
    blocked when
        retentionAgreed(saleId) @ t

default RetentionSale =
    exception retentionSale
    to NormalSale
    when
        retentionAgreed(saleId) @ t
