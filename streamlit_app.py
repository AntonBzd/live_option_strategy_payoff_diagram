import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
from scipy.stats import norm



# Step 0: Strategy Selection
strategies_informations = {
"Covered Call" : """
  - **Buy**: Purchase the underlying stock.
  - **Sell**: Write (sell) a call option with a strike price \( K \), typically out-of-the-money (OTM).
  - **Outlook**:
    - Neutral to bullish on the stock price.
    - Aims to generate income from selling call premiums.
  - **Notes**:
    - This strategy has the same payoff as a short (naked) put.
    - Traders often sell OTM call options periodically to maximize income while holding the stock.
""",
"Covered Put" : """
  - **Buy**: Short the underlying stock.
  - **Sell**: Write (sell) a put option with a strike price \( K \), typically out-of-the-money (OTM).
  - **Outlook**: Neutral to bearish.
  - **Notes**:
    - The strategy generates income by periodically selling OTM put options.
    - This strategy has the same payoff as writing a call option (short/naked call).
""",
"Protective Put": """
  - **Buy**: Purchase the underlying stock and an ATM or OTM put option with a strike price \( K <= S_0 \).
  - **Sell**: None.
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a hedging strategy: the put option protects against downside risk.
""",
"Protective Call": """
  - **Buy**: Purchase an ATM or OTM call option with a strike price \( K >= S_0 \).
  - **Sell**: Short the underlying stock.
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a hedging strategy: the call option protects against the risk of the stock price rising.
""",
"Bull Call Spread": """
  - **Buy**: A close to ATM call option with strike price \( K1 \).
  - **Sell**: An OTM call option with a higher strike price \( K2 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a net debit trade.
    - Profits if the stock price rises (capital gain strategy).
""",
"Bull Put Spread": """
  - **Buy**: An OTM put option with strike price \( K1 \).
  - **Sell**: Another OTM put option with a higher strike price \( K2 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a net credit trade.
    - Generates income while expecting the stock price to rise or remain stable.
""",
"Bear Call Spread": """
  - **Buy**: An OTM call option with strike price \( K1 \).
  - **Sell**: Another OTM call option with a lower strike price \( K2 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a net credit trade.
    - Generates income while expecting the stock price to fall or remain stable.
""",
"Bear Put Spread": """
  - **Buy**: A close to ATM put option with strike price \( K1 \).
  - **Sell**: An OTM put option with a lower strike price \( K2 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a net debit trade.
    - Profits if the stock price falls (capital gain strategy).
""",
"Long Synthetic Forward":"""
  - **Buy**: An ATM call option with strike price \( K = S0 \).
  - **Sell**: An ATM put option with strike price \( K = S0 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This strategy mimics a long stock or futures position.
    - Can result in a net debit or net credit trade.
    - Profits from capital gains.
""",
"Short Synthetic Forward":"""
  - **Buy**: An ATM put option with strike price \( K = S0 \).
  - **Sell**: An ATM call option with strike price \( K = S0 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This strategy mimics a short stock or futures position.
    - Can result in a net debit or net credit trade.
    - Profits from capital gains.
""",
"Long Combo":"""
  - **Buy**: An OTM call option with strike price \( K1 \).
  - **Sell**: An OTM put option with strike price \( K2 \) \( K1 > K2 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a capital gain strategy.
""",
"Short Combo":"""
  - **Buy**: An OTM put option with strike price \( K1 \).
  - **Sell**: An OTM call option with strike price \( K2 \) \( K2 > K1 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a capital gain strategy.
""",
"Bull Call Ladder":"""
  - **Buy**: A close to ATM call option with strike price \( K1 \).
  - **Sell**: An OTM call option with strike price \( K2 \).
  - **Sell**: Another OTM call option with a higher strike price \( K3 \).
  - **Outlook**: Conservatively bullish or non-directional (low volatility expectation).
  - **Notes**:
    - This is a bull call spread financed by selling another OTM call option.
""",
"Bear Call Ladder":"""
  - **Buy**: An OTM call option with strike price \( K2 \).
  - **Buy**: Another OTM call option with a higher strike price \( K3 \).
  - **Sell**: A close to ATM call option with strike price \( K1 \).
  - **Outlook**: Adjusted to bullish if the initial bear call spread goes wrong.
  - **Notes**:
    - Typically arises when a bear call spread fails, and the trader adjusts the position to bullish.
""",
"Bull Put Ladder":"""
  - **Buy**: An OTM put option with strike price \( K2 \).
  - **Buy**: Another OTM put option with a lower strike price \( K3 \).
  - **Sell**: A close to ATM put option with strike price \( K1 \).
  - **Outlook**: Adjusted to bearish if the initial bull put spread goes wrong.
  - **Notes**:
    - Typically arises when a bull put spread fails, and the trader adjusts the position to bearish.
""",
"Bear Put Ladder":"""
  - **Buy**: A close to ATM put option with strike price \( K1 \).
  - **Sell**: An OTM put option with strike price \( K2 \).
  - **Sell**: Another OTM put option with a lower strike price \( K3 \).
  - **Outlook**: Conservatively bearish or non-directional (low volatility expectation).
  - **Notes**:
    - This is a bear put spread financed by selling another OTM put option.
""",
"Calendar Call Spread":"""
  - **Buy**: A close to ATM call option with strike price \( K \) and TTM \( T0 \).
  - **Sell**: A call option with the same strike price \( K \) but shorter TTM \( T < T0 \).
  - **Outlook**: Neutral to bullish.
  - **Notes**:
    - This is a net debit trade.
    - The best case occurs when the stock price at the short call's expiration is \( ST = K \).
    - Resembles a covered call strategy if shorter call options are written periodically.
""",
"Calendar Put Spread":"""
  - **Buy**: A close to ATM put option with strike price \( K \) and TTM \( T0 \).
  - **Sell**: A put option with the same strike price \( K \) but shorter TTM \( T < T0 \).
  - **Outlook**: Neutral to bearish.
  - **Notes**:
    - This is a net debit trade.
    - The best case occurs when the stock price at the short put's expiration is \( ST = K \).
    - Resembles a covered put strategy if shorter put options are written periodically.
""",
"Diagonal Call Spread":"""
  - **Buy**: A deep ITM call option with strike price \( K1 \) and TTM \( T0 \).
  - **Sell**: An OTM call option with strike price \( K2 \) and shorter TTM \( T < T0 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a net debit trade.
    - Resembles a calendar call spread but uses a deep ITM call for more protection against sharp stock price increases.
""",
"Diagonal Put Spread":"""
  - **Buy**: A deep ITM put option with strike price \( K1 \) and TTM \( T0 \).
  - **Sell**: An OTM put option with strike price \( K2 \) and shorter TTM \( T < T0 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a net debit trade.
    - Resembles a calendar put spread but uses a deep ITM put for more protection against sharp stock price decreases.
""",
"Long Straddle":"""
  - **Buy**: An ATM call option and an ATM put option with strike price \( K \).
  - **Sell**: None.
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - This is a net debit trade.
    - Profits from significant price movement in either direction.
""",
"Short Straddle":"""
  - **Buy**: None.
  - **Sell**: An ATM call option and an ATM put option with strike price \( K \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - This is a net credit trade.
    - Profits from little to no price movement but carries significant risk if volatility increases.
""",
"Long Strangle":""""
  - **Buy**: An OTM call option with strike price \( K1 \) and an OTM put option with strike price \( K2 \).
  - **Sell**: None.
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - This is a net debit trade.
    - Less costly than a long straddle, but requires larger price movements to reach breakeven.
""",
"Short Strangle":"""
  - **Buy**: None.
  - **Sell**: An OTM call option with strike price \( K1 \) and an OTM put option with strike price \( K2 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - This is a net credit trade.
    - Less risky than a short straddle but generates lower initial credit.
""",
"Long Guts":"""
  - **Buy**: An ITM call option with strike price \( K1 \) and an ITM put option with strike price \( K2 \).
  - **Sell**: None.
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - This is a net debit trade.
    - More costly than a long straddle, but has higher intrinsic value.
""",
"Short Guts":"""
  - **Buy**: None.
  - **Sell**: An ITM call option with strike price \( K1 \) and an ITM put option with strike price \( K2 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - This is a net credit trade.
    - Higher initial credit than a short straddle but comes with higher risk.
""",
"Long Call Synthetic Straddle":"""
  - **Buy**: Two ATM (or nearest ITM) call options with strike price \( K \).
  - **Sell**: Short the underlying stock.
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - A variation of the long straddle where the put is replaced with a synthetic put.
""",
"Long Put Synthetic Straddle":"""
  - **Buy**: Two ATM (or nearest ITM) put options with strike price \( K \).
  - **Sell**: Purchase the underlying stock.
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - A variation of the long straddle where the call is replaced with a synthetic call.
""",
"Short Call Synthetic Straddle":"""
  - **Buy**: The underlying stock.
  - **Sell**: Two ATM (or nearest OTM) call options with strike price \( K \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - A variation of the short straddle where the put is replaced with a synthetic put.
""",
"Short Put Synthetic Straddle":"""
  - **Buy**: None.
  - **Sell**: Two ATM (or nearest OTM) put options with strike price \( K \).
  - **Sell**: Short the underlying stock.
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - A variation of the short straddle where the call is replaced with a synthetic call.
""",
"Covered Short Straddle":"""
  - **Buy**: The underlying stock.
  - **Sell**: A call option and a put option with the same strike price \( K \).
  - **Outlook**: Bullish.
  - **Notes**:
    - Generates income by combining a covered call and a short put.
""",
"Covered Short Strangle":"""
  - **Buy**: The underlying stock.
  - **Sell**: An OTM call option with strike price \( K \) and an OTM put option with strike price \( K0 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - Generates income while maintaining a bullish outlook.
""",
"Strap":"""
  - **Buy**: Two ATM call options and one ATM put option with strike price \( K \).
  - **Sell**: None.
  - **Outlook**: Bullish, expecting high volatility.
  - **Notes**:
    - A net debit trade that profits from upward price movement.
""",
"Strip":"""
  - **Buy**: One ATM call option and two ATM put options with strike price \( K \).
  - **Sell**: None.
  - **Outlook**: Bearish, expecting high volatility.
  - **Notes**:
    - A net debit trade that profits from downward price movement.
""",
"Call Ratio Backspread":"""
  - **Buy**: \( NL \) OTM call options with strike price \( K2 \) \( NL > NS \).
  - **Sell**: \( NS \) close to ATM call options with strike price \( K1 \).
  - **Outlook**: Strongly bullish.
  - **Notes**:
    - Typically structured as \( NL = 2, NS = 1 \) or \( NL = 3, NS = 2 \).
    - Profits from sharp upward price movements.
    - This is a net debit trade.
""",
"Put Ratio Backspread":"""
  - **Buy**: \( NL \) OTM put options with strike price \( K2 \) \( NL > NS \).
  - **Sell**: \( NS \) close to ATM put options with strike price \( K1 \).
  - **Outlook**: Strongly bearish.
  - **Notes**:
    - Typically structured as \( NL = 2, NS = 1 \) or \( NL = 3, NS = 2 \).
    - Profits from sharp downward price movements.
    - This is a net debit trade.
""",
"Ratio Call Spread":"""
  - **Buy**: \( NL \) ITM call options with strike price \( K2 \) \( NL < NS \).
  - **Sell**: \( NS \) close to ATM call options with strike price \( K1 \).
  - **Outlook**: Neutral to bearish.
  - **Notes**:
    - Typically structured as \( NL = 1, NS = 2 \) or \( NL = 2, NS = 3 \).
    - This is a net credit trade when structured as an income strategy.
""",
"Ratio Put Spread":"""
  - **Buy**: \( NL \) ITM put options with strike price \( K2 \) \( NL < NS \).
  - **Sell**: \( NS \) close to ATM put options with strike price \( K1 \).
  - **Outlook**: Neutral to bullish.
  - **Notes**:
    - Typically structured as \( NL = 1, NS = 2 \) or \( NL = 2, NS = 3 \).
    - This is a net credit trade when structured as an income strategy.
""",
"Long Call Butterfly":"""
  - **Buy**: One OTM call option with strike price \( K1 \) and one ITM call option with strike price \( K3 \).
  - **Sell**: Two ATM call options with strike price \( K2 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strike prices are equidistant: \( K2 - K1 = K3 - K2 = kappa \).
    - This is a net debit trade.
""",
"Modified Call Butterfly":"""
  - **Buy**: An OTM call option with strike price \( K1 \) and an ITM call option with strike price \( K3 \).
  - **Sell**: Two ATM call options with strike price \( K2 \).
  - **Outlook**: Neutral with a bullish bias.
  - **Notes**:
    - The strikes are not equidistant: \( K1 - K2 < K2 - K3 \).
    - A variation of the long call butterfly strategy.
""",
"Long Put Butterfly":"""
  - **Buy**: An OTM put option with strike price \( K1 \) and an ITM put option with strike price \( K3 \).
  - **Sell**: Two ATM put options with strike price \( K2 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K3 - K2 = K2 - K1 = kappa \).
    - This is a net debit trade.
""",
"Modified Put Butterfly":"""
  - **Buy**: An ITM put option with strike price \( K3 \) and an OTM put option with strike price \( K1 \).
  - **Sell**: Two ATM put options with strike price \( K2 \).
  - **Outlook**: Neutral with a bullish bias.
  - **Notes**:
    - The strikes are not equidistant: \( K3 - K2 < K2 - K1 \).
""",
"Short Call Butterfly":"""
  - **Buy**: Two ATM call options with strike price \( K2 \).
  - **Sell**: One ITM call option with strike price \( K1 \) and one OTM call option with strike price \( K3 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K3 - K2 = K2 - K1 = kappa \).
    - This is a net credit trade with lower risk and lower potential reward compared to a short straddle or short strangle.
""",
"Short Put Butterfly":"""
  - **Buy**: Two ATM put options with strike price \( K2 \).
  - **Sell**: One ITM put option with strike price \( K1 \) and one OTM put option with strike price \( K3 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K2 - K3 = K1 - K2 = kappa \).
    - This is a net credit trade with lower risk and lower potential reward compared to a short straddle or short strangle.
""",
"Long Iron Butterfly":"""
  - **Buy**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K3 \).
  - **Sell**: An ATM put option and an ATM call option with strike price \( K2 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K2 - K1 = K3 - K2 = kappa \).
    - This is a net credit trade and an income strategy.
""",
"Short Iron Butterfly":"""
  - **Buy**: An ATM put option and an ATM call option with strike price \( K2 \).
  - **Sell**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K3 \).
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - The strikes are equidistant: \( K2 - K1 = K3 - K2 = kappa \).
    - This is a net debit trade.
""",
"Long Call Condor":"""
  - **Buy**: An ITM call option with strike price \( K1 \) and an OTM call option with strike price \( K4 \).
  - **Sell**: An ITM call option with a higher strike price \( K2 \) and an OTM call option with strike price \( K3 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K4 - K3 = K3 - K2 = K2 - K1 = kappa \).
    - This is a relatively low-cost net debit trade.
""",
"Short Call Condor":"""
  - **Buy**: An ITM call option with strike price \( K2 \) and an OTM call option with strike price \( K3 \).
  - **Sell**: An ITM call option with strike price \( K1 \) and an OTM call option with strike price \( K4 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K4 - K3 = K3 - K2 = K2 - K1 = kappa \).
    - This is a relatively low net credit trade.
    - Lower risk and reward compared to short straddles or strangles.
""",
"Long Put Condor":"""
  - **Buy**: An OTM put option with strike price \( K1 \) and an ITM put option with strike price \( K4 \).
  - **Sell**: An OTM put option with a higher strike price \( K2 \) and an ITM put option with strike price \( K3 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K4 - K3 = K3 - K2 = K2 - K1 = kappa \).
    - This is a relatively low-cost net debit trade.
""",
"Short Put Condor":"""
  - **Buy**: An OTM put option with strike price \( K2 \) and an ITM put option with strike price \( K3 \).
  - **Sell**: An OTM put option with strike price \( K1 \) and an ITM put option with strike price \( K4 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K4 - K3 = K3 - K2 = K2 - K1 = kappa \).
    - This is a relatively low net credit trade.
    - Lower risk and reward compared to short straddles or strangles.
""",
"Long Iron Condor":"""
  - **Buy**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K4 \).
  - **Sell**: An OTM put option with strike price \( K2 \) and an OTM call option with strike price \( K3 \).
  - **Outlook**: Neutral, expecting low volatility.
  - **Notes**:
    - The strikes are equidistant: \( K4 - K3 = K3 - K2 = K2 - K1 = kappa \).
    - This is a net credit trade and an income strategy.
""",
"Short Iron Condor":"""
  - **Buy**: An OTM put option with strike price \( K2 \) and an OTM call option with strike price \( K3 \).
  - **Sell**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K4 \).
  - **Outlook**: Neutral, expecting high volatility.
  - **Notes**:
    - The strikes are equidistant: \( K4 - K3 = K3 - K2 = K2 - K1 = kappa \).
    - This is a net debit trade.
""",
"Long Box":"""
  - **Buy**: An ITM put option with strike price \( K1 \) and an ITM call option with strike price \( K2 \).
  - **Sell**: An OTM put option with strike price \( K2 \) and an OTM call option with strike price \( K1 \).
  - **Outlook**: Neutral.
  - **Notes**:
    - This is a capital gain strategy.
    - Combines a long synthetic forward and a short synthetic forward.
""",
"Collar":"""
  - **Buy**: The underlying stock and an OTM put option with strike price \( K1 \).
  - **Sell**: An OTM call option with a higher strike price \( K2 \).
  - **Outlook**: Moderately bullish.
  - **Notes**:
    - Provides downside protection with limited upside potential.
    - A capital gain strategy.
""",
"Bullish Short Seagull Spread":"""
  - **Buy**: An ATM call option with strike price \( K2 \).
  - **Sell**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K3 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a bull call spread financed with the sale of an OTM put option.
    - Ideally structured as a zero-cost trade.
    - This is a capital gain strategy.
""",
"Bullish Long Seagull Spread":"""
  - **Buy**: An OTM call option with strike price \( K3 \) and an OTM put option with strike price \( K1 \).
  - **Sell**: An ATM put option with strike price \( K2 \).
  - **Outlook**: Bullish.
  - **Notes**:
    - This is a long combo hedged with an OTM put option.
    - Ideally structured as a zero-cost trade.
    - This is a capital gain strategy.
""",
"Bearish Short Seagull Spread":"""
  - **Buy**: An ATM put option with strike price \( K2 \).
  - **Sell**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K3 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a bear put spread financed with the sale of an OTM call option.
    - Ideally structured as a zero-cost trade.
    - This is a capital gain strategy.
""",
"Bearish Long Seagull Spread":"""
  - **Buy**: An OTM put option with strike price \( K1 \) and an OTM call option with strike price \( K3 \).
  - **Sell**: An ATM call option with strike price \( K2 \).
  - **Outlook**: Bearish.
  - **Notes**:
    - This is a short combo hedged with an OTM call option.
    - Ideally structured as a zero-cost trade.
    - This is a capital gain strategy.
"""
}

# Market view
market_view = st.sidebar.radio(
    "**Select Market View:**",
    ["Directional", "Non-Directional"])
# Directional Strategies
if market_view == "Directional":
    direction = st.sidebar.radio(
        "**Select Direction:**",
        ["Bullish", "Bearish"])
    if direction == "Bullish":
        strategy = st.sidebar.selectbox(
            "**Select a Bullish Strategy:**",
            [ "Covered Call",
              "Protective Put",
              "Bull Call Spread",
              "Bull Put Spread",
              "Long Synthetic Forward",
              "Bull Call Ladder",
              "Bear Call Ladder",
              "Long Combo",
              "Diagonal Call Spread",
              "Covered Short Straddle",
              "Covered Short Strangle",
              "Strap",
              "Modified Call Butterfly",
              "Modified Put Butterfly",
              "Call Ratio Backspread",
              "Bullish Short Seagull Spread",
              "Bullish Long Seagull Spread"])
    elif direction == "Bearish":
        strategy = st.sidebar.selectbox(
            "**Select a Bearish Strategy:**",
            [ "Covered Put",
              "Protective Call",
              "Bear Call Spread",
              "Bear Put Spread",
              "Short Synthetic Forward",
              "Short Combo",
              "Bull Put Ladder",
              "Bear Put Ladder",
              "Diagonal Put Spread",
              "Strip",
              "Put Ratio Backspread",
              "Ratio Put Spread",
              "Bearish Short Seagull Spread",
              "Bearish Long Seagull Spread"])
# Non-Directional Strategies
elif market_view == "Non-Directional":
    volatility = st.sidebar.radio(
        "**Select Volatility Outlook:**",
        ["High Volatility", "Low Volatility"])
    if volatility == "High Volatility":
        strategy = st.sidebar.selectbox(
            "**Select a High Volatility Strategy:**",
            [ "Long Straddle",
              "Long Strangle",
              "Long Guts",
              "Short Call Butterfly",
              "Short Put Butterfly",
              "Short Iron Butterfly",
              "Short Call Condor",
              "Short Put Condor",
              "Short Iron Condor",
              "Long Box",
              "Long Call Synthetic Straddle",
              "Long Put Synthetic Straddle"])
    elif volatility == "Low Volatility":
        strategy = st.sidebar.selectbox(
            "**Select a Low Volatility Strategy:**",
            [ "Calendar Call Spread",
              "Calendar Put Spread",
              "Short Straddle",
              "Short Strangle",
              "Short Guts",
              "Short Call Synthetic Straddle",
              "Short Put Synthetic Straddle",
              "Ratio Call Spread",
              "Ratio Put Spread",
              "Long Call Butterfly",
              "Long Put Butterfly",
              "Long Iron Butterfly",
              "Long Call Condor",
              "Long Put Condor",
              "Long Iron Condor",
              "Collar",
              "Long Box"])
#strategy = st.sidebar.selectbox('**Select strategy:**', strategies_informations.keys())
st.title(strategy)

# Step 1: Ticker Selection
ticker = st.sidebar.text_input(f"**Enter Stock Ticker (e.g., AAPL, SPY):**", value="AAPL")
stock = yf.Ticker(ticker)

# Step 2: Fetch Current Stock Price
current_price = stock.history(period="1d")['Close'].iloc[-1]
S_0 = round(current_price, 2)
st.sidebar.write(f'*Current Stock Price: {S_0}$*')
st.sidebar.empty()

if strategy != "Calendar Put Spread" and strategy != "Calendar Call Spread" and strategy != "Diagonal Put Spread" and strategy != "Diagonal Call Spread" :

  # Step 3: Fetch Expiration Dates
  try:
      expiration_dates = stock.options
      expiration_date = st.sidebar.selectbox(f"**Select Expiration Date:**", expiration_dates)
  except IndexError:
      st.sidebar.error("No Options Data Available for the Selected Ticker.")
      st.stop()

  # Step 4: Fetch Options
  option_chain = stock.option_chain(expiration_date)


if strategy == "Covered Call":

  # Step 5: Select Strike Price
  strike_prices = option_chain.calls['strike']
  K = st.sidebar.selectbox(
          "**Select Strike Price K for the Short Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 - np.maximum(S_T - K, 0) + C
  max_profit = K - S_0 + C
  max_loss = S_0 - C
  st.empty()

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5 = st.columns(3)
  with col3:
      st.markdown(f"**Premium received:** {round(C, 2)}")
  with col4:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col5:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Covered Put":

  # Step 5: Select Strike Price
  strike_prices = option_chain.puts['strike']
  K = st.sidebar.selectbox(
          "**Select Strike Price K for the Short Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_0 - S_T - np.maximum(K - S_T, 0) + C
  max_profit = S_0 - K + C
  max_loss = np.inf

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5 = st.columns(3)

  with col3:
      st.markdown(f"**Premium received:** {round(C, 2)}")
  with col4:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col5:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Protective Put":

  # Step 5: Select Strike Price
  strike_prices = option_chain.puts['strike']
  try:
    K = st.sidebar.selectbox(
          "**Select Strike Price K for the Long ATM or OTM Put:**",
          sorted([price for price in strike_prices if price <= S_0]))
  except Exception:
    st.sidebar.error('No Available Put Options below the Current Stock Price.')
    st.stop()

  # Step 6: Get Premium
  D = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 + np.maximum(K - S_T, 0) - D
  max_profit = np.inf
  max_loss = S_0 - K + D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5 = st.columns(3)
  with col3:
      st.markdown(f"**Premium paid:** {round(D, 2)}")
  with col4:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col5:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Protective Call":

  # Step 5: Select Strike Price
  strike_prices = option_chain.calls['strike']
  try:
    K = st.sidebar.selectbox(
        "**Select Strike Price K for the Long ATM or OTM Call:**",
        sorted([price for price in strike_prices if price >= S_0]))
  except Exception:
    st.error('No Available Call Options below the Current Stock Price.')
    st.stop()
  # Step 6: Get Premium
  D = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_0 - S_T + np.maximum(S_T - K, 0) - D
  max_profit = S_0 - D
  max_loss = K - S_0 + D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5 = st.columns(3)

  with col3:
      st.markdown(f"**Premium paid:** {round(D, 2)}")

  with col4:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")

  with col5:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bull Call Spread":

  # Step 5: Select Strike Price
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox("**Select Strike Price K1 for the Long close to ATM Call:**", sorted(strike_prices))
  try:
    K_2 = st.sidebar.selectbox(
        "**Select Strike Price K2 for the Short OTM Call (K1<K2):**",
        sorted([price for price in strike_prices if price > K_1]))
  except Exception:
    st.error('No Available Call Options above the selected Strike Price K1')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D = D_1-C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) - np.maximum(S_T - K_2, 0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bull Put Spread":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox("**Select Strike Price K1 for the Long OTM Put:**", sorted(strike_prices))
  try:
    K_2 = st.sidebar.selectbox(
      "**Select Strike Price K2 for the Short OTM Put (K1<K2):**",
      sorted([price for price in strike_prices if price > K_1]))
  except Exception:
    st.error('No Available Put Options above the selected Strike Price K1')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C = C_1-D_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) + C
  max_profit = C
  max_loss = K_2 - K_1 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bear Call Spread":

  # Step 5: Select Strike Prices

  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Call:**",
          sorted(strike_prices))
  if np.min(strike_prices)<K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Call (K2<K1):**",
            sorted([price for price in strike_prices if price < K_1]))
  else:
    st.error('No Available Call Options below the selected Strike Price K1')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  C = C_1-D_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) - np.maximum(S_T - K_2, 0) + C
  max_profit = C
  max_loss = K_1 - K_2 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bear Put Spread":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long close to ATM Put:**",
          sorted(strike_prices))
  if np.min(strike_prices)<K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Put (K2<K1):**",
            sorted([price for price in strike_prices if price < K_1]))
  else:
    st.error('No Available Put Options below the selected Strike Price K1')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D = D_1-C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) - D
  max_profit = K_1 - K_2 - D
  max_loss = D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Synthetic Forward":

  # Step 5: Select Strike Prices

  strike_prices = option_chain.calls['strike']
  if np.min(strike_prices)<S_0 and S_0<np.max(strike_prices):
    K_1 = st.sidebar.selectbox(
            "**Select Strike Price K for the Long ATM Call (K=S0):**",
            sorted([price for price in strike_prices if (round(0.9*S_0, 0) < price and price < round(1.1*S_0,0))]))
    strike_prices = option_chain.puts['strike']
    K = st.sidebar.selectbox(
            "**Select Strike Price K for the Short ATM Put (K=S0):**",
            sorted([price for price in strike_prices if price==K_1]))
  else:
    st.error('No Available Options for the Current Stock Price.')
    st.stop()

  # Step 6: Get Premium
  D = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  C = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K, 0) - np.maximum(K - S_T, 0) - H
  max_profit = np.inf
  max_loss = K + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Synthetic Forward":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  if np.min(strike_prices)<S_0 and S_0<np.max(strike_prices):
    K_1 = st.sidebar.selectbox(
            "**Select Strike Price K for the Long ATM Put (K=S0):**",
            sorted([price for price in strike_prices if (round(0.9*S_0, 0) < price and price < round(1.1*S_0,0))]))
    strike_prices = option_chain.calls['strike']
    K = st.sidebar.selectbox(
            "**Select Strike Price K for the Short ATM Call (K=S0):**",
            sorted([price for price in strike_prices if price==K_1]))
  else:
    st.error('No Available Options for the Current Stock Price.')
    st.stop()

  # Step 6: Get Premium
  D = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  C = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K - S_T, 0) - np.maximum(S_T - K, 0) - H
  max_profit = K - H
  max_loss = np.inf

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Combo":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Call:**",
          sorted(strike_prices))
  if np.min(strike_prices)<K_1:
    strike_prices = option_chain.puts['strike']
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for a Short OTM Put (K1>K2):**",
            sorted([price for price in strike_prices if price < K_1]))
  else:
    st.error('No Available Put Options below the selected Strike Price K1.')
    st.stop()

  # Step 6: Get Premium
  D = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) - np.maximum(K_2 - S_T,0) - H
  max_profit = np.inf
  max_loss = K_2 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Combo":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put:**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    strike_prices = option_chain.calls['strike']
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Call (K2>K1):**",
            sorted([price for price in strike_prices if price > K_1]))
  else:
    st.error('No Available Call Options above the selected Strike Price K1.')
    st.stop()

  # Step 6: Get Premium
  D = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(S_T - K_2, 0) - H
  max_profit = K_1 - H
  max_loss = np.inf

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D, 2)}")
  with col4:
      st.markdown(f"**Premium Received:** {round(C, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bull Call Ladder":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long close to ATM Call:**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Call (K2>K1):**",
            sorted([price for price in strike_prices if price > K_1]))
  else:
    st.error('No Available Call Options Above the selected Strike Price K1')
    st.stop()
  if np.max(strike_prices)>K_2:
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short OTM Call (K3>K2):**",
            sorted([price for price in strike_prices if price > K_2]))
  else:
    st.error('No Available Call Options Above the selected Strike Price K2')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  H = D_1-C_1-C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) - np.maximum(S_T - K_2, 0) - np.maximum(S_T - K_3, 0) - H
  max_profit = K_2 - K_1 - H
  max_loss = np.inf

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bear Call Ladder":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short close to ATM Call:**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long OTM Call (K2>K1):**",
            sorted([price for price in strike_prices if price > K_1]))
  else:
    st.error('No Available Call Options Above the selected Strike Price K1')
    st.stop()
  if np.max(strike_prices)>K_2:
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Long OTM Call (K3>K2):**",
            sorted([price for price in strike_prices if price > K_2]))
  else:
    st.error('No Available Call Options Above the selected Strike Price K2')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  H = D_1+D_2-C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_3, 0) + np.maximum(S_T - K_2, 0) - np.maximum(S_T - K_1, 0) - H
  max_profit = np.inf
  max_loss = K_2 - K_1 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Received:** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bull Put Ladder":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short close ATM Put:**",
          sorted(strike_prices))
  if np.min(strike_prices)<K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long OTM Put (K1>K2):**",
            sorted([price for price in strike_prices if K_1 > price]))
  else:
    st.error('No Available Put Options Below the selected Strike Price K1')
    st.stop()
  if np.min(strike_prices)<K_2:
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Long OTM Put (K2>K3):**",
            sorted([price for price in strike_prices if K_2 > price]))
  else:
    st.error('No Available Put Options Below the selected Strike Price K2')
    st.stop()

  # Step 6: Get Premium Paid
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  H = D_1+D_2-C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_3 - S_T, 0) + np.maximum(K_2 - S_T, 0) - np.maximum(K_1 - S_T,0) - H
  max_profit = K_3 + K_2 - K_1 - H
  max_loss = K_1 - K_2 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Received:** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bear Put Ladder":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long close to ATM Put:**",
          sorted(strike_prices))
  if np.min(strike_prices)<K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Put (K1>K2):**",
            sorted([price for price in strike_prices if K_1 > price]))
  else:
    st.error('No Available Put Options Below the selected Strike Price K1')
    st.stop()
  if np.min(strike_prices)<K_2:
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short OTM Put (K2>K3):**",
            sorted([price for price in strike_prices if K_2 > price]))
  else:
    st.error('No Available Put Options Below the selected Strike Price K2')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  H = D_1-C_1-C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) - np.maximum(K_3 - S_T, 0) - H
  max_profit = K_1 - K_2 - H
  max_loss = K_3 + K_2 - K_1 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid:** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K for the Long ATM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  if K_1 in strike_prices.tolist():
    K = st.sidebar.selectbox(
            "**Select Strike Price K for the Long ATM Put:**",
            sorted([K_1]))
  else:
    st.error('No Available Put for the selected Strike Price K.')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  D = D_1 + D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K, 0) + np.maximum(K - S_T, 0) - D
  max_profit = np.inf
  max_loss = D
  S_up = K + D
  S_down = K - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K for the Short ATM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  if K_1 in strike_prices.tolist():
    K = st.sidebar.selectbox(
            "**Select Strike Price K for the Short ATM Put:**",
            sorted([K_1]))
  else:
    st.error("No Put options available for the selected strike price.")
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  C = C_1 + C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = -np.maximum(S_T - K, 0) - np.maximum(K - S_T, 0) + C
  max_profit = C
  max_loss = np.inf
  S_up = K + C
  S_down = K - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Strangle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long OTM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D = D_1 + D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) + np.maximum(K_2 - S_T, 0) - D
  max_profit = np.inf
  max_loss = D
  S_up = K_1 + D
  S_down = K_2 - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Strangle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short OTM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short OTM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C = C_1 + C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = -np.maximum(S_T - K_1, 0) - np.maximum(K_2 - S_T, 0) + C
  max_profit = C
  max_loss = np.inf
  S_up = K_1 + C
  S_down = K_2 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Guts":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long ITM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long ITM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D = D_1 + D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) + np.maximum(K_2 - S_T, 0) - D
  max_profit = np.inf
  max_loss = D
  S_up = K_1 + D
  S_down = K_2 - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Guts":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short ITM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short ITM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C = C_1 + C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = -np.maximum(S_T - K_1, 0) - np.maximum(K_2 - S_T, 0) + C
  max_profit = C- (K_2 - K_1)
  max_loss = np.inf
  S_up = K_1 + C
  S_down = K_2 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Call Synthetic Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K = st.sidebar.selectbox(
          "**Select Strike Price K for the Long of 2 ATM or nearest ITM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  D = 2*option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_0 - S_T + 2 * np.maximum(S_T - K, 0) - D
  max_profit = np.inf
  max_loss = D - (S_0 - K)
  S_up = 2 * K - S_0 + D
  S_down = S_0 - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col4, col5, col6 = st.columns(3)
  with col4:
      st.markdown(f"**Premium Paid:** {round(D, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Put Synthetic Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K = st.sidebar.selectbox(
      "**Select Strike Price K for the Long Of 2 ATM or nearest ITM Put:**",
      sorted(strike_prices))

  # Step 6: Get Premium
  D = 2*option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 + 2 * np.maximum(K - S_T, 0) - D
  max_profit = np.inf
  max_loss = D - (K - S_0)
  S_up = S_0 + D
  S_down = 2 * K - S_0 - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col4, col5, col6 = st.columns(3)
  with col4:
      st.markdown(f"**Premium Paid:** {round(D, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Call Synthetic Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K = st.sidebar.selectbox(
          "**Select Strike Price K for the Short of 2 ATM or nearest OTM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = 2*option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 - 2 * np.maximum(S_T - K, 0) + C
  max_profit = K - S_0 + C
  max_loss = np.inf
  S_up = 2 * K - S_0 + C
  S_down = S_0 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col4, col5, col6 = st.columns(3)
  with col4:
      st.markdown(f"**Premium Received:** {round(C, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Put Synthetic Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K = st.sidebar.selectbox(
          "**Select Strike Price K for the Short of 2 ATM or nearest OTM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = 2*option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_0 - S_T - 2 * np.maximum(K - S_T, 0) + C
  max_profit = S_0 - K + C
  max_loss = np.inf
  S_up = S_0 + C
  S_down = 2*K - S_0 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col4, col5, col6 = st.columns(3)
  with col4:
      st.markdown(f"**Premium Received:** {round(C, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Covered Short Straddle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
            "**Select Strike Price K for the Short ATM Call:**",
            sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  if K_1 in strike_prices.tolist():
    K = st.sidebar.selectbox(
              "**Select Strike Price K for the Short ATM Put:**",
              sorted([K_1]))
  else:
    st.error("No Put Options Available for the Selected Strike Price.")
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  C = C_1 + C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 - np.maximum(S_T - K, 0) - np.maximum(K - S_T, 0) + C
  max_profit = K - S_0 + C
  max_loss = S_0 + K - C
  S_up = 0.5 * (S_0 + K - C)

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Covered Short Strangle":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short ATM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  if np.min(strike_prices)<K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Put (K2<K1) :**",
            sorted(strike_prices))
  else:
    st.error('No Available Put Options for the selected Strike Price K1.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C = C_1 + C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 - np.maximum(S_T - K_1, 0) - np.maximum(K_2 - S_T, 0) + C
  max_profit = K_1 - S_0 + C
  max_loss = S_0 + K_2 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Strap":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K for the Long of 2 ATM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  if K_1 in strike_prices.tolist():
    K = st.sidebar.selectbox(
            "**Select Strike Price K for the Long ATM Put:**",
            sorted([K_1]))
  else:
    st.error('No Put Options Available for the selected Strike Price K.')
    st.stop()

  # Step 6: Get Premium
  D_1 = 2*option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  D = D_1 + D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = 2 * np.maximum(S_T - K, 0) + np.maximum(K - S_T, 0) - D
  max_profit = np.inf
  max_loss = D
  S_up = K + D/2
  S_down = K - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Strip":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K for the Long ATM Call:**",
          sorted(strike_prices))
  strike_prices = option_chain.puts['strike']
  if K_1 in strike_prices.tolist():
    K = st.sidebar.selectbox(
          "**Select Strike Price K for the Long of 2 ATM Put:**",
          sorted([K_1]))
  else:
    st.error('No Put Options Available for the Selected Strike Price K.')


  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K]['lastPrice'].values[0]
  D_2 = 2*option_chain.puts[option_chain.puts['strike'] == K]['lastPrice'].values[0]
  D = D_1 + D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K, 0) + 2 * np.maximum(K - S_T, 0) - D
  max_profit = np.inf
  max_loss = D
  S_up = K + D
  S_down = K - D/2

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_2, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Call Ratio Backspread":

  # Step 5: Select Strike Prices
  N_S = st.sidebar.number_input("Enter Number of ATM Call Ns you want to Short:", min_value=1, step=1)
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short of Ns close to ATM Call:**",
          sorted(strike_prices))
  N_L = st.sidebar.number_input("Enter Number of OTM Call Nl you want to Buy (Nl>Ns):", min_value=N_S, step=1)
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long of Nl OTM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = N_S*option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D = N_L*option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = N_L * np.maximum(S_T - K_2, 0) - N_S * np.maximum(S_T - K_1, 0) - H
  max_profit = np.inf
  max_loss = N_S * (K_2 - K_1) + H
  S_down = K_1 + H/N_S
  S_up = (N_L * K_2 - N_S * K_1 + H)/(N_L - N_S)

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Put Ratio Backspread":

  # Step 5: Select Strike Prices
  N_S = st.sidebar.number_input("Enter Number of ATM Put Ns you want to Short:", min_value=1, step=1)
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short of Ns close to ATM Put:**",
          sorted(strike_prices))
  N_L = st.sidebar.number_input("Enter Number of OTM Put Nl you want to Buy (Nl>Ns):", min_value=N_S, step=1)
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long of Nl OTM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = N_S*option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D = N_L*option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = N_L * np.maximum(K_2  - S_T, 0) - N_S * np.maximum(K_1 - S_T, 0) - H
  max_profit = N_L * K_2 - N_S * K_1 - H
  max_loss = N_S * (K_1 - K_2) + H
  S_up = K_1 + H/N_S
  S_down = (N_L * K_2 - N_S*K_1 - H)/(N_L - N_S)

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Ratio Call Spread":

  # Step 5: Select Strike Prices
  N_S = st.sidebar.number_input("Enter Number of ATM Call Ns you want to Short:", min_value=1, step=1)
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short of Ns close to ATM Call:**",
          sorted(strike_prices))
  N_L = st.sidebar.number_input("Enter Number of ITM Call Nl you want to Buy (Ns>Nl):", min_value=1, step=1, max_value = N_S)
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long of Nl ITM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = N_S*option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D = N_L*option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = N_L * np.maximum(S_T - K_2, 0) - N_S * np.maximum(S_T - K_1, 0) - H
  max_profit = N_L * (K_1 - K_2) - H
  max_loss = np.inf
  S_up = K_2 + H/N_L
  S_down = (N_S * K_1 - N_L * K_2 + H)/(N_S - N_L)

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Ratio Put Spread":

  # Step 5: Select Strike Prices
  N_S = st.sidebar.number_input("Enter Number of ATM Put Ns you want to Short:", min_value=1, step=1)
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short of Ns close to ATM Put:**",
          sorted(strike_prices))
  N_L = st.sidebar.number_input("Enter Number of ITM Put Nl you want to Buy (Ns>Nl):", min_value=1, step=1, max_value = N_S)
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long of Nl ITM Put:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C = N_S*option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D = N_L*option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = N_L * np.maximum(K_2 - S_T, 0) - N_S * np.maximum(K_1 - S_T, 0) - H
  max_profit = N_L * (K_2 - K_1) - H
  max_loss = N_S * K_1 - N_L * K_2 + H
  S_up = K_1 + H/N_S
  S_down = (N_L * K_2 - N_S * K_1 + H)/(N_L - N_S)

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6 = st.columns(4)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D, 2)}")
  with col5:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col6:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Call Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Call (kappa=K2-K3=K1-K2):",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short of 2 ATM Call (kappa=K2-K3=K1-K2):**",
          sorted(strike_prices))
  Kappa = K_1 - K_2
  if K_2 + Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Long ITM Call (kappa=K2-K3=K1-K2):**",
            sorted([K_2 - Kappa]))
  else:
    st.error(f'No ITM Call Options Available for the Selected Kappa ({Kappa})')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_1 = 2*option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) + np.maximum(S_T - K_3, 0) - 2 * np.maximum(S_T - K_2,0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D
  S_up = K_1 - D
  S_down = K_3 + D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Modified Call Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Call:**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short of 2 ATM Call:**",
          sorted(strike_prices))
  Kappa = K_1 - K_2

  if np.max(strike_prices)>K_2+Kappa:
    K_3 = st.sidebar.selectbox(
          "**Select Strike Price K3 for the Long ITM Call (K2-K3>K1-K2):**",
          sorted([price for price in strike_prices if( K_2-price>Kappa and price<K_2)]))
  else:
    st.error('No Available Call Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_1 = 2*option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  D = D_1+D_2-C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) + np.maximum(S_T - K_3, 0) - 2 * np.maximum(S_T - K_2, 0) - D
  max_profit = K_2 - K_3 - D
  max_loss = D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Put Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put (kappa=K3-K2=K2-K1):**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short of 2 ATM Put (kappa=K3-K2=K2-K1):**",
          sorted(strike_prices))
  Kappa = K_2-K_1
  if K_2 + Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Long ITM Put (kappa=K3-K2=K2-K1):**",
            sorted([K_2+Kappa]))
  else:
    st.error('No ITM Put Options available for the Selected Kappa')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = 2*option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) + np.maximum(K_3 - S_T, 0) - 2 * np.maximum(K_2 - S_T, 0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D
  S_up = K_3 - D
  S_down = K_1 + D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Modified Put Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put:**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short of 2 ATM Put:**",
          sorted(strike_prices))
  strike_prices_list = [price for price in strike_prices if (K_2-K_1>price-K_2 and price>K_2)]
  if strike_prices_list:
     K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Long ITM Put (K2-K1>K3-K2):**",
            sorted(strike_prices_list))
  else:
    st.error("No Available ITM Put for the selected Kappa.")
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = 2*option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  H = D_1+D_2-C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) + np.maximum(K_3 - S_T, 0) - 2 * np.maximum(K_2 - S_T, 0) - H
  max_profit = K_3 - K_2 - H
  max_loss = 2 * K_2 - K_1 - K_3 + H
  S_down = 2 * K_2 - K_3 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy ==  "Short Call Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short ITM Call (Kappa=K3-K2=K2-K1):**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long of 2 ATM Call (Kappa=K3-K2=K2-K1):**",
          sorted(strike_prices))
  Kappa = K_2-K_1
  if K_2 + Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short ATM Call (Kappa=K3-K2=K2-K1):**",
            sorted([price for price in strike_prices if price-K_2==K_2-K_1]))
  else:
    st.error('No Available Call Option for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D_1 = 2*option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  C = C_1 + C_2 - D_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff =  2 * np.maximum(S_T - K_2, 0) - np.maximum(S_T - K_1, 0) - np.maximum(S_T - K_3, 0) + C
  max_profit = C
  max_loss = K_2- K_1 - C
  S_up = K_3 - C
  S_down = K_1 + C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Put Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short ITM Put (Kappa=K1-K2=K2-K3):**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the long of 2 ATM Put (Kappa=K1-K2=K2-K3):**",
          sorted(strike_prices))
  Kappa = K_1-K_2
  if K_2 - Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short OTM Put (Kappa=K1-K2=K2-K3):**",
            sorted([price for price in strike_prices if K_2 - price == Kappa]))
  else:
    st.error('No Available Put Option for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = 2*option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  C = C_1 + C_2 - D_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = 2 * np.maximum(K_2 - S_T, 0) - np.maximum(K_1 - S_T, 0) - np.maximum(K_3 - S_T, 0) + C
  max_profit = C
  max_loss = Kappa - C
  S_up = K_1 - C
  S_down = K_3 + C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col7:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Iron Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put (Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  K_2_P = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short ATM Put (Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  if K_2_P in strike_prices.tolist():
    K_2 = st.sidebar.selectbox(
              "**Select Strike Price K2 for the Short ATM Call:**",
              sorted([K_2_P]))
  else:
    st.error('No Available Call Option for the Selected K2 Strike Price.')
    st.stop()
  Kappa = K_2-K_1
  if K_2+Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Long OTM Call (Kappa=K2-K1=K3-K2):**",
            sorted([K_2+Kappa]))
  else:
    st.error('No Available Call Option for the Selected Kappa')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  C = C_1 + C_2 - D_1 - D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) - np.maximum(S_T - K_2, 0) + np.maximum(S_T - K_3, 0) + C
  max_profit = C
  max_loss = K_2 - K_1 - C
  S_up = K_2 + C
  S_down = K_2- C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2 Put):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K2 Call):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Iron Butterfly":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short OTM Put (Kappa=K3-K2=K2-K1):**",
          sorted(strike_prices))
  K_2_P = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long ATM Put (Kappa=K3-K2=K2-K1):**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  if K_2_P in strike_prices.tolist():
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long ATM Call (Kappa=K3-K2=K2-K1):**",
            sorted([K_2_P]))
  else:
    st.error('No Available Call Option for the Selected K2 Strike Price.')
    st.stop()
  Kappa = K_2-K_1
  if K_2+Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short OTM Call (Kappa=K3-K2=K2-K1):**",
            sorted([K_2+Kappa]))
  else:
    st.error('No Available Call Option for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_2 - S_T, 0) + np.maximum(S_T - K_2, 0) - np.maximum(K_1 - S_T, 0) - np.maximum(S_T - K_3, 0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D
  S_up = K_2 + D
  S_down = K_2 - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2 Put):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K2 Call):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Call Condor":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long ITM Call (K2>K1, Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short ITM Call (K2>K1, Kappa=K2-K1=K3-K2):**",
            sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error('No Available Call Options Above the selected Strike Price K1.')
    st.stop()
  Kappa=K_2-K_1
  if K_2+Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_2+Kappa]))
  else:
    st.error('No Available Call Options for the selected Kappa.')
    st.stop()
  if K_3+Kappa in strike_prices.tolist():
    K_4 = st.sidebar.selectbox(
            "**Select Strike Price K4 for the Long OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_3+Kappa]))
  else:
    st.error('No Available Call Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_4]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3+K_4)/4) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3+K_4)/4)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_1, 0) - np.maximum(S_T - K_2, 0) - np.maximum(S_T - K_3, 0) + np.maximum(S_T - K_4, 0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D
  S_up = K_4 - D
  S_down = K_1 + D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K4):** {round(D_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Put Condor":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
      K_2 = st.sidebar.selectbox(
              "**Select Strike Price K2 for the Short OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
              sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error('No Available Put Options Above the selected Strike Price K1.')
    st.stop()
  Kappa = K_2-K_1
  if K_2+Kappa in strike_prices.tolist():
    K_3 = st.sidebar.selectbox(
            "**Select Strike Price K3 for the Short ITM Put (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_2+Kappa]))
  else:
      st.error('No Available Put Options for the selected Kappa.')
      st.stop()
  if K_3+Kappa in strike_prices.tolist():
    K_4 = st.sidebar.selectbox(
            "**Select Strike Price K4 for the Long ITM Put (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_3+Kappa]))
  else:
    st.error('No Available Put Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_4]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3+K_4)/4)  * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3+K_4)/4)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) - np.maximum(K_3 - S_T, 0) + np.maximum(K_4 - S_T, 0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D
  S_up = K_4 - D
  S_down = K_1 + D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K4):** {round(D_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Call Condor":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.calls['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short ITM Call (K2>K1, Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long ITM Call (K2>K1, Kappa=K2-K1=K3-K2):**",
            sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error('No Available Call Options Above the selected Strike Price K1.')
    st.stop()
  Kappa = K_2-K_1
  if K_2+Kappa in strike_prices.tolist():
      K_3 = st.sidebar.selectbox(
              "**Select Strike Price K3 for the Long OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
              sorted([K_2+Kappa]))
  else:
      st.error('No Available Call Options for the selected Kappa.')
      st.stop()
  if K_3+Kappa in strike_prices.tolist():
    K_4 = st.sidebar.selectbox(
            "**Select Strike Price K4 for the Short OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_3+Kappa]))
  else:
    st.error('No Available Call Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_4]['lastPrice'].values[0]
  C = C_1 + C_2 - D_1 - D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3+K_4)/4)  * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3+K_4)/4)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(S_T - K_2, 0) + np.maximum(S_T - K_3, 0) - np.maximum(S_T - K_1, 0) - np.maximum(S_T - K_4, 0) + C
  max_profit = C
  max_loss = K_2 - K_1 - C
  S_up = K_4 - C
  S_down = K_1 + C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K4):** {round(C_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy =="Short Put Condor":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
            sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error('No Available Put Options Above the selected Strike Price K1.')
    st.stop()
  Kappa = K_2-K_1
  if K_2+Kappa in strike_prices.tolist():
      K_3 = st.sidebar.selectbox(
              "**Select Strike Price K3 for the Long ITM Put (K4>K3, Kappa=K4-K3=K3-K2):**",
              sorted([K_2+Kappa]))
  else:
      st.error('No Available Put Options for the selected Kappa.')
      st.stop()
  if K_3+Kappa in strike_prices.tolist():
    K_4 = st.sidebar.selectbox(
            "**Select Strike Price K4 for the Short ITM Put (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_3+Kappa]))
  else:
    st.error('No Available Put Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.puts[option_chain.puts['strike'] == K_3]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_4]['lastPrice'].values[0]
  C = C_1 + C_2 - D_1 - D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3+K_4)/4) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3+K_4)/4)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_2 - S_T, 0) + np.maximum(K_3 - S_T, 0) - np.maximum(K_1 - S_T, 0) - np.maximum(K_4 - S_T, 0) + C
  max_profit = C
  max_loss = K_2 - K_1 - C
  S_up = K_4 - C
  S_down = K_1 + C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K4):** {round(C_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Iron Condor":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
            sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error('No Available Put Options Above the selected Strike Price K1.')
    st.stop()
  Kappa = K_2-K_1
  strike_prices = option_chain.calls['strike']
  if K_2+Kappa in strike_prices.tolist():
      K_3 = st.sidebar.selectbox(
              "**Select Strike Price K3 for the Short OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
              sorted([K_2+Kappa]))
  else:
      st.error('No Available Call Options for the selected Kappa.')
      st.stop()
  if K_3+Kappa in strike_prices.tolist():
    K_4 = st.sidebar.selectbox(
            "**Select Strike Price K4 for the Long OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_3+Kappa]))
  else:
    st.error('No Available Call Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_4]['lastPrice'].values[0]
  C = C_1 + C_2 - D_1 - D_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3+K_4)/4) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3+K_4)/4)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) + np.maximum(S_T - K_4, 0) - np.maximum(K_2 - S_T, 0) -  np.maximum(S_T - K_3, 0) + C
  max_profit = C
  max_loss = K_2 - K_1 - C
  S_up = K_3 + C
  S_down = K_2 - C

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K4):** {round(D_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Short Iron Condor":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
          sorted(strike_prices))
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long OTM Put (K2>K1, Kappa=K2-K1=K3-K2):**",
            sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error('No Available Put Options Above the selected Strike Price K1.')
    st.stop()
  Kappa = K_2-K_1
  strike_prices = option_chain.calls['strike']
  if K_2+Kappa in strike_prices.tolist():
      K_3 = st.sidebar.selectbox(
              "**Select Strike Price K3 for the Long OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
              sorted([K_2+Kappa]))
  else:
      st.error('No Available Call Options for the selected Kappa.')
      st.stop()
  if K_3+Kappa in strike_prices.tolist():
    K_4 = st.sidebar.selectbox(
            "**Select Strike Price K4 for the Short OTM Call (K4>K3, Kappa=K4-K3=K3-K2):**",
            sorted([K_3+Kappa]))
  else:
    st.error('No Available Call Options for the selected Kappa.')
    st.stop()

  # Step 6: Get Premium
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_4]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3+K_4)/4) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3+K_4)/4)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_2 - S_T, 0) + np.maximum(S_T - K_3, 0) - np.maximum(K_1 - S_T, 0) - np.maximum(S_T - K_4, 0) - D
  max_profit = K_2 - K_1 - D
  max_loss = D
  S_up = K_3 + D
  S_down = K_2 - D

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7, col8 = st.columns(6)
  with col3:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col4:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K4):** {round(C_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Long Box":

  # Step 5: Select Strike Prices
  put_strike_prices = option_chain.puts['strike']
  call_strike_prices = option_chain.calls['strike']
  K_1_P = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long ITM Put (K1>K2):**",
          sorted(put_strike_prices))
  if K_1_P in call_strike_prices.tolist():
    K_1 = st.sidebar.selectbox(
            "**Select Strike Price K1 for the Short OTM Call (K1>K2):**",
            sorted([K_1_P]))
  else:
    st.error('No Available Call Option for the selected Strike Price K1')
    st.stop()
  K_2_P = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short OTM Put (K1>K2):**",
          sorted(put_strike_prices))
  if K_2_P in call_strike_prices.tolist():
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Long ITM Call (K1>K2):**",
            sorted([K_2_P]))
  else:
    st.error('No Available Call Option for the selected Strike Price K2')
    st.stop()

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_1]['lastPrice'].values[0]
  C_2 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D = D_1 + D_2 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1_P+K_2_P)/2) * (min_percentage / 100)
  S_T_max = ((K_1_P+K_2_P)/2)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) + np.maximum(S_T - K_2, 0) - np.maximum(S_T - K_1, 0) - D
  max_profit = (K_1 - K_2) - D
  max_loss = np.inf

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col3, col4, col5, col6, col7 = st.columns(5)
  with col3:
      st.markdown(f"**Premium Paid (K1 Put):** {round(D_1, 2)}")
  with col4:
      st.markdown(f"**Premium Received (K2 Put):** {round(C_1, 2)}")
  with col5:
      st.markdown(f"**Premium Paid (K2 Call):** {round(D_2, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K1 Call):** {round(C_2, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")


elif strategy == "Collar":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put (K2>K1):**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  if np.max(strike_prices)>K_1:
    K_2 = st.sidebar.selectbox(
            "**Select Strike Price K2 for the Short OTM Call (K2>K1):**",
            sorted([price for price in strike_prices if price>K_1]))
  else:
    st.error("No Available Call Option for the selected Strike Price K1.")

  # Step 6: Get Premium
  D = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  H = D-C

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = S_T - S_0 + np.maximum(K_1 - S_T, 0) - np.maximum(S_T - K_2, 0) - H
  max_profit = K_2 - S_0 - H
  max_loss = S_0 - K_1 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8 = st.columns(4)
  with col5:
      st.markdown(f"**Premium Paid (K1):** {round(D, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K2):** {round(C, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bullish Short Seagull Spread":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short OTM Put:**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long ATM Call:**",
          sorted(strike_prices))
  K_3 = st.sidebar.selectbox(
          "**Select Strike Price K3 for the Short OTM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  H = D_1 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3)  * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3)   * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = -np.maximum(K_1 - S_T, 0) + np.maximum(S_T - K_2, 0) - np.maximum(S_T - K_3, 0) - H
  max_profit = K_3 - K_2 - H
  max_loss = K_1 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8, col9 = st.columns(5)
  with col5:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col7:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col8:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col9:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bullish Long Seagull Spread":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put:**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short ATM Put:**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  K_3 = st.sidebar.selectbox(
          "**Select Strike Price K3 for the Long OTM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  H = D_1 + D_2 - C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(K_2 - S_T, 0) + np.maximum(S_T - K_3, 0) - H
  max_profit = np.inf
  max_loss = K_2 - K_1 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8, col9 = st.columns(5)
  with col5:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col7:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col8:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col9:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bearish Long Seagull Spread":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Long OTM Put:**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Short ATM Call:**",
          sorted(strike_prices))
  K_3 = st.sidebar.selectbox(
          "**Select Strike Price K3 for the Long OTM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  C_1 = option_chain.calls[option_chain.calls['strike'] == K_2]['lastPrice'].values[0]
  D_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  H = D_1 + D_2 - C_1

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = np.maximum(K_1 - S_T, 0) - np.maximum(S_T - K_2, 0) + np.maximum(S_T - K_3, 0) - H
  max_profit = K_1 - H
  max_loss = K_3 - K_2 + H

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8, col9 = st.columns(5)
  with col5:
      st.markdown(f"**Premium Paid (K1):** {round(D_1, 2)}")
  with col6:
      st.markdown(f"**Premium Received (K2):** {round(C_1, 2)}")
  with col7:
      st.markdown(f"**Premium Paid (K3):** {round(D_2, 2)}")
  with col8:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col9:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Bearish Short Seagull Spread":

  # Step 5: Select Strike Prices
  strike_prices = option_chain.puts['strike']
  K_1 = st.sidebar.selectbox(
          "**Select Strike Price K1 for the Short OTM Put:**",
          sorted(strike_prices))
  K_2 = st.sidebar.selectbox(
          "**Select Strike Price K2 for the Long ATM Put:**",
          sorted(strike_prices))
  strike_prices = option_chain.calls['strike']
  K_3 = st.sidebar.selectbox(
          "**Select Strike Price K3 for the Short OTM Call:**",
          sorted(strike_prices))

  # Step 6: Get Premium
  C_1 = option_chain.puts[option_chain.puts['strike'] == K_1]['lastPrice'].values[0]
  D_1 = option_chain.puts[option_chain.puts['strike'] == K_2]['lastPrice'].values[0]
  C_2 = option_chain.calls[option_chain.calls['strike'] == K_3]['lastPrice'].values[0]
  H = D_1 - C_1 - C_2

  # Step 7: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2+K_3)/3) * (min_percentage / 100)
  S_T_max = ((K_1+K_2+K_3)/3)  * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 8: Calculate the payoff, max profit and max loss
  payoff = -np.maximum(K_1 - S_T, 0) + np.maximum(K_2 - S_T, 0) - np.maximum(S_T - K_3, 0) - H
  max_profit = K_2 - K_1 - H
  max_loss = np.inf

  # Step 9: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8, col9 = st.columns(5)
  with col5:
      st.markdown(f"**Premium Received (K1):** {round(C_1, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K2):** {round(D_1, 2)}")
  with col7:
      st.markdown(f"**Premium Received (K3):** {round(C_2, 2)}")
  with col8:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col9:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Calendar Call Spread":

  # Black-Scholes formula for call option price
  def bs_call(S, K, T, r, sigma):
      d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
      d2 = d1 - sigma * np.sqrt(T)
      return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

  # Step 3: Fetch expiration dates
  try:
      expiration_dates = stock.options
      short_expiration = st.sidebar.selectbox("Select Short Call Expiration Date:", expiration_dates)
      long_expiration = st.sidebar.selectbox(
          "Select Long Call Expiration Date (must be after short):",
          [date for date in expiration_dates if date > short_expiration]
      )
  except Exception:
      st.error("No options data available for the selected ticker.")
      st.stop()

  # Step 4: Strike price and market parameters selection
  short_options = stock.option_chain(short_expiration).calls
  long_options = stock.option_chain(long_expiration).calls
  common_strikes = np.intersect1d(short_options['strike'], long_options['strike'])
  K = st.sidebar.selectbox(
          "Select Strike Price K for the Long and Short of a close ATM Call:",
          sorted(common_strikes))
  r = st.sidebar.number_input("Select Risk-Free Rate (r):", min_value=0.0, value=0.05)
  sigma = st.sidebar.number_input("Select Volatility (σ):", min_value=0.0, value=0.2)

  # Step 5: Get premiums
  short_call_premium = short_options[short_options['strike'] == K]['lastPrice'].values[0]
  long_call_premium = long_options[long_options['strike'] == K]['lastPrice'].values[0]
  net_premium = long_call_premium - short_call_premium

  # Step 6: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 7: Calculate the payoff, max profit and max loss
  months_between_short_long = (pd.to_datetime(long_expiration).to_period("M") - pd.to_datetime(short_expiration).to_period("M")).n
  months_between_short_long = months_between_short_long / 12
  short_call_payoff = np.maximum(S_T - K, 0)
  long_call_payoff = bs_call(S_T, K, months_between_short_long, r, sigma)
  payoff = long_call_payoff - short_call_payoff - net_premium
  max_profit = np.max(payoff)
  max_loss = -np.min(payoff)

  # Step 8: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8 = st.columns(4)
  with col5:
      st.markdown(f"**Premium Received (K):** {round(short_call_premium, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K):** {round(long_call_premium, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Calendar Put Spread":

  # Black-Scholes formula for put option price
  def bs_put(S, K, T, r, sigma):
      d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
      d2 = d1 - sigma * np.sqrt(T)
      return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

  # Step 3: Fetch expiration dates
  try:
      expiration_dates = stock.options
      short_expiration = st.sidebar.selectbox("Select Short Put Expiration Date:", expiration_dates)
      long_expiration = st.sidebar.selectbox(
          "Select Long Put Expiration Date (must be after short):",
          [date for date in expiration_dates if date > short_expiration]
      )
  except Exception:
      st.error("No options data available for the selected ticker.")
      st.stop()

  # Step 4: Strike price and market parameters selection
  short_options = stock.option_chain(short_expiration).puts
  long_options = stock.option_chain(long_expiration).puts
  common_strikes = np.intersect1d(short_options['strike'], long_options['strike'])
  K = st.sidebar.selectbox(
          "Select Strike Price K for the Long and Short of a close to ATM Put:",
          sorted(common_strikes))
  r = st.sidebar.number_input("Select Risk-Free Rate (r):", min_value=0.0, value=0.05)
  sigma = st.sidebar.number_input("Select Volatility (σ):", min_value=0.0, value=0.2)

  # Step 5: Get premiums
  short_put_premium = short_options[short_options['strike'] == K]['lastPrice'].values[0]
  long_put_premium = long_options[long_options['strike'] == K]['lastPrice'].values[0]
  net_premium = long_put_premium - short_put_premium

  # Step 6: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = K * (min_percentage / 100)
  S_T_max = K * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 7: Calculate the payoff, max profit and max loss
  months_between_short_long = (pd.to_datetime(long_expiration).to_period("M") - pd.to_datetime(short_expiration).to_period("M")).n
  months_between_short_long = months_between_short_long / 12
  short_put_payoff = np.maximum(K-S_T, 0)
  long_put_payoff = bs_put(S_T, K, months_between_short_long, 0.05, 0.2)
  payoff = long_put_payoff - short_put_payoff - net_premium
  max_profit = np.max(payoff)
  max_loss = -np.min(payoff)

  # Step 8: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8 = st.columns(4)
  with col5:
      st.markdown(f"**Premium Received (K):** {round(short_put_premium, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K):** {round(long_put_premium, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Diagonal Call Spread":

  # Black-Scholes formula for call option price
  def bs_call(S, K, T, r, sigma):
      d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
      d2 = d1 - sigma * np.sqrt(T)
      return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

  # Step 3: Fetch expiration dates
  try:
      expiration_dates = stock.options
      long_expiration = st.sidebar.selectbox(
          "Select Long Call Expiration Date:",
          expiration_dates,
          index=len(expiration_dates) - 1) # max date as default
      short_expiration = st.sidebar.selectbox(
          "Select Short Call Expiration Date (must be before Long):",
          [date for date in expiration_dates if date < long_expiration]
      )
  except Exception:
      st.error("No options data available for the selected ticker.")
      st.stop()

  # Step 4: Strike price and market parameters selection
  short_options = stock.option_chain(short_expiration).calls
  long_options = stock.option_chain(long_expiration).calls
  K_1 = st.sidebar.selectbox(
          "Select Strike Price K1 for the Long deep ITM Call:",
          sorted(long_options['strike']))
  K_2 = st.sidebar.selectbox(
          "Select Strike Price K2 for the Short OTM Call:",
          sorted(short_options['strike']))
  r = st.sidebar.number_input("Select Risk-Free Rate (r):", min_value=0.0, value=0.05)
  sigma = st.sidebar.number_input("Select Volatility (σ):", min_value=0.0, value=0.2)

  # Step 5: Get premiums
  long_call_premium = long_options[long_options['strike'] == K_1]['lastPrice'].values[0]
  short_call_premium = short_options[short_options['strike'] == K_2]['lastPrice'].values[0]
  net_premium = long_call_premium - short_call_premium

  # Step 6: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 7: Calculate the payoff, max profit and max loss
  months_between_short_long = (pd.to_datetime(long_expiration).to_period("M") - pd.to_datetime(short_expiration).to_period("M")).n
  months_between_short_long = months_between_short_long / 12
  short_call_payoff = np.maximum(S_T - K_2, 0)
  long_call_payoff = bs_call(S_T, K_1, months_between_short_long, r, sigma)
  payoff = long_call_payoff - short_call_payoff - net_premium
  max_profit = np.max(payoff)
  max_loss = net_premium

  # Step 8: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8 = st.columns(4)
  with col5:
      st.markdown(f"**Premium Received (K2):** {round(short_call_premium, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K1):** {round(long_call_premium, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


elif strategy == "Diagonal Put Spread":

  # Black-Scholes formula for put option price
  def bs_put(S, K, T, r, sigma):
      d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
      d2 = d1 - sigma * np.sqrt(T)
      return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

  # Step 3: Fetch expiration dates
  try:
      expiration_dates = stock.options
      long_expiration = st.sidebar.selectbox(
          "Select Long Put Expiration Date:",
          expiration_dates,
          index=len(expiration_dates) - 1) # max date as default)
      short_expiration = st.sidebar.selectbox(
          "Select Short Put Expiration Date (must be before long):",
          [date for date in expiration_dates if date < long_expiration]
      )
  except Exception:
      st.error("No options data available for the selected ticker.")
      st.stop()

  # Step 4: Strike price and market parameters selection
  short_options = stock.option_chain(short_expiration).puts
  long_options = stock.option_chain(long_expiration).puts
  K_1 = st.sidebar.selectbox(
          "Select Strike Price K1 for the Long deep ITM Put:",
          sorted(long_options["strike"]))
  K_2 = st.sidebar.selectbox(
          "Select Strike Price K2 for the Short OTM Put:",
          sorted(short_options["strike"]))
  r = st.sidebar.number_input("Select Risk-Free Rate (r):", min_value=0.0, value=0.05)
  sigma = st.sidebar.number_input("Select Volatility (σ):", min_value=0.0, value=0.2)

  # Step 5: Get premiums
  long_put_premium = long_options[long_options['strike'] == K_1]['lastPrice'].values[0]
  short_put_premium = short_options[short_options['strike'] == K_2]['lastPrice'].values[0]
  net_premium = long_put_premium - short_put_premium

  # Step 6: Set min and max percentages for Strike and Calculate S_T
  st.empty()
  min_percentage = st.sidebar.slider(f"**Select Minimum % of Strike Price:**", 0, 100, 50)
  max_percentage = st.sidebar.slider(f"**Select Maximum % of Strike Price:**", 100, 200, 150)
  S_T_min = ((K_1+K_2)/2) * (min_percentage / 100)
  S_T_max = ((K_1+K_2)/2) * (max_percentage / 100)
  S_T = np.linspace(S_T_min, S_T_max, 100)

  # Step 7: Calculate the payoff, max profit and max loss
  months_between_short_long = (pd.to_datetime(long_expiration).to_period("M") - pd.to_datetime(short_expiration).to_period("M")).n
  months_between_short_long = months_between_short_long / 12
  short_put_payoff = np.maximum(K_2-S_T, 0)
  long_put_payoff = bs_put(S_T, K_1, months_between_short_long, r, sigma)
  payoff = long_put_payoff - short_put_payoff - net_premium
  max_profit = np.max(payoff)
  max_loss = net_premium

  # Step 8: Display information
  st.markdown(strategies_informations[strategy])
  col5, col6, col7, col8 = st.columns(4)
  with col5:
      st.markdown(f"**Premium Received (K2):** {round(short_put_premium, 2)}")
  with col6:
      st.markdown(f"**Premium Paid (K1):** {round(long_put_premium, 2)}")
  with col7:
      st.markdown(f"**Max Profit:** {round(max_profit, 2)}")
  with col8:
      st.markdown(f"**Max Loss:** {round(max_loss, 2)}")


# Step 10: Plot Payoff Diagram
fig = go.Figure()

# Add payoff line
fig.add_trace(go.Scatter(x=S_T, y=payoff, mode="lines", name="Payoff", line=dict(color="blue")))

# Add horizontal lines for max profit and max loss
if max_profit != np.inf:
  fig.add_hline(y=max_profit, line_dash="dash", line_color="green", annotation_text="Max Profit", annotation_position="top left")
if max_loss != np.inf:
  fig.add_hline(y=-max_loss, line_dash="dash", line_color="red", annotation_text="Max Loss", annotation_position="bottom left")

# Add vertical line for strike price
if strategy == "Diagonal Call Spread" or strategy == "Diagonal Put Spread" or strategy == "Collar" or strategy == "Long Box" or strategy == "Ratio Put Spread" or strategy == "Ratio Call Spread" or strategy == "Put Ratio Backspread" or strategy == "Call Ratio Backspread" or strategy == "Long Strangle" or strategy == "Short Strangle" or strategy == "Long Guts" or strategy == "Short Guts" or strategy == "Covered Short Strangle" or strategy == "Bull Call Spread" or strategy == "Bull Put Spread" or strategy == "Bear Call Spread" or strategy == "Bear Put Spread" or strategy == "Long Combo" or strategy == "Short Combo":
  fig.add_vline(x=K_1, line_dash="dot", line_color="yellow", annotation_text="K1", annotation_position="bottom right")
  fig.add_vline(x=K_2, line_dash="dot", line_color="orange", annotation_text="K2", annotation_position="bottom right")

elif strategy == "Bearish Short Seagull Spread" or strategy == "Bearish Long Seagull Spread" or strategy == "Bullish Long Seagull Spread" or strategy == "Bullish Short Seagull Spread" or strategy == "Short Iron Butterfly" or strategy == "Long Iron Butterfly" or strategy == "Short Put Butterfly" or strategy == "Short Call Butterfly" or strategy == "Modified Put Butterfly" or strategy == "Modified Call Butterfly" or strategy == "Long Put Butterfly" or strategy == "Long Call Butterfly" or strategy == "Bear Put Ladder" or strategy == "Bear Call Ladder" or strategy == "Bull Put Ladder" or strategy == "Bull Call Ladder":
  fig.add_vline(x=K_1, line_dash="dot", line_color="yellow", annotation_text="K1", annotation_position="bottom right")
  fig.add_vline(x=K_2, line_dash="dot", line_color="orange", annotation_text="K2", annotation_position="bottom right")
  fig.add_vline(x=K_3, line_dash="dot", line_color="brown", annotation_text="K3", annotation_position="bottom right")

elif  strategy == "Short Iron Condor" or strategy == "Long Iron Condor" or strategy == "Short Put Condor" or strategy == "Long Put Condor" or strategy == "Short Call Condor" or strategy == "Long Call Condor" :
  fig.add_vline(x=K_1, line_dash="dot", line_color="yellow", annotation_text="K1", annotation_position="bottom right")
  fig.add_vline(x=K_2, line_dash="dot", line_color="orange", annotation_text="K2", annotation_position="bottom right")
  fig.add_vline(x=K_3, line_dash="dot", line_color="brown", annotation_text="K3", annotation_position="bottom right")
  fig.add_vline(x=K_4, line_dash="dot", line_color="purple", annotation_text="K4", annotation_position="bottom right")

else :
  fig.add_vline(x=K, line_dash="dot", line_color="orange", annotation_text="K", annotation_position="bottom right")

# Add lines for context
fig.add_hline(y = 0, line_color = "black", line_width = 0.5)
fig.add_vline(x=S_0, line_dash="dot", line_color="black", annotation_text="S0", annotation_position="bottom left", line_width = 0.5)

# Update layout
fig.update_layout(
    title= "Payoff Diagram",
    xaxis_title="Stock Price at Expiration",
    yaxis_title="Profit / Loss",
    showlegend=True
)
# Show the chart
st.plotly_chart(fig)

st.write("---")
st.markdown(
    "Created by Antonin Bezard  |   [LinkedIn](https://www.linkedin.com/in/antonin-bezard-a11511177/)"
)
st.markdown(
    "Reference : Chapter 2 of 151 Trading Strategies by Z. Kakushadze and J.A. Serur  |   [Link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3247865)"
)
