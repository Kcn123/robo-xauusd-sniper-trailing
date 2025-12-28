import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os

ARQUIVO_BASE = "historico_trades_mt5"

print("Conectando ao MetaTrader 5...")
if not mt5.initialize():
    print("❌ Erro ao conectar ao MT5")
    quit()

print("✅ Conectado ao MT5\n")

# =============================
# CONFIGURA INTERVALO (6 MESES)
# =============================

timezone = pytz.timezone("Etc/UTC")
end = datetime.now(timezone)
start = end - timedelta(days=180)

print(f"Coletando histórico entre {start} e {end}...\n")

# =============================
# COLETA DE DEALS
# =============================
print("Coletando DEALS...")
deals = mt5.history_deals_get(start, end)

if deals is None:
    print("❌ Erro ao obter deals")
    deals = []
else:
    print(f"Deals encontrados: {len(deals)}")

# Converte em dataframe organizado
df_deals = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys()) if len(deals) > 0 else pd.DataFrame()

# =============================
# COLETA DE ORDERS
# =============================
print("Coletando ORDERS...")
orders = mt5.history_orders_get(start, end)

if orders is None:
    print("❌ Erro ao obter orders")
    orders = []
else:
    print(f"Orders encontradas: {len(orders)}")

df_orders = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys()) if len(orders) > 0 else pd.DataFrame()

# =============================
# COLETA POSIÇÕES HISTÓRICAS
# =============================
print("Coletando POSIÇÕES HISTÓRICAS...")
hist_positions = mt5.positions_get()

df_positions = pd.DataFrame(list(hist_positions), columns=hist_positions[0]._asdict().keys()) if hist_positions else pd.DataFrame()
print(f"Positions históricas: {len(df_positions)}")

# =============================
# SALVA CSV
# =============================

print("\nGerando arquivos CSV...")

df_deals.to_csv(f"{ARQUIVO_BASE}_deals.csv", index=False, encoding="utf-8-sig")
df_orders.to_csv(f"{ARQUIVO_BASE}_orders.csv", index=False, encoding="utf-8-sig")
df_positions.to_csv(f"{ARQUIVO_BASE}_positions.csv", index=False, encoding="utf-8-sig")

print("\n===============================")
print(" HISTÓRICO GERADO COM SUCESSO!")
print("===============================\n")

print("📁 CSV Deals:", f"{ARQUIVO_BASE}_deals.csv")
print("📁 CSV Orders:", f"{ARQUIVO_BASE}_orders.csv")
print("📁 CSV Positions:", f"{ARQUIVO_BASE}_positions.csv")

input("\nPressione qualquer tecla para sair...")
