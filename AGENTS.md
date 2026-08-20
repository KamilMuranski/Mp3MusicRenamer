# MusicRenamer - specyfikacja techniczna dla agenta

Ten plik jest krótkim startem dla agenta. Pełny opis działania aplikacji z perspektywy
użytkownika jest w `Dokumentacja.md`. Czytaj go, gdy zadanie dotyczy zachowania programu
albo reguł rozpoznawania prefiksu numeru ścieżki.

## Najważniejsze zasady pracy

- Pracuj wyłącznie na obecnym kodzie. Nie rób commitów i nie przełączaj brancha.
- Jeżeli prompt nie pasuje do projektu MusicRenamer, powiedz o tym przed dalszą pracą.
- Zmieniaj tylko pliki konieczne do zadania. Preferuj małe, lokalne zmiany.
- Kod i stringi aplikacji pisz po angielsku. Rozmowę prowadź po polsku.
- Program działa na realnych plikach w bieżącym katalogu (patrz niżej — nie katalog exe!).
  Do testów manualnych używaj kopii danych.
- Nie twórz cache ani artefaktów testowych w repo.

## Stack projektu

- Aplikacja konsolowa **.NET Framework 4.7.2** (stary format `.csproj`, NIE SDK-style —
  brak `Nullable`/`ImplicitUsings`, referencje do `System.*` wpisane wprost).
- Główny plik programu: `Program.cs`.
- Projekt: `MusicRenamer.csproj`.
- Build: przez Visual Studio albo `msbuild` (nie `dotnet build` — to nie jest projekt SDK-style).

## Uruchamianie i zakres działania

- **Ważna różnica względem pozostałych 3 programów w pipeline użytkownika**: ten program
  używa `Directory.GetCurrentDirectory()`, nie `AppDomain.CurrentDomain.BaseDirectory`.
  Przy zwykłym uruchomieniu exe dwuklikiem oba katalogi są takie same, ale przy
  uruchomieniu z innej lokalizacji (skrót z innym "Start in", terminal w innym katalogu)
  program przetworzy CURRENT DIRECTORY, nie folder, w którym leży plik exe.
- Program przetwarza wyłącznie pliki `.mp3`, rekurencyjnie (`SearchOption.AllDirectories`)
  od katalogu bieżącego. Nie zmienia nazw folderów.
- Nieudane zmiany nazw trafiają do listy i na końcu są zapisywane do
  `RenameFailures.txt` w katalogu bieżącym (plik tworzony tylko, gdy są błędy).

## Mapa modułów

- `Main` - woła `RenameFiles()`, na końcu zapisuje log błędów, jeśli jakieś wystąpiły.
- `RenameFiles` - dla każdego `.mp3` sprawdza kolejno pięć wariantów prefiksu
  dwucyfrowego (`NN foo`, `NN. foo`, `NN-foo`, `NN- foo`, `NN.foo`) i pięć analogicznych
  wariantów jednocyfrowych (z automatycznym doklejeniem `0` z przodu), normalizując do
  `NN - Tytuł.mp3`.
- `SafeRename` - rozróżnia zwykłą zmianę nazwy od zmiany różniącej się TYLKO wielkością
  liter (którą Windows może nie utrwalić przy bezpośrednim `File.Move`) i dla tej drugiej
  robi dwuetapowy rename przez plik tymczasowy z rollbackiem przy błędzie.
- `MoveFileWithRetry` - `File.Move` z retry (do 5 prób, liniowy backoff 120ms * próba) na
  `IOException`/`UnauthorizedAccessException`.

## Nieoczywiste inwarianty

- Kolejność sprawdzania wzorców w `RenameFiles` ma znaczenie: warianty dwucyfrowe są
  sprawdzane przed jednocyfrowymi, więc `"01 - Tytuł.mp3"` nie zostanie błędnie
  zinterpretowane jako wariant jednocyfrowy.
- Jeśli nazwa pliku nie pasuje do żadnego z dziesięciu wzorców, plik zostaje bez zmian
  (program nie rzuca błędu, po prostu nic nie robi).
- Jeżeli plik docelowy o tej samej nazwie (inny niż case-only) już istnieje, `SafeRename`
  po cichu pomija operację (nie nadpisuje, nie loguje błędu) — to różni się od
  `PrepareFoldersAndFilesNames`, gdzie kolizja nazw jest traktowana jako błąd do zalogowania.
- Program nie dotyka folderów, kapitalizacji ani cyrylicy — to zadania kolejnych kroków
  pipeline'u (`PrepareFoldersAndFilesNames`, `CyryllicToLatinRenamer`).

## Aktualizacja dokumentów

Aktualizuj dokumenty tylko w zakresie zmiany.

- Zmiana zachowania programu albo reguł rozpoznawania prefiksu: aktualizuj `Dokumentacja.md`.
- Nowa zasada pracy agenta, zmiana mapy kodu albo inwariantu technicznego: aktualizuj ten plik.
