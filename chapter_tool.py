#!/usr/bin/env python3
"""
Audio Chapter Marker Tool
Embeds Audacity chapter markers into audio files and exports as MP3
with podcast-standard loudness normalization
"""

import argparse
import sys
from pathlib import Path
from mutagen.id3 import ID3, CTOC, CHAP, TIT2, CTOCFlags
from mutagen.mp3 import MP3
import subprocess
import json


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
                print(f"  DEBUG: Kapitel gefunden: {title} @ {start_time}s")
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
        duration_ms = int(duration_sec * 1000)
        print(f"  DEBUG: Audio-Dauer: {duration_sec:.2f}s ({duration_ms}ms)")
        return duration_ms
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Auslesen der Audio-Dauer: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_loudness(audio_file):
    """Analyze audio loudness using ffmpeg loudnorm filter"""
    print("Analysiere Audio-Lautstärke...")

    cmd = [
        'ffmpeg', '-i', str(audio_file),
        '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json',
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Extract JSON from stderr (ffmpeg outputs to stderr)
        stderr = result.stderr

        # Find JSON block in output
        json_start = stderr.rfind('{')
        json_end = stderr.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            print("  WARNUNG: Konnte Lautstärke-Analyse nicht parsen", file=sys.stderr)
            return None

        loudness_data = json.loads(stderr[json_start:json_end])

        input_i = float(loudness_data.get('input_i', 0))
        input_tp = float(loudness_data.get('input_tp', 0))
        input_lra = float(loudness_data.get('input_lra', 0))
        input_thresh = float(loudness_data.get('input_thresh', 0))

        print(f"  Aktuelle Lautstärke: {input_i:.1f} LUFS")
        print(f"  True Peak: {input_tp:.1f} dBTP")
        print(f"  Loudness Range: {input_lra:.1f} LU")

        return {
            'input_i': input_i,
            'input_tp': input_tp,
            'input_lra': input_lra,
            'input_thresh': input_thresh
        }

    except subprocess.CalledProcessError as e:
        print(f"  WARNUNG: Lautstärke-Analyse fehlgeschlagen: {e}", file=sys.stderr)
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"  WARNUNG: Konnte Lautstärke-Daten nicht parsen: {e}", file=sys.stderr)
        return None


def convert_to_mp3(input_file, output_file, normalize=True, target_lufs=-16):
    """Convert audio file to MP3 using ffmpeg with optional loudness normalization"""
    print(f"Konvertiere zu MP3...")

    if normalize:
        print(f"Normalisiere auf {target_lufs} LUFS (Podcast-Standard)...")

        # First pass: analyze
        loudness_data = analyze_loudness(input_file)

        if loudness_data:
            # Second pass: normalize with measured values
            print("Wende Lautstärke-Normalisierung an...")
            cmd = [
                'ffmpeg', '-i', str(input_file), '-y',
                '-af',
                f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11:measured_I={loudness_data["input_i"]}:measured_TP={loudness_data["input_tp"]}:measured_LRA={loudness_data["input_lra"]}:measured_thresh={loudness_data["input_thresh"]}:linear=true:print_format=summary',
                '-codec:a', 'libmp3lame', '-q:a', '2',
                str(output_file)
            ]
        else:
            # Fallback: single-pass normalization
            print("Verwende Einzel-Pass-Normalisierung...")
            cmd = [
                'ffmpeg', '-i', str(input_file), '-y',
                '-af', f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11',
                '-codec:a', 'libmp3lame', '-q:a', '2',
                str(output_file)
            ]
    else:
        # No normalization
        cmd = ['ffmpeg', '-i', str(input_file), '-y', '-codec:a', 'libmp3lame', '-q:a', '2', str(output_file)]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ {output_file.name} erstellt")

        if normalize:
            print(f"✓ Lautstärke auf {target_lufs} LUFS normalisiert")

    except subprocess.CalledProcessError as e:
        print(f"Fehler bei der Konvertierung: {e}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def embed_chapters_mp3(mp3_file, chapters, total_duration_ms):
    """Embed chapters in MP3 file using ID3v2 CTOC/CHAP frames"""
    print(f"Füge Kapitelmarken zu {mp3_file.name} hinzu...")

    try:
        audio = ID3(mp3_file)
        print("  DEBUG: ID3-Tags geladen")
    except:
        audio = ID3()
        print("  DEBUG: Neue ID3-Tags erstellt")

    # Remove existing chapter frames
    audio.delall('CTOC')
    audio.delall('CHAP')
    print("  DEBUG: Alte Kapitelmarken entfernt")

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

        print(f"  DEBUG: Kapitel {i}: '{chapter['title']}' von {chapter['start_ms']}ms bis {end_ms}ms")

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
    print(f"  DEBUG: CTOC mit {len(chapter_ids)} Kapiteln erstellt")

    audio.save(mp3_file, v2_version=3)
    print(f"✓ {len(chapters)} Kapitelmarken hinzugefügt")

    # Verify chapters were written
    print("\nVerifiziere geschriebene Kapitelmarken...")
    verify_audio = ID3(mp3_file)
    chap_frames = [key for key in verify_audio.keys() if key.startswith('CHAP')]
    ctoc_frames = [key for key in verify_audio.keys() if key.startswith('CTOC')]
    print(f"  DEBUG: {len(chap_frames)} CHAP-Frames gefunden")
    print(f"  DEBUG: {len(ctoc_frames)} CTOC-Frames gefunden")


def main():
    parser = argparse.ArgumentParser(
        description='Fügt Audacity-Kapitelmarken in Audio-Dateien ein und exportiert als MP3 mit Podcast-Lautstärke'
    )
    parser.add_argument('audio_file', type=Path, help='Audio-Eingabedatei')
    parser.add_argument('label_file', type=Path, help='Audacity Label-Datei (.txt)')
    parser.add_argument('-o', '--output-dir', type=Path, default=None,
                        help='Ausgabeverzeichnis (Standard: gleiches Verzeichnis wie Eingabedatei)')
    parser.add_argument('--no-normalize', action='store_true',
                        help='Lautstärke-Normalisierung deaktivieren')
    parser.add_argument('--target-lufs', type=float, default=-16,
                        help='Ziel-Lautstärke in LUFS (Standard: -16 für Podcasts)')

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

    if not chapters:
        print("FEHLER: Keine Kapitelmarken in der Label-Datei gefunden!", file=sys.stderr)
        print("Erwartet wird das Audacity-Label-Format: START\\tEND\\tTITLE", file=sys.stderr)
        sys.exit(1)

    print(f"✓ {len(chapters)} Kapitelmarken gefunden")

    # Get audio duration
    total_duration_ms = get_audio_duration_ms(args.audio_file)

    # Determine output base name
    base_name = args.audio_file.stem

    # Process MP3
    mp3_output = output_dir / f"{base_name}_chapters.mp3"
    convert_to_mp3(
        args.audio_file,
        mp3_output,
        normalize=not args.no_normalize,
        target_lufs=args.target_lufs
    )
    embed_chapters_mp3(mp3_output, chapters, total_duration_ms)

    print("\n✓ Fertig! Kapitelmarken wurden erfolgreich eingebettet.")
    if not args.no_normalize:
        print(f"✓ Audio auf {args.target_lufs} LUFS normalisiert")

    print(f"\nZum Testen der Kapitelmarken:")
    print(f"  VLC: Wiedergabe → Kapitel")
    print(f"  ffprobe: ffprobe -show_chapters '{mp3_output}'")


if __name__ == '__main__':
    main()