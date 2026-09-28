#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aoquetenhodireito - subsidio de desemprego (Portugal), calculado offline.

O QUE FAZ
    A partir dos factos que o utilizador indica, devolve: se cumpre o prazo de
    garantia, quanto pode receber por mes, durante quantos dias, e que artigo
    fundamenta cada numero.

O TECTO QUE ESTE MOTOR NAO CONSEGUE CALCULAR
    O art. 29.o n.os 2 e 3 limita o subsidio a 75 % - e nunca mais - do valor
    LIQUIDO da remuneracao de referencia. O n.o 4 define liquido como o iliquido
    menos a taxa contributiva E A TAXA DE RETENCAO DO IRS.

    A retencao de IRS depende do escalao, do estado civil, do numero de
    dependentes e da regiao. Um programa offline que nao pergunta a situacao
    fiscal NAO PODE aplicar este tecto sem inventar um numero.

    Por isso o valor devolvido e um LIMITE SUPERIOR. O valor real da Seguranca
    Social pode ser menor. Nunca maior. Isto e dito em todas as saidas, e nao
    numa nota de rodape.

DIRECCAO DO ERRO - e o inverso do projecto irmao
    No `porreceber` o erro perigoso e dizer que uma divida esta morta. Aqui e
    SOBRESTIMAR um apoio: quem conta com 900 EUR e recebe 700 EUR ja assinou a
    renda. Perante duvida, este motor devolve o valor MAIS BAIXO e a duracao MAIS
    CURTA que a lei consinta.

Sem dependencias. Sem rede. stdlib apenas.
"""

import argparse
import datetime as _dt
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
ALGORITHM_VERSION = "1.1.0"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def carregar_constantes(caminho=None):
    caminho = caminho or os.path.join(_ROOT, "assets", "constantes.json")
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------- tabela do 37.o
#
# Transcrita do art. 37.o n.o 1. Os escaloes de idade sao [min, max) e os de
# meses sao [min, max). A tabela e dados, nao codigo, para que uma alteracao
# legislativa se veja num diff em vez de se esconder num if.

TABELA_37 = [
    # (idade_min, idade_max, meses_min, meses_max, dias, alinea)
    (0,  30, 0,  15,   150, "a) i)"),
    (0,  30, 15, 24,   210, "a) ii)"),
    (0,  30, 24, None, 330, "a) iii)"),
    (30, 40, 0,  15,   180, "b) i)"),
    (30, 40, 15, 24,   330, "b) ii)"),
    (30, 40, 24, None, 420, "b) iii)"),
    (40, 50, 0,  15,   210, "c) i)"),
    (40, 50, 15, 24,   360, "c) ii)"),
    (40, 50, 24, None, 540, "c) iii)"),
    (50, None, 0,  15, 270, "d) i)"),
    (50, None, 15, 24, 480, "d) ii)"),
    (50, None, 24, None, 540, "d) iii)"),
]

# Art. 37.o n.o 2: acrescimo por cada CINCO anos completos com registo de
# remuneracoes nos ultimos 20 anos.
MAJORACAO_37_2 = [(0, 40, 30, "a)"), (40, 50, 45, "b)"), (50, None, 60, "c)")]


def _na_faixa(v, lo, hi):
    return v >= lo and (hi is None or v < hi)


def periodo_concessao(idade, meses_registo, anos_carreira_20=0):
    """Art. 37.o n.os 1 e 2. Devolve (dias_base, acrescimo, alinea, quinquenios)."""
    base = alinea = None
    for imin, imax, mmin, mmax, dias, al in TABELA_37:
        if _na_faixa(idade, imin, imax) and _na_faixa(meses_registo, mmin, mmax):
            base, alinea = dias, al
            break
    if base is None:
        raise ValueError("idade %r / meses %r nao caem em nenhuma alinea do art. 37.o n.o 1"
                         % (idade, meses_registo))
    passo = alm = None
    for imin, imax, dias, al in MAJORACAO_37_2:
        if _na_faixa(idade, imin, imax):
            passo, alm = dias, al
            break
    # Art. 37.o n.o 2: "por cada cinco anos com registo de remuneracoes NOS ULTIMOS
    # 20 ANOS". Duas restricoes, nao uma:
    #   - quinquenios COMPLETOS: 9 anos dao um, nao 1,8;
    #   - a janela e de 20 anos, logo o MAXIMO e 4 quinquenios.
    # Sem o tecto, uma carreira de 30 anos rendia 6 quinquenios e o motor prometia
    # 900 dias onde a lei da 780 - quatro meses de rendimento que nao existem, e
    # logo ao utilizador tipico da faixa dos 50+, que responde "30" a pergunta
    # "quantos anos de carreira". O oraculo tinha a mesma omissao e confirmava o
    # erro: a falha correlacionada que o docstring do oracle.py declara como limite.
    anos_relevantes = min(int(anos_carreira_20), 20)
    quinquenios = anos_relevantes // 5
    return base, passo * quinquenios, alinea, quinquenios, alm


# ------------------------------------------------- art. 37.o n.os 3 e 4
#
# N.o 3: "Para efeitos do disposto nos numeros anteriores sao considerados os
# periodos de registo de remuneracoes posteriores ao termo da concessao das
# prestacoes devidas pela ultima situacao de desemprego, sem prejuizo do disposto
# no numero seguinte."
#   -> quem ja recebeu prestacoes de desemprego so conta, para os n.os 1 (meses)
#      e 2 (anos), o registo POSTERIOR ao termo dessa concessao.
#
# N.o 4: quem retomou actividade "no decurso dos primeiros seis meses de
# atribuicao" ve ainda considerado, na prestacao imediatamente subsequente, "o
# periodo de remuneracoes tido em conta na atribuicao da prestacao ... anterior".
#   -> soma-se o periodo que a prestacao anterior considerou.
#
# O que o texto NAO diz, e por isso se le pela via mais curta:
#   - se o periodo do n.o 4 fica sujeito a janela de 20 anos do n.o 2, e como se
#     cruza com o total que o utilizador declara. O motor nunca conta MAIS do que
#     o total declarado (meses_com_registo / anos_carreira_ultimos_20);
#   - o n.o 5 (acrescimos nao gozados por retoma antes de esgotar o periodo) nao
#     diz como se convertem dias nao gozados em periodos de registo. NAO e
#     modelado. So pode ALONGAR - o erro fica do lado seguro, e e declarado.
#
# Ausencia do facto = o calculo de sempre (contagem bruta), com o aviso de que o
# n.o 3 pode encurtar. Nunca mais generoso do que antes desta regra existir.

CHAVES_HISTORICO = ("beneficio_anterior", "meses_com_registo_apos_anterior",
                    "anos_carreira_apos_anterior", "retomou_nos_primeiros_6_meses",
                    "meses_considerados_no_anterior", "anos_considerados_no_anterior")


def _tri(caso, chave):
    v = caso.get(chave)
    if v is not None and not isinstance(v, bool):
        raise ValueError("%s tem de ser true, false ou ausente (recebido %r)" % (chave, v))
    return v


def _contagem(caso, chave):
    v = caso.get(chave)
    if v is None:
        return None
    if isinstance(v, bool) or int(v) != v or int(v) < 0:
        raise ValueError("%s tem de ser um inteiro >= 0 (recebido %r)" % (chave, v))
    return int(v)


def contagem_37_3_4(meses_registo, anos_carreira_20, caso):
    """Art. 37.o n.os 3 e 4. Devolve o dict com os meses e anos a levar aos n.os 1 e 2.

    Falha fechado: declarar um beneficio anterior sem dizer quanto registo houve
    depois dele rebenta, em vez de cair em silencio na contagem bruta - que e
    exactamente a contagem que o n.o 3 proibe.
    """
    ant = _tri(caso, "beneficio_anterior")
    retomou = _tri(caso, "retomou_nos_primeiros_6_meses")
    m_apos = _contagem(caso, "meses_com_registo_apos_anterior")
    a_apos = _contagem(caso, "anos_carreira_apos_anterior")
    m_ant = _contagem(caso, "meses_considerados_no_anterior")
    a_ant = _contagem(caso, "anos_considerados_no_anterior")
    passos, avisos = [], []

    if ant is not True:
        soltos = [k for k, v in (("meses_com_registo_apos_anterior", m_apos),
                                 ("anos_carreira_apos_anterior", a_apos),
                                 ("retomou_nos_primeiros_6_meses", retomou),
                                 ("meses_considerados_no_anterior", m_ant),
                                 ("anos_considerados_no_anterior", a_ant)) if v is not None]
        if soltos:
            raise ValueError("%s so faz sentido com beneficio_anterior=true (art. 37.o "
                             "n.os 3-4); recebido beneficio_anterior=%r"
                             % (", ".join(soltos), ant))
        return {"meses": meses_registo, "anos": anos_carreira_20,
                "regra": "desconhecido" if ant is None else "sem_anterior",
                "passos": passos, "avisos": avisos}

    if m_apos is None or a_apos is None:
        raise ValueError("beneficio_anterior=true exige meses_com_registo_apos_anterior e "
                         "anos_carreira_apos_anterior: o art. 37.o n.o 3 so conta o registo "
                         "POSTERIOR ao termo da concessao anterior, e sem esses numeros o "
                         "motor teria de usar a contagem bruta, que sobrestima a duracao.")

    meses_ef, anos_ef, regra = m_apos, a_apos, "n3"
    passos.append("Art. 37.o n.o 3: so contam os periodos de registo posteriores ao termo "
                  "da concessao anterior -> %d meses, %d anos." % (m_apos, a_apos))

    if retomou is True and m_ant is not None and a_ant is not None:
        meses_ef, anos_ef, regra = m_apos + m_ant, a_apos + a_ant, "n3+n4"
        passos.append("Art. 37.o n.o 4: retomou actividade nos primeiros seis meses da "
                      "prestacao anterior -> soma-se o periodo que ela considerou: "
                      "%d + %d = %d meses, %d + %d = %d anos."
                      % (m_apos, m_ant, meses_ef, a_apos, a_ant, anos_ef))
    elif retomou is True:
        avisos.append("Art. 37.o n.o 4 NAO aplicado: declarou que retomou actividade nos "
                      "primeiros seis meses da prestacao anterior, mas nao indicou os meses "
                      "e anos que essa prestacao considerou. O motor usa so o n.o 3 - a "
                      "leitura mais curta. A duracao real pode ser MAIOR.")
    elif retomou is None:
        avisos.append("Se retomou actividade nos primeiros seis meses da prestacao anterior, "
                      "o art. 37.o n.o 4 manda considerar tambem o periodo de remuneracoes "
                      "que ela teve em conta. Nao foi declarado: o motor usa so o n.o 3.")

    if meses_ef > meses_registo:
        passos.append("Nunca mais do que o total declarado: %d meses -> %d."
                      % (meses_ef, meses_registo))
        meses_ef = meses_registo
    if anos_ef > anos_carreira_20:
        passos.append("Nunca mais do que o total declarado nos ultimos 20 anos: %d anos -> %d. "
                      "O texto do n.o 4 nao diz se a janela de 20 anos do n.o 2 se lhe aplica; "
                      "o motor le-o pela via mais curta." % (anos_ef, anos_carreira_20))
        anos_ef = anos_carreira_20

    avisos.append("Art. 37.o n.o 5 NAO modelado: se retomou trabalho antes de esgotar a "
                  "prestacao anterior e nao chegou a gozar os acrescimos do n.o 2, os periodos "
                  "que nao foram considerados relevam agora para o acrescimo. O texto nao diz "
                  "como se convertem, pelo que o acrescimo real pode ser MAIOR do que o "
                  "mostrado - nunca menor por esta razao.")
    avisos.append("Prazo de garantia com prestacao anterior: o art. 22.o n.o 1 capturado conta "
                  "360 dias em 24 meses e nao diz se os dias ja tidos em conta na prestacao "
                  "anterior podem voltar a contar. Este motor nao o sabe. Se nao puderem, pode "
                  "NAO cumprir - confirme na Seguranca Social Direta.")
    return {"meses": meses_ef, "anos": anos_ef, "regra": regra,
            "passos": passos, "avisos": avisos}


def duracao(idade, meses_registo, anos_carreira_20, caso=None):
    """Art. 37.o n.os 1 a 4, encadeados. O que o analisar() e o crosscheck usam."""
    c = contagem_37_3_4(int(meses_registo), int(anos_carreira_20), caso or {})
    base, acresc, alinea, quinq, alm = periodo_concessao(idade, c["meses"], c["anos"])
    return {"dias_base": base, "acrescimo_dias": acresc, "alinea": alinea,
            "quinquenios_contados": quinq, "alinea_acrescimo": alm,
            "dias_total": base + acresc, "contagem": c}


# ------------------------------------------------------------------- montante

def montante_mensal(remuneracao_total_12m, const, remuneracoes_atingem_rmmg=None):
    """Art. 28.o + art. 29.o n.os 1 e 5. Devolve dict com o encadeamento visivel.

    NAO aplica o tecto dos n.os 2/3 do art. 29.o - ver o docstring do modulo.
    """
    ias = const["IAS"]["valor"]
    taxa = const["taxa_subsidio"]["percentagem"]

    # Art. 28.o n.o 4: remuneracao de referencia = R/360.
    ref_diaria = remuneracao_total_12m / 360.0
    # Art. 28.o n.o 1: 65 %, na base de 30 dias por mes.
    bruto_diario = ref_diaria * taxa
    bruto_mensal = bruto_diario * 30.0

    passos = [
        "Art. 28.o n.o 4: remuneracao de referencia = %.2f / 360 = %.4f EUR/dia."
        % (remuneracao_total_12m, ref_diaria),
        "Art. 28.o n.o 1: 65 %% de %.4f = %.4f EUR/dia; x30 = %.2f EUR/mes."
        % (ref_diaria, bruto_diario, bruto_mensal),
    ]

    valor = bruto_mensal
    tecto = 2.5 * ias
    piso = ias
    if valor > tecto:
        passos.append("Art. 29.o n.o 1: tecto de 2,5 x IAS = %.2f EUR -> reduzido." % tecto)
        valor = tecto
    elif valor < piso:
        passos.append("Art. 29.o n.o 1: piso de 1 x IAS = %.2f EUR -> elevado." % piso)
        valor = piso

    # Art. 29.o n.o 5: se as remuneracoes de base atingirem a RMMG, o piso sobe a
    # 1,15 IAS. So se aplica quando o utilizador CONFIRMA o pressuposto - inferi-lo
    # da media anual estaria errado, porque a media pode atingir a RMMG sem que as
    # remuneracoes mensais a atinjam.
    piso_maj = 1.15 * ias
    if remuneracoes_atingem_rmmg and valor < piso_maj:
        passos.append("Art. 29.o n.o 5: remuneracoes atingem a RMMG (%.2f EUR) -> piso "
                      "majorado de 1,15 x IAS = %.2f EUR." % (const["RMMG"]["valor"], piso_maj))
        valor = piso_maj
    elif remuneracoes_atingem_rmmg is None:
        passos.append("Art. 29.o n.o 5 NAO aplicado: nao foi confirmado se as remuneracoes "
                      "atingem a RMMG. Se atingirem, o piso sobe a %.2f EUR." % piso_maj)

    return {"remuneracao_referencia_diaria": round(ref_diaria, 4),
            "bruto_mensal_antes_de_limites": round(bruto_mensal, 2),
            "montante_mensal": round(valor, 2),
            "tecto_2_5_ias": round(tecto, 2),
            "piso_1_ias": round(piso, 2),
            "piso_majorado_1_15_ias": round(piso_maj, 2),
            "passos": passos}


# --------------------------------------------------------------------- recusas

RECUSAS = [
    ("trabalhador_independente",
     "E trabalhador independente / por conta propria (recibos verdes).",
     "Este diploma cobre expressamente 'trabalhadores por conta de outrem' (titulo do "
     "DL 220/2006 e art. 8.o n.o 1). Os independentes tem regime proprio, nao capturado "
     "aqui. Os valores seriam outros.",
     "8.o n.o 1"),

    ("nao_reside_em_portugal",
     "Nao reside em territorio nacional.",
     "Art. 8.o n.o 1: a titularidade exige residencia em territorio nacional. "
     "Situacoes transfronteiricas regem-se por coordenacao europeia nao modelada aqui.",
     "8.o n.o 1"),

    ("ex_pensionista_invalidez",
     "E ex-pensionista de invalidez declarado apto para o trabalho.",
     "Arts. 8.o n.o 3 e 32.o: regime e montantes proprios, e o art. 36.o n.o 2 muda a "
     "data de inicio. Nao esta modelado.",
     "8.o n.o 3"),

    ("subsidio_parcial",
     "Trabalha a tempo parcial e quer subsidio de desemprego PARCIAL.",
     "Arts. 27.o, 33.o e 39.o: regime autonomo de calculo. Nao esta modelado.",
     "33.o"),

    ("saida_voluntaria_sem_justa_causa",
     "Pediu a demissao sem justa causa, ou nao pediu a renovacao de um contrato "
     "que dela dependia.",
     "Art. 9.o: o desemprego so e involuntario nos casos do n.o 1. O n.o 6 exclui "
     "expressamente quem nao solicita a renovacao. Sem desemprego involuntario nao ha "
     "direito ao subsidio. ATENCAO: a resolucao com JUSTA CAUSA pelo trabalhador "
     "(art. 9.o n.o 1 al. c) E involuntaria - se for o seu caso, nao marque este facto.",
     "9.o n.o 6"),

    ("despedimento_por_facto_imputavel_sem_accao",
     "Foi despedido por justa causa por facto que lhe e imputavel e NAO intentou "
     "accao judicial contra o empregador.",
     "Art. 9.o n.o 2 al. a): nesse caso a presuncao de desemprego involuntario so opera "
     "se o trabalhador fizer prova da propositura de accao judicial.",
     "9.o n.o 2"),

    ("condicao_de_recursos",
     "Quer saber o SUBSIDIO SOCIAL de desemprego (condicao de recursos).",
     "O art. 24.o n.o 2 fixa o limiar em 80 % do IAS mas remete a capitacao para a "
     "escala de equivalencia da lei da condicao de recursos (DL n.o 70/2010), que NAO "
     "esta capturada neste repositorio. Calcular a capitacao sem essa escala daria um "
     "numero inventado. O limiar por pessoa e indicado abaixo, a titulo indicativo.",
     "24.o n.o 2"),
]

RECUSAS_POR_CHAVE = {r[0]: r for r in RECUSAS}


# ----------------------------------------------------------------------- motor

def analisar(caso, const=None):
    const = const or carregar_constantes()
    recusas, avisos = [], []

    factos = caso.get("factos") or {}
    desconhecidas = sorted(set(factos) - set(RECUSAS_POR_CHAVE))
    if desconhecidas:
        raise ValueError("factos desconhecidos (nao ha porta de recusa definida): %s"
                         % ", ".join(desconhecidas))
    for chave in sorted(factos):
        if factos[chave]:
            r = RECUSAS_POR_CHAVE[chave]
            recusas.append({"chave": r[0], "facto": r[1], "porque": r[2], "artigo": r[3]})

    out = {"algorithm_version": ALGORITHM_VERSION,
           "ano_constantes": const["_meta"]["ano_vigente"],
           "IAS": const["IAS"]["valor"],
           "recusas": recusas,
           "avisos": avisos}

    if recusas:
        out["estado"] = "RECUSA"
        out["o_que_isto_significa"] = (
            "O motor RECUSA calcular este caso. Nao e uma falha: e o motor a reconhecer "
            "que os factos indicados caem fora do regime que tem verificado. Cada recusa "
            "cita o artigo que a obriga. Contacte a Seguranca Social (300 502 502) ou o "
            "seu centro de emprego.")
        if any(r["chave"] == "condicao_de_recursos" for r in recusas):
            out["indicativo_condicao_de_recursos"] = (
                "A titulo meramente indicativo: o art. 24.o n.o 2 fixa o limiar em 80 %% "
                "do IAS, ou seja %.2f EUR por mes de rendimento do agregado - MAS a "
                "capitacao e ponderada por uma escala de equivalencia que este "
                "repositorio nao tem. Nao use este numero como resposta."
                % (0.8 * const["IAS"]["valor"]))
        return _rodape(out)

    # ---- prazo de garantia (art. 22.o n.o 1) --------------------------------
    dias = int(caso["dias_trabalho_24m"])
    cumpre = dias >= 360
    out["prazo_de_garantia"] = {
        "exigido_dias": 360,
        "declarado_dias": dias,
        "cumpre": cumpre,
        "artigo": "22.o n.o 1",
        "nota": "360 dias de trabalho por conta de outrem com registo de remuneracoes "
                "nos 24 meses imediatamente anteriores a data do desemprego.",
    }
    if not cumpre:
        out["estado"] = "NAO_CUMPRE_PRAZO_DE_GARANTIA"
        out["o_que_isto_significa"] = (
            "Com %d dias nos ultimos 24 meses NAO cumpre o prazo de garantia de 360 dias "
            "do art. 22.o n.o 1, pelo que nao ha direito ao subsidio de desemprego. "
            "NAO PARE AQUI: o art. 22.o n.o 2 preve um prazo de garantia de apenas 180 "
            "dias em 12 meses para o SUBSIDIO SOCIAL de desemprego, e o n.o 3 baixa-o "
            "para 120 dias quando o desemprego resulta de caducidade de contrato a termo. "
            "Esses dependem de condicao de recursos (art. 24.o), que este motor nao "
            "calcula. Va a Seguranca Social - pode ter direito a uma prestacao diferente."
            % dias)
        return _rodape(out)

    # ---- montante -----------------------------------------------------------
    m = montante_mensal(float(caso["remuneracao_total_12m"]), const,
                        caso.get("remuneracoes_atingem_rmmg"))
    out["montante"] = m

    # ---- duracao ------------------------------------------------------------
    idade = int(caso["idade"])
    meses = int(caso["meses_com_registo"])
    anos20 = int(caso.get("anos_carreira_ultimos_20") or 0)
    d = duracao(idade, meses, anos20, caso)
    c = d["contagem"]
    base, acresc, alinea, quinq, alm = (d["dias_base"], d["acrescimo_dias"], d["alinea"],
                                        d["quinquenios_contados"], d["alinea_acrescimo"])
    avisos.extend(c["avisos"])
    out["duracao"] = {
        "dias_base": base,
        "artigo_base": "37.o n.o 1 al. %s" % alinea,
        "acrescimo_dias": acresc,
        "artigo_acrescimo": "37.o n.o 2 al. %s" % alm,
        "quinquenios_contados": quinq,
        "dias_total": base + acresc,
        "meses_aproximados": round((base + acresc) / 30.0, 1),
        "regra_art_37_3": c["regra"],
        "meses_contados": c["meses"],
        "anos_contados": c["anos"],
        "passos": c["passos"],
    }

    out["estado"] = "TEM_DIREITO"
    out["o_que_isto_significa"] = (
        "Cumpre o prazo de garantia (%d dias >= 360, art. 22.o n.o 1). Estimativa: ate "
        "%.2f EUR por mes, durante %d dias (%.1f meses) - %d dias de base pelo art. 37.o "
        "n.o 1 al. %s, mais %d dias de acrescimo pelo n.o 2 (%d quinquenios de carreira)."
        % (dias, m["montante_mensal"], base + acresc, (base + acresc) / 30.0,
           base, alinea, acresc, quinq))
    if c["regra"] in ("n3", "n3+n4"):
        out["o_que_isto_significa"] += (
            " Contados so os periodos que o art. 37.o n.o 3%s admite: %d meses, %d anos."
            % (" e o n.o 4" if c["regra"] == "n3+n4" else "", c["meses"], c["anos"]))

    # A frase que nao pode faltar. Ver o docstring do modulo.
    out["este_valor_e_um_limite_superior"] = (
        "IMPORTANTE - %.2f EUR e um LIMITE SUPERIOR, nao uma promessa. O art. 29.o "
        "n.os 2 e 3 limita o subsidio a 75 %% - e nunca mais - do valor LIQUIDO da sua "
        "remuneracao de referencia, e o n.o 4 define liquido como o iliquido menos a "
        "taxa contributiva E A RETENCAO DE IRS. A sua retencao de IRS depende do "
        "escalao, do estado civil, dos dependentes e da regiao: este programa nao a "
        "pergunta e por isso NAO PODE aplicar esse tecto. O valor que a Seguranca "
        "Social apurar pode ser MENOR do que este. Nunca maior. Nao assuma "
        "compromissos financeiros com base neste numero."
        % m["montante_mensal"])

    # O art. 8.o n.o 1 condiciona a titularidade a cessacao "nos termos do artigo
    # 9.o". O motor nao pergunta como o contrato cessou quando e usado pela linha
    # de comandos simples, pelo que estava a AFIRMAR direito sem nunca enunciar a
    # condicao de que ele depende. Passa a enuncia-la.
    out["esta_estimativa_assume"] = (
        "ASSUME desemprego INVOLUNTARIO nos termos do art. 9.o - iniciativa do "
        "empregador, caducidade do contrato, resolucao com JUSTA CAUSA pelo "
        "trabalhador, ou acordo de revogacao. NAO tem direito se: pediu a demissao "
        "sem justa causa; recusou injustificadamente continuar ao servico no termo "
        "do contrato quando isso lhe foi proposto (art. 9.o n.o 3); ou nao pediu a "
        "renovacao de um contrato que dela dependia (art. 9.o n.o 6). Se foi "
        "despedido por facto que lhe e imputavel, a presuncao de involuntariedade so "
        "opera se intentar accao judicial (art. 9.o n.o 2).")

    # O art. 28.o n.o 4 define uma janela precisa. Um utilizador que some "os
    # ultimos 12 meses de vencimento", incluindo uma compensacao por cessacao,
    # sobrestima R e portanto o montante - sem que nada aqui o avisasse.
    out["o_que_conta_para_R"] = (
        "R nao e 'os ultimos 12 meses de vencimento'. O art. 28.o n.o 4 define-o como "
        "o total das remuneracoes registadas nos PRIMEIROS 12 MESES CIVIS que precedem "
        "o 2.o MES ANTERIOR ao do desemprego - ou seja, a janela termina dois meses "
        "antes de ficar desempregado. O n.o 5 so admite subsidios de ferias e de Natal "
        "devidos nesse periodo. Compensacoes por cessacao do contrato NAO entram. Os "
        "seus valores reais estao na Seguranca Social Direta.")

    # O art. 36.o n.o 5 deduz ao periodo de concessao os dias de atraso nas
    # situacoes do art. 72.o n.o 2 (nao capturado). Continua a ser razao para a
    # duracao poder ser menor, com ou sem o art. 37.o n.o 3.
    dur_36_5 = ("O art. 36.o n.o 5 deduz ao periodo de concessao os dias decorridos entre "
                "o termo do prazo e a apresentacao do requerimento ou das provas, nas "
                "situacoes do art. 72.o n.o 2, que este motor nao modela.")
    if c["regra"] == "desconhecido":
        out["a_duracao_tambem_pode_ser_menor"] = (
            "A duracao acima e igualmente um limite superior. NAO declarou se ja recebeu "
            "prestacoes de desemprego antes. Se recebeu, o art. 37.o n.o 3 so conta os "
            "periodos de registo POSTERIORES ao termo dessa concessao, e o periodo real "
            "pode ser MENOR - declare-o (--beneficio-anterior) para o motor o aplicar. "
            + dur_36_5)
    elif c["regra"] == "sem_anterior":
        out["a_duracao_tambem_pode_ser_menor"] = (
            "A duracao acima e igualmente um limite superior. Declarou que nunca recebeu "
            "prestacoes de desemprego, pelo que o art. 37.o n.o 3 nao encurta a contagem. "
            + dur_36_5 + " E os meses e anos sao os que declarou: os reais estao na "
            "Seguranca Social Direta.")
    else:
        out["a_duracao_tambem_pode_ser_menor"] = (
            "Aplicado o art. 37.o n.o 3%s. A duracao pode ainda ser MENOR: %s E pode ser "
            "MAIOR pelo art. 37.o n.o 5, que nao e modelado - o motor mostra a leitura "
            "mais curta que o texto consente, nunca a mais longa."
            % (" e o n.o 4" if c["regra"] == "n3+n4" else "", dur_36_5))

    out["prazos_a_nao_perder"] = (
        "O art. 36.o n.o 1 diz que as prestacoes sao devidas DESDE A DATA DO "
        "REQUERIMENTO - nao desde a data do desemprego. Cada dia que demorar a "
        "requerer e um dia que nao recebe. Inscreva-se no centro de emprego e requeira "
        "assim que puder.")
    return _rodape(out)


def _rodape(out):
    out["nao_e_aconselhamento"] = (
        "Esta estimativa e uma ferramenta de apoio a decisao. Nao e aconselhamento "
        "juridico nem financeiro, e nao vincula a Seguranca Social, que e a unica "
        "entidade que decide. Os factos e os numeros introduzidos sao da "
        "responsabilidade de quem os introduz. Confirme em seg-social.pt ou pelo "
        "300 502 502.")
    out["direccao_do_erro"] = "conservadora_para_o_beneficiario"
    return out


# -------------------------------------------------------------------- render

def _render(out):
    L = []
    marca = {"TEM_DIREITO": "[TEM DIREITO - ESTIMATIVA]",
             "NAO_CUMPRE_PRAZO_DE_GARANTIA": "[NAO CUMPRE O PRAZO DE GARANTIA]",
             "RECUSA": "[RECUSA]"}[out["estado"]]
    L.append(marca)
    L.append("constantes de %s  ·  IAS %.2f EUR" % (out["ano_constantes"], out["IAS"]))
    L.append("")
    if out["recusas"]:
        L.append("RECUSAS")
        for r in out["recusas"]:
            L.append("  - %s" % r["facto"])
            L.append("    %s  [art. %s]" % (r["porque"], r["artigo"]))
        L.append("")
    if "prazo_de_garantia" in out:
        p = out["prazo_de_garantia"]
        L.append("PRAZO DE GARANTIA (art. %s): %d de %d dias -> %s"
                 % (p["artigo"], p["declarado_dias"], p["exigido_dias"],
                    "CUMPRE" if p["cumpre"] else "NAO CUMPRE"))
        L.append("")
    if "montante" in out:
        m = out["montante"]
        L.append("MONTANTE")
        for s in m["passos"]:
            L.append("  . " + s)
        L.append("  => ate %.2f EUR/mes" % m["montante_mensal"])
        L.append("")
        d = out["duracao"]
        L.append("DURACAO")
        for s in d.get("passos", []):
            L.append("  . " + s)
        L.append("  . base:      %3d dias  (art. %s)" % (d["dias_base"], d["artigo_base"]))
        L.append("  . acrescimo: %3d dias  (art. %s, %d quinquenios)"
                 % (d["acrescimo_dias"], d["artigo_acrescimo"], d["quinquenios_contados"]))
        L.append("  => %d dias  (~%.1f meses)" % (d["dias_total"], d["meses_aproximados"]))
        L.append("")
    if out.get("avisos"):
        L.append("AVISOS")
        for a in out["avisos"]:
            L.append("  ! " + a)
        L.append("")
    L.append("O QUE ISTO SIGNIFICA")
    L.append("  " + out["o_que_isto_significa"])
    for k in ("esta_estimativa_assume", "este_valor_e_um_limite_superior",
              "a_duracao_tambem_pode_ser_menor", "o_que_conta_para_R",
              "prazos_a_nao_perder", "indicativo_condicao_de_recursos"):
        if k in out:
            L.append("")
            L.append("  " + out[k])
    L.append("")
    L.append("-" * 72)
    L.append(out["nao_e_aconselhamento"])
    L.append("Comparar contratos, tarifas e alternativas: https://mowei.pt")
    return "\n".join(L)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="aoquetenhodireito - estimativa de subsidio de desemprego (Portugal)")
    p.add_argument("--caso", help="ficheiro JSON com o caso. E a UNICA forma de "
                                  "declarar factos de recusa (ver --recusas); as "
                                  "opcoes soltas abaixo assumem sempre desemprego "
                                  "involuntario nos termos do art. 9.o")
    p.add_argument("--idade", type=int, help="idade a data do desemprego")
    p.add_argument("--dias-trabalho-24m", type=int,
                   help="dias de trabalho por conta de outrem com registo de "
                        "remuneracoes nos 24 meses anteriores (art. 22.o n.o 1: "
                        "precisa de 360)")
    p.add_argument("--meses-com-registo", type=int,
                   help="meses com registo de remuneracoes no periodo anterior ao "
                        "desemprego (art. 37.o n.o 1). E uma grandeza DIFERENTE dos "
                        "dias acima")
    p.add_argument("--remuneracao-total-12m", type=float,
                   help="R do art. 28.o n.o 4: total das remuneracoes dos PRIMEIROS "
                        "12 MESES CIVIS que precedem o 2.o MES ANTERIOR ao do "
                        "desemprego. Inclui ferias e Natal desse periodo (n.o 5); NAO "
                        "inclui compensacoes por cessacao do contrato")
    p.add_argument("--anos-carreira-20", type=int, default=0,
                   help="anos com registo de remuneracoes NOS ULTIMOS 20 ANOS "
                        "(art. 37.o n.o 2). Valores acima de 20 sao truncados a 20: "
                        "o acrescimo maximo sao 4 quinquenios, mesmo com 40 anos de "
                        "carreira")
    p.add_argument("--atinge-rmmg", action="store_true",
                   help="as remuneracoes mensais que serviram de base atingem a RMMG "
                        "(art. 29.o n.o 5: eleva o piso a 1,15 x IAS)")
    p.add_argument("--beneficio-anterior", choices=("sim", "nao"),
                   help="ja recebeu prestacoes de desemprego numa situacao anterior? "
                        "(art. 37.o n.o 3). Omitido = desconhecido: calculo bruto, com o "
                        "aviso de que a duracao pode ser menor. 'sim' exige as duas "
                        "opcoes seguintes")
    p.add_argument("--meses-apos-anterior", type=int,
                   help="meses com registo de remuneracoes POSTERIORES ao termo da "
                        "concessao anterior (art. 37.o n.o 3). Se retomou trabalho antes "
                        "de esgotar essa prestacao, o texto nao diz se o termo e a data em "
                        "que deixou de receber ou o fim do periodo concedido: conte a "
                        "partir da MAIS TARDIA (a leitura mais curta)")
    p.add_argument("--anos-apos-anterior", type=int,
                   help="anos com registo de remuneracoes, nos ultimos 20, POSTERIORES ao "
                        "termo da concessao anterior (art. 37.o n.os 2 e 3)")
    p.add_argument("--retomou-6-meses", choices=("sim", "nao"),
                   help="retomou actividade nos PRIMEIROS SEIS MESES da prestacao anterior? "
                        "(art. 37.o n.o 4)")
    p.add_argument("--meses-considerados-anterior", type=int,
                   help="meses de registo que a prestacao anterior teve em conta (art. 37.o "
                        "n.o 4; estao na decisao de atribuicao dessa prestacao)")
    p.add_argument("--anos-considerados-anterior", type=int,
                   help="anos de carreira que a prestacao anterior teve em conta para o "
                        "acrescimo (art. 37.o n.o 4)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--recusas", action="store_true", help="listar portas de recusa e sair")
    p.add_argument("--tabela", action="store_true", help="imprimir a tabela do art. 37.o")
    args = p.parse_args(argv)

    const = carregar_constantes()

    if args.recusas:
        for chave, facto, porque, artigo in RECUSAS:
            print("%-42s art. %s" % (chave, artigo))
            print("    %s" % facto)
        return 0

    if args.tabela:
        print("Art. 37.o n.o 1 - periodo de concessao (dias)")
        print("%-18s %-22s %6s  %s" % ("idade", "meses com registo", "dias", "alinea"))
        for imin, imax, mmin, mmax, dias, al in TABELA_37:
            fi = "%d-%s" % (imin, imax if imax else "+")
            fm = "%d-%s" % (mmin, mmax if mmax else "+")
            print("%-18s %-22s %6d  %s" % (fi, fm, dias, al))
        print()
        print("Art. 37.o n.o 2 - acrescimo por cada 5 anos de carreira nos ultimos 20")
        for imin, imax, dias, al in MAJORACAO_37_2:
            print("  idade %-10s +%d dias  (al. %s)"
                  % ("%d-%s" % (imin, imax if imax else "+"), dias, al))
        return 0

    if args.caso:
        with open(args.caso, encoding="utf-8") as fh:
            caso = json.load(fh)
    elif None not in (args.idade, args.dias_trabalho_24m, args.meses_com_registo,
                      args.remuneracao_total_12m):
        caso = {"idade": args.idade,
                "dias_trabalho_24m": args.dias_trabalho_24m,
                "meses_com_registo": args.meses_com_registo,
                "remuneracao_total_12m": args.remuneracao_total_12m,
                "anos_carreira_ultimos_20": args.anos_carreira_20,
                "remuneracoes_atingem_rmmg": True if args.atinge_rmmg else None}
        sn = {"sim": True, "nao": False, None: None}
        for chave, v in (("beneficio_anterior", sn[args.beneficio_anterior]),
                         ("meses_com_registo_apos_anterior", args.meses_apos_anterior),
                         ("anos_carreira_apos_anterior", args.anos_apos_anterior),
                         ("retomou_nos_primeiros_6_meses", sn[args.retomou_6_meses]),
                         ("meses_considerados_no_anterior", args.meses_considerados_anterior),
                         ("anos_considerados_no_anterior", args.anos_considerados_anterior)):
            if v is not None:
                caso[chave] = v
    else:
        p.error("indique --caso FICHEIRO ou --idade --dias-trabalho-24m "
                "--meses-com-registo --remuneracao-total-12m")

    try:
        out = analisar(caso, const)
    except ValueError as e:
        p.error(str(e))
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else _render(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
