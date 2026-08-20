#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MusicRenamer - krok 1 pipeline'u porządkowania muzyki.

Ujednolica prefiks numeru ścieżki w nazwach plików `.mp3` do postaci "NN - Tytuł.mp3"
i wymusza rozszerzenie ".mp3" małymi literami. Przetwarza BIEŻĄCY KATALOG (ten, z którego
skrypt został odpalony), rekurencyjnie po wszystkich podfolderach - NIE folder, w którym
leży ten plik. Przy zwykłym dwukliku oba katalogi się pokrywają (Windows ustawia katalog
bieżący na folder klikniętego pliku), więc w typowym użyciu to bez znaczenia.

Uruchomienie: dwuklik na pliku (albo `python "MusicRenamer.py"`).
Pełny opis zachowania: Dokumentacja.md.
"""

from __future__ import annotations

import os
import re
import sys
import time
import uuid

# --- Wzorce prefiksu numeru ścieżki -------------------------------------------

# Dowolna dalsza treść tytułu - znaki słowa (litery/cyfry/podkreślenie, także cyrylica
# i inne alfabety), gwiazdka, spacja, "[", "(" albo ".". Wystarczy jeden taki znak po
# prefiksie, żeby uznać go za realny początek tytułu (a nie samą liczbę bez nazwy).
TITLE_CHARS = r"[\w* [(\.]+"

# Kolejność ma znaczenie: dwucyfrowe wzorce SPRAWDZANE PRZED jednocyfrowymi, inaczej
# "01 - Tytuł.mp3" zostałoby błędnie zinterpretowane jako wariant jednocyfrowy ("0" + "1").
# Druga wartość w parze to liczba znaków do pominięcia z przodu oryginalnej nazwy (numer
# + separator), zanim doklei się nowy prefiks "NN - ".
TWO_DIGIT_PATTERNS = [
    (re.compile(r"^\d\d\s" + TITLE_CHARS), 3),  # "NN foo"
    (re.compile(r"^\d\d\.\s" + TITLE_CHARS), 4),  # "NN. foo"
    (re.compile(r"^\d\d\-" + TITLE_CHARS), 3),  # "NN-foo"
    (re.compile(r"^\d\d\-\s" + TITLE_CHARS), 4),  # "NN- foo"
    (re.compile(r"^\d\d\." + TITLE_CHARS), 3),  # "NN.foo"
]

ONE_DIGIT_PATTERNS = [
    (re.compile(r"^\d\s" + TITLE_CHARS), 2),  # "N foo"
    (re.compile(r"^\d\.\s" + TITLE_CHARS), 3),  # "N. foo"
    (re.compile(r"^\d\-" + TITLE_CHARS), 2),  # "N-foo"
    (re.compile(r"^\d\-\s" + TITLE_CHARS), 3),  # "N- foo"
    (re.compile(r"^\d\." + TITLE_CHARS), 2),  # "N.foo"
]

MAX_RENAME_ATTEMPTS = 5
RETRY_BACKOFF_MS = 120


def normalize_track_prefix(file_name: str) -> str:
    """
    Rozpoznaje jeden z dziesięciu wariantów prefiksu numeru ścieżki (dwu- albo
    jednocyfrowy, z separatorem " ", ". ", "-", "- " albo ".") i zamienia go na "NN - ".
    Numer jednocyfrowy jest dodatkowo zerowany z przodu. Jeśli nazwa nie pasuje do
    żadnego wzorca, wraca bez zmian.
    """
    for pattern, skip in TWO_DIGIT_PATTERNS:
        if pattern.match(file_name):
            return file_name[0:2] + " - " + file_name[skip:]

    for pattern, skip in ONE_DIGIT_PATTERNS:
        if pattern.match(file_name):
            return "0" + file_name[0:1] + " - " + file_name[skip:]

    return file_name


def force_mp3_extension(file_name: str) -> str:
    """Wymusza rozszerzenie ".mp3" małymi literami, niezależnie od oryginalnej wielkości liter."""
    base, _ext = os.path.splitext(file_name)
    return base + ".mp3"


def is_mp3_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() == ".mp3"


def find_mp3_files(root: str) -> list[str]:
    """Zbiera pełną listę plików .mp3 pod `root` (rekurencyjnie) PRZED jakąkolwiek zmianą nazw."""
    result = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if is_mp3_file(path):
                result.append(path)
    return sorted(result)


def move_with_retry(src: str, dst: str, max_attempts: int = MAX_RENAME_ATTEMPTS) -> None:
    """os.rename z retry (liniowy backoff 120ms * próba) na przejściowe błędy systemowe."""
    attempts = 0
    while True:
        try:
            os.rename(src, dst)
            return
        except OSError:
            attempts += 1
            if attempts > max_attempts:
                raise
            time.sleep(RETRY_BACKOFF_MS * attempts / 1000)


def safe_rename(src_path: str, dst_path: str, failed_renames: list[str]) -> None:
    """
    Rename odporny na zmianę różniącą się TYLKO wielkością liter (Windows może jej nie
    utrwalić przy bezpośrednim rename) - dla takiego przypadku robi dwuetapową zmianę
    przez plik tymczasowy, z rollbackiem przy błędzie. Kolizja z istniejącym plikiem o
    innej nazwie jest pomijana po cichu (nie nadpisujemy, nie logujemy jako błąd).
    """
    equal_ignore_case = src_path.lower() == dst_path.lower()

    try:
        if not equal_ignore_case and os.path.exists(dst_path):
            return

        if equal_ignore_case and src_path != dst_path:
            directory = os.path.dirname(src_path)
            tmp_path = os.path.join(directory, uuid.uuid4().hex + ".tmp")

            try:
                move_with_retry(src_path, tmp_path)

                try:
                    move_with_retry(tmp_path, dst_path)
                except OSError:
                    try:
                        if os.path.exists(tmp_path) and not os.path.exists(src_path):
                            move_with_retry(tmp_path, src_path)
                    except OSError:
                        pass
                    failed_renames.append(f"FILE (case-only): {src_path} -> {dst_path}")
                    raise
            except OSError as ex:
                failed_renames.append(f"FILE: {src_path} -> {dst_path} | {ex}")
                raise
        else:
            try:
                move_with_retry(src_path, dst_path)
            except OSError as ex:
                failed_renames.append(f"FILE: {src_path} -> {dst_path} | {ex}")
                raise
    except OSError:
        pass  # błąd już zarejestrowany; kontynuujemy pętlę wyżej


def rename_files(root: str) -> list[str]:
    """
    Dla każdego pliku .mp3 pod `root` (rekurencyjnie) normalizuje prefiks numeru ścieżki
    i wymusza rozszerzenie ".mp3". Nie rusza folderów. Zwraca listę nieudanych operacji.
    """
    failed_renames: list[str] = []

    for file_path in find_mp3_files(root):
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        renamed = normalize_track_prefix(file_name)
        renamed = force_mp3_extension(renamed)

        dst_path = os.path.join(directory, renamed)
        if file_path == dst_path:
            continue

        safe_rename(file_path, dst_path, failed_renames)

    return failed_renames


# --- Konsola ------------------------------------------------------------------


def setup_console() -> None:
    """Wymusza UTF-8 na wyjściu, żeby cyrylica (ten program działa PRZED jej tłumaczeniem) nie wysypała konsoli."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main() -> int:
    setup_console()

    root = os.getcwd()
    failed_renames = rename_files(root)

    if failed_renames:
        log_path = os.path.join(root, "RenameFailures.txt")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(failed_renames) + "\n")
            print(f"Zapisano listę nieudanych zmian do pliku: {log_path}")
        except OSError as ex:
            print(f"[ERROR] Nie udało się zapisać logu: {ex}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
