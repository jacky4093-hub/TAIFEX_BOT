"""
交易介面工廠。

目前只啟用 sim 模擬交易。
未來 V8 可新增 shioaji 真實下單，但預設必須鎖住，避免誤下單。
"""
from trader import SimulatedTrader


class BrokerFactory:
    SIM = "sim"
    SHIOAJI = "shioaji"

    @staticmethod
    def create(
        mode: str,
        initial_equity: float,
        point_value: int,
        margin_per_contract: int,
        contracts: int,
        **kwargs,
    ):
        mode = (mode or BrokerFactory.SIM).lower()

        if mode == BrokerFactory.SIM:
            return SimulatedTrader(
                initial_equity=initial_equity,
                point_value=point_value,
                margin_per_contract=margin_per_contract,
                contracts=contracts,
            )

        if mode == BrokerFactory.SHIOAJI:
            raise NotImplementedError("Shioaji 真實下單尚未啟用。")

        raise ValueError(f"未知交易模式：{mode}")
