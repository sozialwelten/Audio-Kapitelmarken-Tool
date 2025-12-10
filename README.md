# Audio Kapitelmarken Tool

Ein Python-Kommandozeilen-Tool zum Einbetten von Audacity-Kapitelmarken in Audio-Dateien. Exportiert als M4A und MP3 mit vollständiger Podcast-Kapitelmarken-Unterstützung.

## Features

- Liest Audacity Label-Dateien (.txt)
- Bettet Kapitelmarken mit aktuellen Standards ein:
  - **M4A**: FFMETADATA-Format (MP4-Container)
  - **MP3**: ID3v2.3 CTOC/CHAP Frames
- Exportiert beide Formate oder einzeln

## Installation

```bash
# Repository klonen
git clone https://github.com/sozialwelten/Audio-Kapitelmarken-Tool.git
cd audio-chapter-tool

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

```bash
# Beide Formate erstellen
python chapter_tool.py audio.wav kapitel.txt

# Nur M4A
python chapter_tool.py audio.wav kapitel.txt --m4a-only

# Nur MP3
python chapter_tool.py audio.wav kapitel.txt --mp3-only

# In anderes Verzeichnis exportieren
python chapter_tool.py audio.wav kapitel.txt -o ./output
```

## Audacity Label-Format

```
2.638246	2.638246	Begrüßung
20.311316	20.311316	Experiment mit Audio
49.713455	49.713455	Vibecoding CLI Tool
71.677648	71.677648	Verabschiedung
```

## Kapitelmarken testen

```bash
# Kapitelmarken verifizieren
ffprobe -i datei_chapters.m4a -show_chapters
```

Die Kapitelmarken funktionieren in:
- Apple Podcasts, Overcast, Castro, Pocket Casts
- QuickTime Player (Darstellung → Kapitel einblenden)
- Den meisten modernen Podcast-Apps

## Lizenz

GPL-3.0

## Autor

Michael Karbacher