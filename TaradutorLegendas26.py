"""Tradutor Automático de Legendas (MKV/ASS/SRT) — Ponto de Entrada."""

from tradutor.orchestrator import TranslationOrchestrator
from tradutor.controller import AppController
from tradutor.gui import AppGui


def main():
    model = TranslationOrchestrator()
    view = AppGui()
    AppController(view, model)
    view.mainloop()


if __name__ == "__main__":
    main()