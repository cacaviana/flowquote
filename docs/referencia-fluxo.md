# FlowQuote — Referência Oficial de Fluxos (v1)

> Documento canônico do que um fluxo PODE fazer. É a base determinística da
> funcionalidade **"Criar fluxo com IA"** e a referência de consulta do usuário.
> Fonte da verdade: `frontend/src/lib/dto/flows/types.ts` + runtime `routes/q/[slug]`.

## 1. Anatomia de um fluxo

Um fluxo é um grafo: **nodes** (etapas) ligados por **edges** (setas).
O cliente final percorre do `start` até um `end`, respondendo perguntas.

| Campo do fluxo | O que é |
|---|---|
| `name` / `slug` | nome interno e URL pública (`/q/<slug>`) |
| `status` | `draft` (rascunho) → `published` (no ar) → `archived` |
| `nodes` / `edges` | o grafo em si |
| `pricing_csv` | tabela de preços (só faz sentido em fluxo de orçamento) |
| `tenant_id` | dono do fluxo — NUNCA definido pelo usuário/IA (vem do login) |

## 2. Tipos de NODE (são 4)

### 2.1 `start` — Início (obrigatório, exatamente 1)
- `title`: saudação inicial
- `collectFields`: dados do cliente a coletar (ex.: `name`, `email`, `phone`, `address`)
- Saída: exatamente **1 edge** (sem handle)

### 2.2 `question` — Pergunta
- `title`: a pergunta
- `questionType` (8 tipos):

| questionType | Comportamento | Ramifica? |
|---|---|---|
| `single_choice` | uma escolha entre opções | **SIM** — 1 edge por opção (`sourceHandle` = id da opção) |
| `yes_no` | sim/não | **SIM** — 2 edges |
| `multiple_choice` | várias escolhas | não — 1 edge de saída |
| `dropdown` | lista suspensa (`dropdownPlaceholder`) | não |
| `number` | número (pode virar QUANTIDADE via `quantityProduct`) | não |
| `text` | texto livre | não |
| `date` | data | não |
| `photo` | cliente envia foto | não |

- `options[]` (para tipos de escolha): `{ id, label, value, catalogProduct? }`
  - **`catalogProduct`**: nome EXATO do produto no `pricing_csv` → match determinístico no orçamento
- `quantityProduct` (em `number`/rating): a resposta numérica vira quantidade daquele produto
- `required`, `tooltip`, `ratingMax`
- `imageUrl`: imagem ilustrativa da pergunta (opcional)

### 2.3 `message` — Mensagem intermediária
- `message`: texto informativo (sem resposta)
- `isSpecialist`: marca "encaminhado a um especialista"
- `imageUrl` opcional
- Saída: 1 edge

### 2.4 `end` — Final (obrigatório, ≥1; pode haver vários finais)
- `endType` define O QUE ACONTECE:

| endType | O que faz | Tem valor/orçamento? |
|---|---|---|
| `quote` | **gera ORÇAMENTO com IA** usando `pricing_csv` + respostas + `businessContext` + `aiInstruction` | **SIM** |
| `specialist` | encaminha para atendimento humano | não |
| `thank_you` | agradecimento simples (captação de lead) | não |
| `scheduling` | agendamento (integra com a agenda do tenant) | não |

- Campos do `end` de orçamento: `businessContext` (regras de negócio em texto), `aiInstruction` (instrução pro gerador), `outputFormat` (`pdf` | `txt` | `both`)
- Saída: **nenhuma edge** (é terminal)

## 3. Regras de LIGAÇÃO (edges) — o que pode e o que não pode

Edge: `{ id, source, target, sourceHandle?, label? }`

**Navegação (runtime):** do node atual, procura na ordem:
1. edge com `source = atual` **e** `sourceHandle = id da opção escolhida`
2. edge com `source = atual` **sem** `sourceHandle`
3. qualquer edge com `source = atual`

**Regras determinísticas:**
| Regra | Válido |
|---|---|
| `start` → qualquer node (1 saída) | ✅ |
| `question` ramificada (`single_choice`/`yes_no`) → 1 edge POR OPÇÃO | ✅ |
| `question` não-ramificada / `message` → exatamente 1 saída | ✅ |
| `end` → qualquer coisa | ❌ end é terminal |
| qualquer node → `start` | ❌ |
| node sem caminho até um `end` (beco sem saída) | ❌ |
| node órfão (inalcançável a partir do `start`) | ❌ |
| ciclo (voltar a um node já visitado) | ❌ na v1 |
| 2 edges com o mesmo `sourceHandle` | ❌ ambíguo |

## 4. Fluxo COM valor × SEM valor

- **COM valor (orçamento)**: pelo menos um `end` com `endType: 'quote'` **e** `pricing_csv` preenchido. As opções que influenciam preço devem ter `catalogProduct` casando com o CSV; quantidades via `quantityProduct`.
- **SEM valor (captação/agendamento/triagem)**: finais `thank_you`/`specialist`/`scheduling`; `pricing_csv` ignorado.
- Um mesmo fluxo pode ter os dois finais (ex.: ramo "quero orçamento" → `quote`; ramo "só uma dúvida" → `specialist`).

## 5. Imagens — política da geração por IA

A IA **nunca escolhe imagem**. Ao gerar um fluxo, todo `imageUrl` sai como
placeholder padrão do sistema, e o rascunho lista onde o usuário deve
**substituir a imagem** no editor visual. Imagem é decisão humana.

## 6. Invariantes que TODO fluxo gerado deve passar (validador)

1. Exatamente 1 `start`; pelo menos 1 `end`
2. Todos os nodes alcançáveis a partir do `start`; todos alcançam um `end`
3. Ramificadas: nº de edges com handle = nº de opções (handles = ids das opções)
4. Não-ramificadas/message: exatamente 1 saída; `end`: zero saídas
5. Se existe `end quote` → `pricing_csv` obrigatório; `catalogProduct` referenciados existem no CSV
6. Sem ciclos; sem `sourceHandle` duplicado; ids únicos
7. `status` de fluxo gerado por IA = SEMPRE `draft`
