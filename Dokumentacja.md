# MusicRenamer - dokumentacja produktu

Ten plik opisuje aktualne zachowanie aplikacji z perspektywy użytkownika. Krótka
specyfikacja techniczna dla agentów jest w `AGENTS.md`.

## Zakres aplikacji

MusicRenamer to konsolowe narzędzie, które ujednolica prefiks numeru ścieżki w nazwach
plików `.mp3` do jednej, spójnej postaci: `NN - Tytuł.mp3`. To pierwszy krok w pipeline
porządkowania świeżo pobranej muzyki — pobrane pliki mają zwykle niespójne formaty typu
`01 Tytuł.mp3`, `01. Tytuł.mp3`, `01-Tytuł.mp3` albo z jedną cyfrą (`1 Tytuł.mp3`), a
kolejne kroki pipeline'u (kapitalizacja, tłumaczenie cyrylicy, tagi ID3) zakładają już
dokładnie format `NN - Tytuł.mp3`.

## Pozycja w pipeline

To krok 1 z 4 w typowym przebiegu porządkowania pobranej muzyki:

1. **MusicRenamer** (ten program) - ujednolica prefiks numeru ścieżki.
2. `PrepareFoldersAndFilesNames` - poprawia wielkość liter, usuwa `(bonus track)`,
   nadaje nazwę okładce.
3. `CyryllicToLatinRenamer` - tłumaczy nazwy zapisane cyrylicą (często pomijany).
4. `Mp3TagsSetter` - wpisuje tagi ID3 na podstawie nazw folderów i plików.

## Sposób użycia

Program przetwarza pliki `.mp3` w **bieżącym katalogu terminala** (nie w katalogu, w
którym leży plik exe — to jedyny program w pipeline, który działa w ten sposób). Przy
zwykłym uruchomieniu dwuklikiem z folderu kolekcji to bez znaczenia, bo oba katalogi się
pokrywają.

Program działa rekurencyjnie po wszystkich podfolderach, zmienia tylko nazwy plików
`.mp3` — nie rusza folderów ani innych typów plików.

## Rozpoznawane formaty nazw

Program rozpoznaje na początku nazwy pliku jeden z poniższych wzorców i zamienia go na
`NN - `:

- `NN foo` (spacja po numerze)
- `NN. foo` (kropka + spacja)
- `NN-foo` (myślnik bez spacji)
- `NN- foo` (myślnik + spacja)
- `NN.foo` (sama kropka)

oraz te same warianty z jedną cyfrą zamiast dwóch (`N foo`, `N. foo`, `N-foo`, `N- foo`,
`N.foo`) — w takim wypadku numer jest dodatkowo zerowany z przodu (`1` -> `01`).

Jeśli nazwa pliku nie pasuje do żadnego z powyższych wzorców, plik zostaje bez zmian.

## Błędy i kolizje

Jeśli plik o docelowej nazwie już istnieje (i nie jest to zmiana różniąca się tylko
wielkością liter), operacja jest po cichu pomijana - plik nie jest nadpisywany.

Zmiany nazw różniące się tylko wielkością liter są obsługiwane przez plik tymczasowy,
żeby Windows prawidłowo utrwalił zmianę, z automatycznym rollbackiem do oryginalnej nazwy
przy niepowodzeniu.

Nieudane operacje (po wyczerpaniu prób) trafiają na listę i po zakończeniu pracy program
zapisuje je do pliku `RenameFailures.txt` w katalogu bieżącym. Plik powstaje tylko, gdy
wystąpił choć jeden błąd.

## Build

Projekt jest aplikacją konsolową dla **.NET Framework 4.7.2** (starszy, nie-SDK-style
`.csproj`) - buduje się przez Visual Studio albo `msbuild`, nie przez `dotnet build`.

## Dokumentacja a specyfikacja agenta

Ten plik opisuje funkcje i zachowanie programu. Jeśli zmiana dotyczy technicznej mapy
kodu, reguł pracy agenta albo inwariantów implementacyjnych, aktualizuj `AGENTS.md`.
