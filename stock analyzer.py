
#Stock Analyzer


import sys
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def resolve_ticker(query: str):

    try:
        search = yf.Search(query, max_results=5)
        quotes = search.quotes
        if quotes:
            return quotes[0].get("symbol")
    except Exception:
        pass
    return None


def get_data(ticker: str, period: str):
    data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError(f"No data found for '{ticker}'. Check the ticker symbol.")
    # yfinance sometimes returns multi-index columns for a single ticker
    if getattr(data.columns, "nlevels", 1) > 1:
        data.columns = data.columns.get_level_values(0)
    return data


def find_best_buy_sell(close_prices):
    
    min_price = close_prices.iloc[0]
    min_date = close_prices.index[0]

    best_profit = -1
    buy_date = sell_date = None
    buy_price = sell_price = None

    for date, price in close_prices.items():
        if price < min_price:
            min_price = price
            min_date = date

        profit = price - min_price
        if profit > best_profit:
            best_profit = profit
            buy_date, buy_price = min_date, min_price
            sell_date, sell_price = date, price

    return buy_date, buy_price, sell_date, sell_price, best_profit


def analyze_stock(ticker: str, period: str = "1y"):
    try:
        data = get_data(ticker, period)
    except ValueError:
        # Maybe they typed a company name instead of a ticker symbol
        resolved = resolve_ticker(ticker)
        if resolved and resolved.upper() != ticker.upper():
            print(f"'{ticker}' isn't a valid ticker symbol. Using closest match: {resolved}\n")
            ticker = resolved
            data = get_data(ticker, period)
        else:
            raise

    close = data["Close"]

    start_date, start_price = close.index[0], float(close.iloc[0])
    end_date, end_price = close.index[-1], float(close.iloc[-1])
    total_return_pct = (end_price - start_price) / start_price * 100

    peak_date = close.idxmax()
    peak_price = float(close.max())

    trough_date = close.idxmin()
    trough_price = float(close.min())

    buy_date, buy_price, sell_date, sell_price, profit = find_best_buy_sell(close)
    profit_pct = (profit / buy_price) * 100 if buy_price else 0

    # ---- Report ----
    print("\n" + "=" * 55)
    print(f" ANALYSIS: {ticker.upper()}  (period: {period})")
    print("=" * 55)
    print(f"Start date   : {start_date.date()}  -> ${start_price:.2f}")
    print(f"End date     : {end_date.date()}  -> ${end_price:.2f}")
    print(f"Total return : {total_return_pct:+.2f}%")
    print("-" * 55)
    print(f"Peak (high)  : ${peak_price:.2f} on {peak_date.date()}")
    print(f"Trough (low) : ${trough_price:.2f} on {trough_date.date()}")
    print("-" * 55)
    print("Best historical buy/sell window (max profit, buy before sell):")
    print(f"  Buy  on {buy_date.date()} at ${buy_price:.2f}")
    print(f"  Sell on {sell_date.date()} at ${sell_price:.2f}")
    print(f"  Profit: ${profit:.2f} per share ({profit_pct:+.2f}%)")
    print("=" * 55 + "\n")

    plot_stock(ticker, close, peak_date, peak_price, trough_date, trough_price,
               buy_date, buy_price, sell_date, sell_price)


def plot_stock(ticker, close, peak_date, peak_price, trough_date, trough_price,
               buy_date, buy_price, sell_date, sell_price):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(close.index, close.values, label="Close Price", color="#1f77b4", linewidth=1.5)

    # Peak / trough
    ax.scatter([peak_date], [peak_price], color="green", zorder=5, s=80, marker="^",
                label=f"Peak: ${peak_price:.2f}")
    ax.scatter([trough_date], [trough_price], color="red", zorder=5, s=80, marker="v",
                label=f"Trough: ${trough_price:.2f}")

    # Best buy / sell
    ax.scatter([buy_date], [buy_price], color="lime", zorder=6, s=120, marker="o",
                edgecolors="black", label=f"Best Buy: ${buy_price:.2f}")
    ax.scatter([sell_date], [sell_price], color="darkred", zorder=6, s=120, marker="o",
                edgecolors="black", label=f"Best Sell: ${sell_price:.2f}")

    ax.set_title(f"{ticker.upper()} Price History", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    ticker_input = input("Enter stock ticker (e.g. AAPL, MSFT, TSLA): ").strip()
    period_input = input(
        "Enter period (1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max) [default 1y]: "
    ).strip() or "1y"

    if not ticker_input:
        print("No ticker entered. Exiting.")
        sys.exit(1)

    try:
        analyze_stock(ticker_input, period_input)
    except ValueError as e:
        print(f"Error: {e}")