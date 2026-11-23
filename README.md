# ALEX Mobile v1.0 (Android PWA)

App mobile installabile da Chrome su Android, con dati locali IndexedDB. Nessun abbonamento, backend o database cloud.

## Pubblicazione gratuita (richiede account GitHub gratuito)
1. Crea un repository pubblico GitHub chiamato `alex-mobile`.
2. Carica nella root tutti i file di questa cartella.
3. Apri Settings > Pages, scegli Deploy from a branch, `main`, `/ (root)`, Save.
4. Quando GitHub Pages pubblica il sito HTTPS, apri l'URL da Chrome Android.
5. Menu ⋮ > Installa app / Aggiungi a schermata Home.

Il codice sarà pubblico nel repository, ma i dati inseriti nell'app restano nel browser del telefono e non vengono caricati su GitHub.

## Funzioni incluse
Dashboard, Collection, Archive, Logs, Settings; inserimento manuale; quote 1 e 2 conservate nell'ordine Diretta.it; verifica manuale Bet365/closing; calcolo vincente e totale dal punteggio; prevenzione duplicati tramite ID derivato da data e squadre; CSV esattamente 11 colonne; backup e ripristino JSON; cache offline dopo il primo accesso.

## Limiti
Non c'è ancora raccolta automatica da Diretta.it, verifica automatica delle quote o job in background. Nessun test su 20 partite reali è stato eseguito. I dati sono solo su questo browser/dispositivo: esporta spesso il JSON. Se cancelli i dati del browser, puoi perderli.
