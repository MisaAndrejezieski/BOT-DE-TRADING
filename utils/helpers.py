import os
import json
import platform
from datetime import datetime
from typing import Any, Dict
import pandas as pd

class SystemHelper:
    """Utilitários do sistema"""
    
    @staticmethod
    def get_system_info() -> Dict:
        """Retorna informações do sistema"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'python': platform.python_version(),
            'machine': platform.machine(),
            'node': platform.node()
        }
    
    @staticmethod
    def ensure_directories():
        """Garante que todos os diretórios necessários existam"""
        directories = [
            'data/logs',
            'data/history',
            'data/exports',
            'ml/models',
            'backtest/results',
            'tests/reports'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

class FileHelper:
    """Utilitários de arquivo"""
    
    @staticmethod
    def save_json(data: Any, filename: str):
        """Salva dados em JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_json(filename: str) -> Any:
        """Carrega dados de JSON"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def save_report(data: Dict, report_type: str):
        """Salva relatório com timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reports/{report_type}_{timestamp}.json"
        FileHelper.save_json(data, filename)
        return filename
    
    @staticmethod
    def save_backtest_results(results: Dict, filename: str = None):
        """Salva resultados de backtest"""
        if filename is None:
            filename = f"backtest/results/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        FileHelper.save_json(results, filename)
        return filename

class NumberHelper:
    """Utilitários de números"""
    
    @staticmethod
    def format_currency(value: float, currency: str = 'R$') -> str:
        """Formata valor monetário"""
        return f"{currency} {value:,.2f}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Formata porcentagem"""
        return f"{value:+.2f}%"
    
    @staticmethod
    def format_btc(value: float) -> str:
        """Formata quantidade de BTC"""
        return f"{value:.8f} BTC"

class DataFrameHelper:
    """Utilitários para DataFrames"""
    
    @staticmethod
    def resample_to_timeframe(df: pd.DataFrame, timeframe: str = '1h') -> pd.DataFrame:
        """Remapeia dados para timeframe específico"""
        df = df.set_index('timestamp')
        resampled = df.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        return resampled.reset_index()