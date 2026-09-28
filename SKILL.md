---
name: aoquetenhodireito
description: Use when someone in Portugal has lost their job and needs to know whether they qualify for subsídio de desemprego, roughly how much, and for how many days — with the article behind every number. Computes offline from the consolidated DL 220/2006; refuses the cases it cannot model rather than guessing.
license: MIT
---

# aoquetenhodireito — subsídio de desemprego em Portugal

> **Isto não é aconselhamento jurídico nem financeiro.** É uma ferramenta de apoio
> à decisão e **não vincula a Segurança Social**, que é quem decide.
> Leia o `AVISO-FORMAL.md`.

## O problema que resolve

Quem acabou de perder o emprego precisa de saber três coisas *hoje*, não daqui a
três semanas: **tenho direito? quanto? até quando?** A Segurança Social responde
— mas depois de um requerimento e de uma espera, e entretanto há rendas.

Este motor responde às três a partir do texto consolidado do DL 220/2006, citando
o artigo de cada número, e corre inteiramente na máquina de quem pergunta.

```bash
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

```bash
python scripts/desemprego.py --tabela    # a tabela do art. 37.º, tal como está na lei
python scripts/desemprego.py --recusas   # o que se recusa a calcular, e ao abrigo de quê
```

## O número que este motor NÃO consegue calcular — dito à cabeça

O art. 29.º n.os 2 e 3 limita o subsídio a **75 %, e nunca mais**, do valor
**líquido** da remuneração de referência. E o n.º 4 define líquido como o ilíquido
menos a taxa contributiva **e a taxa de retenção do IRS**.

A retenção de IRS depende do escalão, do estado civil, dos dependentes e da
região. Um programa offline que não pergunta a situação fiscal **não pode**
aplicar este tecto sem inventar um número.

Por isso o valor devolvido é um **limite superior**. O valor real pode ser
**menor**. Nunca maior. Isto aparece em **todas** as saídas com direito — há uma
verificação que falha se alguma saída o omitir.

## Direcção do erro — e porque é a inversa do projecto irmão

No [`porreceber`](https://github.com/yeer0s/porreceber) o erro perigoso é dizer
que uma dívida está morta. **Aqui é sobrestimar um apoio**: quem conta com 900 €
e recebe 700 € já assinou a renda.

Perante dúvida, este motor devolve o valor **mais baixo** e a duração **mais
curta** que a lei consinta. E não é uma declaração: há uma verificação que testa
**comportamento** — mais salário nunca pode dar menos subsídio, mais carreira
nunca pode dar menos dias.

## Não é um beco sem saída

Falhar o prazo de garantia dos 360 dias (art. 22.º n.º 1) **não** encerra o
assunto: o n.º 2 abre o **subsídio social** com 180 dias em 12 meses, e o n.º 3
baixa-o para **120 dias** quando o desemprego vem da caducidade de um contrato a
termo. Quem parar de ler no "não tem direito" perde uma prestação a que pode ter
direito — e há uma verificação que falha se essa saída não encaminhar.

## Já recebeu subsídio antes? Diga-o

O art. 37.º n.º 3 manda contar, para a duração, só o registo de remunerações
**posterior ao termo** da concessão anterior. Quem já recebeu subsídio e não o
declara recebe o cálculo bruto — o de sempre — com o aviso de que a duração real
pode ser **menor**. Quem o declara tem de dizer quanto registo houve depois:

```bash
python scripts/desemprego.py --idade 35 --dias-trabalho-24m 500        --meses-com-registo 60 --remuneracao-total-12m 12000 --anos-carreira-20 12        --beneficio-anterior sim --meses-apos-anterior 18 --anos-apos-anterior 1
#   => 330 dias, onde a contagem bruta dava 480
```

Se retomou trabalho nos **primeiros seis meses** da prestação anterior, o n.º 4
soma o período que ela considerou (`--retomou-6-meses sim` e as duas contagens
dessa prestação). Declarar sem os números **rebenta** — cair em silêncio na
contagem bruta seria usar exactamente a contagem que o n.º 3 proíbe.

## O que se recusa a calcular

| Facto | Porquê | Artigo |
|---|---|---|
| trabalhador independente | o diploma cobre trabalhadores **por conta de outrem** | 8.º n.º 1 |
| não reside em Portugal | a titularidade exige residência em território nacional | 8.º n.º 1 |
| ex-pensionista de invalidez | montantes e data de início próprios | 8.º n.º 3 |
| subsídio parcial | regime autónomo de cálculo | 33.º |
| saída voluntária sem justa causa | sem desemprego involuntário não há direito — **mas a resolução com justa causa pelo trabalhador É involuntária** | 9.º n.º 6 |
| despedimento imputável sem acção judicial | a presunção só opera com prova da acção | 9.º n.º 2 |
| subsídio **social** (condição de recursos) | a escala de equivalência do DL 70/2010 não está capturada | 24.º n.º 2 |

Uma ferramenta que responde a tudo está a mentir sobre alguma coisa.

## Como se sabe que está certo

Não por a suite estar verde. Por ela **saber ficar vermelha**:

```bash
python scripts/oracle.py --crosscheck      # 108960 combinações, dois caminhos independentes
python scripts/oracle.py --mutation-test   # repõe a majoração morta de 2012/13 e exige vermelho
python scripts/oracle.py --blind-spots     # o que este motor NÃO cobre
python scripts/sweep.py --self-test        # prova que o gate sabe falhar e voltar a passar
python scripts/mutants.py                  # mutantes contra os invariantes de produto
python scripts/sweep.py                    # 37 verificações
python scripts/offline_audit.py            # prova estática: sem caminho de importação para a rede
```

- **Dois caminhos independentes.** O motor faz `(R/360) × 0,65 × 30`; o oráculo faz
  `(R/12) × 0,65` e **nunca divide por 360**. A duração é resolvida por procura em
  fronteiras ordenadas em vez de varrimento de tabela.
  O art. 37.º n.os 3–4 é lido pelo oráculo como um conjunto de **períodos
  admitidos** que se somam, e não como ajustes a um número.
  *Limite honesto:* são algebricamente equivalentes, por isso apanham erros de
  transcrição e de arredondamento, **não** erros de leitura da lei. Para esses
  servem a captura verbatim e a revisão adversarial.
- **Uma verificação que fica vermelha sozinha a 1 de Janeiro.** O IAS e a RMMG
  mudam todos os anos; o gate falha quando o ano das constantes fica para trás do
  ano do sistema. Ninguém tem de se lembrar.
- **A majoração morta está registada como morta.** As majorações de 10 % das Leis
  66-B/2012 e 83-C/2013 aparecem como *Notas* ao art. 28.º na versão consolidada
  do DR e são fáceis de confundir com direito vigente. Repô-las inflacionaria tudo
  em 10 % — é exactamente esse o mutante do `--mutation-test`.
- **Invariantes de produto**, não só aritmética: o valor é sempre rotulado como
  limite superior — **e a duração também**; nunca se promete um valor; declara-se
  sempre que a estimativa **assume desemprego involuntário** nos termos do art.
  9.º; explica-se sempre a janela de R do art. 28.º n.º 4; falhar o prazo
  encaminha para o subsídio social; avisa-se sempre que o art. 36.º n.º 1 conta
  desde o **requerimento**, não desde o desemprego; declarar uma prestação
  anterior **nunca alonga** a duração face ao cálculo bruto, e **encurta-a** quando
  o art. 37.º n.º 3 o manda. Cada um tem um mutante em
  `scripts/mutants.py` que prova que a verificação morde.

## Offline

Sem dependências, sem rede, sem telemetria. Quem usa isto está desempregado e a
introduzir salário, idade e carreira contributiva — um perfil de vulnerabilidade
financeira. Nada disso sai da máquina. O `offline_audit.py` prova, a partir da
AST, que não há caminho de importação nem de chamada para a rede, e o CI volta a
correr todo o gate com a camada de sockets desligada. Dito com precisão: a
auditoria estática **não é uma sandbox** e não travaria um contribuidor malicioso
determinado — ver `SECURITY.md`.

## Fontes

- **DL n.º 220/2006, versão CONSOLIDADA** — arts. 8.º, 9.º, 22.º, 24.º, 28.º,
  29.º, 30.º, 35.º, 36.º, 37.º, 38.º, capturados verbatim em `assets/law/`.
  Fonte: **Diário da República** (`legislacao-consolidada/decreto-lei/2006-34533075`).
- **IAS 2026: 537,13 €** — Portaria n.º 480-A/2025/1, de 30 de dezembro.
- **RMMG 2026: 920,00 €** — Decreto-Lei n.º 139/2025, de 29 de dezembro.

A versão consolidada não é um detalhe: este diploma foi alterado mais de uma
dezena de vezes, e os prazos de garantia, os montantes e os períodos de concessão
foram todos mexidos.

---

## Changelog

### v1.1.0 — 2026-09-28

**O limite declarado que se fechou: art. 37.º n.os 3–4.** Até aqui o motor contava
todo o registo de remunerações para a duração, e dizia — honestamente — que quem
já recebeu subsídio podia ter uma duração menor. «Pode ser menor» não é um número.
A pessoa do caso `sd-21` (35 anos, 60 meses de registo, mas só 18 depois do termo
da prestação anterior) lia **480 dias**; a lei dá-lhe **330**. Cinco meses de
rendimento que não existem — exactamente a direcção de erro que este repositório
diz ser a perigosa.

**O que muda, e o que não muda:**

- O n.º 3 é aplicado quando o utilizador declara uma prestação anterior
  (`beneficio_anterior`) e o registo **posterior ao termo** dela, em meses (n.º 1)
  e em anos (n.º 2).
- O n.º 4 soma o período que a prestação anterior considerou, se a pessoa retomou
  actividade nos primeiros seis meses dela.
- **Sem o facto, o número é o de sempre.** A ausência nunca torna a resposta mais
  generosa do que a v1.0.0 — e há uma verificação que o exige, e que exige também
  que a saída nomeie o n.º 3 e diga como o declarar.
- Declarar a prestação sem os números **rebenta**. Cair na contagem bruta seria
  usar, em silêncio, a contagem que o n.º 3 proíbe.

**Onde o texto capturado não chega, e o que se fez em vez de adivinhar:**

- O n.º 4 não diz se a janela de 20 anos do n.º 2 se aplica ao período somado.
  O motor nunca conta mais do que o total que o utilizador declarou — a leitura
  mais curta. O caso `sd-22` mostra a diferença: 480 dias em vez de 510.
- O n.º 3 não diz se o «termo» de uma prestação interrompida por retoma é o fim do
  pagamento ou o fim do período concedido. A ajuda da opção manda contar a partir
  do **mais tardio**.
- O **n.º 5** (acréscimos não gozados) não diz como dias não gozados se convertem
  em períodos de registo. **Não é modelado.** Só pode alongar — o erro fica do lado
  seguro, e a saída di-lo.
- O art. 22.º n.º 1 capturado não diz se os dias já tidos em conta numa prestação
  anterior contam de novo para o prazo de garantia. A saída avisa; não decide.

**Como se sabe que morde:** 6 casos dourados novos, cada um com a aritmética à mão
na nota; 4 verificações novas, todas de comportamento; 4 mutantes novos, um por
verificação; e o crosscheck passa de 4704 para 108960 combinações, com o histórico
de prestações a correr contra um oráculo que lê o artigo como períodos admitidos.
Reverter o n.º 3 no motor põe o crosscheck, os casos dourados e a verificação
dedicada a vermelho ao mesmo tempo.

**Uma contagem que estava errada:** a v1.0.0 dizia «23 casos dourados»; eram 24.
Nenhuma verificação lia esse número. Agora são 30.

**Estado:** 30 casos dourados, 37 verificações, 17 mutantes, 108960 combinações.

**Limites que continuam declarados:** o tecto do art. 29.º n.os 2–3; o art. 37.º
n.º 5; o art. 36.º n.º 5 (dias deduzidos por requerimento fora de prazo, via art.
72.º n.º 2, não capturado); o subsídio social; nenhum caso dourado vem de uma
decisão real.

### v1.0.0 — 2026-07-27

Versão inicial, publicada **depois** de uma revisão adversarial que a corrigiu.

**O defeito que importa, e o que ele prova.** O art. 37.º n.º 2 dá um acréscimo
«por cada cinco anos com registo de remunerações **nos últimos 20 anos**» — logo
o máximo são **4 quinquénios**. Nenhum dos dois caminhos aplicava esse tecto: uma
carreira de 30 anos rendia 6 quinquénios, e o motor prometia **900 dias onde a lei
dá 780**. Quatro meses de rendimento que não existem, ao utilizador *típico* da
faixa dos 50+ — que responde «30» à pergunta «quantos anos de carreira», porque a
opção não tinha sequer texto de ajuda.

O que torna este caso instrutivo é que **o oráculo tinha a mesma omissão**. O
crosscheck de 4704 combinações ficou verde do princípio ao fim. É exactamente a
falha correlacionada que o `oracle.py` declara como limite dos dois caminhos:
caminhos independentes apanham divergências, nunca uma leitura errada partilhada.
A declaração estava certa; o código é que não estava. Agora há tecto nos dois
ficheiros, três casos dourados (19/20/30 anos) e uma verificação dedicada.

**Mais três correcções:**

- A saída afirmava direito sem nunca enunciar a condição de que ele depende. O
  art. 8.º n.º 1 exige cessação «nos termos do artigo 9.º», e a linha de comandos
  simples não consegue exprimir facto de recusa nenhum — logo o *quickstart* do
  README devolvia `TEM DIREITO` a quem se tivesse demitido. Passa a declarar a
  assunção, incluindo o art. 9.º n.º 3 (recusa injustificada de continuar ao
  serviço), que não tinha porta nenhuma.
- A janela de R do art. 28.º n.º 4 — os *primeiros 12 meses civis que precedem o
  2.º mês anterior* — não aparecia em lado nenhum fora de `assets/law/`. Quem
  somasse «os últimos 12 meses de vencimento» com uma compensação por cessação
  sobrestimava R e o montante.
- O rótulo de limite superior cobria só o **montante**. A **duração** também pode
  ser menor (art. 37.º n.os 3–5, não modelado) e isso estava nos documentos mas
  ausente da saída que uma pessoa lê.

**Duas verificações eram quase tautológicas** e foram substituídas: `"28" in
SKILL.md` passava com qualquer preço que contivesse 28. E sete das doze células da
tabela do art. 37.º não tinham caso dourado — estavam protegidas apenas pela
transcrição duplicada, o mesmo mecanismo que acabara de falhar em silêncio. Agora
as doze estão pinadas.

**Estado final:**

- Prazo de garantia (art. 22.º n.º 1), montante (arts. 28.º e 29.º) e período de
  concessão com majoração por carreira limitada a 4 quinquénios (art. 37.º n.os 1 e 2).
- 7 portas de recusa, todas fundamentadas em artigo.
- 23 casos dourados derivados à mão do texto legal, incluindo as fronteiras de
  idade (29/30), do prazo de garantia (359/360), a truncatura dos quinquénios
  (9→1), o tecto dos 20 anos (19/20/30) e as doze células da tabela.
- 33 verificações e 13 mutantes.
- Oráculo independente por via mensal + mutation test que repõe a majoração morta.
- 13 mutantes contra os invariantes de produto — incluindo um que remove o tecto
  dos 20 anos e tem de ficar vermelho.
- 33 verificações, incluindo a que falha na viragem do ano e uma que falha se este
  ficheiro desactualizar a contagem.

**Limites honestos desta versão:**

- O tecto do art. 29.º n.os 2–3 **não é calculado** — depende da retenção de IRS.
  O valor é um limite superior.
- O art. 37.º n.os 3–5 (períodos já usados num desemprego anterior, retoma de
  trabalho nos primeiros seis meses) **não está modelado**: quem já recebeu
  subsídio antes pode ter uma duração **menor** do que a calculada.
  *(Os n.os 3 e 4 passaram a ser modelados na v1.1.0; o n.º 5 continua fora.)*
- Nenhum caso dourado vem de uma decisão real da Segurança Social.
- O subsídio social de desemprego é porta de recusa enquanto o DL 70/2010 não
  estiver capturado.

---

🔗 Comparar contratos, tarifas e alternativas: **[mowei.pt](https://mowei.pt)**
☕ [Buy me a coffee](https://buymeacoffee.com/letsmoweis) · [Ko-fi](https://ko-fi.com/letsmowei)
