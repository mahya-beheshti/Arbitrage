from prometheus_client import Counter, Histogram , Gauge

# Nobitex
NOBITEX_SUCCESS = Counter("nobitex_success_total", "Successful Nobitex requests")
NOBITEX_FAILURE = Counter("nobitex_failure_total", "Failed Nobitex requests")
NOBITEX_RESPONSE_TIME = Histogram(
    "nobitex_response_seconds", "Time to get Nobitex price"
)

# Wallex
WALLEX_SUCCESS = Counter("wallex_success_total", "Successful Wallex requests")
WALLEX_FAILURE = Counter("wallex_failure_total", "Failed Wallex requests")
WALLEX_RESPONSE_TIME = Histogram("wallex_response_seconds", "Time to get Wallex price")

# Arbitrage Opportunities
ARB_OPPORTUNITY_FOUND = Counter(
    "arbitrage_opportunities_total", "Number of arbitrage opportunities found"
)

# Arbitrage Opportunities For Each Currency
LAST_DIFF = Gauge("last_price_difference", "Last price difference per currency", ["currency"])
