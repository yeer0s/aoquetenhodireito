# Security & privacy

## The threat this is designed against

Someone using this tool has just lost their job and is typing in their salary
history, their age, their contribution record and how long they worked. That is a
**financial-vulnerability profile** — precisely the material a credit-marketing or
debt-collection industry would pay for, attached to a person at their least able
to refuse an offer.

The design assumption is that **none of it leaves the machine**, including to us.

There is a second, sharper threat, and it is not about data. A person in this
position is vulnerable to being told a number they want to hear. A tool that
confidently announced "€910 a month" when the real figure was €700 would do more
damage than a data leak, because they would have signed a lease on it. That is why
"always label the figure as an upper bound" is enforced as a **test**, not a
guideline.

## Guarantees, and how they are enforced

| Guarantee | Enforcement |
|---|---|
| No network calls | `scripts/offline_audit.py` parses every shipped file and fails on any networking/`subprocess`/`ctypes` import. Wired into CI |
| No dynamic execution | The same audit fails on builtin `eval`/`exec`/`__import__` |
| No shell-out | Fails on `os.system`, `os.popen`, `os.exec*`, `importlib.import_module` |
| Offline at runtime, not just in theory | CI re-runs **every gate with the socket layer disabled**. Any attempted connection crashes the build |
| No dependencies | Standard library only |
| No telemetry | There is no analytics and no code that could add it without failing the audit |
| The figure is always labelled an upper bound | `valor-sempre-rotulado-como-limite-superior` in `sweep.py`, with a dedicated mutant proving the check bites |
| Never promises an amount | `nunca-promete-um-valor` — the engine estimates; Segurança Social decides |
| Failing the qualifying period is never a dead end | `falhar-o-prazo-encaminha-para-o-social` — art. 22.º n.os 2–3 opens a different benefit at 180 or 120 days |
| Constants cannot silently go stale | `constantes-do-ano-corrente` turns the suite red on 1 January |
| Every regime cites captured statute | `lei-ancoras-verbatim-presentes` — a period with no verbatim anchor fails the build |

Verify all of it yourself:

```bash
python scripts/offline_audit.py --selftest   # prove the audit can fail
python scripts/offline_audit.py              # then trust that it didn't
python scripts/mutants.py                    # prove the product invariants bite
python scripts/sweep.py --self-test          # prove the gate can go red and recover
```

## What this is not

The offline audit is a **static** audit, not a sandbox. It catches the accidental
and the obvious: a networking import, a shell-out, a dynamic import, a builtin
`eval`. It is **not** a defence against a determined malicious contributor, who
has many routes to a network no import-level check can see. The real control is
that this is a small repository where every pull request is read. Said plainly,
rather than implying the audit is a security boundary it isn't.

Likewise, the engine is only as correct as the **figures you type**. It cannot
verify your qualifying days or your contribution record, and it cannot compute the
art. 29.º net cap at all. Those are declared blind spots
(`python scripts/oracle.py --blind-spots`), not solved problems.

## Reporting a vulnerability

Open a private security advisory on GitHub, or email the address on
[mowei.pt](https://mowei.pt).

The following are treated as security-grade defects, not ordinary bugs:

- any path by which user data could leave the machine;
- any input that produces an amount **without** the upper-bound label;
- any input where the engine states a figure as certain or promised;
- any input where failing the qualifying period does not point to art. 22.º n.os 2–3;
- any period or amount citing an article absent from `assets/law/`.

## Supported versions

The `main` branch. This is a small project — there are no backported branches.
