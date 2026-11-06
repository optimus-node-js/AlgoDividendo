# AlgoDividendo: Angel One Portfolio & Dividend Automation

> Python scripts that log in to Angel One SmartAPI, fetch holdings and live LTP/OHLC data, track portfolio performance on a schedule and combine it with dividend data, benchmarked across sequential, multithreaded and asyncio implementations.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white) ![Angel One SmartAPI](https://img.shields.io/badge/Angel%20One%20SmartAPI-E4572E?style=flat-square)

---

## Features

- **Holdings & portfolio tracking**: fetches holdings and computes P&L per stock and overall
- **LTP / OHLC drivers**: `DriverLTP.py`, `DriverOHLC.py` for live price snapshots
- **Dividend + LTP fusion**: `FetchDividendWithLTP_API.py` joins scraped dividend tables with live prices
- **Performance experiments**: multithreaded and `asyncio` versions of the tracker (`Production Environment/Testing`)
- **Scheduling scripts** for unattended runs, CLI and parameterised variants
- **HTML email template** for welcome / report mails

## Structure

```
AlgoScipts/            # core drivers and holdings fetcher
CLI Running Scripts/   # CLI-friendly variants
Param Scripts/         # parameterised runs
General Scripts/       # dividend table scraping + LTP join
Scheduling Scripts/    # scheduled portfolio tracker
Production Environment/  # main.py + async/multithread experiments
Database/              # Mongo upload utilities
Templates/             # HTML templates
```

## Getting Started

```bash
git clone https://github.com/optimus-node-js/AlgoDividendo.git
cd AlgoDividendo
```

```bash
pip install smartapi-python pyotp pymongo requests beautifulsoup4 logzero
```

Set your Angel One API key, client code, PIN, TOTP secret and MongoDB URI (hard-coded values were redacted, so move them to environment variables), then:

```bash
python "Production Environment/main.py"
```

**Related:** [Portfolio-Tracker](https://github.com/optimus-node-js/Portfolio-Tracker) · [PortfolioTrackerNode](https://github.com/optimus-node-js/PortfolioTrackerNode) · [DividendROI-Calculator](https://github.com/optimus-node-js/DividendROI-Calculator)

---

## Author

**Rahul Vishwakarma**, Senior Full Stack Developer based in Ahmedabad, India

[![Portfolio](https://img.shields.io/badge/Portfolio-rahul--vishwakarma--portfolio.vercel.app-0A66C2?style=flat-square&logo=vercel&logoColor=white)](https://rahul-vishwakarma-portfolio.vercel.app/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Rahul%20Vishwakarma-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://linkedin.com/in/rahul-vishwakarma-101346192)
[![Email](https://img.shields.io/badge/Email-karmarahul67%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:karmarahul67@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-optimus--node--js-181717?style=flat-square&logo=github)](https://github.com/optimus-node-js)

