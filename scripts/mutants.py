#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutantes dirigidos aos INVARIANTES DE PRODUTO.

O `--self-test` do sweep corrompe a aritmetica, e a aritmetica e a parte facil.
Os checks que realmente protegem quem usa isto - rotular o valor como limite
superior, nunca prometer um montante, encaminhar quem falha o prazo para o
subsidio social, avisar que o prazo conta desde o requerimento - nunca foram
vistos a ficar vermelhos.

Um check que nunca ficou vermelho nao esta testado: esta observado.

Cada mutante desliga UM comportamento e nomeia o check que TEM de o apanhar.
Se o check sobreviver ao mutante, o check nao vale nada.
"""

import contextlib
import io
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import desemprego  # noqa: E402
import sweep       # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _correr():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = sweep.correr()
    return {n: ok for n, ok, _ in res}


def _patch_analisar(transform):
    orig = desemprego.analisar

    def patched(*a, **k):
        return transform(orig(*a, **k))
    desemprego.analisar = patched
    return lambda: setattr(desemprego, "analisar", orig)


def m_sem_rotulo_limite_superior():
    """Deixa de dizer que o valor e um limite superior (art. 29.º n.os 2-3)."""
    def t(out):
        out.pop("este_valor_e_um_limite_superior", None)
        return out
    return _patch_analisar(t)


def m_promete_o_valor():
    """Passa a prometer o montante em vez de o estimar."""
    def t(out):
        if out["estado"] == "TEM_DIREITO":
            out["o_que_isto_significa"] = "Vai receber %.2f EUR por mes." % \
                out["montante"]["montante_mensal"]
        return out
    return _patch_analisar(t)


def m_beco_sem_saida():
    """Quem falha o prazo de garantia deixa de ser encaminhado para o art. 22.º n.os 2-3."""
    def t(out):
        if out["estado"] == "NAO_CUMPRE_PRAZO_DE_GARANTIA":
            out["o_que_isto_significa"] = "Nao cumpre o prazo de garantia de 360 dias."
        return out
    return _patch_analisar(t)


def m_sem_aviso_do_requerimento():
    """Deixa de avisar que o art. 36.º n.º 1 conta desde o REQUERIMENTO."""
    def t(out):
        out.pop("prazos_a_nao_perder", None)
        return out
    return _patch_analisar(t)


def m_mais_salario_menos_subsidio():
    """Quebra a monotonia: acima de certo ponto, mais salario da menos subsidio."""
    orig = desemprego.montante_mensal

    def patched(R, c, rmmg=None):
        out = orig(R, c, rmmg)
        if R > 20000:
            out["montante_mensal"] = round(out["montante_mensal"] * 0.5, 2)
        return out
    desemprego.montante_mensal = patched
    return lambda: setattr(desemprego, "montante_mensal", orig)


def m_quinquenios_arredondam():
    """Arredonda os quinquenios em vez de os truncar: 9 anos passariam a dar 2."""
    orig = desemprego.periodo_concessao

    def patched(idade, meses, anos20=0):
        base, acr, al, q, alm = orig(idade, meses, anos20)
        passo = {25: 30, 35: 30, 45: 45, 55: 60}
        p = 30 if idade < 40 else (45 if idade < 50 else 60)
        q2 = int(round(float(anos20) / 5.0))
        return base, p * q2, al, q2, alm
    desemprego.periodo_concessao = patched
    return lambda: setattr(desemprego, "periodo_concessao", orig)


def m_constantes_sem_fonte():
    """Uma constante anual sem o diploma que a fixa e um numero inventado."""
    orig = desemprego.carregar_constantes

    def patched(*a, **k):
        c = orig(*a, **k)
        c["IAS"]["fonte"] = ""
        return c
    desemprego.carregar_constantes = patched
    return lambda: setattr(desemprego, "carregar_constantes", orig)


def m_derivados_desalinhados():
    """Os derivados deixam de bater certo com o IAS - o espelho mente."""
    orig = desemprego.carregar_constantes

    def patched(*a, **k):
        c = orig(*a, **k)
        c["derivados"]["tecto_mensal_2_5_IAS"] = 9999.99
        return c
    desemprego.carregar_constantes = patched
    return lambda: setattr(desemprego, "carregar_constantes", orig)


def m_facto_desconhecido_silencioso():
    """Ignora factos de recusa que nao reconhece, em vez de rebentar."""
    orig = desemprego.analisar

    def patched(caso, *a, **k):
        caso = dict(caso)
        caso["factos"] = {k2: v for k2, v in (caso.get("factos") or {}).items()
                          if k2 in desemprego.RECUSAS_POR_CHAVE}
        return orig(caso, *a, **k)
    desemprego.analisar = patched
    return lambda: setattr(desemprego, "analisar", orig)


def m_quinquenios_sem_tecto():
    """Remove o tecto de 20 anos do art. 37.º n.º 2 — o defeito real de 2026-07-27.

    Uma carreira de 30 anos voltava a dar 6 quinquénios e 900 dias onde a lei dá
    780. Note-se que ambos os caminhos tinham a omissão, pelo que o crosscheck
    ficava verde: este mutante ataca o que só um caso dourado e um check dedicado
    conseguem apanhar.
    """
    orig = desemprego.periodo_concessao

    def patched(idade, meses, anos20=0):
        base, acr, al, q, alm = orig(idade, meses, anos20)
        p = 30 if idade < 40 else (45 if idade < 50 else 60)
        q2 = int(anos20) // 5          # sem o min(.., 20)
        return base, p * q2, al, q2, alm
    desemprego.periodo_concessao = patched
    return lambda: setattr(desemprego, "periodo_concessao", orig)


def m_sem_assuncao_involuntariedade():
    """Deixa de enunciar que a estimativa assume desemprego involuntário (art. 9.º)."""
    def t(out):
        out.pop("esta_estimativa_assume", None)
        return out
    return _patch_analisar(t)


def m_sem_caveat_da_duracao():
    """Deixa de dizer que a duração também é um limite superior (art. 37.º n.os 3-5)."""
    def t(out):
        out.pop("a_duracao_tambem_pode_ser_menor", None)
        return out
    return _patch_analisar(t)


def m_sem_janela_de_R():
    """Deixa de explicar a janela de R do art. 28.º n.º 4."""
    def t(out):
        out.pop("o_que_conta_para_R", None)
        return out
    return _patch_analisar(t)


MUTANTES = [
    ("quinquenios-sem-tecto", m_quinquenios_sem_tecto,
     "acrescimo-limitado-a-4-quinquenios"),
    ("sem-assuncao-involuntariedade", m_sem_assuncao_involuntariedade,
     "declara-a-assuncao-de-involuntariedade"),
    ("sem-caveat-da-duracao", m_sem_caveat_da_duracao,
     "duracao-tambem-rotulada-como-limite-superior"),
    ("sem-janela-de-R", m_sem_janela_de_R, "explica-a-janela-de-R"),
    ("sem-rotulo-limite-superior", m_sem_rotulo_limite_superior,
     "valor-sempre-rotulado-como-limite-superior"),
    ("promete-o-valor", m_promete_o_valor, "nunca-promete-um-valor"),
    ("beco-sem-saida", m_beco_sem_saida, "falhar-o-prazo-encaminha-para-o-social"),
    ("sem-aviso-do-requerimento", m_sem_aviso_do_requerimento,
     "avisa-que-conta-desde-o-requerimento"),
    ("mais-salario-menos-subsidio", m_mais_salario_menos_subsidio,
     "monotonia-salario-e-carreira"),
    ("quinquenios-arredondam", m_quinquenios_arredondam, "golden-duracao"),
    ("constantes-sem-fonte", m_constantes_sem_fonte, "constantes-tem-fonte"),
    ("derivados-desalinhados", m_derivados_desalinhados,
     "derivados-batem-certo-com-IAS-e-RMMG"),
    ("facto-desconhecido-silencioso", m_facto_desconhecido_silencioso,
     "facto-desconhecido-rebenta"),
]


def main():
    base = _correr()
    vivos = [n for n, ok in base.items() if not ok]
    if vivos:
        print("ABORTADO: o gate ja esta vermelho: %s" % vivos)
        return 1

    # Um alvo que ja nao existe no sweep tornaria o mutante num SOBREVIVENTE mudo:
    # `res.get(alvo)` devolveria None e `None is False` e falso, pelo que renomear
    # um check desarmaria silenciosamente o mutante que o protege. Aconteceu no
    # projecto irmao. Alvo desconhecido passa a ser erro, nao sobrevivencia.
    fantasmas = [(n, alvo) for n, _, alvo in MUTANTES if alvo not in base]
    if fantasmas:
        for n, alvo in fantasmas:
            print("ERRO: o mutante '%s' aponta para '%s', que nao existe no sweep. "
                  "Foi renomeado? Este mutante nao estava a testar nada." % (n, alvo))
        return 1

    print("%-32s %-44s %s" % ("MUTANTE", "CHECK QUE O DEVE APANHAR", "RESULTADO"))
    print("-" * 94)
    sobreviventes = []
    for nome, aplicar, alvo in MUTANTES:
        restaurar = aplicar()
        try:
            res = _correr()
        finally:
            restaurar()
        apanhado = res.get(alvo) is False
        print("%-32s %-44s %s" % (nome, alvo, "MORTO (bom)" if apanhado else "SOBREVIVEU"))
        if not apanhado:
            sobreviventes.append((nome, alvo))

    if any(not ok for ok in _correr().values()):
        print("\nFALHA: os mutantes nao foram totalmente revertidos")
        return 1

    print()
    if sobreviventes:
        for nome, alvo in sobreviventes:
            print("SOBREVIVENTE: '%s' nao foi apanhado por '%s' - o check nao protege nada"
                  % (nome, alvo))
        return 1
    print("%d/%d mutantes mortos - todos os invariantes de produto estao mesmo a guardar"
          % (len(MUTANTES), len(MUTANTES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
