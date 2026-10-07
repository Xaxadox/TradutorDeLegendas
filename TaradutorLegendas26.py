"""Tradutor Automático de Legendas (MKV/ASS/SRT) — Ponto de Entrada."""

from tradutor.orquestrador import OrquestradorTraducoes
from tradutor.controlador import ControladorApp
from tradutor.interface import InterfaceGrafica


def main():
    model = OrquestradorTraducoes()
    view = InterfaceGrafica()
    ControladorApp(view, model)
    view.mainloop()


if __name__ == "__main__":
    main()