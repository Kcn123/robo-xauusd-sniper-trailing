# Robô XAUUSD — Sniper Trailing (MetaTrader 5 | Python)

Robô automático desenvolvido em Python para o par XAUUSD no MetaTrader 5, com foco em:

- proteção de capital
- controle de risco baseado em USD
- trailing stop progressivo
- bloqueio antiflood por candle já processado
- validação de contexto no gráfico H1
- automação de entradas no gráfico M15
- persistência de estado entre execuções

O projeto foi desenvolvido como estudo aplicado de automação financeira, análise técnica e programação Python,
conectando experiência no mercado financeiro com desenvolvimento orientado a dados.

---

## 🎯 Objetivo do projeto

Implementar uma estratégia automática com:

- entradas técnicas no M15
- verificação de suporte / resistência no H1
- cálculo dinâmico de stop baseado em risco financeiro fixo
- trailing stop progressivo em USD
- validação antiflood (uma decisão por candle)
- registro estruturado das operações
- extração de histórico real via MetaTrader 5
- painel de análise de desempenho

O foco é o aprendizado prático em:

✔ automação de trading  
✔ controle de risco  
✔ análise de performance  
✔ engenharia de dados aplicada a mercado financeiro  

---

## 🧩 Arquitetura do projeto

.
├── core/ # código principal do robô
│ ├── utils/ # funções auxiliares e suporte
│ └── sinal_xauusd_trailing_v3_antiflood_final.py
│
├── data/ # dados exportados do MT5 e logs do robô
│ ├── historico_trades_mt5_deals.csv
│ ├── historico_trades_mt5_orders.csv
│ └── historico_trades_mt5_positions.csv
│
├── analytics/ # módulo de análise e painel Streamlit
│ └── streamlit_mt5.py
│
├── utils/ # scripts de extração e apoio
│ └── extrair_relatorios_mt5.py
│
└── requirements.txt # dependências do projeto

yaml
Copiar código

---

## ⚙️ Principais recursos técnicos

✔ Entrada automática baseada em padrão de candles  
✔ Confirmação de contexto por zona H1 (suporte / resistência)  
✔ Cálculo de stop por risco fixo em USD  
✔ Trailing stop progressivo com atualização dinâmica  
✔ Persistência de estado entre execuções  
✔ Bloqueio antiflood para evitar múltiplas entradas por candle  
✔ Exportação de histórico real do MetaTrader 5  
✔ Registro estruturado em CSV para análise posterior  
✔ Integração com webhook para monitoramento remoto  

---

## 📊 Dados e evidências de execução

Os arquivos no diretório `data/` foram extraídos do MetaTrader 5
por meio do script de exportação incluído no projeto.

Eles registram:

- execuções de ordens
- posições
- deals / resultados
- logs operacionais

Foram utilizados para:

- validação da estratégia
- análise de desempenho
- estudo comportamental do trailing stop

> Observação: os dados referem-se a ambiente de testes / conta demo
> e possuem finalidade exclusivamente educacional e experimental.

---

## 🖥️ Painel de análise (Streamlit)

O módulo `analytics/` permite:

- leitura dos arquivos CSV
- análise visual do desempenho
- acompanhamento de histórico operacional
- suporte ao refinamento da estratégia

Executando:

streamlit run analytics/streamlit_mt5.py

yaml
Copiar código

---

## 🚀 Como executar o robô

Pré-requisitos:

- Python 3.10+
- MetaTrader 5 instalado
- login configurado no MT5
- pacote MetaTrader5 autorizado na plataforma

Instalar dependências:

pip install -r requirements.txt

nginx
Copiar código

Executar robô:

python core/sinal_xauusd_trailing_v3_antiflood_final.py

yaml
Copiar código

---

## 🧠 Objetivo educacional

Este projeto faz parte do meu processo de:

- transição para a área de tecnologia
- aprofundamento em Python aplicado a finanças
- desenvolvimento de automações orientadas a dados

Interesses profissionais:

- Python para automação e análise
- mercado financeiro e data-driven trading
- inteligência artificial aplicada a processos
- RPA e automação operacional

---

## 📬 Contato

Caso tenha interesse em conversar sobre o projeto:

- Aberto a oportunidades de estágio / trainee / entry-level
- Interesse em atuar com Python, automação e dados
