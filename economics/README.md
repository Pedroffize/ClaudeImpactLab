# Economics

Análise de viabilidade econômica, custo-benefício e eficiência de tokens do projeto.

## 1. Análise de custos

### 1.1. Custo por inferência

| Etapa | Modelo | Tokens (in/out) | Custo estimado |
|-------|--------|------------------|----------------|
|       |        |                  |                |

### 1.2. Custo total do MVP

- Tokens consumidos no desenvolvimento:
- Custo do MVP:
- % do orçamento (USD 70) utilizado:

## 2. Análise de benefícios (política pública)

- População-alvo:
- Métrica de impacto:
- Ganho estimado (em R$, em vidas, em tempo, etc.):

## 3. Escalabilidade

Comportamento do custo em diferentes escalas de deployment:

- Piloto (~N usuários): R$
- Municipal (~N usuários): R$
- Estadual (~N usuários): R$

## 4. Estratégias de eficiência adotadas

- [ ] Prompt caching (descontos de ~90% em leituras cacheadas)
- [ ] Uso de Haiku para tarefas simples (classificação, roteamento)
- [ ] Uso de Sonnet/Opus apenas para etapas que exigem raciocínio
- [ ] Batch API quando latência não é crítica (50% de desconto)
- [ ] Structured outputs para evitar reprocessamento
- [ ] Limitação de contexto via RAG ou truncagem
