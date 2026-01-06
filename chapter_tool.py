#!/usr/bin/env python3
"""
Audio Chapter Marker Tool
Embeds Audacity chapter markers into audio files and exports as MP3
"""

import argparse
import sys
from pathlib import Path
from mutagen.id3 import ID3, CTOC, CHAP, TIT2, CTOCFlags
from mutagen.mp3 import MP3
import subprocess


def parse_audacity_labels(label_file):
    """Parse Audacity label file and return list of chapters"""
    chapters = []
    with open(label_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                start_time = float(parts[0])
                title = parts[2]
                chapters.append({
                    'start_ms': int(start_time * 1000),
                    'title': title
                })
    return sorted(chapters, key=lambda x: x['start_ms'])


def get_audio_duration_ms(audio_file):
    """Get audio duration in milliseconds using ffprobe"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_file)],
            capture_output=True,
            text=True,
            check=True
        )
        duration_sec = float(result.stdout.strip())
        return int(duration_sec * 1000)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Auslesen der Audio-Dauer: {e}", file=sys.stderr)
        sys.exit(1)


def convert_to_mp3(input_file, output_file):
    """Convert audio file to MP3 using ffmpeg"""
    print(f"Konvertiere zu MP3...")

    cmd = ['ffmpeg', '-i', str(input_file), '-y', '-codec:a', 'libmp3lame', '-q:a', '2', str(output_file)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ {output_file.name} erstellt")
    except subprocess.CalledProcessError as e:
        print(f"Fehler bei der Konvertierung: {e}", file=sys.stderr)
        sys.exit(1)


def embed_chapters_mp3(mp3_file, chapters, total_duration_ms):
    """Embed chapters in MP3 file using ID3v2 CTOC/CHAP frames"""
    print(f"Füge Kapitelmarken zu {mp3_file.name} hinzu...")

    try:
        audio = ID3(mp3_file)
    except:
        audio = ID3()

    # Remove existing chapter frames
    audio.delall('CTOC')
    audio.delall('CHAP')

    # Create chapter frames
    chapter_ids = []
    for i, chapter in enumerate(chapters):
        chap_id = f'chp{i}'
        chapter_ids.append(chap_id)

        # Determine end time
        if i < len(chapters) - 1:
            end_ms = chapters[i + 1]['start_ms']
        else:
            end_ms = total_duration_ms

        # Create CHAP frame
        chap = CHAP(
            encoding=3,  # UTF-8
            element_id=chap_id,
            start_time=chapter['start_ms'],
            end_time=end_ms,
            sub_frames=[
                TIT2(encoding=3, text=[chapter['title']])
            ]
        )
        audio.add(chap)

    # Create table of contents
    ctoc = CTOC(
        encoding=3,
        element_id='toc',
        flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
        child_element_ids=chapter_ids,
        sub_frames=[
            TIT2(encoding=3, text=['Table of Contents'])
        ]
    )
    audio.add(ctoc)

    audio.save(mp3_file, v2_version=3)
    print(f"✓ {len(chapters)} Kapitelmarken hinzugefügt")


def main():
    parser = argparse.ArgumentParser(
        description='Fügt Audacity-Kapitelmarken in Audio-Dateien ein und exportiert als MP3'
    )
    parser.add_argument('audio_file', type=Path, help='Audio-Eingabedatei')
    parser.add_argument('label_file', type=Path, help='Audacity Label-Datei (.txt)')
    parser.add_argument('-o', '--output-dir', type=Path, default=None,
                        help='Ausgabeverzeichnis (Standard: gleiches Verzeichnis wie Eingabedatei)')

    args = parser.parse_args()

    # Validate input files
    if not args.audio_file.exists():
        print(f"Fehler: Audio-Datei nicht gefunden: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    if not args.label_file.exists():
        print(f"Fehler: Label-Datei nicht gefunden: {args.label_file}", file=sys.stderr)
        sys.exit(1)

    # Set output directory
    output_dir = args.output_dir if args.output_dir else args.audio_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse chapters
    print(f"Lese Kapitelmarken aus {args.label_file.name}...")
    chapters = parse_audacity_labels(args.label_file)
    print(f"✓ {len(chapters)} Kapitelmarken gefunden")

    # Get audio duration
    total_duration_ms = get_audio_duration_ms(args.audio_file)

    # Determine output base name
    base_name = args.audio_file.stem

    # Process MP3
    mp3_output = output_dir / f"{base_name}_chapters.mp3"
    convert_to_mp3(args.audio_file, mp3_output)
    embed_chapters_mp3(mp3_output, chapters, total_duration_ms)

    print("\n✓ Fertig! Kapitelmarken wurden erfolgreich eingebettet.")


if __name__ == '__main__':
    main()