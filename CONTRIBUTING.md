# Contribuir · Contributing

Obrigado. Este repositório calcula números com que pessoas desempregadas fazem
contas à vida, por isso as regras são mais apertadas do que o normal.

*Thank you. This repository computes figures that unemployed people budget on, so
the rules are tighter than usual.*

## As quatro regras que não se negoceiam

### 1. Uma afirmação sobre a lei precisa do texto da lei — consolidado

Se alterar um prazo, um montante, uma percentagem ou uma porta de recusa, o artigo
tem de estar em `assets/law/`, **verbatim**, com fonte e data, e **da versão
consolidada**.

O DL 220/2006 foi alterado mais de uma dezena de vezes. A versão original tem
prazos de garantia e montantes revogados que ainda circulam em blogues e em
PDFs de 2007. Paráfrase não serve. "Li algures que são 65 %" não serve. Nem a
memória de um modelo de linguagem, incluindo a do autor original destas linhas.

### 2. Uma constante anual precisa do diploma que a fixa

O IAS e a RMMG mudam todos os anos. Em `assets/constantes.json`, cada valor traz
o diploma. Ao actualizar, mude também `_meta.ano_vigente` — há uma verificação que
fica vermelha sozinha quando o ano das constantes fica para trás.

### 3. Um teste novo tem de saber ficar vermelho

Antes de submeter, prove que o seu teste falha quando o comportamento que protege
é removido.

```bash
python scripts/sweep.py --self-test
python scripts/mutants.py
```

Adicionou um invariante de produto? Adicione o mutante correspondente em
`scripts/mutants.py`. Um invariante sem mutante entra no repositório por
observação, não por teste. (E se renomear uma verificação, o `mutants.py` rebenta
de propósito — um alvo que já não existe deixaria o mutante a testar nada.)

### 4. Nada de rede, nunca

Zero dependências. Zero chamadas de rede. Zero telemetria. Quem usa isto está a
introduzir o seu histórico salarial num momento mau da vida.

```bash
python scripts/offline_audit.py
```

## Antes de abrir um PR

```bash
python scripts/oracle.py --crosscheck
python scripts/oracle.py --mutation-test
python scripts/sweep.py --verboso
python scripts/sweep.py --self-test
python scripts/mutants.py
python scripts/offline_audit.py --selftest
```

Se alterar o número de verificações, actualize a contagem no `SKILL.md` e nos dois
READMEs — há uma verificação que falha de propósito quando essa contagem envelhece.

## Os contributos mais valiosos

1. **Decisões reais da Segurança Social.** O maior limite declarado é que nenhum
   caso dourado vem de uma decisão real: o corpus prova coerência com o texto
   legal, não com a prática do ISS. Se recebeu um valor diferente do calculado,
   isso vale mais do que qualquer refactor. Abra um issue com os *inputs* (sem
   dados pessoais) e o valor apurado.
2. **O art. 37.º n.os 3 a 5** — períodos já usados num desemprego anterior. Está
   por modelar e é a razão pela qual a duração calculada pode ser optimista.
3. **O DL n.º 70/2010** (escala de equivalência da condição de recursos), que
   destrancaria o subsídio social de desemprego.

## O que não é aceite

- Remover ou suavizar o rótulo de **limite superior** no montante. É o produto,
  não ruído.
- Fazer o motor calcular o tecto do art. 29.º n.os 2–3 **estimando** uma retenção
  de IRS. Um número inventado com ar de exacto é pior do que um limite honesto.
- Repor as majorações de 10 % das Leis 66-B/2012 e 83-C/2013. Não estão em vigor;
  aparecem como *Notas* no DR e há um mutante dedicado a impedir o regresso.
- Fazer o motor responder onde hoje recusa, sem o diploma que fundamente a resposta.
- Qualquer redacção que faça o resultado parecer uma decisão da Segurança Social.

## Código de conduta

Seja decente. Estamos a construir uma coisa para pessoas que acabaram de perder o
emprego, o que raramente é o melhor dia da vida delas.
