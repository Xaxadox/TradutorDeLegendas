import time
from googletrans import Translator
from .base import ITradutor
from ..logger import app_logger

class ExcecaoDisjuntorAberto(Exception):
    pass

class MotorTraducaoGoogle(ITradutor):
    """
    Implementação Concreta para a API do Google Translate.
    Encapsula rate-limits, retentativas e possui Circuit Breaker:
    se falhar 5 vezes seguidas, para de tentar por 60 segundos
    para evitar banimentos permanentes ou travamentos da thread.
    """
    
    def __init__(self, max_retries=3, failure_threshold=5, recovery_timeout=60):
        self._engine = Translator()
        self._max_retries = max_retries
        
        # Estado do Circuit Breaker
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._last_failure_time = 0
        self._recovery_timeout = recovery_timeout
        self._is_open = False

    def _check_circuit(self):
        if self._is_open:
            if time.time() - self._last_failure_time > self._recovery_timeout:
                app_logger.info("Circuit Breaker: Testando recuperação da API (Half-Open).")
                self._is_open = False
            else:
                raise ExcecaoDisjuntorAberto("Circuit Breaker ABERTO: Abortando para evitar banimentos.")

    def _record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._is_open = True
            app_logger.error(f"Circuit Breaker disparado! Atingiu {self._failure_threshold} falhas seguidas.")

    def _record_success(self):
        if self._failure_count > 0:
            app_logger.info("Circuit Breaker: Conexão estabilizada. Resetando falhas.")
        self._failure_count = 0
        self._is_open = False

    def translate(self, text: str, src_lang: str, dest_lang: str) -> str:
        self._check_circuit()
        
        for tentativa in range(self._max_retries):
            try:
                resposta = self._engine.translate(text, src=src_lang, dest=dest_lang)
                self._record_success()
                return resposta.text
            except (TypeError, ValueError, AttributeError) as e:
                self._record_failure()
                app_logger.error(f"Erro permanente na API do Google: {e}")
                raise RuntimeError(f"Erro permanente na API do Google: {e}")
            except Exception as e:
                if tentativa == self._max_retries - 1:
                    self._record_failure()
                    raise RuntimeError(f"Falha no Google após {self._max_retries} tentativas: {e}")
                
                app_logger.warning(f"Google API falhou. Retentando em breve... Erro: {e}")
                time.sleep(2 ** tentativa)
