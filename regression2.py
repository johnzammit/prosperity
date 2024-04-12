import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List
import numpy as np

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."

logger = Logger()

class Trader:
    max_position = {'AMETHYSTS' : 20, 'STARFRUIT' : 20}
    position = {'AMETHYSTS' : 0, 'STARFRUIT' : 0}
    def amethysts(self, order_depth, statePos):
        orders = {'AMETHYSTS' : []}
        prod = "AMETHYSTS"
        self.position[prod] = statePos.get(prod, 0)
        alrBought = 0
        alrSold = 0
        best_ask = 10000
        best_bid = 10000
        if len(order_depth[prod].sell_orders) != 0:
            sells = list(order_depth[prod].sell_orders.items())
            best_ask = sells[0][0]
            for ask, ask_amount in sells:
                if int(ask) < 10000:
                    if self.position[prod] + alrBought - ask_amount <= 20:
                        alrBought -= ask_amount
                        orders['AMETHYSTS'].append(Order(prod, ask, -ask_amount))
                    else:
                        num = max(20 - self.position[prod] - alrBought, 0)
                        orders['AMETHYSTS'].append(Order(prod, ask, num))
                        alrBought += num
                        logger.print("num: " + str(num))
                if int(ask) == 10000 and self.position[prod] + alrBought < 0:
                    alrBought -= ask_amount
                    orders['AMETHYSTS'].append(Order(prod, ask, -ask_amount))

        if len(order_depth[prod].buy_orders) != 0:
            buys = list(order_depth[prod].buy_orders.items())
            best_bid = buys[0][0]
            for bid, bid_amount in buys:
                if int(bid) > 10000:
                    if self.position[prod] - alrSold - bid_amount >= -20:
                        alrSold += bid_amount
                        orders['AMETHYSTS'].append(Order(prod, bid, -bid_amount))
                    else:
                        num = min(-20 - self.position[prod] + alrSold, 0)
                        orders['AMETHYSTS'].append(Order(prod, bid, num))
                        alrSold -= num
                        logger.print("num: " + str(num))
                if int(ask) == 10000 and self.position[prod] - alrSold > 0:
                    alrSold += bid_amount
                    orders['AMETHYSTS'].append(Order(prod, bid, -bid_amount))

        logger.print("Positions: " + str(self.position[prod]))
        logger.print("AlrSold: " + str(alrSold))
        logger.print("AlrBought: " + str(alrBought))

        orders['AMETHYSTS'].append(Order(prod, max(10003, best_ask - 1), min(0, -(self.position[prod] + self.max_position[prod] - alrSold))))
        orders['AMETHYSTS'].append(Order(prod, min(9997, best_bid + 1), max(0, self.max_position[prod] - self.position[prod] - alrBought)))

    
        return orders['AMETHYSTS']
    #################################################
    def spread_ (self, order_depth):
        best_bid = max(order_depth.buy_orders.keys(), default=0)
        best_ask = min(order_depth.sell_orders.keys(), default=0)
        mid_price = (best_ask + best_bid) / 2
        spread = (best_ask - best_bid) / mid_price
        return spread, mid_price


    # Orderbook imbalance: MAX ASK DEPTH - MAX BID DEPTH, or normalized version:  (MAX_ASK_DEPTH - MAX_BID_DEPTH)/TOTAL_ORDERBOOK_DEPTH  and MAX_ASK_DEPTH/MAX_BID_DEPTH. 
    def orderbook_imbalance (self, order_depth):
        max_ask_depth = len(order_depth.sell_orders.values())
        max_bid_depth = len(order_depth.buy_orders.values())
        total_depth = abs(max_ask_depth) + abs(max_bid_depth)

        if total_depth == 0:
            normalized_imbalance = 0
        else:
            normalized_imbalance = (max_ask_depth - max_bid_depth) / total_depth

        max_ratio = max_ask_depth / max_bid_depth if max_bid_depth != 0 else float('inf')

        return normalized_imbalance, max_ratio

    # RIP_INDICATOR: 1 if return on price in last x timestamps is >=y%, and 0 otherwise. (need to pick x and y). 
    def rip_indicator (self, trades, x, y):
        if len(trades) < x:
            return 0 
        returns = trades.pct_change(periods=x)
        
        return 1 if returns >= y else 0

    # X_VOL: (normalized) volatility (aka standard deviation) of stock in last x timestamps (need to pick x). 
    def x_vol (self, trades, x):
        if len(trades) < x:
            return 0
        latest_trades = trades[-x:]
        return np.std(latest_trades)

    # VOL_RATIO: (MAX_VOL_LAST_x_TIMESTAMPS - MIN_VOL_LAST_x_TIMESTAMPS)/AVG_VOL_LAST_x_TIMESTAMPS, (need to pick/refine x). 
    def vol_ratio (self, trades, x):
        if len(trades) < x:
            return 0 
        return trades.rolling(window=10).std().rolling(window=10).apply(lambda x: (max(x) - min(x)) / np.mean(x))


        


    def predict_returns(self,m1, m2, m3):
        
        coef_m1=  0.39326134154061504
        coef_m2=  0.3195257554864681
        coef_m3=  0.2866245722765353
        intercept=  2.9548692564912926

        prediction = (
                    coef_m1 * m1 + 
            coef_m2 * m2 + 
            coef_m3 * m3 + 
            intercept)

        return prediction

    def starfruit(self, order_depth, statePos, prev_mid_price):
        orders = {'STARFRUIT' : []}
        prod = "STARFRUIT"
        
        self.position[prod] = statePos.get(prod, 0)
        total = 0
        alrSold = 0
        best_ask = 0
        ask_vol = 0
        best_bid = 0
        bid_vol = 0
        if len(order_depth[prod].sell_orders) != 0:
            sells = list(order_depth[prod].sell_orders.items())
            best_ask = sells[0][0]
            ask_vol = sells[0][1]

        if len(order_depth[prod].buy_orders) != 0:
            buys = list(order_depth[prod].buy_orders.items())
            best_bid = buys[0][0]
            bid_vol = buys[0][1]

        mid_price = (best_ask + best_bid) / 2
        prev_mid_price = self.prev_mid_price
        if len(prev_mid_price) <= 3:
            prev_mid_price.append(mid_price)
            return orders['STARFRUIT']
        
        features = [prev_mid_price[-1], prev_mid_price[-2], prev_mid_price[-3]]
        returns = self.predict_returns(*features)
        returns = round(returns)
        logger.print(returns)
        
        if self.position[prod] < 15:
            max_buy = 20 - self.position[prod]
            orders['STARFRUIT'].append(Order('STARFRUIT', min(int(returns) - 2, best_bid + 1), max_buy))
        if self.position[prod] > -15:
            max_sell = 20 + self.position[prod]
            orders['STARFRUIT'].append(Order('STARFRUIT',max(int(returns) + 2, best_ask - 1), -max_sell))
        prev_mid_price.append(mid_price)
        return orders['STARFRUIT']
    
    def __init__(self):
        self.prev_mid_price = []
    def run(self, state: TradingState) -> tuple[dict[Symbol, list[Order]], int, str]:

        result = {'AMETHYSTS': [], 'STARFRUIT': []}
        conversions = 0
        trader_data = ""

        # TODO: Add logic
        prev_bid_ask_vol = []
        prev_mid_price = []
        amethystOrders = self.amethysts(state.order_depths, state.position)
        starfruitOrders = self.starfruit(state.order_depths, state.position, prev_mid_price)
        result['STARFRUIT'] = starfruitOrders
        result['AMETHYSTS'] = amethystOrders

        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data