import time

class ArbitrageScanner:
    """Stub simples de scanner de arbitragem"""
    def __init__(self):
        self.exchanges = []
        self.running = False

    def add_exchange(self, exchange_id: str):
        self.exchanges.append(exchange_id)

    def start_scanner(self, interval: int = 60):
        """Loop básico que apenas imprime status"""
        self.running = True
        while self.running:
            print(f"[Arbitrage] verificando em {self.exchanges}...")
            time.sleep(interval)

    def stop_scanner(self):
        self.running = False