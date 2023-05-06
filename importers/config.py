import os
import sys

# beancount doesn't run from this directory
sys.path.append(os.path.dirname(__file__))

from moneymanager import MoneyManagerImporter

CONFIG = [
    MoneyManagerImporter(),
]
