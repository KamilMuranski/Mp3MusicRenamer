# MusicRenamer - specyfikacja techniczna dla agenta

Ten plik jest krótkim startem dla agenta. Pełny opis działania aplikacji z perspektywy
użytkownika jest w `Dokumentacja.md`. Czytaj go, gdy zadanie dotyczy zachowania programu
albo reguł rozpoznawania prefiksu numeru ścieżki.

## Najważniejsze zasady pracy

- Pracuj wyłącznie na obecnym kodzie. Nie rób commitów i nie przełączaj brancha.
- Jeżeli prompt nie pasuje do projektu MusicRenamer, powiedz o tym przed dalszą pracą.
- Zmieniaj tylko pliki konieczne do zadania. Preferuj małe, lokalne zmiany.
- Kod i stringi aplikacji pisz po angielsku (poza polskimi komunikatami konsoli, które już
  tam są). Rozmowę prowadź po polsku.
- Program działa na realnych plikach w bieżącym katalogu (patrz niżej — nie katalog
  skryptu!). Do testów manualnych używaj kopii danych.
- Nie twórz cache ani artefaktów testowych w repo.

## Stack projektu

- Aplikacja konsolowa, jeden plik `MusicRenamer.py`, czysta biblioteka standardowa
  Pythona (3.9+). Zero zależności, zero budowania - uruchamiana dwuklikiem (Windows
  odpala ją zarejestrowanym `py.exe`).
- **Ważna różnica względem pozostałych 3 programów w pipeline użytkownika**: ten program
  używa `os.getcwd()`, nie folderu, w którym leży plik `.py`. Przy zwykłym uruchomieniu
  dwuklikiem oba katalogi są takie same (Windows ustawia katalog bieżący na folder
  klikniętego pliku), ale przy uruchomieniu z innej lokalizacji (skrót z innym
  "Start in", terminal w innym katalogu) program przetworzy CURRENT DIRECTORY, nie folder
  ze skryptem.
- Program przetwarza wyłącznie pliki `.mp3` (rozszerzenie sprawdzane bez rozróżniania
  wielkości liter), rekurencyjnie, od katalogu bieżącego. Nie zmienia nazw folderów.
- Kończy się bez pauzy na klawisz — w przeciwieństwie do `CyryllicToLatinRenamer.py` to
  narzędzie w pełni automatyczne (wynik do sprawdzenia wizualnie nie jest potrzebny w
  typowym użyciu; błędy trafiają do `RenameFailures.txt`).
- Do testów manualnych kopiuj `MusicRenamer.py` razem z danymi testowymi do osobnego
  katalogu i uruchamiaj stamtąd (`python MusicRenamer.py`).

## Pozycja w pipeline użytkownika

Ten program to krok 1 z 4 w pipeline porządkowania pobranej muzyki (patrz `Dokumentacja.md`
po pełny opis pipeline'u). Kolejne kroki (`PrepareFoldersAndFilesNames`,
`CyryllicToLatinRenamer`, `Mp3TagsSetter`) zakładają, że pliki mają już format
`NN - Tytuł.mp3` — jeśli ten krok zostanie pominięty na kolekcji z niespójnymi prefiksami,
kolejne kroki mogą nie rozpoznać nazw plików poprawnie.

## Mapa modułów

- `main` - ustawia UTF-8 konsoli, woła `rename_files(os.getcwd())`, na końcu zapisuje log
  błędów do `RenameFailures.txt`, jeśli jakieś wystąpiły. Bez pauzy na klawisz.
- `find_mp3_files` - zbiera PEŁNĄ listę plików `.mp3` pod danym katalogiem (rekurencyjnie,
  `os.walk`) PRZED jakąkolwiek zmianą nazw — kolejne rename nie mogą wpłynąć na listę do
  przetworzenia w tym samym przebiegu.
- `rename_files` - dla każdego znalezionego pliku woła `normalize_track_prefix` +
  `force_mp3_extension`, po czym `safe_rename`. Zwraca listę nieudanych operacji.
- `normalize_track_prefix` - sprawdza kolejno pięć wariantów prefiksu dwucyfrowego
  (`NN foo`, `NN. foo`, `NN-foo`, `NN- foo`, `NN.foo`) i pięć analogicznych wariantów
  jednocyfrowych (z automatycznym doklejeniem `0` z przodu), normalizując do
  `NN - Tytuł.mp3`. Jeśli nic nie pasuje (np. prefiks już poprawny), wraca bez zmian.
- `force_mp3_extension` - wymusza rozszerzenie `.mp3` małymi literami niezależnie od
  oryginalnej wielkości liter (`.MP3` -> `.mp3`).
- `safe_rename` - rozróżnia zwykłą zmianę nazwy od zmiany różniącej się TYLKO wielkością
  liter (którą Windows może nie utrwalić przy bezpośrednim rename) i dla tej drugiej robi
  dwuetapowy rename przez plik tymczasowy z rollbackiem przy błędzie.
- `move_with_retry` - `os.rename` z retry (do 5 prób, liniowy backoff 120ms * próba) na
  `OSError` (odpowiednik połączonych `IOException`/`UnauthorizedAccessException` z
  oryginalnej wersji C# - Python nie rozróżnia tych dwóch tak samo drobiazgowo, ale efekt
  - 5 retry z tym samym backoffem - jest identyczny).

## Nieoczywiste inwarianty

- Kolejność sprawdzania wzorców w `normalize_track_prefix` ma znaczenie: warianty
  dwucyfrowe są sprawdzane przed jednocyfrowymi, więc `"01 - Tytuł.mp3"` nie zostanie
  błędnie zinterpretowane jako wariant jednocyfrowy.
- Jeśli nazwa pliku nie pasuje do żadnego z dziesięciu wzorców, plik zostaje bez zmian
  (funkcja nie rzuca błędu, po prostu nic nie robi) — rozszerzenie i tak jest normalizowane
  osobno przez `force_mp3_extension`.
- Jeżeli plik docelowy o tej samej nazwie (inny niż case-only) już istnieje, `safe_rename`
  po cichu pomija operację (nie nadpisuje, nie loguje błędu) — to różni się od
  `PrepareFoldersAndFilesNames`, gdzie kolizja nazw jest traktowana jako błąd do zalogowania.
- Przy nieudanej zmianie case-only (druga faza dwuetapowego rename) do listy błędów trafiają
  DWA wpisy (`FILE (case-only): ...` i `FILE: ... | {błąd}`) — to zachowanie przeniesione
  1:1 z oryginalnej wersji C#, nie traktuj tego jako bug do naprawienia bez pytania.
- `find_mp3_files` materializuje pełną listę plików PRZED zaczęciem zmian nazw (nie jest to
  leniwy generator przeplatany z rename'ami) — inaczej modyfikacja katalogu w trakcie
  przechodzenia mogłaby dać niespójny wynik.
- Program nie dotyka folderów, kapitalizacji ani cyrylicy — to zadania kolejnych kroków
  pipeline'u (`PrepareFoldersAndFilesNames`, `CyryllicToLatinRenamer`).

## Aktualizacja dokumentów

Aktualizuj dokumenty tylko w zakresie zmiany.

- Zmiana zachowania programu albo reguł rozpoznawania prefiksu: aktualizuj `Dokumentacja.md`.
- Nowa zasada pracy agenta, zmiana mapy kodu albo inwariantu technicznego: aktualizuj ten plik.
