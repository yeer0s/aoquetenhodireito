<p align="center">
  <img src="docs/images/aoquetenhodireito-wide-light-1k.svg#gh-light-mode-only" alt="aoquetenhodireito" width="640">
  <img src="docs/images/aoquetenhodireito-wide-dark-1k.svg#gh-dark-mode-only" alt="aoquetenhodireito" width="640">
</p>

<p align="center">
  <b>Just lost your job in Portugal. Do you qualify, how much, for how long?</b><br>
  Portuguese unemployment benefit, computed offline from the <i>consolidated</i> statute,
  with the article behind every number — and an honest upper bound instead of a confident lie.
</p>

<p align="center">
  <a href="#licença--licence"><img src="https://img.shields.io/badge/licence-MIT-blue.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/dependencies-0-brightgreen.svg" alt="zero dependencies">
  <img src="https://img.shields.io/badge/network-none-brightgreen.svg" alt="no network">
  <img src="https://img.shields.io/badge/checks-33-brightgreen.svg" alt="33 checks">
  <img src="https://img.shields.io/badge/statute-consolidated%20DR-informational.svg" alt="statute">
</p>

<p align="center">
  <a href="README.pt.md"><b>🇵🇹 Ler em português</b></a> ·
  <a href="SKILL.md">Skill</a> ·
  <a href="AVISO-FORMAL.md">Formal notice</a> ·
  <a href="https://mowei.pt">mowei.pt</a>
</p>

---

> **Not advice, and binding on nobody.** Only Segurança Social decides.
> See [`AVISO-FORMAL.md`](AVISO-FORMAL.md).

## Three questions, today — not in three weeks

You were let go on Friday. By Monday you need to know: **do I qualify? how much?
until when?** Segurança Social will answer — after a claim and a wait. Rent does
not wait.

```bash
git clone https://github.com/yeer0s/aoquetenhodireito.git && cd aoquetenhodireito
python scripts/desemprego.py --idade 35 --dias-trabalho-24m 720 \
       --meses-com-registo 24 --remuneracao-total-12m 16800 \
       --anos-carreira-20 12 --atinge-rmmg
```

```
[TEM DIREITO - ESTIMATIVA]
constantes de 2026  ·  IAS 537.13 EUR

PRAZO DE GARANTIA (art. 22.o n.o 1): 720 de 360 dias -> CUMPRE

MONTANTE
  . Art. 28.o n.o 4: remuneracao de referencia = 16800.00 / 360 = 46.6667 EUR/dia.
  . Art. 28.o n.o 1: 65 % de 46.6667 = 30.3333 EUR/dia; x30 = 910.00 EUR/mes.
  => ate 910.00 EUR/mes

DURACAO
  . base:      420 dias  (art. 37.o n.o 1 al. b) iii))
  . acrescimo:  60 dias  (art. 37.o n.o 2 al. a), 2 quinquenios)
  => 480 dias  (~16.0 meses)
```

No install. No dependencies. Python 3.8+.

## The number this tool cannot compute — said first, not in a footnote

Art. 29.º n.os 2–3 caps the benefit at **75 %, and never more**, of the **net**
reference remuneration. Art. 29.º n.º 4 defines net as gross minus the
contributory rate **and income-tax withholding**.

Your withholding depends on bracket, marital status, dependants and region. An
offline program that never asks your tax situation **cannot** apply that cap
without inventing a number.

So the figure is an **upper bound**. The real amount can be **lower**. Never
higher. It says so on every qualifying output — and a check fails if any output
omits it.

A tool that gave you a confident €910 when the truth was €700 would do more damage
than one that leaked your data, because you would have signed a lease on it.

## Direction of error — the inverse of the sibling project

In [`porreceber`](https://github.com/yeer0s/porreceber) the dangerous error is
declaring a live debt dead. **Here it is overstating a benefit.**

So when uncertain, this engine returns the **lowest** amount and the **shortest**
duration the statute allows. And that is not a claim in a README — a check tests
**behaviour**: more salary can never yield less benefit, more career can never
yield fewer days.

## Not a dead end

Failing the 360-day qualifying period (art. 22.º n.º 1) does **not** end it. Art.
22.º n.º 2 opens the **social** unemployment benefit at 180 days in 12 months, and
n.º 3 drops it to **120 days** where the job ended by expiry of a fixed-term
contract. Anyone who stops reading at "you don't qualify" loses a benefit they may
be entitled to — and a check fails if that output doesn't say so.

## What it refuses to compute

| Fact | Why | Article |
|---|---|---|
| self-employed | the statute covers employees (*por conta de outrem*) | 8.º n.º 1 |
| not resident in Portugal | entitlement requires national residence | 8.º n.º 1 |
| former invalidity pensioner | own amounts and start date | 8.º n.º 3 |
| partial benefit | autonomous calculation regime | 33.º |
| voluntary exit without cause | no involuntary unemployment, no right — **but resignation *with* just cause IS involuntary** | 9.º n.º 6 |
| attributable dismissal, no court action | the presumption needs proof of proceedings | 9.º n.º 2 |
| **social** benefit (means test) | the DL 70/2010 equivalence scale isn't captured | 24.º n.º 2 |

A tool that answers everything is lying about something.

## How you know it's right

Not because the suite is green. Because it **knows how to go red**:

```bash
python scripts/oracle.py --crosscheck      # 4704 combinations, two independent paths
python scripts/oracle.py --mutation-test   # restores the dead 2012/13 uplift, demands red
python scripts/oracle.py --blind-spots     # what this engine does NOT cover
python scripts/sweep.py --self-test        # proves the gate can fail and recover
python scripts/mutants.py                  # mutants against the product invariants
python scripts/sweep.py                    # 33 checks
python scripts/offline_audit.py            # static proof: no import/call path to the network
```

- **Two independent implementations.** The engine computes `(R/360) × 0.65 × 30`;
  the oracle computes `(R/12) × 0.65` and **never divides by 360**. Duration is
  resolved by ordered-boundary search rather than table scan.
  *Honest limit:* they are algebraically equivalent, so they catch transcription
  and rounding errors, **not** misreadings of the law. For those, the verbatim
  capture and adversarial review are the control.
- **A check that turns red by itself on 1 January.** IAS and RMMG change every
  year; the gate fails once the constants year falls behind the system year.
  Nobody has to remember.
- **The dead uplift is registered as dead.** The 10 % uplifts from Leis 66-B/2012
  and 83-C/2013 appear as *Notas* to art. 28.º in the DR's consolidated view and
  are easy to mistake for live law. Restoring them would inflate every figure by
  10 % — that is exactly the `--mutation-test` mutant.
- **Product invariants**, not just arithmetic: always label the figure an upper
  bound; **always label the duration one too**; never promise an amount; always
  state that entitlement assumes involuntary unemployment under art. 9.º; always
  explain the art. 28.º n.º 4 window for R; always route a failed qualifying period
  to the social benefit; always warn that art. 36.º n.º 1 counts from the **claim
  date**, not the job-loss date. Each has a mutant proving the check bites.

## Fully offline — structurally, not as a promise

Zero dependencies, zero network calls, zero telemetry. Someone using this is
typing their salary history while unemployed — a financial-vulnerability profile.
None of it leaves the machine. `offline_audit.py` proves there is no import- or
call-level path to the network, and CI re-runs the **entire gate with the socket
layer disabled** — the dynamic proof, not just the static one. Stated precisely:
the AST audit is not a sandbox and would not stop a determined malicious
contributor; the CI socket job and the fact that every PR is read are the real
controls. See [`SECURITY.md`](SECURITY.md).

## Sources

- **DL n.º 220/2006, CONSOLIDATED version** — arts. 8.º, 9.º, 22.º, 24.º, 28.º,
  29.º, 30.º, 35.º, 36.º, 37.º, 38.º, captured verbatim in
  [`assets/law/`](assets/law/). Source: **Diário da República**, the official
  journal — not a private compilation.
- **IAS 2026: €537.13** — Portaria n.º 480-A/2025/1, 30 December.
- **RMMG 2026: €920.00** — Decreto-Lei n.º 139/2025, 29 December.

The consolidated version is not a detail: this statute has been amended more than
a dozen times, and the qualifying periods, amounts and durations were all touched.

## Related

- **[porreceber](https://github.com/yeer0s/porreceber)** — is that old debt still collectable?
- **[AoCentimo](https://github.com/yeer0s/AoCentimo)** — Portuguese IRS engine
- **[recibosegarantia](https://github.com/yeer0s/recibosegarantia)** — receipts, e-Fatura QR, EU guarantees

## Licença · Licence

MIT — see [`LICENSE`](LICENSE). Unmodified, no additional restrictions.

## Support

Free and MIT, forever. If it helped on a bad week:

☕ [Buy me a coffee](https://buymeacoffee.com/letsmoweis) · [Ko-fi](https://ko-fi.com/letsmowei)

Built alongside **[mowei.pt](https://mowei.pt)** — Portuguese consumer comparison
for energy, telecoms, insurance, banking and more.
