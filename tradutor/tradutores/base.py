from abc import ABC, abstractmethod

class ITradutor(ABC):
    """
    Interface abstrata (Contrato) para todos os motores de tradução.
    Qualquer nova API (DeepL, OpenAI, etc) deve implementar esta interface.
    Isso blinda a aplicação principal de mudanças nas bibliotecas de terceiros.
    """
    
    @abstractmethod
    def translate(self, text: str, src_lang: str, dest_lang: str) -> str:
        """
        Recebe um texto puro (ou bloco com quebras de linha) e retorna a tradução.
        Deve lidar internamente com retentativas e exceptions da própria API.
        """
        pass
