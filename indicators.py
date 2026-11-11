from config import (
    EMA_FAST,
    EMA_MEDIUM_1,
    EMA_MEDIUM_2,
    EMA_SLOW
)


class Indicators:

    def add_ema(self, df):

        df[f"EMA{EMA_FAST}"] = (
            df["close"]
            .ewm(span=EMA_FAST, adjust=False)
            .mean()
        )

        df[f"EMA{EMA_MEDIUM_1}"] = (
            df["close"]
            .ewm(span=EMA_MEDIUM_1, adjust=False)
            .mean()
        )

        df[f"EMA{EMA_MEDIUM_2}"] = (
            df["close"]
            .ewm(span=EMA_MEDIUM_2, adjust=False)
            .mean()
        )

        df[f"EMA{EMA_SLOW}"] = (
            df["close"]
            .ewm(span=EMA_SLOW, adjust=False)
            .mean()
        )

        return df


indicators = Indicators()