# Audio Kapitelmarken Tool

Ein Python-Kommandozeilen-Tool zum Einbetten von Audacity-Kapitelmarken in Audio-Dateien mit automatischer Lautstärke-Normalisierung auf Podcast-Standard. Exportiert als MP3 mit vollständiger Podcast-Kapitelmarken-Unterstützung.

## Features

- Liest Audacity Label-Dateien (.txt)
- Bettet Kapitelmarken mit aktuellem Standard ein (ID3v2.3 CTOC/CHAP Frames)
- **Automatische Lautstärke-Normalisierung** auf -16 LUFS (Podcast-Standard)
- Zwei-Pass-Normalisierung für präzise Ergebnisse
- True Peak Limiting (-1.5 dBTP) verhindert Clipping
- Exportiert im MP3-Format
- Debug-Ausgaben zur Fehlerbehebung

## Installation

```bash
# Repository klonen
git clone https://github.com/sozialwelten/Audio-Kapitelmarken-Tool.git
cd Audio-Kapitelmarken-Tool

# Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oder: .venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install mutagen

# ffmpeg muss installiert sein
# macOS: brew install ffmpeg
# Ubuntu/Debian: sudo apt install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

## Verwendung

### Basis-Verwendung
```bash
# MP3 mit Kapitelmarken und Lautstärke-Normalisierung erstellen
python chapter_tool.py audio.wav kapitel.txt
```

### Erweiterte Optionen
```bash
# In anderes Verzeichnis exportieren
python chapter_tool.py audio.wav kapitel.txt -o ./output

# Lautstärke-Normalisierung deaktivieren
python chapter_tool.py audio.wav kapitel.txt --no-normalize

# Andere Ziel-Lautstärke verwenden (z.B. -18 LUFS)
python chapter_tool.py audio.wav kapitel.txt --target-lufs -18
```

### Optionen

- `-o`, `--output-dir`: Ausgabeverzeichnis (Standard: gleiches Verzeichnis wie Eingabedatei)
- `--no-normalize`: Deaktiviert die Lautstärke-Normalisierung
- `--target-lufs`: Ziel-Lautstärke in LUFS (Standard: -16 für Podcasts)

## Audacity Label-Format

Erstelle in Audacity Label-Marken an den gewünschten Kapitel-Positionen und exportiere sie als Text-Datei:

```
2.638246    2.638246   Begrüßung
20.311316   20.311316  Experiment mit Audio
49.713455   49.713455  Vibecoding CLI Tool
71.677648   71.677648  Verabschiedung
```

**Format**: `START_TIME\tEND_TIME\tCHAPTER_TITLE`

## Lautstärke-Normalisierung

Das Tool normalisiert die Audio-Lautstärke automatisch auf Podcast-Standard:

- **-16 LUFS**: Ziel-Lautstärke (Standard für Spotify, Apple Podcasts, etc.)
- **-1.5 dBTP**: True Peak Limit (verhindert Clipping)
- **11 LU**: Loudness Range (erhält natürliche Dynamik)

Diese Werte entsprechen den Empfehlungen der EBU R128 für Broadcasting und sind optimal für Podcast-Plattformen.

### Warum Normalisierung?

- Konsistente Lautstärke über alle Episoden
- Keine plötzlichen Lautstärke-Sprünge für Hörer
- Kompatibel mit allen gängigen Podcast-Plattformen
- Verhindert zu leise oder zu laute Aufnahmen

## Kapitelmarken testen

```bash
# ID3-Tags mit Python/Mutagen verifizieren
python3 -c "from mutagen.id3 import ID3; tags = ID3('datei_chapters.mp3'); print('CHAP:', [k for k in tags.keys() if k.startswith('CHAP')]); print('CTOC:', [k for k in tags.keys() if k.startswith('CTOC')])"

# Lautstärke überprüfen
ffmpeg -i datei_chapters.mp3 -af loudnorm=print_format=summary -f null -
```

## Kompatibilität

Die erzeugten MP3-Dateien mit Kapitelmarken funktionieren in:

- **Podcast-Apps**: Pocket Casts, Apple Podcasts, Overcast, Castro, AntennaPod
- **Media-Player**: VLC (Wiedergabe → Kapitel), mpv, foobar2000
- **Plattformen**: Podcasting 2.0-Apps
- **Mobile**: iOS Music App, Android Media Player

**Hinweis zu Mastodon**: Mastodon konvertiert hochgeladene Audiodateien manchmal neu, was die ID3-Kapitelmarken entfernen kann. Teste die Kapitelmarken am besten zunächst lokal in deiner Podcast-App (z.B. Pocket Casts), bevor du die Datei hochlädst. Falls Mastodon die Kapitel entfernt, prüfe die Server-Einstellungen oder nutze alternative Upload-Methoden.

## Fehlersuche

Das Tool gibt Debug-Informationen aus:
- Gefundene Kapitel mit Zeitstempeln
- Audio-Dauer in Sekunden und Millisekunden
- Aktuelle Lautstärke vor der Normalisierung
- Anzahl der geschriebenen ID3-Frames mit Details

Bei Problemen:
1. Prüfe das Audacity-Label-Format (Tab-getrennt)
2. Stelle sicher, dass ffmpeg installiert ist: `ffmpeg -version`
3. Verifiziere die ID3-Tags mit dem Mutagen-Befehl oben
4. Teste die Datei lokal in einer Podcast-App, bevor du sie hochlädst

### Kapitelmarken werden nicht angezeigt?

Falls Kapitelmarken in deiner App nicht angezeigt werden:
- Prüfe mit dem Mutagen-Befehl, ob CHAP/CTOC Frames vorhanden sind
- Teste in verschiedenen Apps (Pocket Casts ist sehr zuverlässig)
- Bei Mastodon-Uploads: Lade die Original-MP3 herunter und prüfe die Tags
- Manche Apps zeigen Kapitel nur bei längeren Dateien (>5 Min) an

## Lizenz

GPL-3.0

## Autor

Michael Karbacher