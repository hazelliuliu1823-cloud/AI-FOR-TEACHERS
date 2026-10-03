#!/usr/bin/env python3
"""Decode CFR output, scan quiet audio and extract all final-timeline joins."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
SILENCE = re.compile(r'silence_(start|end):\s*(' + NUMBER + r')')
AUDIO = re.compile(r'pts_time:(' + NUMBER + r').*?rate:(\d+).*?nb_samples:(\d+)')
TIMEBASE = re.compile(r'^#tb\s+0:\s*(\d+)\s*/\s*(\d+)\s*$')
DIMENSIONS = re.compile(r'^#dimensions\s+0:\s*(\d+)x(\d+)\s*$')


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', errors='replace', shell=False)
    if result.returncode:
        raise RuntimeError(f'FFmpeg returned {result.returncode}: {result.stderr[-2400:]}')
    return result


def parse_video(text):
    tb, dimensions, frames = None, None, []
    for line in text.splitlines():
        match = TIMEBASE.match(line)
        if match:
            tb = Fraction(int(match[1]), int(match[2]))
        match = DIMENSIONS.match(line)
        if match:
            dimensions = [int(match[1]), int(match[2])]
        if not line.strip() or line.startswith('#'):
            continue
        values = [s.strip() for s in line.split(',')]
        if len(values) != 6:
            raise ValueError('Unrecognized framemd5 record; parsing cannot certify output')
        stream, dts, pts, duration, size = map(int, values[:5])
        if stream != 0 or duration <= 0 or size <= 0:
            raise ValueError('Invalid decoded video record')
        frames.append((pts, duration))
    if tb is None or not frames or dimensions is None:
        raise ValueError('No decoded frames, dimensions or timebase parsed')
    times = [pts * tb for pts, _ in frames]
    if any(b <= a for a, b in zip(times[:-1], times[1:])):
        raise ValueError('Non-increasing decoded video timestamps')
    start = times[0]
    end = max((pts + duration) * tb for pts, duration in frames)
    return {'frames': len(frames), 'start_seconds': float(start), 'end_seconds': float(end),
            'duration_seconds': float(end - start), 'dimensions': dimensions,
            'timebase': str(tb)}, times


def parse_audio(text):
    audio_frames = []
    for line in text.splitlines():
        if 'ashowinfo' not in line or 'nb_samples:' not in line:
            continue
        m = AUDIO.search(line)
        if not m:
            raise ValueError('Unrecognized ashowinfo record')
        pts, rate, samples = float(m[1]), int(m[2]), int(m[3])
        if rate <= 0 or samples <= 0:
            raise ValueError('Invalid audio frame data')
        audio_frames.append((pts, pts + samples / rate))
    if not audio_frames:
        raise ValueError('No decoded audio records; cannot interpret as no silence')
    start, end = min(x[0] for x in audio_frames), max(x[1] for x in audio_frames)
    quiet, pending = [], None
    for line in text.splitlines():
        if 'silence_start:' not in line and 'silence_end:' not in line:
            continue
        m = SILENCE.search(line)
        if not m:
            raise ValueError('Unrecognized silence event')
        kind, time = m[1], float(m[2])
        if kind == 'start':
            if pending is not None:
                raise ValueError('Duplicate silence start without end')
            pending = time
        else:
            if pending is None or time < pending:
                raise ValueError('Silence end missing a valid start')
            quiet.append({'start_seconds': pending, 'end_seconds': time})
            pending = None
    if pending is not None:
        quiet.append({'start_seconds': pending, 'end_seconds': end})
    return {'start_seconds': start, 'end_seconds': end, 'duration_seconds': end - start,
            'decoded_audio_frames': len(audio_frames), 'quiet_windows': quiet}


def parser_selftest():
    sample = '#tb 0: 1/25\n#dimensions 0: 320x180\n0, 0, 0, 1, 86400, abc\n0, 1, 1, 1, 86400, def\n'
    result, _ = parse_video(sample)
    if result['frames'] != 2 or abs(result['duration_seconds'] - .08) > 1e-9:
        raise RuntimeError('Video parser self-test failed')
    log = ('[ashowinfo] n:0 pts:0 pts_time:0 fmt:s16 channels:1 rate:48000 nb_samples:96000\n'
           '[silencedetect] silence_start: 2.5e-1\n[silencedetect] silence_end: 1.25 | silence_duration: 1\n')
    if parse_audio(log)['quiet_windows'] != [{'start_seconds': .25, 'end_seconds': 1.25}]:
        raise RuntimeError('Silence parser self-test failed')
    for fn, text in [(parse_video, 'not-a-frame'), (parse_audio, '[silencedetect] no matches')]:
        try:
            fn(text)
        except ValueError:
            pass
        else:
            raise RuntimeError('Parser incorrectly accepted missing data')


def join_samples(manifest, count):
    fps = manifest['fps_num'] / manifest['fps_den']
    rows = []
    for join in manifest['joins']:
        a, b = join['start_frame'], join['end_frame']
        if type(a) is not int or type(b) is not int or not 0 < a <= b < count:
            raise ValueError('Join outside decoded output')
        indices = [a - 1, a, (a + b) // 2, b - 1, b] if b > a else [max(0, a - max(1, round(fps * .25))), a - 1, a, min(count - 1, a + max(1, round(fps * .25)))]
        rows.append({**join, 'sample_frames': list(dict.fromkeys(indices))})
    return rows


def contacts(ffmpeg, media, manifest, report, folder):
    rows = join_samples(manifest, report['video']['frames'])
    if not rows:
        return {'status': 'not_applicable', 'reason': 'no joins', 'rows': []}
    numbers = sorted({n for row in rows for n in row['sample_frames']})
    frame_folder = folder / ('frames_' + report['file_sha256'][:12] + '_' + report['manifest_sha256'][:12])
    frame_folder.mkdir(parents=True, exist_ok=True)
    select = '+'.join(f'eq(n\\,{n})' for n in numbers)
    run([ffmpeg, '-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-i', str(media),
         '-map', '0:v:0', '-an', '-vf', 'select=' + select, '-fps_mode', 'vfr',
         '-y', str(frame_folder / '%06d.png')])
    images = sorted(frame_folder.glob('*.png'))
    if len(images) != len(numbers):
        raise ValueError('Contact extraction frame count mismatch')
    by_frame = dict(zip(numbers, images))
    for row in rows:
        row['images'] = [{'frame': n, 'file': str(by_frame[n])} for n in row['sample_frames']]
    index = {'file_sha256': report['file_sha256'], 'manifest_sha256': report['manifest_sha256'], 'rows': rows}
    (folder / 'contact-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return {'status': 'frames_only', 'reason': 'Pillow unavailable; montage not generated', **index}
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 15)
    except OSError:
        font = ImageFont.load_default()
    pages = []
    for page_start in range(0, len(rows), 6):
        subset = rows[page_start:page_start + 6]
        sheet = Image.new('RGB', (1250, len(subset) * 200), 'white')
        draw = ImageDraw.Draw(sheet)
        for row_number, row in enumerate(subset):
            y = row_number * 200
            draw.text((8, y + 4), f'{row["join_id"]} {row["from_event"]} -> {row["to_event"]} [{row["start_frame"]}, {row["end_frame"]})', fill='black', font=font)
            for col, number in enumerate(row['sample_frames']):
                with Image.open(by_frame[number]) as original:
                    im = original.convert('RGB')
                    im.thumbnail((240, 140))
                    sheet.paste(im, (col * 250 + 5, y + 28))
                seconds = number * manifest['fps_den'] / manifest['fps_num']
                draw.text((col * 250 + 5, y + 172), f'F{number}  {seconds:.3f}s', fill='black', font=font)
        destination = folder / f'cuts_{page_start // 6 + 1:02d}.png'
        sheet.save(destination)
        pages.append(str(destination))
    return {'status': 'generated_not_reviewed', 'pages': pages, **index}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--outdir', type=Path, required=True)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--threshold-db', type=float, default=-50)
    parser.add_argument('--minimum-quiet', type=float, default=1)
    parser.add_argument('--contacts', action='store_true')
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    report = {'technical_status': 'error', 'checks_scope': 'decoded CFR media, quiet detection and contact extraction; not editorial approval',
              'errors': [], 'review_required': [], 'playback_verified': False}
    try:
        parser_selftest()
        executable = shutil.which(args.ffmpeg)
        if not executable:
            raise ValueError('FFmpeg unavailable; media audit not performed')
        if args.minimum_quiet <= 0 or args.threshold_db > 0:
            raise ValueError('Invalid silence parameters')
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        if manifest.get('coordinate_space') != 'output':
            raise ValueError('Audit requires compiled output coordinates')
        fps = Fraction(manifest['fps_num'], manifest['fps_den'])
        target = manifest['total_frames']
        if fps <= 0 or type(target) is not int or target <= 0:
            raise ValueError('Invalid expected frame count or rate')
        report.update(file=str(args.media), file_sha256=file_hash(args.media), manifest_sha256=file_hash(args.manifest),
                      expected_frames=target, expected_duration_seconds=float(target / fps),
                      threshold_db=args.threshold_db, minimum_quiet_seconds=args.minimum_quiet)
        output = run([executable, '-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-copyts', '-i', str(args.media),
                      '-map', '0:v:0', '-an', '-fps_mode', 'passthrough', '-threads', '1', '-f', 'framemd5', '-'])
        (args.outdir / 'decoded-video.framemd5').write_text(output.stdout, encoding='utf-8')
        video, times = parse_video(output.stdout)
        report['video'] = video
        delta = video['frames'] - target
        report['frame_delta'] = delta
        if delta:
            report['errors'].append(f'Frame count differs by {delta}; even one frame requires resolution')
        frame_time = float(1 / fps)
        if abs(video['duration_seconds'] - float(target / fps)) > frame_time + 1e-6:
            report['errors'].append('Decoded video duration differs by more than one target frame')
        if abs(video['start_seconds']) > frame_time + 1e-6:
            report['errors'].append('Nonzero output video start requires explicit time mapping')
        if any(abs(float(b - a - 1 / fps)) > 1e-6 for a, b in zip(times[:-1], times[1:])):
            report['errors'].append('Decoded timestamps do not follow target CFR cadence')
        if video['dimensions'] != [manifest['width'], manifest['height']]:
            report['errors'].append('Output dimensions mismatch')
        try:
            audio_output = run([executable, '-hide_banner', '-nostdin', '-v', 'info', '-xerror', '-copyts', '-i', str(args.media),
                                '-map', '0:a:0', '-vn', '-af', f'silencedetect=n={args.threshold_db}dB:d={args.minimum_quiet},ashowinfo',
                                '-f', 'null', '-'])
            (args.outdir / 'audio-scan.log').write_text(audio_output.stderr, encoding='utf-8')
            audio = parse_audio(audio_output.stderr)
            for window in audio['quiet_windows']:
                a = (window['start_seconds'] - video['start_seconds']) * float(fps)
                b = (window['end_seconds'] - video['start_seconds']) * float(fps)
                window['expected_reason'] = next((q['reason'] for q in manifest.get('expected_quiet_ranges', [])
                                                  if q.get('reason') and q['start_frame'] - 1 <= a and b <= q['end_frame'] + 1), None)
                if not window['expected_reason']:
                    report['review_required'].append({'quiet_window': window})
            if abs(audio['start_seconds'] - video['start_seconds']) > max(.1, 2 * frame_time) or abs(audio['end_seconds'] - video['end_seconds']) > max(.1, 2 * frame_time):
                report['review_required'].append('Audio/video presentation ranges differ; inspect padding, truncation and sync')
            report['audio'] = audio
            report['audio_scan_status'] = 'completed'
        except (RuntimeError, ValueError) as exc:
            if manifest.get('audio_required', True) is False and 'matches no streams' in str(exc):
                report['audio_scan_status'] = 'not_applicable_no_audio_expected'
            else:
                report['audio_scan_status'] = 'error'
                report['errors'].append(str(exc))
        if args.contacts:
            if report['errors']:
                report['contacts'] = {'status': 'not_generated', 'reason': 'resolve media integrity errors first'}
            else:
                report['contacts'] = contacts(executable, args.media, manifest, report, args.outdir)
        report['technical_status'] = 'fail' if report['errors'] else 'pass'
    except (ValueError, KeyError, TypeError, ZeroDivisionError, OSError, RuntimeError) as exc:
        report['errors'].append(str(exc))
    destination = args.outdir / 'render-audit.json'
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'technical_status': report['technical_status'], 'report': str(destination), 'errors': report['errors'],
                      'review_items': len(report['review_required']), 'playback_verified': False}, ensure_ascii=False))
    return 1 if report['technical_status'] != 'pass' else 0


if __name__ == '__main__':
    raise SystemExit(main())
