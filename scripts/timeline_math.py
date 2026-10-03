#!/usr/bin/env python3
"""Shared deterministic timeline math for validation and compilation."""
from fractions import Fraction


def _int(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{label} must be integer >= {minimum}')
    return value


def _speed_fraction(value):
    if type(value) not in (int, float) or not 0 < value < float('inf'):
        raise ValueError('Invalid speed')
    # str() avoids importing binary floating-point noise into the canonical math.
    return Fraction(str(value))


def round_half_up(value):
    """Quantize a non-negative Fraction to the nearest frame, ties upward."""
    if value < 0:
        raise ValueError('Frame quantity must be non-negative')
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def canonical_assembly_ranges(events, fps_num, fps_den):
    """Return cumulative-quantized assembly ranges.

    Source-event durations are accumulated as exact rational frame durations and
    only the cumulative boundary is quantized. This prevents independent per-event
    rounding from accumulating drift. Card durations remain explicit integer-frame
    durations from the assembly plan.
    """
    n = _int(fps_num, 'fps_num', 1)
    d = _int(fps_den, 'fps_den', 1)
    exact_cursor = Fraction(0)
    ranges = []
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f'events[{i}] must be object')
        start = round_half_up(exact_cursor)
        kind = event.get('kind')
        if kind == 'source':
            sin = _int(event.get('source_in_ms'), f'events[{i}].source_in_ms')
            sout = _int(event.get('source_out_ms'), f'events[{i}].source_out_ms', 1)
            if sout <= sin:
                raise ValueError(f'events[{i}]: source_out_ms must be > source_in_ms')
            speed = _speed_fraction(event.get('speed', 1))
            exact_frames = Fraction((sout - sin) * n, 1000 * d) / speed
        elif kind == 'card':
            a = _int(event.get('out_in_frame'), f'events[{i}].out_in_frame')
            b = _int(event.get('out_out_frame'), f'events[{i}].out_out_frame', 1)
            if b <= a:
                raise ValueError(f'events[{i}]: card output range must be nonempty')
            exact_frames = Fraction(b - a)
        else:
            raise ValueError(f'events[{i}]: unsupported event kind')
        exact_cursor += exact_frames
        end = round_half_up(exact_cursor)
        if end <= start:
            raise ValueError(f'events[{i}]: cumulative quantization produced empty event')
        ranges.append({'assembly_in_frame': start, 'assembly_out_frame': end,
                       'length_frames': end - start, 'exact_end_frames': exact_cursor})
    return ranges


def output_ranges_from_overlaps(assembly_ranges, overlaps):
    """Map cumulative assembly ranges to output ranges after adjacent overlaps."""
    if len(overlaps) != len(assembly_ranges):
        raise ValueError('overlaps must contain one value per event (first must be zero)')
    out = []
    for i, (assembly, overlap) in enumerate(zip(assembly_ranges, overlaps)):
        overlap = _int(overlap, f'overlaps[{i}]')
        length = assembly['length_frames']
        if i == 0:
            if overlap != 0:
                raise ValueError('first event overlap must be zero')
            start = 0
        else:
            if overlap >= min(assembly_ranges[i - 1]['length_frames'], length):
                raise ValueError('Overlap must be shorter than both adjacent events')
            if i > 1 and overlaps[i - 1] + overlap >= assembly_ranges[i - 1]['length_frames']:
                raise ValueError('Three-event overlap or zero stable middle segment is unsupported')
            start = out[-1]['out_out_frame'] - overlap
        end = start + length
        out.append({'out_in_frame': start, 'out_out_frame': end, 'length_frames': length})
    return out, (out[-1]['out_out_frame'] if out else 0)
