import yfinance as yf

ticker = yf.Ticker("AAPL")
balance_sheet = ticker.balance_sheet
print(balance_sheet)
total_debt = balance_sheet.loc['Total Debt']