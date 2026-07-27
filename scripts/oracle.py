#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Oraculo independente - segunda implementacao do calculo do subsidio.

PORQUE EXISTE
    Um corpus de teste gerado a partir do proprio motor nao prova nada. Se o
    motor estiver errado, os casos dourados ficam errados da mesma maneira e a
    suite fica verde - foi assim que um projecto irmao carregou nove taxas de IRS
    obsoletas com 29/29 checks verdes.

    Aqui os dois caminhos sao:

      desemprego.py   diario:  (R/360) x 0,65 x 30
      oracle.py       mensal:  (R/12) x 0,65        - nunca divide por 360

    Sao algebricamente equivalentes (30/360 = 1/12) mas escritos a partir de
    leituras diferentes do art. 28.o, e um erro de fecho num deles nao aparece no
    outro. A duracao e resolvida por procura em fronteiras ordenadas em vez de
    varrimento de tabela.

    Nota honesta sobre os limites disto: dois caminhos algebricamente equivalentes
    apanham erros de TRANSCRICAO e de arredondamento, nao erros de LEITURA DA LEI.
    Se eu tiver lido mal o art. 28.o, ambos os caminhos leem-no mal. Isso e o que
    a captura verbatim em assets/law/ e a revisao adversarial existem para apanhar.
"""

import argparse
import datetime as _dt
import itertools
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import desemprego  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# ------------------------------------------------------- caminho independente

def montante_oracle(R, ias, atinge_rmmg=None):
    """Via media MENSAL. Nunca divide por 360."""
    mensal = (R / 12.0) * 0.65
    tecto, piso = 2.5 * ias, 1.0 * ias
    v = min(max(mensal, piso), tecto)
    if atinge_rmmg:
        v = max(v, min(1.15 * ias, tecto))
    return round(v, 2)


# Fronteiras do art. 37.o n.o 1 escritas como listas ordenadas, nao como tabela.
_IDADE = [30, 40, 50]
_MESES = [15, 24]
_DIAS = [[150, 210, 330],   # < 30
         [180, 330, 420],   # 30-39
         [210, 360, 540],   # 40-49
         [270, 480, 540]]   # >= 50
_PASSO = [30, 30, 45, 60]   # acrescimo do n.o 2, por faixa de idade


def _idx(v, fronteiras):
    i = 0
    for f in fronteiras:
        if v >= f:
            i += 1
    return i


def duracao_oracle(idade, meses, anos20):
    fi = _idx(idade, _IDADE)
    fm = _idx(meses, _MESES)
    # A janela do art. 37.o n.o 2 e de 20 anos -> no maximo 4 quinquenios.
    # Este `min` faltava aqui E no motor, e por isso os dois caminhos concordavam
    # num resultado errado. Fica como lembrete de que caminhos independentes so
    # apanham divergencias, nunca uma leitura errada partilhada.
    return _DIAS[fi][fm] + _PASSO[fi] * (min(int(anos20), 20) // 5)


# -------------------------------------------------------------- pontos cegos

BLIND_SPOTS = [
    "O tecto do art. 29.o n.os 2 e 3 (75 % do valor LIQUIDO da remuneracao de "
    "referencia) NAO e calculado por nenhum dos dois caminhos: depende da retencao "
    "de IRS, que o motor nao pergunta. O valor devolvido e um limite superior.",

    "Os dois caminhos sao algebricamente equivalentes. Apanham erros de transcricao "
    "e de arredondamento; NAO apanham um erro de leitura da lei, porque ambos leriam "
    "o mesmo artigo da mesma maneira errada.",

    "Nenhum caso dourado vem de uma decisao real da Seguranca Social. O corpus prova "
    "coerencia com o texto legal, nao com a pratica do ISS.",

    "O art. 37.o n.os 3, 4 e 5 (periodos ja usados em desemprego anterior, retoma de "
    "trabalho nos primeiros seis meses, acrescimos nao gozados) NAO estao modelados. "
    "Quem ja recebeu subsidio antes pode ter uma duracao MENOR do que a calculada.",

    "O subsidio social de desemprego (arts. 24.o, 30.o, 38.o) e porta de recusa: a "
    "escala de equivalencia da condicao de recursos (DL n.o 70/2010) nao esta capturada.",

    "As constantes (IAS, RMMG) mudam todos os anos. sweep.py falha quando o ano das "
    "constantes fica para tras do ano do sistema, mas isso deteta a passagem do ano - "
    "nao deteta uma alteracao legislativa a meio do ano.",
]


# ------------------------------------------------------------------ crosscheck

def _grelha():
    idades = [18, 29, 30, 39, 40, 49, 50, 64]
    meses = [0, 1, 14, 15, 23, 24, 36]
    anos20 = [0, 4, 5, 9, 10, 19, 20]
    Rs = [3000.0, 9000.0, 12040.0, 16800.0, 30000.0, 90000.0]
    return itertools.product(idades, meses, anos20, Rs)


def crosscheck(const):
    ias = const["IAS"]["valor"]
    falhas, total = [], 0
    for idade, meses, anos20, R in _grelha():
        for rmmg in (None, True):
            total += 1
            a = desemprego.montante_mensal(R, const, rmmg)["montante_mensal"]
            b = montante_oracle(R, ias, rmmg)
            if abs(a - b) > 0.005:
                falhas.append("montante idade=%d R=%.0f rmmg=%s motor=%.2f oraculo=%.2f"
                              % (idade, R, rmmg, a, b))
            base, acr, _, _, _ = desemprego.periodo_concessao(idade, meses, anos20)
            d = duracao_oracle(idade, meses, anos20)
            if base + acr != d:
                falhas.append("duracao idade=%d meses=%d anos20=%d motor=%d oraculo=%d"
                              % (idade, meses, anos20, base + acr, d))
    print("crosscheck: %d combinacoes" % total)
    if falhas:
        for f in falhas[:20]:
            print("  DIVERGENCIA " + f)
        if len(falhas) > 20:
            print("  ... e mais %d" % (len(falhas) - 20))
        return False
    print("crosscheck: OK - os dois caminhos concordam em todas as combinacoes")
    return True


def mutation_test(const):
    """Prova que o crosscheck SABE FALHAR."""
    orig = desemprego.montante_mensal

    def patched(R, c, rmmg=None):
        out = orig(R, c, rmmg)
        out["montante_mensal"] = round(out["montante_mensal"] * 1.10, 2)  # a majoracao morta
        return out
    desemprego.montante_mensal = patched
    try:
        ok = crosscheck(const)
    finally:
        desemprego.montante_mensal = orig
    if ok:
        print("MUTATION TEST FALHOU: o crosscheck ficou verde com a majoracao de 10 % "
              "de 2012/2013 reposta - exactamente o erro que a versao consolidada evita.")
        return False
    print("mutation test: OK - o crosscheck detectou a majoracao de 10 % indevida")
    if not crosscheck(const):
        print("MUTATION TEST FALHOU: nao restaurou o estado original")
        return False
    print("mutation test: OK - estado original restaurado")
    return True


def main(argv=None):
    p = argparse.ArgumentParser(description="Oraculo independente do aoquetenhodireito")
    p.add_argument("--crosscheck", action="store_true")
    p.add_argument("--mutation-test", action="store_true")
    p.add_argument("--blind-spots", action="store_true")
    args = p.parse_args(argv)
    const = desemprego.carregar_constantes()
    if args.blind_spots:
        print("PONTOS CEGOS DECLARADOS (%d)" % len(BLIND_SPOTS))
        for b in BLIND_SPOTS:
            print("  - " + b)
        return 0
    if args.mutation_test:
        return 0 if mutation_test(const) else 1
    return 0 if crosscheck(const) else 1


if __name__ == "__main__":
    sys.exit(main())
