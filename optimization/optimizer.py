from typing import Dict, Any, List
import itertools
import pandas as pd

class StrategyOptimizer:
    """Ferramenta simples de busca em grade para otimização de estratégia"""

    def __init__(self, backtest_engine):
        self.backtest = backtest_engine

    def optimize_parameters(self, df: pd.DataFrame, param_grid: Dict[str, List[Any]],
                            metric: str = 'sharpe') -> Dict:
        """Retorna o melhor conjunto de parâmetros com base na métrica desejada

        param_grid: dicionário nome -> lista de valores
        metric: nome da métrica em result['metrics'] (por exemplo 'sharpe_ratio')
        """
        # gera todas combinações
        keys = list(param_grid.keys())
        all_values = list(param_grid.values())

        all_results = []
        best_result = None
        best_params = {}

        for combo in itertools.product(*all_values):
            params = dict(zip(keys, combo))
            result = self.backtest.run_backtest(df, params)
            # obtém score da métrica
            score = 0
            if 'metrics' in result and result['metrics']:
                score = result['metrics'].get(metric + ('_ratio' if not metric.endswith('_ratio') else ''),
                                              result['metrics'].get(metric, 0))
            all_results.append({'params': params, 'metrics': result.get('metrics', {}), 'score': score})
            if best_result is None or score > best_result:
                best_result = score
                best_params = params

        # ordena resultados pela métrica
        all_results.sort(key=lambda x: x['score'], reverse=True)

        return {
            'best_params': best_params,
            'best_result': best_result,
            'all_results': all_results
        }


# classe auxiliar caso seja utilizada em algum outro lugar
class ParameterSuggestion:
    pass