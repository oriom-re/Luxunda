# app_v2/__init__.py
"""
LuxOS app_v2 - Czysta architektura z komunikacją między bytami

Struktura modułów:
- beings/: Klasy reprezentujące byty (Being, Genotype)
- core/: Podstawowe funkcjonalności (komunikacja, rejestr modułów)
- services/: Logika biznesowa (zarządzanie bytami, zależności)
- database/: Warstwa dostępu do danych (repositories)
- gen_files/: Pliki modułów .module
"""

__version__ = "2.0.0"
__author__ = "LuxOS Team"
__description__ = "System komunikacji i zarządzania bytami z czystą architekturą"
