from dataclasses import dataclass
from enum import Enum


class State(Enum):
    UP = "UP"
    DOWN = "DOWN"


@dataclass
class Candle:
    i: int
    high: float
    low: float


@dataclass
class ConfirmedSL:
    sl_i: int
    price: float
    confirmed_i: int


class StructureEngine:
    def __init__(self):
        self.state = State.UP

        # UP: högsta och näst högsta ägda low
        self.highest_low = None
        self.second_highest_low = None

        # DOWN: lägsta och näst lägsta high
        self.lowest_high = None
        self.second_lowest_high = None

        # DOWN: exakt en potentiell SL
        self.potential_sl_i = None
        self.potential_sl_price = None

        self.confirmed_sls: list[ConfirmedSL] = []

    def on_candle(self, c: Candle):
        if self.state == State.UP:
            self._handle_up(c)
        else:
            self._handle_down(c)

    def _handle_up(self, c: Candle):
        # Uppdatera högsta och näst högsta low i UP
        if self.highest_low is None:
            self.highest_low = c.low

        elif c.low > self.highest_low:
            self.second_highest_low = self.highest_low
            self.highest_low = c.low

        elif c.low < self.highest_low and (
            self.second_highest_low is None or c.low > self.second_highest_low
        ):
            self.second_highest_low = c.low

        # Två ägda lows tagna = nedsekvens startar
        if self.second_highest_low is not None and c.low < self.second_highest_low:
            self.state = State.DOWN

            self.potential_sl_i = c.i
            self.potential_sl_price = c.low

            self.lowest_high = c.high
            self.second_lowest_high = None

            self.highest_low = None
            self.second_highest_low = None

            print(f"{c.i}: UP → DOWN | potential SL = {c.low}")

    def _handle_down(self, c: Candle):
        # Två ägda highs tagna = bekräfta SL
        if self.second_lowest_high is not None and c.high > self.second_lowest_high:
            sl = ConfirmedSL(
                sl_i=self.potential_sl_i,
                price=self.potential_sl_price,
                confirmed_i=c.i,
            )
            self.confirmed_sls.append(sl)

            print(
                f"{c.i}: SL confirmed | SL candle = {sl.sl_i}, "
                f"price = {sl.price}"
            )

            self.state = State.UP

            self.highest_low = c.low
            self.second_highest_low = None

            self.lowest_high = None
            self.second_lowest_high = None
            self.potential_sl_i = None
            self.potential_sl_price = None
            return

        # Ny lägre low = flytta potentiell SL
        if c.low < self.potential_sl_price:
            self.potential_sl_i = c.i
            self.potential_sl_price = c.low
            print(f"{c.i}: potential SL moved to {c.low}")

        # Uppdatera lägsta och näst lägsta high i DOWN
        if self.lowest_high is None:
            self.lowest_high = c.high

        elif c.high < self.lowest_high:
            self.second_lowest_high = self.lowest_high
            self.lowest_high = c.high

        elif c.high > self.lowest_high and (
            self.second_lowest_high is None or c.high < self.second_lowest_high
        ):
            self.second_lowest_high = c.high


if __name__ == "__main__":
    candles = [
        Candle(1, high=100, low=95),
        Candle(2, high=98, low=92),
        Candle(3, high=96, low=90),
        Candle(4, high=97, low=91),
        Candle(5, high=101, low=94),
        Candle(6, high=99, low=88),
        Candle(7, high=95, low=84),
        Candle(8, high=96, low=85),
        Candle(9, high=100, low=89),
    ]

    engine = StructureEngine()

    for candle in candles:
        engine.on_candle(candle)

    print("\nConfirmed SLs:")
    for sl in engine.confirmed_sls:
        print(sl)