#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate do aoquetenhodireito. Falha fechado.

REGRA DA CASA: um check que nunca foi visto a ficar VERMELHO nao e um check, e um
enfeite. Prove-o com `--self-test` e com `scripts/mutants.py`.
"""

import argparse
import contextlib
import datetime as _dt
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import desemprego  # noqa: E402
import oracle      # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RESULTS = []


def check(nome, ok, detalhe=""):
    RESULTS.append((nome, bool(ok), detalhe))
    return bool(ok)


def _ler(*p):
    with io.open(os.path.join(_ROOT, *p), encoding="utf-8") as fh:
        return fh.read()


def correr(hoje=None):
    del RESULTS[:]
    const = desemprego.carregar_constantes()
    golden = json.loads(_ler("assets", "golden-cases.json"))
    lei = _ler("assets", "law", "dl-220-2006.md")
    hoje = hoje or _dt.date.today()

    # ---- 1. o estatuto existe ---------------------------------------------
    precisos = ["8.º", "9.º", "22.º", "24.º", "28.º", "29.º", "30.º", "35.º",
                "36.º", "37.º", "38.º"]
    faltam = [a for a in precisos if ("### Artigo %s" % a) not in lei]
    check("lei-artigos-capturados", not faltam, "faltam: %s" % faltam)

    check("lei-e-versao-consolidada",
          "consolidada" in lei.lower() and "2006-34533075" in lei,
          "a versao original tem prazos e montantes revogados")

    # Frases sem as quais o motor estaria a implementar um artigo que nao tem.
    ancoras = {
        "22.º": "360 dias de trabalho por conta de outrem",
        "28.º": "igual a 65 % da remuneração de referência",
        "29.º": "duas vezes e meia o valor do indexante",
        "37.º": "150 dias",
    }
    sem = [a for a, f in ancoras.items() if f not in lei]
    check("lei-ancoras-verbatim-presentes", not sem, "sem ancora: %s" % sem)

    # ---- 2. constantes ------------------------------------------------------
    # O check que fica vermelho sozinho em 1 de Janeiro. Um motor de apoios
    # sociais com o IAS do ano passado devolve numeros errados com toda a
    # confianca, e ninguem se lembra de o actualizar sem a suite a gritar.
    check("constantes-do-ano-corrente",
          const["_meta"]["ano_vigente"] >= hoje.year,
          "constantes de %s, hoje e %s - actualize IAS e RMMG"
          % (const["_meta"]["ano_vigente"], hoje.year))

    check("constantes-tem-fonte",
          all(const[k].get("fonte") for k in ("IAS", "RMMG")),
          "um valor sem diploma que o fixe e um numero inventado")

    ias, rmmg = const["IAS"]["valor"], const["RMMG"]["valor"]
    d = const["derivados"]
    erros = []
    for chave, esperado in (("tecto_mensal_2_5_IAS", 2.5 * ias),
                            ("piso_mensal_1_IAS", ias),
                            ("piso_majorado_1_15_IAS", 1.15 * ias),
                            ("limiar_condicao_recursos_80pc_IAS", 0.8 * ias),
                            ("majoracao_diaria_por_filho", 0.10 * rmmg / 30.0)):
        if abs(d[chave] - round(esperado, 2)) > 0.005:
            erros.append("%s: %s != %.2f" % (chave, d[chave], esperado))
    check("derivados-batem-certo-com-IAS-e-RMMG", not erros, "; ".join(erros))

    check("majoracoes-mortas-registadas",
          any(m["estado"] == "NAO VIGENTE" for m in const["majoracoes_nao_vigentes"]),
          "as majoracoes de 10 % de 2012/2013 aparecem como Notas no DR e sao "
          "faceis de repor por engano")

    # ---- 3. dois caminhos ---------------------------------------------------
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok_cross = oracle.crosscheck(const)
    check("dual-path-concorda", ok_cross, buf.getvalue().strip()[-200:])

    # ---- 4. casos dourados --------------------------------------------------
    f_est, f_mont, f_dur, f_rec, f_txt = [], [], [], [], []
    for c in golden["cases"]:
        out = desemprego.analisar(c["caso"], const)
        e = c["esperado"]
        if out["estado"] != e["estado"]:
            f_est.append("%s: %s != %s" % (c["id"], out["estado"], e["estado"]))
        if "montante_mensal" in e:
            got = out.get("montante", {}).get("montante_mensal")
            if got is None or abs(got - e["montante_mensal"]) > 0.005:
                f_mont.append("%s: %s != %s" % (c["id"], got, e["montante_mensal"]))
        if "dias_total" in e:
            got = out.get("duracao", {}).get("dias_total")
            if got != e["dias_total"]:
                f_dur.append("%s: %s != %s" % (c["id"], got, e["dias_total"]))
        rec = sorted(r["chave"] for r in out["recusas"])
        if rec != sorted(c["recusas_esperadas"]):
            f_rec.append("%s: %s != %s" % (c["id"], rec, sorted(c["recusas_esperadas"])))
        blob = json.dumps(out, ensure_ascii=False)
        falta = [s for s in c["deve_conter"] if s not in blob]
        if falta:
            f_txt.append("%s: falta %s" % (c["id"], falta))

    check("golden-estado", not f_est, "; ".join(f_est))
    check("golden-montante", not f_mont, "; ".join(f_mont))
    check("golden-duracao", not f_dur, "; ".join(f_dur))
    check("golden-recusas-conjunto-exacto", not f_rec, "; ".join(f_rec))
    check("golden-cita-o-que-tem-de-citar", not f_txt, "; ".join(f_txt))

    # ---- 5. invariantes de produto -----------------------------------------
    # Estes nao sao sobre aritmetica. Sao sobre o que uma pessoa sem rendimento le.

    # (a) Um valor apresentado como certo, quando o art. 29.o n.os 2-3 pode
    #     reduzi-lo, faz alguem assinar uma renda que nao vai conseguir pagar.
    sem_tecto = [c["id"] for c in golden["cases"]
                 if desemprego.analisar(c["caso"], const)["estado"] == "TEM_DIREITO"
                 and "este_valor_e_um_limite_superior"
                 not in desemprego.analisar(c["caso"], const)]
    check("valor-sempre-rotulado-como-limite-superior", not sem_tecto,
          "casos: %s" % sem_tecto)

    # (b) Nunca prometer. O motor estima; quem decide e a Seguranca Social.
    promessa = re.compile(r"vai receber|ira receber|ir[aá] receber|tem garantido|"
                          r"garantimos|receber[aá] \d", re.I)
    maus = [c["id"] for c in golden["cases"]
            if promessa.search(json.dumps(desemprego.analisar(c["caso"], const),
                                          ensure_ascii=False))]
    check("nunca-promete-um-valor", not maus, "casos: %s" % maus)

    # (c) Falhar o prazo de garantia NAO pode ser um beco sem saida: o art. 22.o
    #     n.os 2 e 3 abre o subsidio social com 180 ou 120 dias. Quem parar de ler
    #     perde uma prestacao a que pode ter direito.
    becos = []
    for c in golden["cases"]:
        out = desemprego.analisar(c["caso"], const)
        if out["estado"] == "NAO_CUMPRE_PRAZO_DE_GARANTIA":
            t = out["o_que_isto_significa"]
            if "180" not in t or "120" not in t:
                becos.append(c["id"])
    check("falhar-o-prazo-encaminha-para-o-social", not becos, "casos: %s" % becos)

    # (d) O art. 36.o n.o 1 conta desde o REQUERIMENTO. Nao avisar custa dinheiro
    #     real por cada dia de atraso.
    sem_prazo = [c["id"] for c in golden["cases"]
                 if desemprego.analisar(c["caso"], const)["estado"] == "TEM_DIREITO"
                 and "prazos_a_nao_perder" not in desemprego.analisar(c["caso"], const)]
    check("avisa-que-conta-desde-o-requerimento", not sem_prazo, "casos: %s" % sem_prazo)

    # (d2) O art. 8.o n.o 1 condiciona a titularidade a cessacao "nos termos do
    #      artigo 9.o", e o motor nao pergunta como o contrato cessou quando e
    #      usado pela linha de comandos simples. Afirmar direito sem enunciar essa
    #      condicao e afirmar de mais.
    sem_assuncao = []
    for c in golden["cases"]:
        out = desemprego.analisar(c["caso"], const)
        if out["estado"] != "TEM_DIREITO":
            continue
        t = out.get("esta_estimativa_assume", "")
        if not t or "9." not in t:
            sem_assuncao.append(c["id"])
    check("declara-a-assuncao-de-involuntariedade", not sem_assuncao,
          "casos: %s" % sem_assuncao)

    # (d3) A duracao tambem e um limite superior (art. 37.o n.os 3-5, nao modelado).
    #      Estava declarado nos documentos e ausente da saida que o utilizador le.
    sem_cav_dur = [c["id"] for c in golden["cases"]
                   if desemprego.analisar(c["caso"], const)["estado"] == "TEM_DIREITO"
                   and "a_duracao_tambem_pode_ser_menor"
                   not in desemprego.analisar(c["caso"], const)]
    check("duracao-tambem-rotulada-como-limite-superior", not sem_cav_dur,
          "casos: %s" % sem_cav_dur)

    # (d4) A janela de R (art. 28.o n.o 4) tem de aparecer na saida. Quem somar
    #      "os ultimos 12 meses de vencimento" com uma compensacao por cessacao
    #      sobrestima R - e portanto o montante - sem nada o avisar.
    sem_R = [c["id"] for c in golden["cases"]
             if desemprego.analisar(c["caso"], const)["estado"] == "TEM_DIREITO"
             and "o_que_conta_para_R" not in desemprego.analisar(c["caso"], const)]
    check("explica-a-janela-de-R", not sem_R, "casos: %s" % sem_R)

    # (d5) O tecto de 4 quinquenios do art. 37.o n.o 2. Uma carreira de 40 anos nao
    #      pode dar mais dias do que uma de 20: a janela e de 20 anos.
    excesso = []
    for idade in (25, 35, 45, 55):
        tecto = sum(desemprego.periodo_concessao(idade, 24, 20)[:2])
        for anos in (21, 25, 30, 40):
            v = sum(desemprego.periodo_concessao(idade, 24, anos)[:2])
            if v != tecto:
                excesso.append("idade=%d anos=%d -> %d (tecto %d)" % (idade, anos, v, tecto))
        _, _, _, q, _ = desemprego.periodo_concessao(idade, 24, 40)
        if q > 4:
            excesso.append("idade=%d: %d quinquenios, maximo legal 4" % (idade, q))
    check("acrescimo-limitado-a-4-quinquenios", not excesso, "; ".join(excesso))

    # (e) Direccao do erro, testada em COMPORTAMENTO e nao declarada numa string:
    #     mais salario nunca pode dar menos subsidio, e mais carreira nunca pode
    #     dar menos dias. Sobrestimar um apoio e o erro que magoa aqui.
    viol = []
    for R in (6000, 12000, 20000, 40000, 100000):
        a = desemprego.montante_mensal(R, const)["montante_mensal"]
        b = desemprego.montante_mensal(R + 1200, const)["montante_mensal"]
        if b < a:
            viol.append("R=%d -> %.2f mas R=%d -> %.2f" % (R, a, R + 1200, b))
    for idade in (25, 35, 45, 55):
        for anos in (0, 5, 10, 15, 20):
            x = sum(desemprego.periodo_concessao(idade, 24, anos)[:2])
            y = sum(desemprego.periodo_concessao(idade, 24, anos + 5)[:2])
            if y < x:
                viol.append("idade=%d anos=%d -> %d mas anos=%d -> %d"
                            % (idade, anos, x, anos + 5, y))
    check("monotonia-salario-e-carreira", not viol, "; ".join(viol))

    # (f) Um facto de recusa desconhecido tem de REBENTAR. Um typo em
    #     "trabalhador_independente" nao pode virar uma estimativa normal.
    try:
        desemprego.analisar({"idade": 35, "dias_trabalho_24m": 720,
                             "meses_com_registo": 24, "remuneracao_total_12m": 16800,
                             "factos": {"trabalhador_independentee": True}}, const)
        rebentou = False
    except ValueError:
        rebentou = True
    check("facto-desconhecido-rebenta", rebentou)

    # (g) A tabela do art. 37.o tem de cobrir TODA a grelha idade x meses. Um buraco
    #     faria o motor levantar excepcao a um utilizador real.
    buracos = []
    for idade in range(16, 71):
        for meses in range(0, 60):
            try:
                desemprego.periodo_concessao(idade, meses, 0)
            except ValueError:
                buracos.append((idade, meses))
    check("tabela-37-cobre-toda-a-grelha", not buracos, "buracos: %s" % buracos[:8])

    # ---- 6. honestidade do repositorio -------------------------------------
    check("pontos-cegos-declarados", len(oracle.BLIND_SPOTS) >= 6,
          "%d declarados" % len(oracle.BLIND_SPOTS))
    check("ponto-cego-do-tecto-liquido-declarado",
          any("29" in b and "IRS" in b for b in oracle.BLIND_SPOTS),
          "o maior limite do motor tem de estar na lista, nao so no docstring")

    # `"28" in skill` passava com qualquer preco que contivesse 28. Um check assim
    # e quase tautologico: nao verifica que o artigo esta EXPLICADO, so que dois
    # digitos aparecem algures. Passa a exigir a citacao na forma em que a lei e
    # citada, e a explicacao do tecto que o motor nao consegue calcular.
    skill = _ler("SKILL.md")
    for art in ("22.º", "28.º", "29.º", "37.º"):
        check("skill-cita-art-%s" % art.replace(".º", ""),
              ("art. %s" % art) in skill, "citacao na forma 'art. %s'" % art)
    check("skill-explica-o-tecto-que-nao-calcula",
          "IRS" in skill and "limite superior" in skill.lower(),
          "o maior limite do motor tem de estar explicado, nao so mencionado")

    promessa_doc = re.compile(
        r"(presta\w*|oferec\w*|damos|garant\w*)[^.\n]{0,40}aconselhamento|"
        r"(?<!n[aã]o )substitui[^.\n]{0,20}(advogad|contabilist|seguran[cç]a social)", re.I)
    achados = []
    for f in ("SKILL.md", "README.md", "README.pt.md", "AVISO-FORMAL.md", "DISCLAIMER.md"):
        for m in promessa_doc.finditer(_ler(f)):
            achados.append("%s: %r" % (f, m.group(0)[:60]))
    check("nenhum-documento-promete-aconselhamento", not achados, "; ".join(achados))

    m = re.search(r"(\d+)\s+verifica", skill)
    check("skill-conta-os-checks-corretamente",
          m and int(m.group(1)) == len(RESULTS) + 1,
          "SKILL.md diz %s, o sweep tem %d" % (m.group(1) if m else "?", len(RESULTS) + 1))
    return RESULTS


def _imprimir(res, verboso):
    for nome, ok, det in res:
        if ok and not verboso:
            continue
        print("%-4s %s" % ("PASS" if ok else "FAIL", nome))
        if not ok and det:
            print("       %s" % str(det)[:400])
    falhou = sum(1 for _, ok, _ in res if not ok)
    print()
    print("%d/%d verificacoes passaram" % (len(res) - falhou, len(res)))
    return falhou


def self_test():
    print("--- estado normal ---")
    base = correr()
    if any(not ok for _, ok, _ in base):
        print("SELF-TEST ABORTADO: o gate ja esta vermelho")
        return 1
    print("%d/%d verde" % (len(base), len(base)))

    print("--- com a taxa do art. 28.o corrompida (65 %% -> 70 %%) ---")
    orig = desemprego.montante_mensal

    def patched(R, c, rmmg=None):
        out = orig(R, c, rmmg)
        out["montante_mensal"] = round(out["montante_mensal"] / 0.65 * 0.70, 2)
        return out
    desemprego.montante_mensal = patched
    try:
        falhas = [n for n, ok, _ in correr() if not ok]
    finally:
        desemprego.montante_mensal = orig
    if not falhas:
        print("SELF-TEST FALHOU: o gate ficou verde com a taxa errada")
        return 1
    print("o gate detectou: %s" % ", ".join(falhas[:6]))

    print("--- com as constantes do ano passado ---")
    falhas2 = [n for n, ok, _ in correr(hoje=_dt.date(2099, 1, 1)) if not ok]
    if "constantes-do-ano-corrente" not in falhas2:
        print("SELF-TEST FALHOU: as constantes velhas nao acenderam o alarme")
        return 1
    print("o gate detectou a passagem do ano")

    print("--- restaurado ---")
    if any(not ok for _, ok, _ in correr()):
        print("SELF-TEST FALHOU: nao restaurou")
        return 1
    print("verde de novo")
    print()
    print("SELF-TEST OK - o gate sabe falhar e sabe voltar a passar")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Gate do aoquetenhodireito")
    p.add_argument("-v", "--verboso", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return self_test()
    return 1 if _imprimir(correr(), args.verboso) else 0


if __name__ == "__main__":
    sys.exit(main())
