<p align="center">
  <img src="docs/images/aoquetenhodireito-wide-light-1k.svg#gh-light-mode-only" alt="aoquetenhodireito" width="640">
  <img src="docs/images/aoquetenhodireito-wide-dark-1k.svg#gh-dark-mode-only" alt="aoquetenhodireito" width="640">
</p>

<p align="center">
  <b>Ficou sem emprego. Tem direito? Quanto? Até quando?</b><br>
  Subsídio de desemprego calculado <i>offline</i> a partir da versão <b>consolidada</b>
  do DL 220/2006, com o artigo por trás de cada número — e um limite superior honesto
  em vez de uma mentira confiante.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg" alt="MIT">
  <img src="https://img.shields.io/badge/depend%C3%AAncias-0-brightgreen.svg" alt="zero dependências">
  <img src="https://img.shields.io/badge/rede-nenhuma-brightgreen.svg" alt="sem rede">
  <img src="https://img.shields.io/badge/verifica%C3%A7%C3%B5es-37-brightgreen.svg" alt="37 verificações">
</p>

<p align="center">
  <a href="README.md"><b>🇬🇧 Read in English</b></a> ·
  <a href="SKILL.md">Skill</a> ·
  <a href="AVISO-FORMAL.md">Aviso formal</a> ·
  <a href="https://mowei.pt">mowei.pt</a>
</p>

---

> **Não é aconselhamento, e não vincula ninguém.** Quem decide é a Segurança Social.
> Ver [`AVISO-FORMAL.md`](AVISO-FORMAL.md).

## Três perguntas, hoje — não daqui a três semanas

Foi dispensado na sexta. Na segunda precisa de saber: **tenho direito? quanto? até
quando?** A Segurança Social responde — depois de um requerimento e de uma espera.
A renda não espera.

```bash
git clone https://github.com/yeer0s/aoquetenhodireito.git && cd aoquetenhodireito
python scripts/desemprego.py --idade 35 --dias-trabalho-24m 720 \
       --meses-com-registo 24 --remuneracao-total-12m 16800 \
       --anos-carreira-20 12 --atinge-rmmg
```

```bash
python scripts/desemprego.py --tabela    # a tabela do art. 37.º, tal como está na lei
python scripts/desemprego.py --recusas   # o que recusa calcular, e ao abrigo de quê
```

Sem instalação. Sem dependências. Python 3.8+.

## O número que esta ferramenta NÃO consegue calcular — dito à cabeça

O art. 29.º n.os 2 e 3 limita o subsídio a **75 %, e nunca mais**, do valor
**líquido** da remuneração de referência. O n.º 4 define líquido como o ilíquido
menos a taxa contributiva **e a retenção de IRS**.

A sua retenção depende do escalão, do estado civil, dos dependentes e da região.
Um programa offline que não pergunta a situação fiscal **não pode** aplicar esse
tecto sem inventar um número.

Por isso o valor é um **limite superior**. O real pode ser **menor**. Nunca maior.
Está em todas as saídas com direito — e há uma verificação que falha se alguma o
omitir.

Uma ferramenta que lhe desse 910 € com ar de certeza quando a verdade eram 700 €
faria mais estragos do que uma que lhe entornasse os dados, porque já tinha
assinado o contrato de arrendamento.

## Direcção do erro — a inversa do projecto irmão

No [`porreceber`](https://github.com/yeer0s/porreceber) o erro perigoso é declarar
morta uma dívida viva. **Aqui é sobrestimar um apoio.**

Perante dúvida, este motor devolve o valor **mais baixo** e a duração **mais
curta** que a lei consinta. E não é uma afirmação de README: há uma verificação que
testa **comportamento** — mais salário nunca pode dar menos subsídio, mais carreira
nunca pode dar menos dias.

## Não é um beco sem saída

Falhar o prazo de garantia de 360 dias (art. 22.º n.º 1) **não** encerra o
assunto. O n.º 2 abre o **subsídio social** com 180 dias em 12 meses, e o n.º 3
baixa-o para **120 dias** quando o desemprego vem da caducidade de um contrato a
termo. Quem parar de ler no «não tem direito» perde uma prestação a que pode ter
direito — e há uma verificação que falha se essa saída não o disser.

## O que se recusa a calcular

| Facto | Porquê | Artigo |
|---|---|---|
| trabalhador independente | o diploma cobre trabalhadores **por conta de outrem** | 8.º n.º 1 |
| não reside em Portugal | a titularidade exige residência em território nacional | 8.º n.º 1 |
| ex-pensionista de invalidez | montantes e data de início próprios | 8.º n.º 3 |
| subsídio parcial | regime autónomo de cálculo | 33.º |
| saída voluntária sem justa causa | sem desemprego involuntário não há direito — **mas a resolução com justa causa É involuntária** | 9.º n.º 6 |
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

- **Duas implementações independentes.** O motor faz `(R/360) × 0,65 × 30`; o
  oráculo faz `(R/12) × 0,65` e **nunca divide por 360**. A duração é resolvida
  por procura em fronteiras ordenadas em vez de varrimento de tabela.
  *Limite honesto:* são algebricamente equivalentes, por isso apanham erros de
  transcrição e de arredondamento, **não** erros de leitura da lei.
- **Uma verificação que fica vermelha sozinha a 1 de Janeiro.** O IAS e a RMMG
  mudam todos os anos; o gate falha quando o ano das constantes fica para trás.
- **A majoração morta está registada como morta.** As majorações de 10 % das Leis
  66-B/2012 e 83-C/2013 aparecem como *Notas* ao art. 28.º na versão consolidada do
  DR e são fáceis de confundir com direito vigente. Repô-las inflacionaria tudo em
  10 % — é esse o mutante do `--mutation-test`.
- **Invariantes de produto**: rotular sempre o valor como limite superior — **e a
  duração também**; nunca prometer um montante; declarar sempre que a estimativa
  assume desemprego involuntário nos termos do art. 9.º; explicar sempre a janela
  de R do art. 28.º n.º 4; encaminhar sempre para o subsídio social quem falha o
  prazo; avisar sempre que o art. 36.º n.º 1 conta desde o **requerimento**;
  declarar uma prestação anterior **nunca alonga** a duração, e encurta-a quando o
  art. 37.º n.º 3 o manda. Cada um tem um mutante que prova que a verificação morde.

## Totalmente offline — por estrutura, não por promessa

Zero dependências, zero chamadas de rede, zero telemetria. Quem usa isto está a
introduzir o seu histórico salarial enquanto está desempregado — um perfil de
vulnerabilidade financeira. Nada disso sai da máquina. O `offline_audit.py` prova que não há caminho de
importação nem de chamada para a rede, e o CI volta a correr **todo o gate com a
camada de sockets desligada** — a prova dinâmica, não só a estática. Com
precisão: a auditoria da AST não é uma sandbox e não travaria um contribuidor
malicioso determinado; o trabalho de CI e a leitura de cada PR são os controlos
reais. Ver [`SECURITY.md`](SECURITY.md).

## Fontes

- **DL n.º 220/2006, versão CONSOLIDADA** — arts. 8.º, 9.º, 22.º, 24.º, 28.º,
  29.º, 30.º, 35.º, 36.º, 37.º, 38.º, capturados verbatim em
  [`assets/law/`](assets/law/). Fonte: **Diário da República**, a fonte oficial —
  não uma compilação privada.
- **IAS 2026: 537,13 €** — Portaria n.º 480-A/2025/1, de 30 de dezembro.
- **RMMG 2026: 920,00 €** — Decreto-Lei n.º 139/2025, de 29 de dezembro.

A versão consolidada não é um detalhe: este diploma foi alterado mais de uma dezena
de vezes, e os prazos de garantia, os montantes e os períodos de concessão foram
todos mexidos.

## Relacionados

- **[porreceber](https://github.com/yeer0s/porreceber)** — aquela dívida antiga ainda pode ser cobrada?
- **[AoCentimo](https://github.com/yeer0s/AoCentimo)** — motor de IRS português
- **[recibosegarantia](https://github.com/yeer0s/recibosegarantia)** — recibos, QR e-Fatura, garantias

## Licença

MIT — ver [`LICENSE`](LICENSE). Sem modificações, sem restrições adicionais.

## Apoiar

Livre e MIT, para sempre. Se ajudou numa semana má:

☕ [Buy me a coffee](https://buymeacoffee.com/letsmoweis) · [Ko-fi](https://ko-fi.com/letsmowei)

Construído a par do **[mowei.pt](https://mowei.pt)** — comparação de energia,
telecomunicações, seguros, banca e mais.
