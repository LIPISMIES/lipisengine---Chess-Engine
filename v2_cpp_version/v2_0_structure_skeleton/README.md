Tyyliohjeet:
Vastaa suomeksi. Koodikommentit englanniksi. Jokaisen tiedoston alussa tiedostonimen kertova kommentti, esim "// main.cpp".

Projektin perustiedot:
* Shakkimoottori: Lipisengine v2
* C++-kielinen
* Ohjelmointiympäristö: VSCode, Windows
* Komentorivityökalu: bash / PowerShell
* Projektin hakemistorakenne:
jaakk@LAPTOP-RI0IGN01 MINGW64 ~/OneDrive - TUNI.fi/Työpöytä/lipisengine/v2_cpp_version/v2_0_structure_skeleton
$ ls
board.cpp main.cpp move.h movegen.h perft.h uci.cpp zobrist.cpp board.h move.cpp movegen.cpp perft.cpp types.h uci.h zobrist.h

Shakkimoottorista:
* UCI-yhteensopiva (Universal Chess Interface, tekstipohjainen)
* Pohjana minmax-/alphabeta-haku klassisella käsinkirjoitetulla evalilla.
* Kaikki rakenteet ja movegen itse koodattu alusta loppuun.
* Käyttää Bitboard-rakenteita.
* Inspiraationa Stockfish.

Kääntäminen omalle koneelle (suorituskykyoptimoitu):
* g++ komentoriviltä
* g++ -std=c++20 -O3 -march=native -mtune=native -flto -fno-exceptions -fno-rtti -DNDEBUG 

Dev/Debug-käännös:
* g++ -std=c++20 -O0 -g