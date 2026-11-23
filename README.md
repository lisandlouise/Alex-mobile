# ALEX NBA Collectors v2.0 — Android PWA

Questa build è progettata per essere pubblicata su GitHub Pages e usata da Chrome su Android. Non richiede PC, Python o app desktop per l'utilizzo quotidiano.

## Installazione/aggiornamento
1. Prima di sostituire i file, apri ALEX sul telefono e fai **Settings → Backup completo JSON**.
2. Nel repository GitHub Pages sostituisci `index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, `icon-192.png`, `icon-512.png`.
3. Apri l'app su Android e ricarica. Se vedi ancora la vecchia versione, chiudi completamente la PWA e riaprila; il service worker usa una nuova cache.
4. Il database IndexedDB `alex_mobile` viene aggiornato alla versione 2 e mantiene gli object store esistenti `games` e `logs`.

## Cosa funziona in questa build
- App mobile PWA, database locale IndexedDB.
- Archivi distinti Match e Player Stats.
- Match con campi espliciti `home` e `away`; quota 1 casa, quota 2 trasferta; risultato casa–trasferta.
- Acquisizione iniziale selezionabile per le stagioni 2021-22 ... 2025-26 e aggiornamento per 2026-27.
- Import CSV/JSON Match con upsert tramite ID e prevenzione duplicati.
- Selezione giocatori e import CSV Player Stats.
- Export CSV separati e backup/ripristino JSON.
- Log attività.

## Limite da non confondere
Questa build NON effettua ancora il prelievo automatico live di Diretta.it o NBA Stats dal browser. GitHub Pages è hosting statico e il browser Android non può garantire il fetch cross-origin delle pagine di Diretta.it. I pulsanti import funzionano per dati esportati/forniti in CSV/JSON. Per automatizzare davvero la raccolta serve il backend/API autorizzato e il relativo endpoint; non viene simulato né dichiarato come completato.

## Formato CSV Match
Intestazioni riconosciute: `data`, `casa`, `trasferta`, `1`, `2`, `linea`, `over`, `under`, `risultato`, `url`. Risultato nel formato `punteggioCasa-punteggioTrasferta`. Quote 1/2 devono già essere rispettivamente casa/trasferta.

## Formato CSV Player Stats
Intestazioni riconosciute: `player`, `player id`, `date`, `team`, `min`, `pts`, `reb`, `ast`, `stl`, `blk`. Puoi includere ulteriori colonne nel CSV; queste vengono ignorate.

Dati memorizzati localmente nel browser del telefono: esporta regolarmente il backup JSON.
