"""Report and provisioning script generators for software inventory audits."""

import datetime
import html
import os
import platform
from typing import Any, List


class ReportGenerator:
    """Generates self-contained interactive HTML audit reports and migration scripts."""

    @classmethod
    def generate_html_report(cls, programs: List[Any], app_version: str = "2.3.0") -> str:
        """Builds a luxury dark Obsidian HTML report with dynamic search, metrics, and print styles."""
        total_count = len(programs)
        updates_count = sum(1 for p in programs if getattr(p.action, "value", str(p.action)) in ("update", "UPGRADE_AVAILABLE"))
        uptodate_count = sum(1 for p in programs if getattr(p.action, "value", str(p.action)) in ("ok", "UP_TO_DATE"))
        ignored_count = total_count - (updates_count + uptodate_count)

        now_str = datetime.datetime.now().strftime("%B %d, %Y - %I:%M %p")
        os_name = f"Windows {platform.release()} (Build {platform.version()})"
        arch_name = platform.machine()
        computer_name = os.environ.get("COMPUTERNAME", "PC")

        rows_html = []
        for p in programs:
            raw_action = getattr(p.action, "value", str(p.action))
            if raw_action in ("update", "UPGRADE_AVAILABLE"):
                badge_cls = "badge-update"
                badge_text = "Update Available"
            elif raw_action in ("ok", "UP_TO_DATE"):
                badge_cls = "badge-ok"
                badge_text = "Up to Date"
            elif raw_action in ("pinned", "PINNED"):
                badge_cls = "badge-pinned"
                badge_text = "Pinned"
            elif raw_action in ("excluded", "EXCLUDED"):
                badge_cls = "badge-excluded"
                badge_text = "Excluded"
            else:
                badge_cls = "badge-neutral"
                badge_text = raw_action.title()

            p_id = p.id or ""
            p_name = html.escape(p.name or "Unknown")
            p_inst = html.escape(str(p.installed_version or "—"))
            p_latest = html.escape(str(p.latest_version or "—"))
            p_source = html.escape(str(p.source or "System Registry"))
            p_loc = html.escape(str(p.install_location or "Standard System Path"))

            copy_btn = (
                f'<button class="copy-btn" onclick="copyCmd(\'{html.escape(p_id)}\')" title="Copy winget install command">📋</button>'
                if p_id
                else ""
            )

            row = f"""
            <tr data-status="{badge_cls}" data-search="{p_name.lower()} {p_id.lower()} {p_source.lower()}">
                <td class="col-name"><strong>{p_name}</strong></td>
                <td class="col-id"><code>{p_id or "—"}</code> {copy_btn}</td>
                <td class="col-ver">{p_inst}</td>
                <td class="col-ver col-latest">{p_latest}</td>
                <td><span class="badge {badge_cls}">{badge_text}</span></td>
                <td class="col-source"><span class="source-tag">{p_source}</span></td>
                <td class="col-loc" title="{p_loc}">{p_loc}</td>
            </tr>
            """
            rows_html.append(row)

        table_body = "\n".join(rows_html)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Software Inventory Audit Report — {html.escape(computer_name)}</title>
<style>
  :root {{
    --bg-page: #0c0d18;
    --bg-card: #151326;
    --bg-card-hover: #1c1933;
    --border: #292444;
    --fg-primary: #f8fafc;
    --fg-secondary: #94a3b8;
    --fg-muted: #64748b;
    --accent: #881337;
    --accent-glow: #e11d48;
    --badge-up-bg: #3b1120;
    --badge-up-fg: #f43f5e;
    --badge-ok-bg: #064e3b;
    --badge-ok-fg: #34d399;
    --badge-pin-bg: #3b2808;
    --badge-pin-fg: #fbbf24;
    --font-stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: "Cascadia Code", Consolas, "Courier New", monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background-color: var(--bg-page);
    color: var(--fg-primary);
    font-family: var(--font-stack);
    line-height: 1.5;
    padding: 32px 24px;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{
    max-width: 1400px;
    margin: 0 auto;
  }}
  /* Header */
  .header {{
    background: linear-gradient(135deg, #18152e 0%, #110e20 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .header-left h1 {{
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .header-left p {{
    color: var(--fg-secondary);
    font-size: 13px;
    margin-top: 4px;
  }}
  .header-badges {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .meta-tag {{
    background: #201c38;
    border: 1px solid #363056;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    color: var(--fg-secondary);
  }}
  .meta-tag strong {{ color: #fff; }}
  /* Metrics Grid */
  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .metric-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
  }}
  .metric-num {{
    font-size: 32px;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 4px;
  }}
  .metric-label {{
    font-size: 12px;
    color: var(--fg-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .m-total .metric-num {{ color: #38bdf8; }}
  .m-update .metric-num {{ color: #f43f5e; }}
  .m-ok .metric-num {{ color: #34d399; }}
  .m-other .metric-num {{ color: #a78bfa; }}
  /* Controls Bar */
  .controls-bar {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .search-box {{
    flex: 1;
    min-width: 260px;
  }}
  .search-box input {{
    width: 100%;
    background: #0e0d1a;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: #fff;
    padding: 9px 14px;
    font-size: 13px;
    outline: none;
    transition: border-color 0.15s;
  }}
  .search-box input:focus {{
    border-color: var(--accent-glow);
  }}
  .filter-pills {{
    display: flex;
    gap: 8px;
  }}
  .pill-btn {{
    background: #201c38;
    border: 1px solid #363056;
    color: var(--fg-secondary);
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.15s;
  }}
  .pill-btn:hover, .pill-btn.active {{
    background: var(--accent);
    color: #fff;
    border-color: var(--accent-glow);
  }}
  /* Data Table */
  .table-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 13px;
  }}
  thead th {{
    background: #19162e;
    color: var(--fg-secondary);
    padding: 12px 16px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--border);
  }}
  tbody tr {{
    border-bottom: 1px solid #1c1833;
    transition: background 0.1s;
  }}
  tbody tr:hover {{
    background: var(--bg-card-hover);
  }}
  tbody td {{
    padding: 12px 16px;
    color: #cbd5e1;
    vertical-align: middle;
  }}
  .col-name strong {{
    color: #fff;
    font-size: 13.5px;
  }}
  .col-id code {{
    font-family: var(--font-mono);
    color: #93c5fd;
    font-size: 12px;
    background: #171f38;
    padding: 2px 6px;
    border-radius: 4px;
  }}
  .copy-btn {{
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 12px;
    margin-left: 4px;
    opacity: 0.6;
    transition: opacity 0.15s;
  }}
  .copy-btn:hover {{ opacity: 1; }}
  .col-ver {{
    font-family: var(--font-mono);
    font-size: 12.5px;
  }}
  .col-latest {{
    color: #38bdf8;
    font-weight: 600;
  }}
  .badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
  }}
  .badge-update {{ background: var(--badge-up-bg); color: var(--badge-up-fg); border: 1px solid #7c1e38; }}
  .badge-ok {{ background: var(--badge-ok-bg); color: var(--badge-ok-fg); border: 1px solid #065f46; }}
  .badge-pinned {{ background: var(--badge-pin-bg); color: var(--badge-pin-fg); border: 1px solid #78350f; }}
  .badge-neutral {{ background: #262145; color: #a5b4fc; border: 1px solid #3c3468; }}
  .source-tag {{
    background: #1b1830;
    border: 1px solid #2e2850;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    color: var(--fg-secondary);
  }}
  .col-loc {{
    color: var(--fg-muted);
    font-size: 11.5px;
    max-width: 260px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  /* Footer */
  .footer {{
    margin-top: 24px;
    text-align: center;
    color: var(--fg-muted);
    font-size: 12px;
  }}
  @media print {{
    body {{ background: #fff !important; color: #000 !important; padding: 0; }}
    .controls-bar, .copy-btn {{ display: none !important; }}
    .header, .metric-card, .table-card {{ border: 1px solid #ccc; box-shadow: none; background: #fff !important; }}
    table th, table td {{ color: #000 !important; border-bottom: 1px solid #ddd; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <h1>🛡️ Software Inventory &amp; System Audit</h1>
      <p>Generated by Winget Updater v{app_version} on {now_str}</p>
    </div>
    <div class="header-badges">
      <div class="meta-tag">Device: <strong>{html.escape(computer_name)}</strong></div>
      <div class="meta-tag">OS: <strong>{html.escape(os_name)}</strong></div>
      <div class="meta-tag">Arch: <strong>{html.escape(arch_name)}</strong></div>
    </div>
  </div>

  <div class="metrics-grid">
    <div class="metric-card m-total">
      <span class="metric-num">{total_count}</span>
      <span class="metric-label">Total Installed Applications</span>
    </div>
    <div class="metric-card m-update">
      <span class="metric-num">{updates_count}</span>
      <span class="metric-label">Updates Available</span>
    </div>
    <div class="metric-card m-ok">
      <span class="metric-num">{uptodate_count}</span>
      <span class="metric-label">Up to Date</span>
    </div>
    <div class="metric-card m-other">
      <span class="metric-num">{ignored_count}</span>
      <span class="metric-label">Excluded / Pinned / System</span>
    </div>
  </div>

  <div class="controls-bar">
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Search application name, ID, or source..." oninput="filterTable()">
    </div>
    <div class="filter-pills">
      <button class="pill-btn active" onclick="setFilter('all', this)">All ({total_count})</button>
      <button class="pill-btn" onclick="setFilter('badge-update', this)">Updates ({updates_count})</button>
      <button class="pill-btn" onclick="setFilter('badge-ok', this)">Up to Date ({uptodate_count})</button>
    </div>
  </div>

  <div class="table-card">
    <table id="softwareTable">
      <thead>
        <tr>
          <th>Application Name</th>
          <th>Package ID</th>
          <th>Installed</th>
          <th>Latest</th>
          <th>Status</th>
          <th>Source</th>
          <th>Install Path</th>
        </tr>
      </thead>
      <tbody>
        {table_body}
      </tbody>
    </table>
  </div>

  <div class="footer">
    Software &amp; Package Updater for Windows 11 — High-precision package orchestration engine.
  </div>
</div>

<script>
  let currentFilter = 'all';

  function setFilter(filterType, btn) {{
    currentFilter = filterType;
    document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterTable();
  }}

  function filterTable() {{
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    const rows = document.querySelectorAll('#softwareTable tbody tr');
    let visible = 0;

    rows.forEach(r => {{
      const statusMatch = (currentFilter === 'all') || (r.getAttribute('data-status') === currentFilter);
      const textMatch = !query || r.getAttribute('data-search').includes(query);
      if (statusMatch && textMatch) {{
        r.style.display = '';
        visible++;
      }} else {{
        r.style.display = 'none';
      }}
    }});
  }}

  function copyCmd(pkgId) {{
    const cmd = `winget install --id "${{pkgId}}" -e --silent --accept-source-agreements --accept-package-agreements`;
    navigator.clipboard.writeText(cmd).then(() => {{
      alert(`Copied install command for ${{pkgId}}`);
    }}).catch(() => {{
      prompt("Copy command:", cmd);
    }});
  }}
</script>
</body>
</html>
"""
        return html_template

    @classmethod
    def generate_batch_script(cls, programs: List[Any]) -> str:
        """Generates an automated setup_pc.bat file installing all known Winget packages."""
        lines = [
            "@echo off",
            ":: ===========================================================================",
            ":: Winget Updater — Automated PC Setup & Package Migration Script",
            ":: Generated automatically from your installed software inventory",
            ":: ===========================================================================",
            "setlocal enabledelayedexpansion",
            "title Provisioning PC Software via Windows Package Manager",
            "",
            "echo [i] Checking Windows Package Manager (winget)...",
            "where winget >nul 2>&1",
            "if %ERRORLEVEL% neq 0 (",
            "    echo [!] ERROR: winget is not installed or not in PATH.",
            "    echo [!] Install 'App Installer' from the Microsoft Store first.",
            "    pause",
            "    exit /b 1",
            ")",
            "",
            "echo [i] Starting automated software installation...",
            "echo.",
        ]

        installed_ids = []
        for p in programs:
            if p.id and p.id.strip():
                clean_id = p.id.strip()
                if clean_id not in installed_ids:
                    installed_ids.append(clean_id)
                    p_name = p.name or clean_id
                    lines.append(f'echo [+] Installing {p_name} ({clean_id})...')
                    lines.append(f'winget install --id "{clean_id}" -e --silent --accept-source-agreements --accept-package-agreements')
                    lines.append("echo.")

        lines.extend([
            "echo ===========================================================================",
            f"echo [OK] Migration script complete! Attempted installation of {len(installed_ids)} packages.",
            "echo ===========================================================================",
            "pause",
            "exit /b 0",
        ])
        return "\r\n".join(lines)

    @classmethod
    def generate_ps1_script(cls, programs: List[Any]) -> str:
        """Generates an automated setup_pc.ps1 PowerShell migration script."""
        installed_ids = [p.id.strip() for p in programs if p.id and p.id.strip()]
        unique_ids = list(dict.fromkeys(installed_ids))

        lines = [
            "# ===========================================================================",
            "# Winget Updater — Automated PC Setup & Package Migration Script (PowerShell)",
            "# ===========================================================================",
            "$ErrorActionPreference = 'Continue'",
            "Write-Host '==> Verifying Windows Package Manager...' -ForegroundColor Cyan",
            "if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {",
            "    Write-Host 'ERROR: winget executable not found in PATH.' -ForegroundColor Red",
            "    Exit 1",
            "}",
            "",
            f"$packages = @(",
        ]
        for pid in unique_ids:
            lines.append(f"    '{pid}',")
        lines.extend([
            ")",
            "",
            "$total = $packages.Count",
            "$current = 0",
            "Write-Host \"==> Provisioning $total applications via Winget...\" -ForegroundColor Green",
            "",
            "foreach ($pkg in $packages) {",
            "    $current++",
            "    Write-Progress -Activity 'Installing Software Packages' -Status \"$current / $total : $pkg\" -PercentComplete (($current / $total) * 100)",
            "    Write-Host \"[$current/$total] Installing $pkg...\" -ForegroundColor Yellow",
            "    & winget install --id $pkg -e --silent --accept-source-agreements --accept-package-agreements",
            "}",
            "",
            "Write-Host '==> Software setup finished successfully!' -ForegroundColor Green",
            "Read-Host 'Press Enter to exit'",
        ])
        return "\r\n".join(lines)

