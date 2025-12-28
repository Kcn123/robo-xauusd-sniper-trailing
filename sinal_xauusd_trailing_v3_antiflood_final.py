#!/usr/bin/env python3
# sinal_xauusd_trailing_v3_antiflood_final.py
# ROBÔ FINAL — ANTIFLOOD ABSOLUTO VALIDADO
# Entrada M15 | Zona H1 | Trailing USD Prioritário
# CMD COMPLETO + LOG CUMULATIVO DE ERROS/MOTIVOS
# IA TOTALMENTE DESATIVADA

import os
import json
import time
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ================= CONFIGURAÇÕES =================
PAR = "XAUUSD"
MAGIC_NUMBER = 888999
COMMENT = "SNIPER_TRAILING_FINAL"
WEBHOOK_URL = "https://hook.us2.make.com/u19u6giww36xney1dfcuvp5pxy7hmc2u"

import MetaTrader5 as mt5

TIMEFRAME_M15 = mt5.TIMEFRAME_M15
TIMEFRAME_H1  = mt5.TIMEFRAME_H1
TIMEFRAME_M5  = mt5.TIMEFRAME_M5

CANDLES_BACK = 300
SLEEP_LOOP = 3

RISCO_FIXO_USD = 10.0

TRAILING_LEVELS_USD = [
    (5.0, -5.0),
    (10.0, 5.0),
    (15.0, 10.0)
]

VELAS_ZONA = 30
ZONA_BUFFER_USD = 12.0

ESTADO_FILE = "estado_antiflood.json"
TRADES_FILE = "trades_trailing.csv"

import requests

# ================= LOG FIXO =================
LOG_FIXO = []

def log_event(msg):
    linha = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    LOG_FIXO.append(linha)
    try:
        requests.post(WEBHOOK_URL, json={"text": linha}, timeout=5)
    except:
        pass

# ================= ESTADO =================
def carregar_estado():
    if not os.path.exists(ESTADO_FILE):
        estado = {
            "ultima_barra": None,
            "lucro_maximo": 0.0,
            "ticket_ativo": None
        }
        salvar_estado(estado)
        return estado
    estado = json.load(open(ESTADO_FILE, "r"))
    estado.setdefault("lucro_maximo", 0.0)
    estado.setdefault("ticket_ativo", None)
    return estado

def salvar_estado(estado):
    with open(ESTADO_FILE, "w") as f:
        json.dump(estado, f)

# ================= INDICADORES =================
def obter_df(tf, candles):
    rates = mt5.copy_rates_from_pos(PAR, tf, 0, candles)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    return df

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def stochrsi(series, rsi_period=8, stoch_period=8, k=3, d=3):
    r = rsi(series, rsi_period)
    min_r = r.rolling(stoch_period).min()
    max_r = r.rolling(stoch_period).max()
    stoch = (r - min_r) / (max_r - min_r)
    k_line = stoch.rolling(k).mean()
    d_line = k_line.rolling(d).mean()
    return k_line, d_line

# ================= ZONA H1 (INALTERADA) =================
def detectar_zona_h1():
    df = obter_df(TIMEFRAME_H1, VELAS_ZONA)
    if df is None or len(df) < VELAS_ZONA:
        return None, None, None, "NAO_CARREGADA"

    suporte = df["low"].min()
    resistencia = df["high"].max()
    preco = df["close"].iloc[-1]

    if preco <= suporte + ZONA_BUFFER_USD:
        zona = "SUPORTE"
    elif preco >= resistencia - ZONA_BUFFER_USD:
        zona = "RESISTENCIA"
    else:
        zona = "NEUTRA"

    return suporte, resistencia, preco, zona

# ================= CMD (100% FIEL) =================
def imprimir_cmd(df):
    os.system("cls")

    tick = mt5.symbol_info_tick(PAR)
    preco = tick.last if tick else 0
    spread = (tick.ask - tick.bid) if tick else 0

    r = rsi(df["close"]).iloc[-1]
    k, d = stochrsi(df["close"])
    vol = abs(df["close"].pct_change().iloc[-1]) * 100

    suporte, resistencia, preco_h1, zona = detectar_zona_h1()

    print("="*80)
    print("XAUUSD SNIPER FINAL — ANTIFLOOD ABSOLUTO")
    print("="*80)
    print(f"Hora: {datetime.now()}")
    print(f"Preço: {preco:.2f} | Spread: {spread:.2f}")
    print(f"RSI: {r:.2f} | StochK/D: {k.iloc[-1]:.2f}/{d.iloc[-1]:.2f}")
    print(f"Volatilidade: {vol:.2f}%")
    print("-"*80)

    print("ZONA H1 DEBUG:")
    print(f"VELAS_ZONA = {VELAS_ZONA} | BUFFER = {ZONA_BUFFER_USD} USD")
    print(f"SUPORTE H1 = {round(suporte,2) if suporte else 'None'}")
    print(f"RESISTENCIA H1 = {round(resistencia,2) if resistencia else 'None'}")
    print(f"PREÇO H1 = {round(preco_h1,2) if preco_h1 else 'None'}")
    print(f">>> ZONA ATUAL: {zona}")

    print("-"*80)

    pos = mt5.positions_get(symbol=PAR)
    if pos:
        p = pos[0]
        print(f"POSIÇÃO: {'BUY' if p.type==0 else 'SELL'} | Lote {p.volume} | Lucro {p.profit:.2f} | SL {p.sl}")
    else:
        print("POSIÇÃO: nenhuma")

    print("-"*80)
    print("LOG FIXO:")
    for l in LOG_FIXO[-10:]:
        print(l)
    print("="*80)

# ================= NOTIFICA FECHAMENTO =================
def verificar_fechamento(estado):
    if estado["ticket_ativo"] is None:
        return

    if mt5.positions_get(ticket=estado["ticket_ativo"]):
        return

    now = datetime.now()
    deals = mt5.history_deals_get(now - timedelta(hours=2), now)

    if not deals:
        return

    fechamento = [d for d in deals if d.position_id == estado["ticket_ativo"] and d.entry == mt5.DEAL_ENTRY_OUT]
    if not fechamento:
        return

    d = fechamento[-1]
    resultado = "GAIN" if d.profit > 0 else "STOP"

    log_event(
        f"{resultado} | Ticket {d.position_id} | "
        f"Lucro {d.profit:.2f} USD | Preço {d.price:.2f} | Volume {d.volume}"
    )

    estado["ticket_ativo"] = None
    salvar_estado(estado)

# ================= TRAILING USD (INALTERADO) =================
def aplicar_trailing(pos, estado):
    info = mt5.symbol_info(PAR)
    value_per_point = info.trade_tick_value / info.trade_tick_size

    tick = mt5.symbol_info_tick(PAR)
    preco_atual = tick.bid if pos.type == mt5.POSITION_TYPE_BUY else tick.ask
    direcao = 1 if pos.type == mt5.POSITION_TYPE_BUY else -1

    lucro_atual = (preco_atual - pos.price_open) * direcao * pos.volume * value_per_point

    if lucro_atual > estado["lucro_maximo"]:
        estado["lucro_maximo"] = lucro_atual
        salvar_estado(estado)

    novo_sl = None
    for lucro_min, sl_gain in TRAILING_LEVELS_USD:
        if estado["lucro_maximo"] >= lucro_min:
            delta = sl_gain / (pos.volume * value_per_point)
            novo_sl = pos.price_open + delta if direcao == 1 else pos.price_open - delta

    if novo_sl is None:
        return
    if direcao == 1 and novo_sl <= pos.sl:
        return
    if direcao == -1 and pos.sl != 0 and novo_sl >= pos.sl:
        return

    result = mt5.order_send({
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": PAR,
        "position": pos.ticket,
        "sl": round(novo_sl, 2),
        "tp": pos.tp
    })

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_event(f"TRAILING | Lucro Máx {estado['lucro_maximo']:.2f} | SL -> {round(novo_sl,2)}")

# ================= EXECUÇÃO (INALTERADA) =================
def executar_entrada(df, estado):
    pos = mt5.positions_get(symbol=PAR)
    if pos:
        return

    candle_time = str(df.index[-1])
    if estado["ultima_barra"] == candle_time:
        return

    v1, v2, v3, v4 = df.iloc[-5], df.iloc[-4], df.iloc[-3], df.iloc[-2]
    tick = mt5.symbol_info_tick(PAR)
    ask, bid = tick.ask, tick.bid

    sinal = None
    if v1.close > v1.open and v2.close > v2.open and v3.close > v3.open and v4.close < v4.open and ask > max(v4.open, v4.close):
        sinal = "BUY"
    if v1.close < v1.open and v2.close < v2.open and v3.close < v3.open and v4.close > v4.open and bid < min(v4.open, v4.close):
        sinal = "SELL"

    if not sinal:
        return

    suporte, resistencia, preco_h1, zona = detectar_zona_h1()
    if (zona == "RESISTENCIA" and sinal == "BUY") or (zona == "SUPORTE" and sinal == "SELL"):
        log_event(f"ENTRADA BLOQUEADA: {sinal} em {zona}")
        estado["ultima_barra"] = candle_time
        salvar_estado(estado)
        return

    info = mt5.symbol_info(PAR)
    value_per_point = info.trade_tick_value / info.trade_tick_size

    for lote in [0.02, 0.01]:
        dist = RISCO_FIXO_USD / (lote * value_per_point)

        if sinal == "BUY":
            sl_calc = ask - dist
            sl_min = v4.low
            if sl_calc <= sl_min or lote == 0.01:
                sl = min(sl_calc, sl_min)
                tp = ask + (abs(ask - sl) * 2)
            else:
                continue
        else:
            sl_calc = bid + dist
            sl_max = v4.high
            if sl_calc >= sl_max or lote == 0.01:
                sl = max(sl_calc, sl_max)
                tp = bid - (abs(bid - sl) * 2)
            else:
                continue

        res = mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": PAR,
            "volume": lote,
            "type": mt5.ORDER_TYPE_BUY if sinal == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": ask if sinal == "BUY" else bid,
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "magic": MAGIC_NUMBER,
            "comment": COMMENT
        })

        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            estado["ultima_barra"] = candle_time
            estado["lucro_maximo"] = 0.0
            estado["ticket_ativo"] = res.order
            salvar_estado(estado)
            log_event(f"ENTRADA {sinal} | Lote {lote} | SL {round(sl,2)} | TP {round(tp,2)}")
        else:
            log_event("Falha ao enviar ordem")
        return

    log_event("ENTRADA BLOQUEADA: SL não alcança vela de reversão (0.02 / 0.01)")
    estado["ultima_barra"] = candle_time
    salvar_estado(estado)

# ================= LOOP =================
def main():
    estado = carregar_estado()

    while True:
        df = obter_df(TIMEFRAME_M15, CANDLES_BACK)
        if df is None or len(df) < 6:
            time.sleep(2)
            continue

        imprimir_cmd(df)
        verificar_fechamento(estado)

        pos = mt5.positions_get(symbol=PAR)
        if pos:
            aplicar_trailing(pos[0], estado)
        else:
            executar_entrada(df, estado)

        time.sleep(SLEEP_LOOP)

# ================= START =================
if __name__ == "__main__":
    if not mt5.initialize():
        print("Erro MT5")
        exit()
    main()
