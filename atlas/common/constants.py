"""
ATLAS - Advanced Ticket Lottery Analytics System

File:
    constants.py

Description:
    Global constants shared across the project.

Author:
    Miguel Ramos Alarcón
    OpenAI - ATLAS Project

License:
    MIT
"""

from decimal import Decimal

###############################################################################
# Game configuration
###############################################################################

GAME_NAME: str = "Melate"

MIN_NUMBER: int = 1
MAX_NUMBER: int = 56

NUMBERS_PER_DRAW: int = 6
NUMBERS_PER_TICKET: int = 6

HAS_ADDITIONAL_NUMBER: bool = True

###############################################################################
# Ticket System
###############################################################################

DEFAULT_TICKETS_PER_SYSTEM: int = 8

###############################################################################
# Monetary values
###############################################################################

DEFAULT_JACKPOT: Decimal = Decimal("0.00")

###############################################################################
# Validation
###############################################################################

MIN_CONTEST_NUMBER: int = 1

###############################################################################
# Project metadata
###############################################################################

PROJECT_NAME: str = "ATLAS"

PROJECT_VERSION: str = "0.1.0"
