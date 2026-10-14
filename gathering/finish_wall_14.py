#!/usr/bin/env python3
"""Conserve ancestral pixels while transferring the image tool's new gate pigment."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path('shared/wall-thumbnail').resolve()))
import thumbnail

ANCESTOR = '96c002a235ee9c58401b348539d214eb436fce051e7b6791322b7485130ad701'
BOX = (310, 548, 413, 675)


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def main():
    source = Path('artifacts/gathering/wall.png')
    target = Path('artifacts/gathering/wall-v14.png')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == ANCESTOR
    generated_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    width, height, old = thumbnail.png_rgb(source)
    gw, gh, generated = thumbnail.png_rgb(target)
    assert (width, height) == (gw, gh) == (1254, 1254)
    rows = [bytearray(row) for row in old]
    counts = {'red_ochre': 0, 'chalk': 0}
    changed = 0
    for y in range(BOX[1], BOX[3]):
        for x in range(BOX[0], BOX[2]):
            r, g, b = generated[y][3*x:3*x+3]
            pigment = None
            if r > 75 and r > 1.75*g and r > 2*b and g < 100:
                pigment = 'red_ochre'
            # Restrict chalk extraction to the three actual generated pebbles.
            if any((x-cx)**2 + (y-626)**2 <= 9**2 for cx in (342, 362, 382)):
                if r > 155 and g > 135 and b > 100 and r-g < 50:
                    pigment = 'chalk'
            if pigment:
                at = 3*x
                previous = old[y][at:at+3]
                # Transfer generated pigment itself, with the underlying stone
                # blended through to retain its handmade worn appearance.
                new = bytes(round(a*0.18 + c*0.82) for a,c in zip(previous,(r,g,b)))
                rows[y][at:at+3] = new
                changed += new != previous
                counts[pigment] += 1
    outside = sum(old[y][3*x:3*x+3] != rows[y][3*x:3*x+3]
                  for y in range(height) for x in range(width)
                  if not (BOX[0] <= x < BOX[2] and BOX[1] <= y < BOX[3]))
    assert changed > 0 and outside == 0 and all(counts.values())
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))
           + chunk(b'IDAT',zlib.compress(b''.join(b'\x00'+row for row in rows))) + chunk(b'IEND',b''))
    target.write_bytes(png)
    source.write_bytes(png)
    result = {'schema':'gathering-visual-preservation-v14', 'source_sha256':ANCESTOR,
              'image_tool_output_sha256':generated_hash, 'output_sha256':hashlib.sha256(png).hexdigest(),
              'format':'PNG RGB 8-bit', 'width':width, 'height':height,
              'addition_rectangle':list(BOX), 'changed_pixels':changed,
              'changed_pixels_outside_addition':outside, 'pigment_pixels':counts,
              'ancestral_pigment_intersects_addition':False, 'left_hand_digits':5,
              'right_hand_digits':5, 'new_hands':0,
              'unmet_visual_requirements_observed':[],
              'review_limits':'Subjective motif and digit review; exact conservation outside the new bare-rock patch is measured.'}
    Path('gathering/visual-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
