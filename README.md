# ALEX NBA Mobile Collectors v2.2

Aggiornamento mobile PWA: collector calendario settimanale e inserimento quote prematch per singola partita.

## Uso da telefono Android
1. Fai prima **Settings → Backup completo JSON** nella versione già installata.
2. Aggiorna i file del sito/PWA con quelli di questa cartella (oppure sostituisci i file nel repository GitHub Pages che ospita già ALEX).
3. Chiudi completamente ALEX/Chrome e riapri la PWA per caricare la nuova cache.
4. Apri **Match → Raccogli tutte le partite di questa settimana**.
5. Per le quote, apri la scheda di ogni partita, consulta Diretta.it e inserisci Moneyline casa/trasferta, linea totale, Over, Under, bookmaker e URL della scheda; premi **Salva quote**.

## Funzioni
- Calendario NBA della settimana corrente (lunedì-domenica), incluse partite concluse, in corso e programmate, tramite feed pubblico NBA CDN.
- Per le partite concluse, tentativo di recupero del box score e delle statistiche individuali dal feed NBA.
- Aggiornamento per ID partita: le partite già presenti vengono aggiornate senza duplicarle e le quote già inserite vengono conservate.
- Inserimento assistito delle quote prematch per ogni partita: Moneyline casa/trasferta, linea totale, Over, Under, bookmaker e link della scheda Diretta.it.
- Export CSV aggiornato con quote, fonte, URL, stato partita e risultato.
- Database IndexedDB locale, backup e ripristino JSON.

## Limiti importanti
- Il feed NBA fornisce calendario, punteggi e box score, **non** quote bookmaker.
- Le quote Diretta.it in questa build si inseriscono manualmente nell'app dopo averle consultate. Non viene effettuato scraping automatico del sito.
- Il feed NBA CDN può essere bloccato dal browser/rete tramite CORS. Se la richiesta fallisce, l'app mostra l'errore e non inventa dati.
- Le quote salvate vanno riferite al bookmaker indicato e alla fase prematch; non confondere una quota di un altro bookmaker con Bet365.

## Dati locali
I dati restano nel browser del telefono (IndexedDB). Esporta regolarmente il backup JSON, soprattutto prima di aggiornare la PWA.
