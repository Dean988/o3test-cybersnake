# CyberSnake

Una versione moderna e avanzata del classico gioco Snake con tema cyber e effetti visivi incredibili!

## Caratteristiche Principali
- **Menu iniziale animato** con selezione della difficoltà
- **Tre livelli di difficoltà**: Easy, Medium, Hard
- **Effetti visivi avanzati**:
  - Particelle dinamiche e reattive
  - Effetti di scia dietro al serpente
  - Nebbie e stelle animate in background
  - Effetti luminosi e animazioni fluide
- **Sistema di ostacoli innovativi**:
  - Portali: teletrasporto tra diverse aree della mappa
  - Mine: esplodono creando zone pericolose
  - Scudi: proteggono da una collisione
- **Sistema di punteggio avanzato**:
  - Combo: cambi di direzione rapidi per moltiplicare i punti
  - Effetti visivi che mostrano i punti guadagnati
- **Audio e musica**:
  - Effetti sonori reattivi
  - Musica di sottofondo

## Come Giocare
Esegui il gioco con Python:
```
python gioco.py
```

### Requisiti
- Python 3.x
- Pygame (`pip install pygame`)

### Controlli
- Frecce direzionali o WASD per muoversi
- P per mettere in pausa il gioco
- ESC per accedere al menu
- R per ricominciare dopo il game over
- S per attivare/disattivare gli effetti sonori
- M per attivare/disattivare la musica

## Note
Per sfruttare tutte le funzionalità audio, aggiungi i file sonori nella cartella "sounds":
- eat.wav
- game_over.wav
- teleport.wav
- shield.wav
- explosion.wav
- menu_select.wav
- menu_confirm.wav
- background_music.mp3 