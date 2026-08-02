# Retro Tron Wireframe Visualizer

Visualizzatore grafico procedurale in Python/Pygame pensato principalmente per un
Raspberry Pi 3 con Raspberry Pi OS 64-bit e un pannello HDMI 480×320.

Il programma genera in tempo reale un paesaggio wireframe in stile retro-Tron:
griglia prospettica, montagne, città, sole, droni, portali, stelle, scanline e
variazioni di palette. Non è un gioco completo: non ci sono personaggio,
collisioni, livelli, rete o salvataggi.

## Hardware e video

Configurazione principale:

- Raspberry Pi 3 o modello equivalente;
- Raspberry Pi OS 64-bit, testato/documentato per Bookworm o Trixie;
- pannello HDMI fisso da 480×320 pixel.

L’applicazione renderizza internamente a 480×320. Gli script di avvio usano:

- fullscreen;
- `scale=1`;
- 30 FPS;
- profilo prestazionale `pi`.

Il renderer è procedurale: il repository non contiene immagini, sprite, font,
musica o altri asset audio.

## Installazione

```bash
sudo apt update
sudo apt install -y git python3-pygame python3-numpy python3-sounddevice
cd ~
git clone https://github.com/tatosgames/supertronicopygame.git
cd supertronicopygame
```

Per avviare direttamente il target HDMI:

```bash
cd ~/supertronicopygame
bash scripts/run-display.sh --target hdmi
```

Per eseguire anche l’installazione del servizio di avvio automatico:

```bash
cd ~/supertronicopygame
bash scripts/install-display.sh --target hdmi
```

L’installer crea e avvia `tronico-screen.service`. Il servizio usa X11 (`DISPLAY=:0`)
e riavvia l’applicazione solo se termina in errore o in modo anomalo; la chiusura
con `ESC` resta chiusa. Stato e log sono disponibili con:

```bash
systemctl status tronico-screen.service
journalctl -u tronico-screen.service -f
```

Gli argomenti dell’applicazione possono essere passati dopo `--`. Per esempio:

```bash
bash scripts/run-display.sh --target hdmi -- --no-auto
```

Una volta aperta la finestra, premere `F` per mostrare gli FPS e le informazioni
di debug.

Nota: `run-display.sh` abilita per impostazione predefinita un controllo degli
aggiornamenti verso `origin/main`. Usare `--no-update` per disabilitarlo.

## Target HDMI e TFT GPIO

Il target HDMI è quello principale del progetto. Sono mantenuti anche gli script
per un vecchio/alternativo pannello TFT collegato via GPIO, basato sul controller
Cytron XPT2046:

```text
https://github.com/CytronTechnologies/xpt2046-LCD-Driver-for-Raspberry-Pi
```

Dopo aver installato e verificato separatamente il driver del pannello:

```bash
cd ~/supertronicopygame
bash scripts/install-display.sh --target gpio
bash scripts/run-display.sh --target gpio
```

Gli wrapper equivalenti sono:

```bash
bash scripts/hdmi.sh
bash scripts/rpi.sh
```

Attualmente `--target hdmi` e `--target gpio` sono principalmente etichette di
avvio e descrizione del servizio: entrambi eseguono lo stesso `main.py` con lo
stesso renderer e con i parametri video 480×320. La configurazione specifica del
driver TFT non è implementata in questo repository.

## Profili prestazionali

`main.py` supporta tre profili:

- `high`: qualità completa, profilo predefinito per esecuzioni generiche;
- `pi`: riduce elementi e costi degli effetti, usato dagli script hardware e
  adatto al Raspberry Pi 3;
- `minimal`: disabilita ulteriori effetti e riduce il numero di elementi se il
  display è troppo lento.

Esempio di avvio manuale:

```bash
python3 main.py --profile pi --width 480 --height 320 --scale 1 --fullscreen
```

## Controlli

- `ESC`: chiude l’applicazione;
- `F`: mostra/nasconde FPS e informazioni di debug;
- `S`: attiva/disattiva le scanline;
- `G`: attiva/disattiva il glow simulato;
- `C`: cambia palette;
- `V`: attiva/disattiva la variazione automatica;
- `SPACE`: rigenera terreno, città e droni;
- `UP` / `DOWN`: aumenta o riduce la velocità;
- `LEFT` / `RIGHT`: modifica l’orizzonte.

## Microfono USB e audio

Il microfono USB viene rilevato automaticamente all’avvio e il suo livello RMS
smussato viene mostrato come una linea VU nella parte inferiore dello schermo.
La cattura usa `sounddevice`/PortAudio e non il mixer di Pygame. Il microfono non
è obbligatorio: se non viene trovato, il visualizzatore parte comunque e il meter
resta a zero.

Test rapido su Raspberry Pi OS:

```bash
sudo apt install -y alsa-utils
arecord -l
arecord -f S16_LE -r 44100 -c 1 -d 5 test-microfono.wav
aplay test-microfono.wav
```

Il servizio corrente imposta `SDL_AUDIODRIVER=dummy`: il visualizzatore non
produce audio tramite il mixer di Pygame. La cattura del microfono continua a
funzionare separatamente tramite PortAudio/ALSA.

## Aggiornamento e diagnostica

Per aggiornare il repository:

```bash
cd ~/supertronicopygame
git pull --ff-only origin main
```

Per controllare il boot e la catena di avvio del display, vedere
[docs/boot.md](docs/boot.md):

```bash
bash scripts/boot-check.sh
bash scripts/boot-check.sh --full
```

Le ottimizzazioni di boot sono opzionali e possono modificare servizi di sistema:

```bash
sudo bash scripts/boot-speedup.sh
```
