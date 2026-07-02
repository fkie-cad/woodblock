"""Generate an interactive, self-contained HTML visualization of a generated image.

The visualization shows the image as a colored map of fragments (one color per source
file), a list of the contained files, and a hex viewer for inspecting the bytes that were
actually written to the image. It is built from the ground-truth metadata produced by
:class:`woodblock.image.Image` (see :attr:`woodblock.image.Image.metadata`).

The actual image bytes -- needed for the hex viewer -- are either embedded into the HTML as
base64 (for small images) or read on demand from a user-selected file in the browser (for
large images). This keeps the HTML self-contained and usable offline via ``file://`` while
still scaling to arbitrarily large images.
"""

import base64
import json
import pathlib

#: Images up to this size (in bytes) are embedded directly into the HTML. Larger images are
#: loaded via a file picker in the browser so the HTML stays a reasonable size.
DEFAULT_MAX_EMBED_BYTES = 16 * 1024 * 1024


def build_view_model(metadata: dict) -> dict:
    """Turn image ground-truth metadata into a flat view model for the HTML/JS front end.

    The returned dictionary contains the image-wide settings, a list of files (each assigned a
    stable color index), a list of fragments sorted by their position in the image, and a list
    of layout *segments* (fragments interleaved with the padding regions between them).

    Args:
        metadata: The metadata as produced by :attr:`woodblock.image.Image.metadata`.

    Returns:
        A JSON-serializable view model.
    """
    block_size = metadata['block_size']
    files = []
    files_by_id = {}
    fragments = []
    color_index = 0
    image_end = 0
    # 1-based index of each real corpus file within its scenario (first-appearance order). This
    # mirrors the config's ``fileN`` used in the layout syntax; ground truth does not record the
    # config's literal number, so we recover it from layout order (deterministic, and equal to the
    # config for in-order layouts). Fillers are not numbered -- they map to the ``R``/``Z`` tokens.
    scenario_file_count = {}

    for scenario in metadata['scenarios']:
        for file in scenario['files']:
            original = file['original']
            file_id = original['id']
            is_filler = original['type'] == 'filler'
            if file_id not in files_by_id:
                scenario_file_number = None
                if not is_filler:
                    scenario_file_number = scenario_file_count.get(scenario['name'], 0) + 1
                    scenario_file_count[scenario['name']] = scenario_file_number
                entry = {
                    'id': file_id,
                    'type': original['type'],
                    'path': original['path'],
                    'sha256': original['sha256'],
                    'size': original['size'],
                    'scenario': scenario['name'],
                    'scenario_file_number': scenario_file_number,
                    'num_fragments': len(file['fragments']),
                    'color_index': None if is_filler else color_index,
                }
                if not is_filler:
                    color_index += 1
                files_by_id[file_id] = entry
                files.append(entry)
            for frag in file['fragments']:
                image_offsets = frag['image_offsets']
                file_offsets = frag['file_offsets']
                image_end = max(image_end, image_offsets['end'])
                if is_filler:
                    # ``str(datagen.Zeroes())`` is ``'zeroes'`` and ``str(datagen.Random())`` is ``'random'``.
                    label = 'Z' if original['path'] == 'zeroes' else 'R'
                else:
                    label = f'{files_by_id[file_id]["scenario_file_number"]}.{frag["number"]}'
                fragments.append(
                    {
                        'file_id': file_id,
                        'type': original['type'],
                        'path': original['path'],
                        'number': frag['number'],
                        'num_fragments': len(file['fragments']),
                        'label': label,
                        'size': frag['size'],
                        'sha256': frag['sha256'],
                        'image_start': image_offsets['start'],
                        'image_end': image_offsets['end'],
                        'file_start': file_offsets['start'],
                        'file_end': file_offsets['end'],
                        'scenario': scenario['name'],
                        'color_index': files_by_id[file_id]['color_index'],
                    }
                )

    fragments.sort(key=lambda frag: frag['image_start'])
    image_size = image_end
    if image_size % block_size != 0:
        image_size += block_size - (image_size % block_size)

    segments = []
    cursor = 0
    for frag in fragments:
        if frag['image_start'] > cursor:
            segments.append({'kind': 'padding', 'image_start': cursor, 'image_end': frag['image_start']})
        segments.append({'kind': 'fragment', **frag})
        cursor = frag['image_end']
    if cursor < image_size:
        segments.append({'kind': 'padding', 'image_start': cursor, 'image_end': image_size})

    return {
        'block_size': block_size,
        'seed': metadata.get('seed'),
        'corpus': metadata.get('corpus'),
        'image_size': image_size,
        'num_files': sum(1 for f in files if f['type'] == 'file'),
        'num_fragments': len(fragments),
        'files': files,
        'fragments': fragments,
        'segments': segments,
    }


def render_html(metadata: dict, image_bytes: bytes | None = None, title: str | None = None) -> str:
    """Render the interactive HTML visualization as a string.

    Args:
        metadata: The image ground-truth metadata.
        image_bytes: The raw bytes of the generated image. When given, they are embedded so the
            hex viewer works without any further user interaction. When ``None``, the hex viewer
            offers a file picker to load the image in the browser.
        title: Optional page title.

    Returns:
        The complete HTML document as a string.
    """
    view_model = build_view_model(metadata)
    title = title or 'Woodblock image visualization'
    embedded = base64.b64encode(image_bytes).decode('ascii') if image_bytes is not None else None

    view_model_json = json.dumps(view_model).replace('<', '\\u003c')
    html = _TEMPLATE
    html = html.replace('__TITLE__', _escape_html(title))
    html = html.replace('__VIEW_MODEL_JSON__', view_model_json)
    html = html.replace('__IMAGE_BASE64__', embedded or '')
    html = html.replace('__HAS_EMBEDDED__', 'true' if embedded is not None else 'false')
    return html


def create_visualization(
    metadata,
    image=None,
    output=None,
    max_embed_bytes: int = DEFAULT_MAX_EMBED_BYTES,
) -> pathlib.Path:
    """Build an HTML visualization file from metadata and (optionally) the image.

    Args:
        metadata: Either the metadata dictionary or a path to a ground-truth ``.json`` file.
        image: Optional path to the generated image. Its bytes are embedded for the hex viewer
            when the image is no larger than ``max_embed_bytes``; otherwise the viewer loads the
            image via a file picker in the browser.
        output: Output path for the HTML file. Defaults to the image path (or metadata path)
            with a ``.html`` suffix.
        max_embed_bytes: Maximum image size to embed directly into the HTML.

    Returns:
        The path the HTML visualization was written to.
    """
    metadata_path = None
    if isinstance(metadata, (str, pathlib.Path)):
        metadata_path = pathlib.Path(metadata)
        with metadata_path.open('r') as handle:
            metadata = json.load(handle)

    image_bytes = None
    image_path = pathlib.Path(image) if image is not None else None
    if image_path is not None and image_path.is_file() and image_path.stat().st_size <= max_embed_bytes:
        image_bytes = image_path.read_bytes()

    if output is None:
        if image_path is not None:
            # Mirror how the metadata file is named: "<image>.html" next to "<image>" and "<image>.json".
            output = image_path.with_name(image_path.name + '.html')
        elif metadata_path is not None:
            stem = metadata_path.name
            if stem.endswith('.json'):
                stem = stem[: -len('.json')]
            output = metadata_path.with_name(stem + '.html')
        else:
            raise ValueError('An output path is required when neither an image nor a metadata path is given.')
    output = pathlib.Path(output)

    title = f'Woodblock visualization – {image_path.name}' if image_path is not None else None
    output.write_text(render_html(metadata, image_bytes=image_bytes, title=title))
    return output


def _escape_html(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --bg: #14171c; --panel: #1c2128; --panel-2: #232a33; --border: #2d3540;
    --fg: #e6edf3; --muted: #8b98a8; --accent: #58a6ff; --padding-col: #313742;
    --row-h: 18px;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--fg);
    font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  header {
    padding: 14px 20px; border-bottom: 1px solid var(--border); background: var(--panel);
    display: flex; flex-wrap: wrap; gap: 8px 28px; align-items: baseline;
  }
  header h1 { font-size: 16px; margin: 0 24px 0 0; }
  header .stat { color: var(--muted); font-size: 13px; }
  header .stat b { color: var(--fg); font-weight: 600; }
  .layout { display: grid; grid-template-columns: 320px 1fr; gap: 16px; padding: 16px 20px; align-items: start; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; }
  .panel h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted);
              margin: 0; padding: 12px 14px; border-bottom: 1px solid var(--border); }
  /* Image map */
  .map-wrap { padding: 14px; }
  .map { display: flex; width: 100%; height: 64px; border-radius: 6px; overflow: hidden;
         border: 1px solid var(--border); background: var(--padding-col); cursor: pointer; }
  .viewport-track { position: relative; height: 12px; margin-bottom: 6px; border-radius: 6px;
         background: var(--panel-2); cursor: pointer; }
  .viewport { position: absolute; top: 0; height: 100%; min-width: 14px; border-radius: 6px;
         background: var(--accent); cursor: grab; touch-action: none; }
  .viewport:hover { filter: brightness(1.1); }
  .viewport:active { cursor: grabbing; }
  .seg { height: 100%; min-width: 2px; cursor: pointer; position: relative; transition: filter .08s, opacity .08s; }
  .seg.padding { cursor: default; background-image: repeating-linear-gradient(
        45deg, transparent, transparent 4px, rgba(255,255,255,.05) 4px, rgba(255,255,255,.05) 8px); }
  .map.has-hl .seg:not(.hl) { opacity: .25; }
  .seg.hl { box-shadow: inset 0 0 0 2px #fff; z-index: 2; }
  .seg.selected { box-shadow: inset 0 0 0 2px var(--accent), 0 0 0 1px var(--accent); z-index: 3; }
  /* Map labels: compact N.M / R / Z tokens placed below the bar without overlapping */
  .map-labels { position: relative; height: 15px; margin-top: 4px; }
  .map-label { position: absolute; top: 0; font: 11px/15px ui-monospace, monospace;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer;
          text-align: center; }
  .map-label:hover, .map-label.hl { text-decoration: underline; }
  .axis { display: flex; justify-content: space-between; color: var(--muted);
          font: 11px ui-monospace, monospace; padding: 6px 2px 0; }
  .legend { padding: 0 14px 14px; color: var(--muted); font-size: 12px; }
  .legend .chip { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin: 0 4px -1px 12px; }
  /* File list */
  .files { max-height: 70vh; overflow: auto; }
  .file { display: flex; gap: 10px; align-items: flex-start; padding: 10px 14px;
          border-bottom: 1px solid var(--border); cursor: pointer; }
  .file:last-child { border-bottom: 0; }
  .file.hl { background: var(--panel-2); }
  .file .swatch { width: 14px; height: 14px; border-radius: 3px; flex: 0 0 auto; margin-top: 2px; }
  .file .meta { min-width: 0; flex: 1; }
  .file .name { font-weight: 600; word-break: break-all; }
  .file .sub { color: var(--muted); font-size: 12px; font-family: ui-monospace, monospace; word-break: break-all; }
  /* Hex viewer */
  .hex-head { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center;
              padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--muted); font-size: 12px; }
  .hex-head .title { color: var(--fg); font-weight: 600; font-size: 13px; }
  .hex-head .spacer { flex: 1; }
  button { background: var(--panel-2); color: var(--fg); border: 1px solid var(--border);
           border-radius: 6px; padding: 5px 10px; cursor: pointer; font: inherit; font-size: 12px; }
  button:hover:not(:disabled) { border-color: var(--accent); }
  button:disabled { opacity: .4; cursor: default; }
  .hex { height: 60vh; padding: 12px 14px; overflow: auto; position: relative;
         font: 12.5px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; }
  .hex-inner { display: flex; align-items: flex-start; }
  .hex-row { height: var(--row-h); line-height: var(--row-h); white-space: pre; }
  .hex .off { color: var(--muted); padding-right: 14px; user-select: none; }
  .hex .b { padding: 0 3px; border-radius: 2px; }
  .hex .b.gap { padding-right: 11px; }
  .hex .b.region { color: #fff; }
  .hex .asc { color: var(--muted); padding-left: 14px; }
  .hex .asc .region { color: var(--fg); }
  /* File-indicator gutter: one band per segment, colored stripe + sticky fragment label */
  #hex-gutter { flex: 0 0 180px; margin-left: 16px; }
  .frag-band { position: relative; border-left: 4px solid transparent; }
  .frag-label { position: sticky; top: 0; display: block; max-width: 100%; padding: 0 6px;
         font-size: 11px; line-height: var(--row-h); white-space: nowrap; overflow: hidden;
         text-overflow: ellipsis; color: var(--fg); }
  .frag-band.padding { border-left-color: var(--padding-col); }
  .frag-band.padding .frag-label { color: var(--muted); }
  .frag-band.hl { background: var(--panel-2); }
  .placeholder { padding: 22px 14px; color: var(--muted); }
  .placeholder input { margin-top: 8px; color: var(--fg); }
  a { color: var(--accent); }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <span class="stat"><b id="s-files">0</b> files</span>
  <span class="stat"><b id="s-frags">0</b> fragments</span>
  <span class="stat">size <b id="s-size">0</b></span>
  <span class="stat">block size <b id="s-block">0</b></span>
  <span class="stat">seed <b id="s-seed">-</b></span>
  <span class="stat">corpus <b id="s-corpus">-</b></span>
</header>

<div class="layout">
  <section class="panel">
    <h2>Files</h2>
    <div class="files" id="files"></div>
  </section>

  <div>
    <section class="panel">
      <h2>Image map</h2>
      <div class="map-wrap">
        <div class="viewport-track" id="viewport-track"><div class="viewport" id="viewport"></div></div>
        <div class="map" id="map"></div>
        <div class="map-labels" id="map-labels"></div>
        <div class="axis"><span>0</span><span id="axis-end">0</span></div>
      </div>
      <div class="legend">
        labels below the map use the config <code>N.M</code> / <code>R</code> /
        <code>Z</code> layout notation (file.fragment, random/zeroes filler)
        &middot; hover a fragment, the hex bytes, or the right-hand gutter to highlight it on the map
        &middot; click to select, drag the scrollbar to scroll
      </div>
    </section>

    <section class="panel" style="margin-top:16px">
      <h2>Hex viewer</h2>
      <div class="hex-head">
        <span class="title" id="hex-title">Nothing selected</span>
        <span id="hex-sub"></span>
        <span class="spacer"></span>
        <span>visible <span id="hex-range"></span></span>
      </div>
      <div id="hex-body">
        <div class="hex" id="hex-scroll">
          <div class="hex-inner"><div id="hex-rows"></div><div id="hex-gutter"></div></div>
        </div>
        <div id="hex-placeholder" style="display:none"></div>
      </div>
    </section>
  </div>
</div>

<script type="application/json" id="view-model">__VIEW_MODEL_JSON__</script>
<script type="application/json" id="image-data">__IMAGE_BASE64__</script>
<script>
const VM = JSON.parse(document.getElementById('view-model').textContent);
const HAS_EMBEDDED = __HAS_EMBEDDED__;
const COLS = 16;             // bytes per hex row
const ROW_H = 18;            // px per hex row -- must match --row-h in the CSS
const OVERSCAN = 8;          // extra rows rendered above/below the viewport
const totalRows = Math.ceil(VM.image_size / COLS);

// ---- byte source -------------------------------------------------------------------------
let imageBlob = null;        // File/Blob selected by the user (large images)
let imageArray = null;       // Uint8Array of the whole image (embedded, small images)

function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
if (HAS_EMBEDDED) {
  imageArray = b64ToBytes(document.getElementById('image-data').textContent.trim());
}
function bytesAvailable() { return imageArray !== null || imageBlob !== null; }
async function readBytes(start, end) {
  start = Math.max(0, start); end = Math.min(VM.image_size, end);
  if (end <= start) return new Uint8Array(0);
  if (imageArray) return imageArray.subarray(start, end);
  const buf = await imageBlob.slice(start, end).arrayBuffer();
  return new Uint8Array(buf);
}

// ---- helpers -----------------------------------------------------------------------------
const color = (i) => `hsl(${(i * 137.508) % 360}deg 62% 56%)`;
const fmtSize = (n) => {
  if (n < 1024) return `${n} B`;
  const u = ['KiB', 'MiB', 'GiB']; let v = n; let k = -1;
  do { v /= 1024; k++; } while (v >= 1024 && k < u.length - 1);
  return `${v.toFixed(v < 10 ? 1 : 0)} ${u[k]}`;
};
const hex = (n, w) => n.toString(16).padStart(w, '0');
const segColor = (s) => s.kind === 'padding' || s.color_index === null ? null : color(s.color_index);
const fragKey = (f) => `${f.file_id}:${f.number}`;

// ---- header ------------------------------------------------------------------------------
document.getElementById('s-files').textContent = VM.num_files;
document.getElementById('s-frags').textContent = VM.num_fragments;
document.getElementById('s-size').textContent = `${fmtSize(VM.image_size)} (${VM.image_size} B)`;
document.getElementById('s-block').textContent = `${VM.block_size} B`;
document.getElementById('s-seed').textContent = VM.seed === null || VM.seed === undefined ? '–' : VM.seed;
document.getElementById('s-corpus').textContent = VM.corpus || '–';
document.getElementById('axis-end').textContent = `0x${hex(VM.image_size, 0)} (${VM.image_size} B)`;

// ---- image map ---------------------------------------------------------------------------
const mapEl = document.getElementById('map');
const mapLabelsEl = document.getElementById('map-labels');
const segByFile = {};   // file_id -> [seg elements]
const segByFrag = {};   // fragKey -> seg element
const bandByFrag = {};  // fragKey -> gutter band element
const labelByFrag = {}; // fragKey -> map label element
let selectedEl = null;

VM.segments.forEach((s) => {
  const el = document.createElement('div');
  el.className = 'seg' + (s.kind === 'padding' ? ' padding' : '');
  el.style.flexGrow = Math.max(s.image_end - s.image_start, 1);
  el.style.flexBasis = '0';
  const c = segColor(s);
  if (c) el.style.background = c;
  if (s.kind === 'fragment') {
    el.dataset.fileId = s.file_id;
    el.title = `${s.label}  ${s.path}  —  fragment ${s.number}/${s.num_fragments}\n`
      + `image 0x${hex(s.image_start, 0)}– 0x${hex(s.image_end, 0)} (${fmtSize(s.size)})`;
    el.addEventListener('mouseenter', () => highlight(s.file_id));
    el.addEventListener('mouseleave', clearHighlight);
    el.addEventListener('click', (ev) => { ev.stopPropagation(); selectFragment(s, el); });
    (segByFile[s.file_id] = segByFile[s.file_id] || []).push(el);
    segByFrag[fragKey(s)] = el;
  } else {
    const span = fmtSize(s.image_end - s.image_start);
    el.title = `padding  —  0x${hex(s.image_start, 0)}– 0x${hex(s.image_end, 0)} (${span})`;
  }
  mapEl.appendChild(el);
});

// click anywhere on the map (padding/background) to jump the hex viewer to that offset;
// fragment segments handle their own click and stop propagation so this does not double-fire.
mapEl.addEventListener('click', (ev) => {
  const rect = mapEl.getBoundingClientRect();
  if (!rect.width) return;
  const frac = Math.min(Math.max((ev.clientX - rect.left) / rect.width, 0), 1);
  scrollToOffset(Math.min(VM.image_size - 1, Math.floor(frac * VM.image_size)));
});

function highlight(fileId) {
  mapEl.classList.add('has-hl');
  (segByFile[fileId] || []).forEach((e) => e.classList.add('hl'));
  const f = fileRows[fileId]; if (f) f.classList.add('hl');
}
// Byte-precise highlight: light up a single fragment across the map, gutter, map label and file
// list. Used when hovering the hex bytes, the gutter, or a map label.
function highlightFragment(key) {
  const seg = segByFrag[key];
  if (!seg) return;
  mapEl.classList.add('has-hl');
  seg.classList.add('hl');
  if (bandByFrag[key]) bandByFrag[key].classList.add('hl');
  if (labelByFrag[key]) labelByFrag[key].classList.add('hl');
  const f = fileRows[seg.dataset.fileId]; if (f) f.classList.add('hl');
}
function clearHighlight() {
  mapEl.classList.remove('has-hl');
  document.querySelectorAll('.seg.hl').forEach((e) => e.classList.remove('hl'));
  document.querySelectorAll('.file.hl').forEach((e) => e.classList.remove('hl'));
  document.querySelectorAll('.frag-band.hl').forEach((e) => e.classList.remove('hl'));
  document.querySelectorAll('.map-label.hl').forEach((e) => e.classList.remove('hl'));
}

// Place compact N.M / R / Z labels below the map. Labels are positioned from each fragment's byte
// offsets, and laid out largest-fragment-first so the most prominent fragments win the space; a
// label is only drawn if it does not collide with one already placed, so dense clusters of tiny
// fragments stay readable (the rest remain reachable via hover and the hex gutter). Recomputed on
// resize because positions are in pixels.
function layoutMapLabels() {
  const mapWidth = mapEl.getBoundingClientRect().width;
  mapLabelsEl.innerHTML = '';
  Object.keys(labelByFrag).forEach((k) => delete labelByFrag[k]);
  if (!mapWidth || !VM.image_size) return;
  const CHAR = 6.6, PAD = 6, GAP = 4;
  const cands = VM.fragments.map((f) => ({
    f,
    cx: (f.image_start + f.size / 2) / VM.image_size * mapWidth,
    w: Math.min(f.label.length * CHAR + PAD, 120),
  })).sort((a, b) => b.f.size - a.f.size);
  const placed = [];   // occupied [left, right] intervals in the lane
  cands.forEach((c) => {
    const left = Math.min(Math.max(c.cx - c.w / 2, 0), Math.max(mapWidth - c.w, 0));
    const right = left + c.w;
    if (placed.some((p) => left < p.right + GAP && right > p.left - GAP)) return;
    placed.push({ left, right });
    const key = fragKey(c.f);
    const el = document.createElement('div');
    el.className = 'map-label';
    el.style.left = left + 'px';
    el.style.width = c.w + 'px';
    el.style.color = c.f.color_index === null ? 'var(--muted)' : color(c.f.color_index);
    el.textContent = c.f.label;
    el.title = `${c.f.label} · ${c.f.path}`;
    el.addEventListener('mouseenter', () => highlightFragment(key));
    el.addEventListener('mouseleave', clearHighlight);
    el.addEventListener('click', () => selectFragment(c.f, segByFrag[key]));
    mapLabelsEl.appendChild(el);
    labelByFrag[key] = el;
  });
}

// ---- file list ---------------------------------------------------------------------------
const filesEl = document.getElementById('files');
const fileRows = {};
const firstFragOf = {};
VM.fragments.forEach((f) => { if (!(f.file_id in firstFragOf)) firstFragOf[f.file_id] = f; });

VM.files.forEach((f) => {
  const row = document.createElement('div');
  row.className = 'file';
  const swatch = f.color_index === null
    ? '<span class="swatch" style="background:var(--padding-col)"></span>'
    : `<span class="swatch" style="background:${color(f.color_index)}"></span>`;
  const label = f.type === 'filler' ? `${f.path} filler` : f.path;
  row.innerHTML = `${swatch}<div class="meta">`
    + `<div class="name">${escapeHtml(label)}</div>`
    + `<div class="sub">${fmtSize(f.size)} · ${f.num_fragments} frag${f.num_fragments > 1 ? 's' : ''}`
    + ` · ${f.sha256.slice(0, 12)}…</div></div>`;
  row.addEventListener('mouseenter', () => highlight(f.id));
  row.addEventListener('mouseleave', clearHighlight);
  row.addEventListener('click', () => {
    const frag = firstFragOf[f.id];
    if (frag) selectFragment(frag, (segByFile[f.id] || [])[0]);
  });
  filesEl.appendChild(row);
  fileRows[f.id] = row;
});

function escapeHtml(s) {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

// ---- hex viewer (scrollable, virtualized over the whole image) ---------------------------
const hexScroll = document.getElementById('hex-scroll');
const hexRows = document.getElementById('hex-rows');
const hexGutter = document.getElementById('hex-gutter');
const hexPlaceholder = document.getElementById('hex-placeholder');
const viewportEl = document.getElementById('viewport');
const viewportTrack = document.getElementById('viewport-track');
const hexRangeEl = document.getElementById('hex-range');
let selectedRegion = null;   // { start, end } image range of the selected fragment (highlighted)
let renderToken = 0;         // guards against out-of-order async reads on large images

// Right-hand gutter: one band per segment, height proportional to its byte span, with a colored
// stripe matching the image map and a sticky fragment label that stays pinned while the fragment
// is on screen. Built once -- segments never change and it needs no image bytes.
function buildGutter() {
  VM.segments.forEach((s) => {
    const band = document.createElement('div');
    band.className = 'frag-band' + (s.kind === 'padding' ? ' padding' : '');
    band.style.height = ((s.image_end - s.image_start) / COLS * ROW_H) + 'px';
    const c = segColor(s);
    if (c) band.style.borderLeftColor = c;
    const label = document.createElement('div');
    label.className = 'frag-label';
    if (s.kind === 'fragment') {
      const text = `${s.label} · ${s.path}`;
      label.textContent = text;
      label.title = `${text} · fragment ${s.number}/${s.num_fragments}`;
      const key = fragKey(s);
      bandByFrag[key] = band;
      band.addEventListener('mouseenter', () => highlightFragment(key));
      band.addEventListener('mouseleave', clearHighlight);
    } else {
      label.textContent = 'padding';
    }
    band.appendChild(label);
    hexGutter.appendChild(band);
  });
}
buildGutter();

function updateViewport(startByte, endByte) {
  if (!VM.image_size) return;
  viewportEl.style.left = (startByte / VM.image_size * 100) + '%';
  viewportEl.style.width = (Math.max(endByte - startByte, 0) / VM.image_size * 100) + '%';
}

// The viewport thumb doubles as a horizontal scrollbar for the whole-image hex view: drag it
// (or click the track) to scroll. updateViewport() keeps it in sync as the content scrolls.
let dragging = false, grabDx = 0;
viewportEl.addEventListener('pointerdown', (ev) => {
  ev.preventDefault();
  ev.stopPropagation();
  dragging = true;
  grabDx = ev.clientX - viewportEl.getBoundingClientRect().left;
  viewportEl.setPointerCapture(ev.pointerId);
});
viewportEl.addEventListener('pointermove', (ev) => {
  if (!dragging) return;
  const track = viewportTrack.getBoundingClientRect();
  if (!track.width) return;
  const thumbW = viewportEl.getBoundingClientRect().width;
  const left = Math.min(Math.max(ev.clientX - track.left - grabDx, 0), Math.max(track.width - thumbW, 0));
  scrollToOffset((left / track.width) * VM.image_size);
});
function endDrag(ev) {
  if (!dragging) return;
  dragging = false;
  if (viewportEl.hasPointerCapture && viewportEl.hasPointerCapture(ev.pointerId)) {
    viewportEl.releasePointerCapture(ev.pointerId);
  }
}
viewportEl.addEventListener('pointerup', endDrag);
viewportEl.addEventListener('pointercancel', endDrag);
viewportEl.addEventListener('click', (ev) => ev.stopPropagation());   // avoid a track-click after release
viewportTrack.addEventListener('click', (ev) => {
  const track = viewportTrack.getBoundingClientRect();
  if (!track.width) return;
  const frac = Math.min(Math.max((ev.clientX - track.left) / track.width, 0), 1);
  scrollToOffset(frac * VM.image_size);
});

function scrollToOffset(off) {
  hexScroll.scrollTop = Math.floor(Math.max(0, off) / COLS) * ROW_H;
  renderVisible();
}

// Which fragment (if any) owns a given image offset. Binary search over VM.fragments, which
// build_view_model already sorts by image_start. Returns a fragKey or null (padding).
function fragKeyAt(off) {
  let lo = 0, hi = VM.fragments.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const f = VM.fragments[mid];
    if (off < f.image_start) hi = mid - 1;
    else if (off >= f.image_end) lo = mid + 1;
    else return fragKey(f);
  }
  return null;
}

async function renderVisible() {
  const scrollTop = hexScroll.scrollTop || 0;
  const clientHeight = hexScroll.clientHeight || 0;
  // range actually on screen (no overscan) -- drives the readout and the map viewport marker
  const visStart = Math.min(VM.image_size, Math.floor(scrollTop / ROW_H) * COLS);
  const visEnd = Math.min(VM.image_size, Math.ceil((scrollTop + clientHeight) / ROW_H) * COLS);
  updateViewport(visStart, visEnd);
  hexRangeEl.textContent = `0x${hex(visStart, 0)}– 0x${hex(visEnd, 0)}`;

  if (!bytesAvailable()) { renderPlaceholder(); return; }
  hexScroll.style.display = '';
  hexPlaceholder.style.display = 'none';

  const firstRow = Math.max(0, Math.floor(scrollTop / ROW_H) - OVERSCAN);
  const lastRow = Math.min(totalRows, firstRow + Math.ceil(clientHeight / ROW_H) + 2 * OVERSCAN);
  const startByte = firstRow * COLS;
  const endByte = Math.min(VM.image_size, lastRow * COLS);
  const token = ++renderToken;
  const bytes = await readBytes(startByte, endByte);
  if (token !== renderToken) return;   // a newer scroll superseded this read

  const regStart = selectedRegion ? selectedRegion.start : -1;
  const regEnd = selectedRegion ? selectedRegion.end : -1;
  let rows = '';
  for (let row = firstRow; row < lastRow; row++) {
    const rowByte = row * COLS;
    let hexCells = '', asc = '';
    for (let i = 0; i < COLS; i++) {
      const off = rowByte + i;
      if (off < VM.image_size) {
        const v = bytes[off - startByte];
        const inRegion = off >= regStart && off < regEnd;
        const cls = 'b' + (i === 7 ? ' gap' : '') + (inRegion ? ' region' : '');
        hexCells += `<span class="${cls}">${hex(v, 2)}</span>`;
        const ch = v >= 32 && v < 127 ? escapeHtml(String.fromCharCode(v)) : '.';
        asc += inRegion ? `<span class="region">${ch}</span>` : ch;
      } else {
        hexCells += `<span class="b${i === 7 ? ' gap' : ''}">  </span>`;
        asc += ' ';
      }
    }
    const fk = fragKeyAt(rowByte);
    const fragAttr = fk ? ` data-frag="${fk}"` : '';
    rows += `<div class="hex-row"${fragAttr}><span class="off">${hex(rowByte, 8)}</span>`
      + `${hexCells}<span class="asc">${asc}</span></div>`;
  }
  hexRows.style.paddingTop = (firstRow * ROW_H) + 'px';
  hexRows.style.paddingBottom = ((totalRows - lastRow) * ROW_H) + 'px';
  hexRows.innerHTML = rows;
}

let scrollPending = false;
hexScroll.addEventListener('scroll', () => {
  if (scrollPending) return;
  scrollPending = true;
  requestAnimationFrame(() => { scrollPending = false; renderVisible(); });
});

// Hovering the hex bytes highlights the owning fragment on the map/gutter (delegated, since rows
// are re-rendered on every scroll).
let hoveredFrag = null;
hexRows.addEventListener('mouseover', (ev) => {
  const row = ev.target.closest && ev.target.closest('.hex-row');
  const key = row ? row.dataset.frag : null;
  if (key === hoveredFrag) return;
  clearHighlight();
  hoveredFrag = key || null;
  if (key) highlightFragment(key);
});
hexRows.addEventListener('mouseleave', () => { hoveredFrag = null; clearHighlight(); });

function selectFragment(frag, el) {
  selectedRegion = { start: frag.image_start, end: frag.image_end };
  if (selectedEl) selectedEl.classList.remove('selected');
  selectedEl = el || null;
  if (selectedEl) selectedEl.classList.add('selected');
  document.getElementById('hex-title').textContent =
    `${frag.path}  —  fragment ${frag.number}/${frag.num_fragments}`;
  const range = `0x${hex(frag.image_start, 0)}– 0x${hex(frag.image_end, 0)}`;
  document.getElementById('hex-sub').textContent =
    `image ${range} · ${fmtSize(frag.size)} · sha256 ${frag.sha256.slice(0, 16)}…`;
  scrollToOffset(frag.image_start);
}

function renderPlaceholder() {
  hexScroll.style.display = 'none';
  hexPlaceholder.style.display = '';
  hexPlaceholder.innerHTML =
    '<div class="placeholder">The image bytes are not embedded in this file. '
    + 'Select the generated image to inspect its bytes:<br>'
    + '<input type="file" id="file-input"></div>';
  document.getElementById('file-input').addEventListener('change', (ev) => {
    imageBlob = ev.target.files[0] || null;
    if (imageBlob) scrollToOffset(selectedRegion ? selectedRegion.start : 0);
  });
}

// map labels depend on the rendered map width, so lay them out now and on every resize
layoutMapLabels();
let resizePending = false;
window.addEventListener('resize', () => {
  if (resizePending) return;
  resizePending = true;
  requestAnimationFrame(() => { resizePending = false; layoutMapLabels(); });
});

// select the first fragment by default (scrolls to offset 0)
if (VM.fragments.length) {
  const f0 = VM.fragments[0];
  selectFragment(f0, (segByFile[f0.file_id] || [])[0]);
} else {
  renderVisible();
}
</script>
</body>
</html>
"""
