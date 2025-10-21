import logging

from rich.logging import RichHandler


def setup():
    logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler(markup=True)])
