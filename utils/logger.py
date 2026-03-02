import logging
import sys
from datetime import datetime
from pathlib import Path

# Criar diretório de logs se não existir
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Configuração do logger
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Arquivo de log com data
log_file = log_dir / f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Funções de conveniência
def info(msg):
    logger.info(msg)

def warning(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)

def debug(msg):
    logger.debug(msg)

def critical(msg):
    logger.critical(msg)