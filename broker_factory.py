from sim_broker import SimBroker

class BrokerFactory:
    @staticmethod
    def create(mode: str, initial_equity: float, point_value: int, margin_per_contract: int, contracts: int):
        if mode == "sim":
            return SimBroker(initial_equity, point_value, margin_per_contract, contracts)
        if mode == "shioaji":
            raise NotImplementedError("Shioaji 真實下單尚未啟用。V5 只接行情，V8 才會開真實下單。")
        raise ValueError(f"未知交易模式：{mode}")
