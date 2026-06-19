"""
Paper Trading Binance Client Wrapper
Import this instead of making real API calls
"""
import sys
sys.path.insert(0, "/root/neko-futures-trader")

from paper_trading_mode import (
    paper_place_order as place_order,
    paper_place_algo_order as place_algo_order,
    paper_get_open_algo_orders as get_open_algo_orders,
    paper_get_position_risk as get_position_risk,
    paper_get_account as get_account
)

# Mock API_KEY check
API_KEY = "PAPER_MODE"
