"""
Dataflows module — unified data loading with fallback chains.

Usage:
    from dataflows import DataLoader
    loader = DataLoader()
    text = loader.load("AAPL", "2024-01-15", "fundamentals")
"""
from .data_loader import DataLoader
from . import sources
