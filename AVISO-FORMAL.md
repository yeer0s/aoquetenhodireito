# Aviso Formal · Formal Notice

> **Estatuto deste documento.** Isto é um **aviso**, não uma condição de licença.
> O software é distribuído sob a licença MIT, sem modificações e sem restrições
> adicionais — ver `LICENSE`. Nada neste ficheiro limita os direitos que a MIT
> concede. Se alguma frase aqui parecer contradizer a MIT, **prevalece a MIT**.
>
> *Status of this document. This is a **notice**, not a licence condition. The
> software is MIT, unmodified, with no additional restrictions. Where this file
> appears to conflict with MIT, **MIT prevails**.*

---

## Português

### 1. Isto não é aconselhamento, e não vincula ninguém

`aoquetenhodireito` é uma **ferramenta de apoio à decisão**. Não é aconselhamento
jurídico, financeiro nem fiscal.

Sobretudo: **não vincula a Segurança Social**. A decisão sobre o seu direito, o
montante e a duração é do Instituto da Segurança Social, e só dele. Um resultado
deste programa não é um deferimento, não é uma promessa, e não pode ser invocado
perante nenhuma entidade.

Nem os autores nem o projecto Mowei têm qualquer relação com a Segurança Social.

### 2. O valor apresentado é um LIMITE SUPERIOR

Esta é a limitação mais importante do programa, e não está escondida numa nota.

O art. 29.º n.os 2 e 3 do DL 220/2006 limita o subsídio a **75 %, e nunca mais**,
do valor **líquido** da remuneração de referência. O n.º 4 define líquido como o
ilíquido menos a taxa contributiva **e a taxa de retenção do IRS**.

A sua retenção de IRS depende do escalão, do estado civil, do número de
dependentes e da região. Este programa **não pergunta** a sua situação fiscal e
por isso **não pode** aplicar esse tecto.

**Consequência prática:** o valor que a Segurança Social apurar pode ser **menor**
do que o apresentado aqui. Nunca maior. **Não assuma compromissos financeiros —
rendas, prestações, créditos — com base neste número.**

### 3. A responsabilidade é de quem decide

O motor calcula a partir dos números **que o utilizador introduz**: dias de
trabalho, meses com registo de remunerações, total de remunerações, anos de
carreira. Não os verifica e não os pode verificar.

Um erro de um dia no prazo de garantia, ou de um mês no registo de remunerações,
muda o resultado e passa em todos os testes deste repositório. Os seus números
reais estão na Segurança Social Direta — confirme-os lá.

Isto decorre da arquitectura: o programa corre **inteiramente na sua máquina**,
sem rede e sem telemetria. Nada é transmitido, ninguém do outro lado vê o seu
caso — e por isso ninguém do outro lado o pode validar. A privacidade e a
responsabilidade são o mesmo facto visto de dois lados.

### 4. Limites conhecidos, declarados

- O **art. 37.º n.os 3 a 5** não está modelado. Quem já recebeu subsídio de
  desemprego antes, ou retomou trabalho durante a atribuição, pode ter uma
  duração **menor** do que a calculada.
- O **subsídio social de desemprego** é porta de recusa: a escala de equivalência
  da condição de recursos (DL n.º 70/2010) não está capturada.
- O texto legal em `assets/law/` vem do **Diário da República** (versão
  consolidada), mas uma captura tem **data**. A lei muda.
- O **IAS** e a **RMMG** mudam todos os anos. O gate falha quando ficam para trás
  do ano corrente, mas isso deteta a viragem do ano — não uma alteração a meio.
- Nenhum caso de teste vem de uma **decisão real** da Segurança Social.

### 5. Onde obter a resposta que vincula

- **Segurança Social Direta** — [seg-social.pt](https://www.seg-social.pt)
- **Linha Segurança Social** — 300 502 502 (dias úteis)
- **IEFP / centro de emprego** — a inscrição é condição do subsídio
- **Apoio judiciário**, se precisar de contestar uma decisão —
  [seg-social.pt/protecao-juridica](https://www.seg-social.pt/protecao-juridica)

### 6. Sem garantia

Nos termos da licença MIT, o software é fornecido **"tal como está"**, sem
garantia de qualquer espécie. Os autores não respondem por quaisquer danos,
incluindo decisões financeiras tomadas com base nas suas estimativas.

---

## English

### 1. Not advice, and binding on no one

`aoquetenhodireito` is a **decision-support tool** — not legal, financial or tax
advice. Above all it **does not bind Portuguese Social Security**, which is the
only body that decides entitlement, amount and duration. A result here is not an
approval and cannot be relied on before any authority.

### 2. The figure shown is an UPPER BOUND

Art. 29.º n.os 2–3 of DL 220/2006 caps the benefit at **75 %, and never more**, of
the **net** reference remuneration, and n.º 4 defines net as gross minus the
contributory rate **and income-tax withholding**. Withholding depends on bracket,
marital status, dependants and region — this program does not ask, and therefore
**cannot** apply that cap.

The amount Social Security determines may be **lower** than shown here. Never
higher. **Do not commit to rent, loans or instalments on the basis of this
figure.**

### 3. Responsibility sits with the person deciding

The engine computes from figures **the user supplies** and cannot verify them. A
one-day error in the qualifying period changes the result and passes every test
in this repository. Your real figures are in Segurança Social Direta.

This follows from the architecture: it runs **entirely on your machine**, with no
network and no telemetry. Nothing is transmitted — so nobody on the other side
can validate it either.

### 4. Declared limits

Art. 37.º n.os 3–5 (prior unemployment spells, returning to work during payment)
is **not modelled** — a previous claim may mean a **shorter** duration than
calculated. The social unemployment benefit is a refusal gate. IAS and RMMG change
annually. No test case comes from a real Social Security decision.

### 5. No warranty

Provided **"as is"** under MIT, without warranty of any kind. The authors accept
no liability for any damages, including financial decisions based on its estimates.

---

*Última revisão: 2026-07-27 · [mowei.pt](https://mowei.pt)*
