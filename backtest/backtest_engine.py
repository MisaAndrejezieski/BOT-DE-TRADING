import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
from typing import List, Dict, Optional
import json

class BacktestEngine:
    """Motor de backtesting para testar estratégias"""
    
    def __init__(self, capital_inicial=1000, taxa=0.001):
        self.capital_inicial = capital_inicial
        self.capital = capital_inicial
        self.taxa = taxa
        self.trades = []
        self.metrics = {}
        
    def fetch_historical_data(self, exchange='binance', symbol='BTC/USDT', 
                              timeframe='1h', days=30) -> Optional[pd.DataFrame]:
        """Busca dados históricos reais da exchange"""
        try:
            exchange_class = getattr(ccxt, exchange)
            exch = exchange_class()
            
            since = exch.parse8601((datetime.now() - timedelta(days=days)).isoformat())
            
            ohlcv = exch.fetch_ohlcv(symbol, timeframe, since=since)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            print(f"Erro ao buscar dados: {e}")
            return None
    
    def run_backtest(self, df: pd.DataFrame, strategy_params: Dict) -> Dict:
        """Executa backtesting com dados históricos"""
        
        self.capital = self.capital_inicial
        self.trades = []
        
        position = None
        buy_signals = []
        sell_signals = []
        
        for i in range(len(df)):
            preco = df.iloc[i]['close']
            volume = df.iloc[i]['volume']
            timestamp = df.iloc[i]['timestamp']
            
            # Simula lógica da estratégia
            if position is None:
                # Verifica sinal de compra
                if self._check_buy_signal(df, i, strategy_params):
                    quantidade = self.capital / preco
                    valor_compra = quantidade * preco
                    taxa_paga = valor_compra * self.taxa
                    
                    position = {
                        'preco': preco,
                        'quantidade': quantidade,
                        'timestamp': timestamp,
                        'taxa': taxa_paga
                    }
                    
                    self.capital -= (valor_compra + taxa_paga)
                    
                    buy_signals.append({
                        'timestamp': timestamp,
                        'preco': preco,
                        'capital': self.capital
                    })
            
            else:
                # Verifica sinal de venda
                if self._check_sell_signal(df, i, position['preco'], strategy_params):
                    valor_venda = position['quantidade'] * preco
                    taxa_paga = valor_venda * self.taxa
                    
                    self.capital += (valor_venda - taxa_paga)
                    
                    lucro = ((preco - position['preco']) / position['preco']) * 100
                    lucro_abs = valor_venda - (position['quantidade'] * position['preco'])
                    
                    trade_info = {
                        'compra': position['timestamp'],
                        'venda': timestamp,
                        'preco_compra': position['preco'],
                        'preco_venda': preco,
                        'lucro': lucro,
                        'lucro_abs': lucro_abs,
                        'taxas': position['taxa'] + taxa_paga,
                        'hold_time': (timestamp - position['timestamp']).total_seconds() / 3600
                    }
                    
                    self.trades.append(trade_info)
                    
                    sell_signals.append({
                        'timestamp': timestamp,
                        'preco': preco,
                        'capital': self.capital,
                        'lucro': lucro
                    })
                    
                    position = None
        
        # Calcula métricas
        self._calculate_metrics()
        
        return {
            'capital_final': self.capital,
            'lucro_total': self.capital - self.capital_inicial,
            'rentabilidade': ((self.capital - self.capital_inicial) / self.capital_inicial) * 100,
            'trades': len(self.trades),
            'trades_lucro': len([t for t in self.trades if t['lucro'] > 0]),
            'trades_prejuizo': len([t for t in self.trades if t['lucro'] <= 0]),
            'maior_lucro': max([t['lucro'] for t in self.trades]) if self.trades else 0,
            'maior_prejuizo': min([t['lucro'] for t in self.trades]) if self.trades else 0,
            'lucro_medio': np.mean([t['lucro'] for t in self.trades]) if self.trades else 0,
            'taxas_totais': sum([t['taxas'] for t in self.trades]) if self.trades else 0,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'trades_detalhados': self.trades,
            'metrics': self.metrics
        }
    
    def _calculate_metrics(self):
        """Calcula métricas de performance"""
        if not self.trades:
            return
        
        lucros = [t['lucro'] for t in self.trades]
        
        # Sharpe Ratio simplificado
        retorno_medio = np.mean(lucros)
        desvio_padrao = np.std(lucros)
        
        if desvio_padrao > 0:
            sharpe = (retorno_medio / desvio_padrao) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Drawdown
        capital_series = [self.capital_inicial]
        for t in self.trades:
            capital_series.append(capital_series[-1] * (1 + t['lucro']/100))
        
        max_capital = capital_series[0]
        drawdowns = []
        
        for cap in capital_series:
            if cap > max_capital:
                max_capital = cap
            drawdown = (cap - max_capital) / max_capital * 100
            drawdowns.append(drawdown)
        
        self.metrics = {
            'sharpe_ratio': sharpe,
            'max_drawdown': min(drawdowns),
            'win_rate': (len([l for l in lucros if l > 0]) / len(lucros)) * 100,
            'avg_win': np.mean([l for l in lucros if l > 0]) if any(l > 0 for l in lucros) else 0,
            'avg_loss': np.mean([l for l in lucros if l < 0]) if any(l < 0 for l in lucros) else 0,
            'profit_factor': abs(sum([l for l in lucros if l > 0]) / sum([l for l in lucros if l < 0])) if any(l < 0 for l in lucros) else float('inf')
        }
    
    def _check_buy_signal(self, df, i, strategy_params):
        """Verifica sinal de compra baseado na estratégia -2%/+4%"""
        if i < 2:
            return False
        
        preco_atual = df.iloc[i]['close']
        preco_anterior = df.iloc[i-1]['close']
        
        queda = (preco_atual - preco_anterior) / preco_anterior * 100
        
        # Compra na queda de 2%
        return queda <= strategy_params.get('buy_threshold', -2.0)
    
    def _check_sell_signal(self, df, i, preco_compra, strategy_params):
        """Verifica sinal de venda baseado na estratégia -2%/+4%"""
        preco_atual = df.iloc[i]['close']
        
        lucro = (preco_atual - preco_compra) / preco_compra * 100
        
        # Proteção contra quedas
        if i > 2:
            precos_periodo = df.iloc[max(0, i-10):i]['close']
            preco_minimo = precos_periodo.min()
            queda_maxima = (preco_minimo - preco_compra) / preco_compra * 100
            
            if queda_maxima <= strategy_params.get('stop_loss', -3.0):
                # Se teve queda brusca, só vende se lucro > 4%
                return lucro >= strategy_params.get('sell_threshold', 4.0)
        
        # Vende no lucro de 4%
        return lucro >= strategy_params.get('sell_threshold', 4.0)