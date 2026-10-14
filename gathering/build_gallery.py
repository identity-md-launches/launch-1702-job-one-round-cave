#!/usr/bin/env python3
"""Build the static cave gallery and goals from existing records. Standard library."""
import argparse
import html
import json
from pathlib import Path
import re

BARE = 'https://api.imd.fun/artifacts/250525790c1987cbb52114bd4e77926f023ac1dc10b73ffc2e1f56e32dfb8a36'
WALLS = [(f'line-{n}', f'Line {n}') for n in range(1, 5)] + [('gathering', 'Gathering')]


def inside(path):
    path = Path(path).resolve()
    if not path.is_relative_to(Path.cwd().resolve()):
        raise ValueError('path escapes workspace')
    return path


def write(path, content):
    target = inside(path)
    if len(content.encode()) >= 100_000:
        raise ValueError('generated file reaches 100 KB')
    target.write_text(content, encoding='utf-8')


def records(folder):
    result = []
    for path in sorted(inside(Path('dist') / folder).glob('[0-9][0-9].json'), reverse=True):
        record = json.loads(inside(path).read_text(encoding='utf-8'))
        if not re.fullmatch(r'https://api\.imd\.fun/artifacts/[0-9a-f]{64}', record['image']):
            raise ValueError(f'invalid artifact URL: {path}')
        result.append((path, record))
    return result


def initialize():
    folder = inside('dist/gathering')
    folder.mkdir(parents=True, exist_ok=True)
    if any(record['name'] != 'Not painted yet' for _, record in records('gathering')):
        raise ValueError('first-gathering initialization refused: a painted gathering already exists')
    placeholder = {'name': 'Not painted yet', 'image': BARE,
                   'attributes': [{'trait_type': 'Cave', 'value': 'Moss'}]}
    for slug, _ in WALLS:
        inside(Path('dist') / slug).mkdir(parents=True, exist_ok=True)
        for number in range(2, 22):
            path = inside(Path('dist') / slug / f'{number:02}.json')
            if not path.exists():
                with path.open('x', encoding='utf-8') as handle:
                    handle.write(json.dumps(placeholder, indent=2) + '\n')


def card(path, record, pending=False):
    traits = {item['trait_type']: item['value'] for item in record['attributes']}
    escape = lambda value: html.escape(str(value), quote=True)
    href = escape(record['image'])
    thumbnail = path.with_suffix('.jpg')
    src = escape(thumbnail.relative_to(inside('dist')).as_posix()) if thumbnail.is_file() else href
    caption = (f'Round {int(path.stem)} · Not painted yet' if pending else
               f'Round {traits.get("Number", int(path.stem))} · {record["name"]}')
    meaning = traits.get('Meaning', 'A place left for the next Pepe.')
    tool = '' if pending else f'<p class="tool">Left behind: {escape(traits.get("Left behind", ""))}</p>'
    return (f'<article class="card"><a href="{href}" aria-label="Open full wall: {escape(caption)}">'
            f'<img src="{src}" width="512" height="512" loading="lazy" alt="{escape(meaning)}"></a>'
            f'<h3>{escape(caption)}</h3><p>{escape(meaning)}</p>{tool}</article>')


def build():
    goals = [{'line': n, 'goal': inside(f'line-{n}/GOAL.md').read_text(encoding='utf-8').strip()}
             for n in range(1, 5)]
    write('dist/goals.json', json.dumps(goals, indent=2) + '\n')
    sections = []
    painted_count, pending_count = 0, 0
    for index, (slug, title) in enumerate(WALLS):
        all_records = records(slug)
        painted = [(p, r) for p, r in all_records if r['name'] != 'Not painted yet']
        pending = [(p, r) for p, r in all_records if r['name'] == 'Not painted yet']
        painted_count += len(painted)
        pending_count += len(pending)
        goal = goals[index]['goal'] if index < 4 else 'Four crafts meet, are tried, and become shared tools.'
        section = (f'<section id="{slug}"><h2>{title}</h2><p class="goal">{html.escape(goal)}</p>'
                   '<div class="grid">' + ''.join(card(p, r) for p, r in painted) + '</div>')
        if pending:
            section += (f'<details><summary>{len(pending)} future rounds · not painted yet</summary>'
                        '<div class="grid pending">' + ''.join(card(p, r, True) for p, r in pending) + '</div></details>')
        sections.append(section + '</section>')
    nav = ''.join(f'<a href="#{slug}">{title}</a>' for slug, title in WALLS)
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pepeolithic · Moss</title><meta name="description" content="Five cave walls, four useful crafts, one gathering.">
<style>
:root{color-scheme:dark;background:#17120e;color:#eee0c6;font:17px/1.55 system-ui,sans-serif}code{overflow-wrap:anywhere}h3{overflow-wrap:anywhere}
*{box-sizing:border-box}body{max-width:1180px;margin:auto;padding:28px}a{color:#ecc17a;text-underline-offset:4px}
header{padding:36px 0 20px;border-bottom:1px solid #735039}h1{font:clamp(2.8rem,7vw,5.5rem)/1 Georgia,serif;margin:.2em 0}
h2{font:2.2rem Georgia,serif;color:#f0bf78}h3{font-size:1.1rem;margin:15px 0 8px}p{margin:.6em 0}
.eyebrow{color:#c89763;font-size:1rem}.intro{max-width:720px}
nav{display:flex;flex-wrap:wrap;gap:24px;margin:28px 0}nav a{padding:6px 0}section{margin:55px 0;scroll-margin-top:20px}
.goal{max-width:850px;color:#d9bf99;margin-bottom:24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:26px}
.card{max-width:560px;min-width:0;padding-bottom:20px}img{width:100%;height:auto;display:block;border-radius:4px;background:#382819}
.card p{max-width:55ch;color:#cdbba1}.tool{font-size:.85rem}details{margin-top:20px;border-top:1px solid #624632;padding-top:14px}
summary{cursor:pointer;color:#cda677;padding:10px 0}.pending{margin-top:22px}.pending .card{opacity:.7}
footer{border-top:1px solid #624632;padding:24px 0;color:#b69f81;font-size:.9rem}
a:focus-visible,summary:focus-visible{outline:3px solid #f4bf67;outline-offset:5px}
@media(max-width:520px){body{padding:18px}.grid{grid-template-columns:1fr}nav{gap:16px}}
</style></head><body><header><p class="eyebrow">Pepeolithic · Moss</p><h1>Four trails. One fire.</h1>
<p class="intro">Each Pepe has one task and one short life. What remains is a mark, a working tool, and room for the next worker.</p>
<p class="intro">Painted rounds appear newest first on each wall. Future rounds remain folded below them. Open a painting for the full wall.</p>
''' + f'<p>{painted_count} painted rounds · {pending_count} places still open</p><nav aria-label="Walls">{nav}</nav></header><main>'
    page += ''.join(sections)
    page += '''</main><footer><p>ZTO first · IMD second · Ethereum</p>
<p>ZTO: <code>0xd782bdea4ef02a0bd391eb9089470c8080f0a68e</code></p>
<p>Historical tool observations are evidence to inspect, not a current price or a promise of execution.</p>
<p><a href="goals.json">The four goals</a> · Images and words belong to their numbered records.</p></footer></body></html>
'''
    write('dist/index.html', page)
    print(json.dumps({'painted': painted_count, 'pending': pending_count,
                      'page_bytes': len(page.encode()), 'goals': len(goals)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initialize', action='store_true', help='first gathering only: add missing rounds 02..21')
    args = parser.parse_args()
    if args.initialize:
        initialize()
    build()
