#!/usr/bin/env python3
"""Generate an interactive collapsible tree visualisation of a codebase.

Creates a self-contained codebase-map.html and opens it in the default browser.
Uses only the Python standard library — no packages to install.

Usage:
    python visualize.py [directory]   (defaults to current directory)
"""
from __future__ import annotations

import json
import sys
import webbrowser
from collections import Counter
from pathlib import Path

IGNORE = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

COLORS: dict[str, str] = {
    ".py": "#3776ab", ".js": "#f7df1e", ".ts": "#3178c6", ".tsx": "#3178c6",
    ".jsx": "#61dafb", ".go": "#00add8", ".rs": "#dea584", ".rb": "#cc342d",
    ".css": "#264de4", ".html": "#e34c26", ".json": "#6b7280", ".md": "#083fa1",
    ".yaml": "#cb171e", ".yml": "#cb171e", ".sh": "#4eaa25", ".toml": "#9c4221",
}


def scan(path: Path, stats: dict) -> dict:
    node: dict = {"name": path.name, "children": [], "size": 0}
    try:
        for item in sorted(path.iterdir()):
            if item.name in IGNORE or item.name.startswith("."):
                continue
            if item.is_file():
                size = item.stat().st_size
                ext = item.suffix.lower() or "(no ext)"
                node["children"].append({"name": item.name, "size": size, "ext": ext})
                node["size"] += size
                stats["files"] += 1
                stats["extensions"][ext] += 1
                stats["ext_sizes"][ext] += size
            elif item.is_dir():
                stats["dirs"] += 1
                child = scan(item, stats)
                if child["children"]:
                    node["children"].append(child)
                    node["size"] += child["size"]
    except PermissionError:
        pass
    return node


def fmt_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    if b < 1_048_576:
        return f"{b / 1024:.1f} KB"
    return f"{b / 1_048_576:.1f} MB"


def generate_html(data: dict, stats: dict, output: Path) -> None:
    total_size = sum(stats["ext_sizes"].values()) or 1
    sorted_exts = sorted(stats["ext_sizes"].items(), key=lambda x: -x[1])[:8]

    lang_bars = "".join(
        f'<div class="bar-row">'
        f'<span class="bar-label">{ext}</span>'
        f'<div class="bar" style="width:{(size/total_size)*100:.1f}%;background:{COLORS.get(ext,"#6b7280")}"></div>'
        f'<span class="bar-pct">{(size/total_size)*100:.1f}%</span>'
        f"</div>"
        for ext, size in sorted_exts
    )

    html = f"""<!DOCTYPE html>
<html><head>
  <meta charset="utf-8"><title>Codebase Explorer — {data['name']}</title>
  <style>
    body{{font:14px/1.5 system-ui,sans-serif;margin:0;background:#1a1a2e;color:#eee}}
    .container{{display:flex;height:100vh}}
    .sidebar{{width:280px;background:#252542;padding:20px;border-right:1px solid #3d3d5c;overflow-y:auto;flex-shrink:0}}
    .main{{flex:1;padding:20px;overflow-y:auto}}
    h1{{margin:0 0 10px;font-size:18px}}
    h2{{margin:20px 0 10px;font-size:13px;color:#888;text-transform:uppercase;letter-spacing:.05em}}
    .stat{{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #3d3d5c}}
    .stat-value{{font-weight:bold}}
    .bar-row{{display:flex;align-items:center;margin:5px 0}}
    .bar-label{{width:55px;font-size:12px;color:#aaa}}
    .bar{{height:16px;border-radius:3px;min-width:2px}}
    .bar-pct{{margin-left:7px;font-size:12px;color:#666}}
    .tree{{list-style:none;padding-left:18px;margin:0}}
    details>summary{{padding:3px 7px;border-radius:4px;list-style:none;cursor:pointer}}
    details>summary:hover{{background:#2d2d44}}
    .file{{display:flex;align-items:center;padding:3px 7px;border-radius:4px}}
    .file:hover{{background:#2d2d44}}
    .sz{{color:#666;margin-left:auto;font-size:12px;padding-left:12px}}
    .dot{{width:8px;height:8px;border-radius:50%;margin-right:7px;flex-shrink:0}}
  </style>
</head><body>
  <div class="container">
    <div class="sidebar">
      <h1>Summary</h1>
      <div class="stat"><span>Files</span><span class="stat-value">{stats['files']:,}</span></div>
      <div class="stat"><span>Directories</span><span class="stat-value">{stats['dirs']:,}</span></div>
      <div class="stat"><span>Total size</span><span class="stat-value">{fmt_bytes(data['size'])}</span></div>
      <div class="stat"><span>File types</span><span class="stat-value">{len(stats['extensions'])}</span></div>
      <h2>By file type</h2>
      {lang_bars}
    </div>
    <div class="main">
      <h1>📁 {data['name']}</h1>
      <ul class="tree" id="root"></ul>
    </div>
  </div>
  <script>
    const data={json.dumps(data)};
    const colors={json.dumps(COLORS)};
    function fmt(b){{if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';return(b/1048576).toFixed(1)+' MB'}}
    function render(node,parent){{
      if(node.children){{
        const det=document.createElement('details');
        det.open=parent===document.getElementById('root');
        det.innerHTML=`<summary>📁 ${{node.name}}<span class="sz">${{fmt(node.size)}}</span></summary>`;
        const ul=document.createElement('ul');ul.className='tree';
        node.children.sort((a,b)=>(b.children?1:0)-(a.children?1:0)||a.name.localeCompare(b.name));
        node.children.forEach(c=>render(c,ul));
        det.appendChild(ul);
        const li=document.createElement('li');li.appendChild(det);parent.appendChild(li);
      }}else{{
        const li=document.createElement('li');li.className='file';
        li.innerHTML=`<span class="dot" style="background:${{colors[node.ext]||'#6b7280'}}"></span>${{node.name}}<span class="sz">${{fmt(node.size)}}</span>`;
        parent.appendChild(li);
      }}
    }}
    data.children.forEach(c=>render(c,document.getElementById('root')));
  </script>
</body></html>"""

    output.write_text(html)


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    stats: dict = {"files": 0, "dirs": 0, "extensions": Counter(), "ext_sizes": Counter()}
    data = scan(target, stats)
    out = Path("codebase-map.html")
    generate_html(data, stats, out)
    print(f"Generated {out.absolute()}")
    webbrowser.open(f"file://{out.absolute()}")


if __name__ == "__main__":
    main()
