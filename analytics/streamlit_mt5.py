# streamlit_pro_v2.py  (corrigido - parsing de datas e filtros robustos)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import io, base64

CSV_PATH = "historico_trades_mt5_deals.csv"
st.set_page_config(page_title="Painel PRO v2 — Histórico MT5", layout="wide")
st.title("📊 Painel PRO v2 — Histórico de Trades (MT5 deals → trades)")

@st.cache_data
def load_raw(csv_path=CSV_PATH):
    try:
        df = pd.read_csv(csv_path, dtype=str)  # ler tudo como str para parsing seguro
        return df
    except Exception as e:
        st.error(f"Erro ao ler CSV: {e}")
        return None

def try_parse_datetime_series(s):
    """Tenta várias interpretações para uma Series de strings/nums e retorna datetime64[ns] ou NaT."""
    if s is None:
        return pd.Series([], dtype="datetime64[ns]")
    # se já for datetime dtype
    if np.issubdtype(s.dtype, np.datetime64):
        return s
    # primeira tentativa: pandas to_datetime (auto)
    res = pd.to_datetime(s, errors="coerce", utc=False)
    if res.notna().any():
        return res
    # se números grandes (ms)
    try:
        nums = pd.to_numeric(s, errors="coerce")
        # heurística: se médiana > 1e12 provavelmente ms
        if nums.dropna().shape[0] > 0:
            med = nums.dropna().median()
            if med > 1e12:
                return pd.to_datetime(nums, unit="ms", errors="coerce", utc=False)
            elif med > 1e9:
                return pd.to_datetime(nums, unit="s", errors="coerce", utc=False)
    except Exception:
        pass
    # fallback: all NaT
    return pd.Series([pd.NaT]*len(s), index=s.index, dtype="datetime64[ns]")

def normalize_deals(df_raw):
    """Consolida deals em trades agrupando por position_id (robusto para CSVs com col names variados)."""
    if df_raw is None:
        return None
    df = df_raw.copy()
    # strip column names
    df.columns = [c.strip() for c in df.columns]

    # detect / normalize position id
    if 'position_id' not in df.columns:
        if 'position' in df.columns:
            df = df.rename(columns={'position':'position_id'})
        elif 'ticket' in df.columns:
            # in some exports ticket identifies deal, but position_id may be absent;
            # use 'position_id' = 'position_id' if present else fallback to 'ticket' (best-effort)
            df['position_id'] = df['ticket']
        elif 'order' in df.columns:
            df['position_id'] = df['order']
        else:
            # fallback synthetic
            df['position_id'] = (np.arange(len(df)) // 2).astype(str)

    # find best time column
    time_cols_candidates = ['hora_execucao','time','time_msc','timestamp','date','hora','hora_exec']
    time_col = None
    for c in time_cols_candidates:
        if c in df.columns:
            # choose first parseable column
            parsed = try_parse_datetime_series(df[c])
            if parsed.notna().any():
                df[c + "_parsed"] = parsed
                time_col = c + "_parsed"
                break
    # fallback: try to parse any column
    if time_col is None:
        for c in df.columns:
            parsed = try_parse_datetime_series(df[c])
            if parsed.notna().any():
                df[c + "_parsed"] = parsed
                time_col = c + "_parsed"
                break
    # final fallback: create monotonic times (index-based)
    if time_col is None:
        df['time_parsed'] = try_parse_datetime_series(pd.Series([pd.NaT]*len(df)))
        time_col = 'time_parsed'

    # ensure numeric columns exist and cast where possible
    def to_float(colname):
        if colname in df.columns:
            return pd.to_numeric(df[colname], errors='coerce')
        return pd.Series([np.nan]*len(df))
    df['_profit'] = to_float('profit') if 'profit' in df.columns else (to_float('lucro') if 'lucro' in df.columns else pd.Series([0.0]*len(df)))
    df['_volume'] = to_float('volume') if 'volume' in df.columns else (to_float('lot') if 'lot' in df.columns else pd.Series([np.nan]*len(df)))
    df['_price'] = to_float('price') if 'price' in df.columns else (to_float('entry') if 'entry' in df.columns else pd.Series([np.nan]*len(df)))
    # symbol
    sym_col = None
    for c in ['symbol','ativo','ticker','instrument']:
        if c in df.columns:
            sym_col = c; break
    if sym_col is None:
        df['symbol'] = None
    else:
        df['symbol'] = df[sym_col].astype(str)

    # group by position_id and build trades
    trades = []
    grouped = df.groupby('position_id', sort=False)
    for pid, g in grouped:
        g2 = g.sort_values(by=time_col, na_position='first').reset_index(drop=True)
        # need at least 2 rows (entry + exit)
        if len(g2) < 2:
            continue
        first = g2.iloc[0]
        last = g2.iloc[-1]
        profit = float(last['_profit']) if not pd.isna(last['_profit']) else 0.0
        entry_time = first[time_col] if time_col in g2.columns else pd.NaT
        exit_time = last[time_col] if time_col in g2.columns else pd.NaT
        entry_price = float(first['_price']) if not pd.isna(first['_price']) else np.nan
        exit_price = float(last['_price']) if not pd.isna(last['_price']) else np.nan
        volume = float(first['_volume']) if not pd.isna(first['_volume']) else np.nan
        tipo = None
        if 'type' in g2.columns:
            tipo = str(first['type']).upper()
        elif 'order' in g2.columns:
            tipo = str(first['order']).upper()
        trades.append({
            "position_id": str(pid),
            "symbol": first.get('symbol', None),
            "type": tipo,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "volume": volume,
            "profit": profit
        })
    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        return trades_df
    # coercions & derived columns
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], errors='coerce')
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], errors='coerce')
    # drop rows without exit_time (open trades)
    trades_df = trades_df.dropna(subset=['exit_time']).reset_index(drop=True)
    trades_df['exit_date'] = trades_df['exit_time'].dt.date
    trades_df['entry_date'] = trades_df['entry_time'].dt.date
    # normalize type values
    trades_df['type'] = trades_df['type'].astype(str).str.upper().replace({'0':'BUY','1':'SELL'})
    # ensure numeric profit
    trades_df['profit'] = pd.to_numeric(trades_df['profit'], errors='coerce').fillna(0.0)
    return trades_df

def compute_metrics(trades_df):
    if trades_df is None or trades_df.empty:
        return {}
    df = trades_df.copy()
    total_profit = float(df['profit'].sum())
    total_trades = len(df)
    wins = int(df[df['profit'] > 0].shape[0])
    losses = int(df[df['profit'] <= 0].shape[0])
    winrate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    # daily profit grouped by exit_date
    daily = df.groupby('exit_date', sort=True)['profit'].sum().reset_index().sort_values('exit_date')
    # best and worst day
    if not daily.empty:
        best_idx = daily['profit'].idxmax(); worst_idx = daily['profit'].idxmin()
        best_day = daily.loc[best_idx].to_dict()
        worst_day = daily.loc[worst_idx].to_dict()
    else:
        best_day = None; worst_day = None

    # lot performance
    lot_perf = df.groupby('volume', dropna=True).agg(lucro_total=('profit','sum'), qtd_trades=('profit','count')).reset_index()
    if not lot_perf.empty:
        lot_perf = lot_perf.sort_values('lucro_total', ascending=False)
        top_lote = lot_perf.iloc[0].to_dict()
    else:
        top_lote = None

    metrics = {
        "total_profit": total_profit,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "winrate": winrate,
        "daily": daily,
        "best_day": best_day,
        "worst_day": worst_day,
        "top_lote": top_lote,
        "lot_perf": lot_perf
    }
    return metrics

def to_download_link(df, filename="trades_unified.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">⬇️ Baixar trades processados (.csv)</a>'
    return href

# ---------------- main app flow ----------------
raw = load_raw(CSV_PATH)
if raw is None:
    st.stop()

st.sidebar.header("Parâmetros e filtros")
st.sidebar.caption("Processamento: agrupa deals → trades por position_id (entrada=primeiro deal, saída=último deal)")

trades = normalize_deals(raw)
if trades is None or trades.empty:
    st.warning("Nenhum trade consolidado encontrado no CSV (verifique position_id ou formato).")
    st.write(raw.head(10))
    st.stop()

# safe min/max dates
valid_dates = trades['exit_date'].dropna().unique()
if len(valid_dates) == 0:
    min_date = None
    max_date = None
else:
    min_date = min(valid_dates)
    max_date = max(valid_dates)

symbols = ['Todos'] + sorted(trades['symbol'].dropna().astype(str).unique().tolist())
# volumes: present as strings to avoid mixed-type sort errors
volumes_raw = trades['volume'].dropna().unique().tolist()
volumes_str = ['Todos'] + sorted([str(v) for v in volumes_raw], key=lambda x: float(x) if x.replace('.','',1).isdigit() else x)

sym_sel = st.sidebar.selectbox("Símbolo", symbols, index=0)
type_sel = st.sidebar.selectbox("Tipo", ['Todos', 'BUY', 'SELL'], index=0)

# handle date inputs robustly
if min_date is None or max_date is None:
    st.sidebar.write("Aviso: não foram detectadas datas válidas no CSV. Filtros de data desabilitados.")
    date_ini = None
    date_fim = None
else:
    date_ini = st.sidebar.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date)
    date_fim = st.sidebar.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date)
vol_sel = st.sidebar.selectbox("Lote (volume)", volumes_str, index=0)

# apply filters
df_filtered = trades.copy()
if sym_sel != 'Todos':
    df_filtered = df_filtered[df_filtered['symbol'].astype(str) == sym_sel]
if type_sel != 'Todos':
    df_filtered = df_filtered[df_filtered['type'] == type_sel]
if date_ini is not None and date_fim is not None:
    df_filtered = df_filtered[(df_filtered['exit_date'] >= date_ini) & (df_filtered['exit_date'] <= date_fim)]
if vol_sel != 'Todos':
    # convert selection back to float for comparison
    try:
        sel_val = float(vol_sel)
        df_filtered = df_filtered[df_filtered['volume'] == sel_val]
    except Exception:
        pass

metrics = compute_metrics(df_filtered)

# top summary
col1, col2, col3, col4 = st.columns(4)
col1.metric("Lucro total", f"${metrics.get('total_profit', 0.0):.2f}")
col2.metric("Trades", f"{metrics.get('total_trades', 0)}")
col3.metric("Wins", f"{metrics.get('wins', 0)}")
col4.metric("Losses", f"{metrics.get('losses', 0)}")

st.markdown("---")
with st.expander("🔎 Insights automáticos avançados", expanded=True):
    if metrics.get('total_trades', 0) == 0:
        st.write("Sem trades no filtro atual.")
    else:
        st.write(f"Conta em lucro no período: ${metrics.get('total_profit',0):.2f}.")
        st.write(f"Total de trades filtrados: {metrics.get('total_trades',0)}")
        st.write(f"Win rate: {metrics.get('winrate',0):.1f}%")
        best_day = metrics.get('best_day'); worst_day = metrics.get('worst_day')
        if best_day:
            st.write(f"Melhor dia: {best_day['exit_date']} → ${best_day['profit']:.2f}")
        if worst_day:
            st.write(f"Pior dia: {worst_day['exit_date']} → ${worst_day['profit']:.2f}")
        top_lote = metrics.get('top_lote')
        if top_lote:
            st.write(f"Lote mais lucrativo: {top_lote['volume']} · Lucro: ${top_lote['lucro_total']:.2f} · Trades: {int(top_lote['qtd_trades'])}")

st.markdown("---")
st.markdown("### Lucro acumulado ao longo do tempo")
df_chart = df_filtered.sort_values('exit_time').copy()
if not df_chart.empty:
    df_chart['lucro_acumulado'] = df_chart['profit'].cumsum()
    st.line_chart(df_chart.set_index('exit_time')['lucro_acumulado'])
else:
    st.info("Sem dados para o gráfico acumulado.")

st.markdown("### Lucro diário")
daily = metrics.get('daily', pd.DataFrame({'exit_date':[], 'profit':[]})).copy()
if not daily.empty:
    st.bar_chart(daily.set_index('exit_date')['profit'])
else:
    st.info("Sem dados diários.")

st.markdown("### Proporção de trades (Win / Loss)")
wins = df_filtered[df_filtered['profit'] > 0].shape[0]
losses = df_filtered[df_filtered['profit'] <= 0].shape[0]
st.write(f"Ganhos: {wins} — Perdas: {losses} — Winrate: {metrics.get('winrate',0):.1f}%")

st.markdown("### Trades filtrados (preview)")
st.dataframe(df_filtered.sort_values('exit_time', ascending=False).head(500))

st.markdown(to_download_link(trades, "trades_unified.csv"), unsafe_allow_html=True)
st.write("Observações: consolidamos DEALS → TRADES por position_id. Ajuste o CSV original se quiser agrupar por outro identificador.")
