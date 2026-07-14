"""
ATLAS - Advanced Ticket Lottery Analytics System

File:
    exceptions.py

Description:
    Domain exceptions used across the ATLAS project.

Author:
    Miguel Ramos Alarcón
    OpenAI - ATLAS Project

License:
    MIT
"""

from __future__ import annotations


class AtlasError(Exception):
    """
    Base exception for every domain-specific error in ATLAS.
    """


class ValidationError(AtlasError):
    """
    Raised when domain validation fails.
    """


class InvalidLotteryNumberError(ValidationError):
    """
    Raised when a lottery number is outside the allowed range.
    """


class DuplicateNumberError(ValidationError):
    """
    Raised when duplicate numbers are found.
    """


class InvalidTicketError(ValidationError):
    """
    Raised when a ticket violates the game rules.
    """


class InvalidDrawError(ValidationError):
    """
    Raised when a draw is invalid.
    """