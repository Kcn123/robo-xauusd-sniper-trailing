# Núcleo do Robô — Estratégia Sniper Trailing XAUUSD

Este diretório contém o código principal do robô automático para o par XAUUSD no MetaTrader 5.

O robô implementa uma estratégia baseada em:

- entradas no gráfico M15
- validação de contexto no H1 (suporte / resistência)
- trailing stop progressivo em USD
- gestão de risco por valor financeiro fixo
- bloqueio antiflood por candle já processado
- persistência de estado entre execuções
- integração com webhook para monitoramento remoto

O objetivo do projeto é aplicar conceitos de automação financeira, controle de risco e análise técnica,
conectando experiência no mercado financeiro com desenvolvimento em Python.

O arquivo principal deste módulo é:

`sinal_xauusd_trailing_v3_antiflood_final.py`


