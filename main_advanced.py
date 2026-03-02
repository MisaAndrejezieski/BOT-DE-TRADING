#!/usr/bin/env python3
"""
Bot de Trading Avançado - Versão Completa
Estratégia: -2% para COMPRA, +4% para VENDA
"""

import asyncio
import argparse
import sys
import threading
from datetime import datetime
import time

#--------- importuração das dependências externas --------------------------------
# these libraries must be installed via requirements.txt; if missing, show a clear
# error message and exit gracefully.
missing = []
try:
    import pandas as pd
except ImportError:
    missing.append('pandas')
try:
    import numpy as np
except ImportError:
    missing.append('numpy')
try:
    import ccxt
except ImportError:
    missing.append('ccxt')
try:
    from dotenv import load_dotenv
except ImportError:
    missing.append('python-dotenv')

if missing:
    print('Erro: bibliotecas necessárias não encontradas: ' + ', '.join(missing))
    print('Por favor, execute o script `scripts\\setup_windows.bat` para criar/ativar o ambiente virtual e instale as dependências.')
    print('Exemplo:')
    print('   powershell> scripts\\setup_windows.bat')
    sys.exit(1)

#--------------------------------------------------------------------------------

# Importações do projeto
from core.exchange import ExchangeManager
from core.strategy_avancada import EstrategiaAvancada
from core.indicators import AnaliseTecnica
from risk.risk_manager import RiskManager
from database.db_manager import DatabaseManager
from paper_trading.simulator import PaperTradingSimulator
from config.advanced_settings import AdvancedSettings
from optimization.optimizer import StrategyOptimizer
from backtest.backtest_engine import BacktestEngine
from utils.logger import logger, info, error, warning
from utils.helpers import SystemHelper, FileHelper, NumberHelper

# Tentar importar módulos opcionais
try:
    from mobile.telegram_advanced import TelegramBotAdvanced
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    warning("Módulo Telegram não disponível")

try:
    from ml.trainer import MLTrainer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    warning("Módulo Machine Learning não disponível")

try:
    from arbitrage.arbitrage_scanner import ArbitrageScanner
    ARBITRAGE_AVAILABLE = True
except ImportError:
    ARBITRAGE_AVAILABLE = False
    warning("Módulo Arbitragem não disponível")


class AdvancedTradingBot:
    """Versão avançada do bot com estratégia -2%/+4%"""
    
    def __init__(self):
        # Carrega configurações
        self.settings = AdvancedSettings.load_from_file()
        info("✅ Configurações carregadas")
        
        # Inicializa componentes core
        self.db = DatabaseManager()
        self.risk_manager = RiskManager(self.settings.trade_quantity * 350000)
        self.strategy = EstrategiaAvancada()
        self.indicators = AnaliseTecnica()
        self.backtest = BacktestEngine()
        self.paper_trading = PaperTradingSimulator()
        self.exchange = None
        
        # Componentes opcionais
        self.telegram = None
        self.ml_trainer = None
        self.arbitrage = None
        self.optimizer = None
        
        # Status
        self.running = False
        self.mode = 'paper'  # real, paper, backtest
        self.start_time = None
        self.capital_atual = 1000  # Valor inicial padrão
        
        # Threads
        self.threads = []
        
        # Garante diretórios
        SystemHelper.ensure_directories()
        
        info("🚀 Bot Avançado inicializado com sucesso!")
        self._print_banner()
    
    def _print_banner(self):
        """Mostra banner de inicialização"""
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║     🤖 BOT DE TRADING AVANÇADO - ESTRATÉGIA -2%/+4%     ║
        ╠══════════════════════════════════════════════════════════╣
        ║                                                          ║
        ║     🎯 COMPRA: -2% | VENDA: +4% | STOP: -3%             ║
        ║     🛡️ Risk Management Ativo                            ║
        ║     📊 Análise Técnica + ML (opcional)                  ║
        ║     📱 Controle via Telegram (opcional)                 ║
        ║     💾 Banco de Dados SQLite                            ║
        ║                                                          ║
        ╚══════════════════════════════════════════════════════════╝
        """)
    
    def initialize_telegram(self, token: str):
        """Inicializa bot do Telegram"""
        if not TELEGRAM_AVAILABLE:
            error("❌ Módulo Telegram não instalado")
            return
        
        try:
            self.telegram = TelegramBotAdvanced(token, self)
            telegram_thread = threading.Thread(target=self.telegram.run, daemon=True)
            telegram_thread.start()
            self.threads.append(telegram_thread)
            info("✅ Telegram bot inicializado")
        except Exception as e:
            error(f"❌ Erro ao inicializar Telegram: {e}")
    
    def initialize_ml(self):
        """Inicializa módulo de Machine Learning"""
        if not ML_AVAILABLE:
            warning("⚠️ Módulo ML não disponível")
            return
        
        try:
            self.ml_trainer = MLTrainer()
            if self.settings.ml_model_path:
                self.ml_trainer.load_model(self.settings.ml_model_path)
            info("✅ ML Trainer inicializado")
        except Exception as e:
            error(f"❌ Erro ao inicializar ML: {e}")
    
    def initialize_arbitrage(self):
        """Inicializa scanner de arbitragem"""
        if not ARBITRAGE_AVAILABLE:
            warning("⚠️ Módulo Arbitragem não disponível")
            return
        
        try:
            self.arbitrage = ArbitrageScanner()
            # Adiciona exchanges principais
            for exchange in self.settings.arbitrage_exchanges:
                self.arbitrage.add_exchange(exchange)
            
            # Inicia scanner automático
            scanner_thread = threading.Thread(
                target=self.arbitrage.start_scanner, 
                args=(60,), 
                daemon=True
            )
            scanner_thread.start()
            self.threads.append(scanner_thread)
            info("✅ Arbitrage Scanner inicializado")
        except Exception as e:
            error(f"❌ Erro ao inicializar arbitragem: {e}")
    
    def initialize_optimizer(self):
        """Inicializa otimizador de estratégia"""
        try:
            self.optimizer = StrategyOptimizer(self.backtest)
            info("✅ Strategy Optimizer inicializado")
        except Exception as e:
            error(f"❌ Erro ao inicializar optimizer: {e}")
    
    def run_paper_trading(self, days: int = 30):
        """Executa modo paper trading"""
        self.mode = 'paper'
        info(f"📊 Iniciando PAPER TRADING por {days} dias")
        
        # Define cenário
        print("\n📊 Cenários disponíveis:")
        print("   • normal - Mercado normal (recomendado)")
        print("   • crash - Mercado em queda")
        print("   • pump - Mercado em alta")
        print("   • lateral - Mercado lateral")
        print("   • volatile - Alta volatilidade")
        
        scenario = input("\nEscolha cenário (ENTER para normal): ").lower()
        if not scenario:
            scenario = 'normal'
        
        self.paper_trading.set_scenario(scenario)
        
        # Executa simulação
        try:
            asyncio.run(self.paper_trading.run_simulation(
                self.strategy, 
                hours=days*24
            ))
        except KeyboardInterrupt:
            print("\n\n🛑 Simulação interrompida pelo usuário")
        except Exception as e:
            error(f"❌ Erro na simulação: {e}")
    
    def run_backtest(self, days: int = 90, optimize: bool = False):
        """Executa modo backtesting"""
        self.mode = 'backtest'
        info(f"📊 Iniciando BACKTEST de {days} dias")
        
        # Busca dados históricos
        info("Buscando dados históricos...")
        df = self.backtest.fetch_historical_data(days=days)
        
        if df is None or df.empty:
            error("❌ Não foi possível obter dados históricos")
            return
        
        info(f"✅ Dados obtidos: {len(df)} candles")
        
        if optimize:
            # Otimização de parâmetros
            info("🔍 Iniciando otimização de parâmetros...")
            
            if not self.optimizer:
                self.initialize_optimizer()
            
            param_grid = {
                'buy_threshold': [-1.5, -2.0, -2.5],
                'sell_threshold': [3.5, 4.0, 4.5],
                'stop_loss': [-2.5, -3.0, -3.5]
            }
            
            results = self.optimizer.optimize_parameters(df, param_grid, metric='sharpe')
            
            info(f"✅ Melhores parâmetros encontrados:")
            info(f"   Compra: {results['best_params'].get('buy_threshold', -2.0)}%")
            info(f"   Venda: {results['best_params'].get('sell_threshold', 4.0)}%")
            info(f"   Stop: {results['best_params'].get('stop_loss', -3.0)}%")
            
            # Usa melhores parâmetros
            strategy_params = results['best_params']
        else:
            # Usa parâmetros atuais
            strategy_params = {
                'buy_threshold': self.settings.buy_threshold,
                'sell_threshold': self.settings.sell_threshold,
                'stop_loss': self.settings.stop_loss
            }
        
        # Executa backtest
        info("Executando backtest...")
        result = self.backtest.run_backtest(df, strategy_params)
        
        # Mostra resultados
        self._show_backtest_results(result)
        
        # Salva no banco
        self.db.save_setting('last_backtest', str(result))
        
        # Salva em arquivo
        filename = FileHelper.save_backtest_results(result)
        info(f"💾 Resultados salvos em: {filename}")
        
        return result
    
    def _show_backtest_results(self, result: dict):
        """Mostra resultados do backtest"""
        print("\n" + "="*70)
        print("📊 RESULTADOS DO BACKTEST - Estratégia -2%/+4%")
        print("="*70)
        
        print(f"\n💰 RESULTADO FINANCEIRO:")
        print(f"   Capital Inicial: {NumberHelper.format_currency(self.backtest.capital_inicial)}")
        print(f"   Capital Final: {NumberHelper.format_currency(result['capital_final'])}")
        print(f"   Lucro Total: {NumberHelper.format_currency(result['lucro_total'])}")
        print(f"   Rentabilidade: {NumberHelper.format_percentage(result['rentabilidade'])}")
        
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"   Total de Trades: {result['trades']}")
        print(f"   Trades com Lucro: {result['trades_lucro']}")
        print(f"   Trades com Prejuízo: {result['trades_prejuizo']}")
        
        if result['trades'] > 0:
            win_rate = (result['trades_lucro'] / result['trades']) * 100
            print(f"   Win Rate: {win_rate:.1f}%")
        
        print(f"   Maior Lucro: {NumberHelper.format_percentage(result['maior_lucro'])}")
        print(f"   Maior Prejuízo: {NumberHelper.format_percentage(result['maior_prejuizo'])}")
        print(f"   Lucro Médio: {NumberHelper.format_percentage(result['lucro_medio'])}")
        
        print(f"\n💸 TAXAS:")
        print(f"   Taxas Totais: {NumberHelper.format_currency(result['taxas_totais'])}")
        
        if result['lucro_total'] > 0:
            taxas_percent = (result['taxas_totais'] / result['lucro_total']) * 100
            print(f"   Taxas como % do Lucro: {taxas_percent:.1f}%")
        
        if 'metrics' in result and result['metrics']:
            print(f"\n📊 MÉTRICAS DE RISCO:")
            print(f"   Sharpe Ratio: {result['metrics'].get('sharpe_ratio', 0):.3f}")
            print(f"   Max Drawdown: {result['metrics'].get('max_drawdown', 0):.2f}%")
            print(f"   Profit Factor: {result['metrics'].get('profit_factor', 0):.3f}")
    
    def run_optimize(self, days: int = 180):
        """Executa apenas otimização"""
        info(f"🔍 Iniciando OTIMIZAÇÃO com {days} dias de dados")
        
        if not self.optimizer:
            self.initialize_optimizer()
        
        # Busca dados
        df = self.backtest.fetch_historical_data(days=days)
        
        if df is None or df.empty:
            error("❌ Não foi possível obter dados históricos")
            return
        
        # Grid de parâmetros
        param_grid = {
            'buy_threshold': [-1.0, -1.5, -2.0, -2.5, -3.0],
            'sell_threshold': [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
            'stop_loss': [-2.0, -2.5, -3.0, -3.5, -4.0, -5.0]
        }
        
        # Otimiza
        results = self.optimizer.optimize_parameters(df, param_grid, metric='sharpe')
        
        print("\n" + "="*70)
        print("🏆 MELHORES PARÂMETROS ENCONTRADOS")
        print("="*70)
        
        print(f"\n🎯 COMPRA: {results['best_params'].get('buy_threshold', 0)}%")
        print(f"🎯 VENDA: {results['best_params'].get('sell_threshold', 0)}%")
        print(f"🛑 STOP: {results['best_params'].get('stop_loss', 0)}%")
        print(f"📊 Sharpe Ratio: {results['best_result']:.3f}")
        
        print("\n📋 TOP 10 MELHORES COMBINAÇÕES:")
        for i, r in enumerate(results['all_results'][:10]):
            params = r['params']
            print(f"{i+1}. Compra: {params.get('buy_threshold', 0)}% | "
                  f"Venda: {params.get('sell_threshold', 0)}% | "
                  f"Stop: {params.get('stop_loss', 0)}% | "
                  f"Sharpe: {r['metrics'].get('sharpe_ratio', 0):.3f}")
    
    def run_real(self):
        """Executa modo real com dinheiro de verdade"""
        self.mode = 'real'
        warning("⚠️  MODO REAL ATIVADO - DINHEIRO DE VERDADE EM JOGO!")
        
        # Verifica configurações de segurança
        self._check_safety_settings()
        
        # Pergunta confirmação
        print("\n❓ CONFIRMAÇÕES NECESSÁRIAS:")
        print("1. Você leu e entendeu os riscos?")
        print("2. Está preparado para perder dinheiro?")
        print("3. Testou em paper trading por pelo menos 30 dias?")
        
        response = input("\nDigite 'SIM' para confirmar e continuar: ")
        if response != 'SIM':
            info("Operação cancelada pelo usuário")
            return
        
        # Inicializa exchange
        try:
            self.exchange = ExchangeManager()
            info("✅ Exchange inicializada")
        except Exception as e:
            error(f"❌ Erro ao inicializar exchange: {e}")
            return
        
        # Verifica saldo
        balance = self.exchange.get_balance()
        if balance <= 0:
            error("❌ Saldo insuficiente ou erro na conexão")
            return
        
        info(f"💰 Saldo disponível: {NumberHelper.format_currency(balance)}")
        
        # Registra início
        self.start_time = datetime.now()
        self.running = True
        self.capital_atual = balance
        
        # Inicia loop principal
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            error(f"❌ Erro fatal: {e}")
            self.shutdown()
    
    def _check_safety_settings(self):
        """Verifica configurações de segurança"""
        info("🔒 Verificando configurações de segurança...")
        
        # Verifica stop loss
        if self.settings.stop_loss >= 0:
            error("❌ STOP LOSS não configurado! Configure um valor negativo.")
            sys.exit(1)
        
        # Verifica limite de trades
        if self.settings.max_daily_trades > 5:
            warning("⚠️ Limite de trades diário muito alto (>5)")
        
        # Verifica tamanho da posição
        position_value = self.settings.trade_quantity * 350000
        if position_value > self.capital_atual * 0.1:
            warning(f"⚠️ Posição de {NumberHelper.format_currency(position_value)} > 10% do capital")
        
        info("✅ Verificações de segurança concluídas")
    
    def _main_loop(self):
        """Loop principal do bot"""
        info("▶️ Iniciando loop principal...")
        
        check_interval = 60  # segundos
        last_snapshot = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # 1. Obtém preço atual
                ticker = self.exchange.get_ticker(self.settings.symbol)
                if not ticker:
                    time.sleep(check_interval)
                    continue
                
                current_price = ticker['last']
                volume = ticker.get('volume', 0)
                
                # 2. Atualiza indicadores
                self.strategy.update_price_history(current_price)
                self.strategy.update_volume_history(volume)
                
                # 3. Verifica sinais de trading
                if not self.strategy.position:
                    # Análise para compra
                    analysis = self.strategy.analisar_momento_compra(current_price)
                    
                    if analysis['decisao']:
                        info(f"🎯 SINAL DE COMPRA! Confiança: {analysis['confianca']:.1f}%")
                        for motivo in analysis['motivos']:
                            info(f"   • {motivo}")
                        
                        # Verifica risco
                        trade_value = current_price * self.settings.trade_quantity
                        risk_check = self.risk_manager.check_trade_allowed(trade_value)
                        
                        if risk_check['allowed']:
                            order = self.exchange.create_buy_order(
                                self.settings.symbol,
                                self.settings.trade_quantity
                            )
                            
                            if order:
                                position = self.strategy.execute_buy(current_price)
                                
                                # Registra no banco
                                self.db.save_trade({
                                    'type': 'BUY',
                                    'price': current_price,
                                    'quantity': self.settings.trade_quantity,
                                    'value': trade_value,
                                    'fee': trade_value * 0.001,
                                    'strategy_params': analysis
                                })
                                
                                # Snapshot
                                self.db.save_capital_snapshot(
                                    self.risk_manager.capital_atual,
                                    current_price
                                )
                                
                                # Notificação
                                if self.telegram:
                                    asyncio.create_task(
                                        self.telegram.send_notification(
                                            f"🟢 COMPRA EXECUTADA\n"
                                            f"Preço: {NumberHelper.format_currency(current_price)}\n"
                                            f"Confiança: {analysis['confianca']:.1f}%"
                                        )
                                    )
                        else:
                            warning(f"⚠️ Trade bloqueado: {risk_check['reasons']}")
                
                else:
                    # Análise para venda
                    analysis = self.strategy.analisar_momento_venda(
                        current_price, 
                        self.strategy.position['buy_price']
                    )
                    
                    if analysis['decisao']:
                        info(f"🎯 SINAL DE VENDA! Confiança: {analysis['confianca']:.1f}%")
                        for motivo in analysis['motivos']:
                            info(f"   • {motivo}")
                        
                        order = self.exchange.create_sell_order(
                            self.settings.symbol,
                            self.settings.trade_quantity
                        )
                        
                        if order:
                            result = self.strategy.execute_sell(current_price)
                            
                            # Registra trade
                            self.db.save_trade({
                                'type': 'SELL',
                                'price': current_price,
                                'quantity': self.settings.trade_quantity,
                                'value': current_price * self.settings.trade_quantity,
                                'fee': current_price * self.settings.trade_quantity * 0.001,
                                'profit_percentage': result['profit_percentage'],
                                'profit_abs': result['profit_abs'],
                                'strategy_params': analysis
                            })
                            
                            # Registra no risk manager
                            self.risk_manager.register_trade({
                                'pnl': result['profit_abs'],
                                'percentage': result['profit_percentage']
                            })
                            
                            # Atualiza capital
                            self.capital_atual += result['profit_abs']
                            
                            # Snapshot
                            self.db.save_capital_snapshot(
                                self.capital_atual,
                                current_price
                            )
                            
                            # Notificação
                            if self.telegram:
                                asyncio.create_task(
                                    self.telegram.send_notification(
                                        f"🔴 VENDA EXECUTADA\n"
                                        f"Preço: {NumberHelper.format_currency(current_price)}\n"
                                        f"Lucro: {NumberHelper.format_percentage(result['profit_percentage'])}\n"
                                        f"Motivos: {', '.join(analysis['motivos'][:2])}"
                                    )
                                )
                
                # Snapshot periódico (a cada 15 minutos)
                if current_time - last_snapshot > 900:
                    self.db.save_capital_snapshot(
                        self.capital_atual,
                        current_price
                    )
                    last_snapshot = current_time
                    
                    # Log de status
                    info(f"📊 Status: Capital {NumberHelper.format_currency(self.capital_atual)} | "
                         f"Preço BTC {NumberHelper.format_currency(current_price)}")
                
                # Verifica alerts
                self._check_alerts(current_price)
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                error(f"❌ Erro no loop principal: {e}")
                time.sleep(check_interval)
    
    def _check_alerts(self, current_price: float):
        """Verifica condições de alerta"""
        
        # Drawdown alert
        risk_report = self.risk_manager.get_risk_report()
        drawdown = risk_report['drawdown']
        
        if drawdown > 10:
            msg = f"⚠️ Drawdown alto: {drawdown:.1f}%"
            warning(msg)
            self.db.add_alert('drawdown', msg)
            
            if self.telegram:
                asyncio.create_task(
                    self.telegram.send_notification(f"🚨 {msg}")
                )
        
        # Lucro significativo
        if self.strategy.position:
            profit = (current_price - self.strategy.position['buy_price']) / self.strategy.position['buy_price'] * 100
            if profit > 5:
                msg = f"🎯 Lucro de {profit:.1f}% na posição atual"
                info(msg)
                self.db.add_alert('profit', msg)
    
    def generate_report(self):
        """Gera relatório completo de performance"""
        info("📊 Gerando relatório de performance...")
        
        # Busca dados do banco
        trades_df = self.db.get_trade_history(days=30)
        capital_df = self.db.get_capital_history(days=30)
        
        print("\n" + "="*70)
        print("📈 RELATÓRIO DE PERFORMANCE - 30 DIAS")
        print("="*70)
        
        if trades_df.empty:
            print("\nNenhum trade encontrado no período")
            return
        
        # Estatísticas de trades
        total_trades = len(trades_df)
        trades_lucro = len(trades_df[trades_df['profit_percentage'] > 0])
        trades_prejuizo = len(trades_df[trades_df['profit_percentage'] <= 0])
        
        print(f"\n📊 ESTATÍSTICAS DE TRADES:")
        print(f"   Total de Trades: {total_trades}")
        print(f"   Trades com Lucro: {trades_lucro} ({trades_lucro/total_trades*100:.1f}%)")
        print(f"   Trades com Prejuízo: {trades_prejuizo} ({trades_prejuizo/total_trades*100:.1f}%)")
        print(f"   Lucro Médio: {trades_df['profit_percentage'].mean():.2f}%")
        print(f"   Maior Lucro: {trades_df['profit_percentage'].max():.2f}%")
        print(f"   Maior Prejuízo: {trades_df['profit_percentage'].min():.2f}%")
        
        # Resultado financeiro
        if not capital_df.empty:
            capital_inicial = capital_df.iloc[0]['capital']
            capital_final = capital_df.iloc[-1]['capital']
            lucro_total = capital_final - capital_inicial
            
            print(f"\n💰 RESULTADO FINANCEIRO:")
            print(f"   Capital Inicial: {NumberHelper.format_currency(capital_inicial)}")
            print(f"   Capital Final: {NumberHelper.format_currency(capital_final)}")
            print(f"   Lucro/Prejuízo: {NumberHelper.format_currency(lucro_total)}")
            print(f"   Rentabilidade: {NumberHelper.format_percentage((lucro_total/capital_inicial)*100)}")
        
        # Performance por dia
        print(f"\n📅 PERFORMANCE DIÁRIA:")
        trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.date
        daily_pnl = trades_df.groupby('date')['profit_abs'].sum()
        
        for date, pnl in daily_pnl.items():
            print(f"   {date}: {NumberHelper.format_currency(pnl)}")
        
        # Salva relatório
        report_data = {
            'trades': trades_df.to_dict('records'),
            'capital_history': capital_df.to_dict('records') if not capital_df.empty else [],
            'summary': {
                'total_trades': total_trades,
                'win_rate': trades_lucro/total_trades*100,
                'total_profit': lucro_total if 'lucro_total' in locals() else 0
            }
        }
        
        filename = FileHelper.save_report(report_data, 'performance')
        print(f"\n💾 Relatório salvo em: {filename}")
        print("="*70)
    
    def shutdown(self):
        """Desliga o bot com segurança"""
        info("🛑 Iniciando desligamento seguro...")
        
        self.running = False
        
        # Salva snapshot final
        try:
            if hasattr(self, 'exchange') and self.exchange:
                ticker = self.exchange.get_ticker()
                if ticker:
                    self.db.save_capital_snapshot(
                        self.capital_atual,
                        ticker['last']
                    )
        except:
            pass
        
        # Salva configurações
        self.settings.save_to_file()
        
        info("👋 Bot desligado com sucesso!")
        sys.exit(0)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Bot de Trading Avançado - Estratégia -2%/+4%')
    
    parser.add_argument('--mode', type=str, default='paper',
                        choices=['real', 'paper', 'backtest', 'optimize'],
                        help='Modo de operação (padrão: paper)')
    
    parser.add_argument('--days', type=int, default=30,
                        help='Dias para backtest/paper trading (padrão: 30)')
    
    parser.add_argument('--telegram', type=str,
                        help='Token do Telegram bot')
    
    parser.add_argument('--ml', action='store_true',
                        help='Ativar Machine Learning')
    
    parser.add_argument('--arbitrage', action='store_true',
                        help='Ativar arbitragem')
    
    parser.add_argument('--optimize', action='store_true',
                        help='Otimizar parâmetros (para backtest)')
    
    parser.add_argument('--report', action='store_true',
                        help='Gerar relatório')
    
    args = parser.parse_args()
    
    # Cria bot
    bot = AdvancedTradingBot()
    
    # Inicializa componentes opcionais
    if args.telegram:
        bot.initialize_telegram(args.telegram)
    
    if args.ml:
        bot.initialize_ml()
    
    if args.arbitrage:
        bot.initialize_arbitrage()
    
    # Executa modo escolhido
    if args.mode == 'paper':
        bot.run_paper_trading(days=args.days)
    
    elif args.mode == 'backtest':
        bot.run_backtest(days=args.days, optimize=args.optimize)
    
    elif args.mode == 'real':
        bot.run_real()
    
    elif args.mode == 'optimize':
        bot.run_optimize(days=args.days)
    
    # Gera relatório se solicitado
    if args.report:
        bot.generate_report()


if __name__ == "__main__":
    main()