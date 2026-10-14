"""One-time transfer of new pigment only; not a dependency of the delivered tool."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('thumbnail', ROOT / 'shared/wall-thumbnail/thumbnail.py')
thumbnail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thumbnail)
ancestor_path = ROOT / 'artifacts/line-3/wall.png'
output_path = ROOT / 'artifacts/line-3/wall-v14.png'
ancestor_bytes = ancestor_path.read_bytes()
generated_bytes = output_path.read_bytes()
assert hashlib.sha256(ancestor_bytes).hexdigest() == '2bd990549a24fbb2123c6f1a9be7845a7fdeea0ca734d316afaec675de0e3ae2'
w, h, ancestor = thumbnail.png_rgb(ancestor_path)
gw, gh, generated = thumbnail.png_rgb(output_path)
assert (w, h) == (gw, gh) == (1254, 1254)
rows = [bytearray(row) for row in ancestor]
# Only new barrier and new stone pixels are retained from the generated edit.
# Transfer them to clear rock; discard all generated ancestral changes and rock.
source = (850, 918, 982, 995)
target = (984, 850, 1116, 927)
for sy in range(source[1], source[3]):
    for sx in range(source[0], source[2]):
        red, green, blue = generated[sy][3*sx:3*sx+3]
        charcoal = red < 100 and green < 80 and blue < 65
        stone_inside = ((sx-941)/34)**2 + ((sy-961)/25)**2 < 1
        ochre = stone_inside and red > 150 and 85 < green < 150 and blue < 80
        if not (charcoal or ochre):
            continue
        tx, ty = target[0]+sx-source[0], target[1]+sy-source[1]
        # Blend new earth pigment with inherited stone texture.
        pigment = (43, 30, 21) if charcoal else (179, 113, 43)
        for channel in range(3):
            index = 3*tx+channel
            rows[ty][index] = (ancestor[ty][index]*2 + pigment[channel]*3)//5


def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind+payload)))


png = (b'\x89PNG\r\n\x1a\n'
       + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(b''.join(b'\0'+row for row in rows), 9))
       + chunk(b'IEND', b''))
changed = outside = 0
for y in range(h):
    for x in range(w):
        if rows[y][3*x:3*x+3] != ancestor[y][3*x:3*x+3]:
            changed += 1
            if not (target[0] <= x < target[2] and target[1] <= y < target[3]):
                outside += 1
assert changed > 0 and outside == 0
output_path.write_bytes(png)
ancestor_path.write_bytes(png)
jpeg = thumbnail.jpeg(thumbnail.resize(w, h, rows, 512))
assert len(jpeg) < 100000
with (ROOT / 'dist/line-3/34.jpg').open('xb') as stream:
    stream.write(jpeg)
report = {'ancestor_sha256': hashlib.sha256(ancestor_bytes).hexdigest(),
          'generated_sha256': hashlib.sha256(generated_bytes).hexdigest(),
          'wall_sha256': hashlib.sha256(png).hexdigest(),
          'format': 'PNG', 'dimensions': [w, h], 'mode': 'RGB',
          'source_pigment_box': source, 'addition_box': target,
          'changed_pixels': changed, 'changed_pixels_outside_addition': outside,
          'thumbnail': {'format': 'JPEG', 'dimensions': [512, 512], 'bytes': len(jpeg)},
          'manual_review_pending': True, 'unmet_visual_requirements': []}
(ROOT / 'line-3/visual-checks-34.json').write_text(json.dumps(report, indent=2)+'\n')
record = {'name': 'The Trail Gate',
          'image': 'https://api.imd.fun/artifacts/'+report['wall_sha256'],
          'attributes': [
              {'trait_type': 'Cave', 'value': 'Moss'},
              {'trait_type': 'Wall', 'value': 'Line 3'},
              {'trait_type': 'Number', 'value': 34},
              {'trait_type': 'Left behind', 'value': 'Code Call Routes'},
              {'trait_type': 'Meaning', 'value': 'Pepe checks whether the trail reaches the called stone.'},
              {'trait_type': 'One thing', 'value': 'Ethereum executable code identity'}]}
with (ROOT / 'dist/line-3/34.json').open('x') as stream:
    stream.write(json.dumps(record, indent=2)+'\n')
print(json.dumps(report, indent=2))
