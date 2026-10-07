import logging
import os
from datetime import datetime

def setup_logger():
    """Configura o sistema de log estruturado para escrever em arquivos."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    filename = datetime.now().strftime('tradutor_%Y%m%d.log')
    filepath = os.path.join(log_dir, filename)

    # Cria o logger raiz do projeto
    logger = logging.getLogger("Taradutor")
    logger.setLevel(logging.INFO)

    # Evita adicionar múltiplos handlers se for chamado mais de uma vez
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')

        # File Handler (Arquivo)
        fh = logging.FileHandler(filepath, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)

        # Stream Handler (Console para erros graves)
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

app_logger = setup_logger()
