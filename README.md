# Robô XAUUSD — Sniper Trailing

Robô automático desenvolvido em Python para o par XAUUSD no MetaTrader 5, com foco em proteção de capital, automação de entradas e gestão ativa de lucro.

O projeto foi desenvolvido como estudo aplicado de automação financeira, controle de risco e análise técnica, conectando minha experiência no mercado financeiro com o desenvolvimento em Python.

---

## Objetivo do projeto

Implementar uma estratégia automática com:

- entradas no gráfico M15
- validação de zona no H1 (suporte / resistência)
- controle de risco baseado em USD
- trailing stop progressivo
- prevenção de entradas incorretas (antiflood)
- persistência de estado entre execuções
- registro de operações para análise de performance

---

## Principais recursos técnicos

- Integração Python + MetaTrader 5
- Trailing Stop baseado em lucro financeiro (não em pontos)
- Bloqueio de entrada por candle já processado
- Filtro de operação por zonas no H1
- Log estruturado enviado via webhook
- Salvamento de histórico em CSV para estudos de melhoria da estratégia

---

## Próximos passos planejados

- análise estatística dos resultados
- backtests e validação de estratégia
- possíveis integrações com modelos de decisão

---

Projeto em evolução contínua como parte da minha transição de carreira para tecnologia, com foco em Python aplicado a finanças e automação.
