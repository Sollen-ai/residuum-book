module Envio

const tau : PropositionTime

seeded verb checked()
seeded verb lowConfidence()
seeded verb cached()
derived verb verified()
derived verb send()

rule sendCheckedLowConfidence(t) = checked() @ t & lowConfidence() @ t <= send() @ t
rule sendCached(t) = cached() @ t <= send() @ t
rule refuseLowConfidence(t) = lowConfidence() @ t <= ~send() @ t
rule sendCachedChecked(t) = cached() @ t & checked() @ t <= send() @ t
rule verifyChecked(t) = checked() @ t <= verified() @ t
rule sendVerified(t) = verified() @ t <= send() @ t
