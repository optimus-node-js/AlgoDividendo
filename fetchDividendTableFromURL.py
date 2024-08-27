import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
from datetime import datetime

IssuerCompany, share_symbols, StockCode, Ex_DividendDate, RecordDate, DividendType, DividendAmount, CMP = [], [], [], [], [], [], [], []

# URL to fetch the data from
url = 'https://www.chittorgarh.com/report/stock-dividend/135/'

# Set headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Fetch HTML data from the URL
response = requests.get(url, headers=headers)
html_table_data = response.text

# Parse HTML table data
soup = BeautifulSoup(html_table_data, 'html.parser')

# Find all rows in the table
rows = soup.find_all('tr')

for row in rows:
    columns = row.find_all('td')
    if len(columns) >= 8:
        company_name_tag = columns[0].find('a')
        company_name = company_name_tag.get_text(strip=True) if company_name_tag else columns[0].get_text(strip=True)
        company_name = company_name.replace('$', '')  # Remove the $ symbol
        stock_symbol = columns[1].get_text(strip=True)
        stock_code = columns[2].get_text(strip=True)
        ex_dividend_date = columns[3].get_text(strip=True)
        record_date = columns[4].get_text(strip=True)
        dividend_type = columns[5].get_text(strip=True)
        dividend_amount = columns[6].get_text(strip=True)
        cmp = columns[7].get_text(strip=True)

        IssuerCompany.append(company_name)
        share_symbols.append(stock_symbol + '-EQ')
        StockCode.append(stock_code)
        Ex_DividendDate.append(ex_dividend_date)
        RecordDate.append(record_date)
        DividendType.append(dividend_type)
        DividendAmount.append(dividend_amount)
        CMP.append(cmp)

# Prompt user for investment amount
investment_amount = float(input("Enter your investment amount: "))

# Calculate Qty, Potential Dividend, and Invest Amount
Qty = []
PotentialDividend = []
InvestAmount = []
DividendStatus = []

# Current date for checking dividend status
current_date = datetime.now().date()

for i in range(len(CMP)):
    current_price = float(CMP[i])
    qty = investment_amount // current_price

    try:
        potential_dividend = qty * float(DividendAmount[i])
    except ValueError:
        potential_dividend = 'N/A'

    invest_amount = qty * current_price

    # Determine dividend status
    ex_date = datetime.strptime(Ex_DividendDate[i], '%b %d, %Y').date()
    if current_date >= ex_date:
        status = 'Missed'
    else:
        status = 'Active'

    Qty.append(qty)
    PotentialDividend.append(f"{potential_dividend:.2f}" if potential_dividend != 'N/A' else potential_dividend)
    InvestAmount.append(f"{invest_amount:.2f}")
    DividendStatus.append(status)

# Create a table using tabulate
table_data = list(
    zip(IssuerCompany, share_symbols, Ex_DividendDate, DividendStatus, DividendAmount, CMP, Qty, PotentialDividend,
        InvestAmount))
headers = ["Company Name", "Stock Symbol", "Ex-Date", "Dividend Status", "Dividend Amount", "Current Price", "Qty",
           "Potential Dividend", "Invest Amount"]

print(tabulate(table_data, headers=headers, tablefmt="pretty"))
