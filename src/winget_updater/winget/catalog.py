"""Curated software catalog and discovery engine for Windows Package Manager.
Provides an instant, rich catalog of top Windows applications across all categories,
with live search resolution and installation status mapping.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from winget_updater.models import PackageType, ProgramItem, UpdateAction


@dataclass
class CatalogEntry:
    id: str
    name: str
    publisher: str
    category: str
    version: str = "Latest"
    source: str = "winget"
    notes: str = ""
    package_type: PackageType = PackageType.WIN32_EXE


CURATED_CATALOG: List[CatalogEntry] = [
    # --- Development & Programming ---
    CatalogEntry(
        id="Microsoft.VisualStudioCode",
        name="Visual Studio Code",
        publisher="Microsoft Corporation",
        category="Development",
        version="1.97.0",
        notes="Code editing redefined. Free, built on open source, runs everywhere.",
    ),
    CatalogEntry(
        id="Git.Git",
        name="Git",
        publisher="The Git Development Community",
        category="Development",
        version="2.48.1",
        notes="Fast, scalable, distributed revision control system.",
    ),
    CatalogEntry(
        id="Microsoft.WindowsTerminal",
        name="Windows Terminal",
        publisher="Microsoft Corporation",
        category="Development",
        version="1.21.3231.0",
        notes="Modern, fast, efficient, and powerful terminal application.",
    ),
    CatalogEntry(
        id="Microsoft.PowerToys",
        name="Microsoft PowerToys",
        publisher="Microsoft Corporation",
        category="Utilities",
        version="0.88.0",
        notes="Set of utilities for power users to tune and streamline Windows.",
    ),
    CatalogEntry(
        id="Python.Python.3.12",
        name="Python 3.12",
        publisher="Python Software Foundation",
        category="Development",
        version="3.12.9",
        notes="Popular high-level interpreted programming language.",
    ),
    CatalogEntry(
        id="OpenJS.NodeJS",
        name="Node.js (LTS)",
        publisher="OpenJS Foundation",
        category="Development",
        version="22.14.0",
        notes="Asynchronous event-driven JavaScript runtime built on V8.",
    ),
    CatalogEntry(
        id="Docker.DockerDesktop",
        name="Docker Desktop",
        publisher="Docker Inc.",
        category="Development",
        version="4.38.0",
        notes="Containerization platform for building, sharing, and running applications.",
    ),
    CatalogEntry(
        id="Postman.Postman",
        name="Postman",
        publisher="Postman Inc.",
        category="Development",
        version="11.32.1",
        notes="Comprehensive API platform for building, testing, and debugging APIs.",
    ),
    CatalogEntry(
        id="Notepad++.Notepad++",
        name="Notepad++",
        publisher="Don HO",
        category="Development",
        version="8.7.7",
        notes="Free source code editor and powerful Notepad replacement.",
    ),
    CatalogEntry(
        id="SublimeHQ.SublimeText.4",
        name="Sublime Text 4",
        publisher="Sublime HQ Pty Ltd",
        category="Development",
        version="4.4192",
        notes="Sophisticated text editor for code, markup and prose.",
    ),
    CatalogEntry(
        id="JetBrains.PyCharm.Community",
        name="PyCharm Community",
        publisher="JetBrains s.r.o.",
        category="Development",
        version="2024.3.3",
        notes="The Python IDE for professional developers, free community edition.",
    ),
    CatalogEntry(
        id="JetBrains.IntelliJIDEA.Community",
        name="IntelliJ IDEA Community",
        publisher="JetBrains s.r.o.",
        category="Development",
        version="2024.3.3",
        notes="Capable and ergonomic Java IDE for JVM development.",
    ),
    CatalogEntry(
        id="GitHub.GitHubDesktop",
        name="GitHub Desktop",
        publisher="GitHub, Inc.",
        category="Development",
        version="3.4.14",
        notes="Focus on what matters instead of fighting with Git commands.",
    ),
    CatalogEntry(
        id="dbeaver.dbeaver",
        name="DBeaver Community",
        publisher="DBeaver Corp",
        category="Development",
        version="24.3.4",
        notes="Free multi-platform database tool for developers, SQL programmers, DBAs.",
    ),

    # --- Web Browsers ---
    CatalogEntry(
        id="Google.Chrome",
        name="Google Chrome",
        publisher="Google LLC",
        category="Browsers",
        version="133.0.6943.142",
        notes="Fast, secure, and customizable web browser built by Google.",
    ),
    CatalogEntry(
        id="Mozilla.Firefox",
        name="Mozilla Firefox",
        publisher="Mozilla",
        category="Browsers",
        version="135.0.1",
        notes="Free, open-source, privacy-respecting browser from Mozilla.",
    ),
    CatalogEntry(
        id="Brave.Brave",
        name="Brave Browser",
        publisher="Brave Software",
        category="Browsers",
        version="1.75.178",
        notes="Privacy-first browser with built-in ad and tracker blocking.",
    ),
    CatalogEntry(
        id="Opera.OperaGX",
        name="Opera GX",
        publisher="Opera Norway",
        category="Browsers",
        version="116.0.5366.126",
        notes="Gaming browser with CPU, RAM, and network bandwidth limiters.",
    ),
    CatalogEntry(
        id="TorProject.TorBrowser",
        name="Tor Browser",
        publisher="The Tor Project",
        category="Browsers",
        version="14.0.6",
        notes="Defend yourself against tracking and surveillance with onion routing.",
    ),

    # --- System & Utilities ---
    CatalogEntry(
        id="7zip.7zip",
        name="7-Zip",
        publisher="Igor Pavlov",
        category="Utilities",
        version="24.09",
        notes="High compression ratio file archiver with open architecture.",
    ),
    CatalogEntry(
        id="RARLab.WinRAR",
        name="WinRAR",
        publisher="win.rar GmbH",
        category="Utilities",
        version="7.10.0",
        notes="Powerful archive manager that can backup data and reduce file sizes.",
    ),
    CatalogEntry(
        id="voidtools.Everything",
        name="Everything",
        publisher="voidtools",
        category="Utilities",
        version="1.4.1.1026",
        notes="Locate files and folders by name instantly on Windows.",
    ),
    CatalogEntry(
        id="Rufus.Rufus",
        name="Rufus",
        publisher="Pete Batard",
        category="Utilities",
        version="4.6",
        notes="Format and create bootable USB flash drives easily.",
    ),
    CatalogEntry(
        id="BleachBit.BleachBit",
        name="BleachBit",
        publisher="Andrew Ziem",
        category="Utilities",
        version="4.6.0",
        notes="Clean your system, free disk space, and maintain privacy.",
    ),
    CatalogEntry(
        id="CPUID.CPU-Z",
        name="CPU-Z",
        publisher="CPUID",
        category="Utilities",
        version="2.13.0",
        notes="Gathers information on the main devices of your system.",
    ),
    CatalogEntry(
        id="CPUID.HWMonitor",
        name="HWMonitor",
        publisher="CPUID",
        category="Utilities",
        version="1.56.0",
        notes="Hardware monitoring program that reads voltages, temperatures and fans.",
    ),
    CatalogEntry(
        id="CrystalDewWorld.CrystalDiskInfo",
        name="CrystalDiskInfo",
        publisher="Crystal Dew World",
        category="Utilities",
        version="9.5.0",
        notes="HDD/SSD health monitoring utility supporting S.M.A.R.T.",
    ),
    CatalogEntry(
        id="JAMSoftware.TreeSize.Free",
        name="TreeSize Free",
        publisher="JAM Software GmbH",
        category="Utilities",
        version="4.7.3",
        notes="Quickly scan hard drives to visualize space usage and find hogs.",
    ),
    CatalogEntry(
        id="ShareX.ShareX",
        name="ShareX",
        publisher="ShareX Team",
        category="Utilities",
        version="16.1.0",
        notes="Screen capture, file sharing and productivity tool.",
    ),
    CatalogEntry(
        id="AutoHotkey.AutoHotkey",
        name="AutoHotkey",
        publisher="Lexikos",
        category="Utilities",
        version="2.0.19",
        notes="Powerful automation scripting language and hotkey engine for Windows.",
    ),
    CatalogEntry(
        id="TeamViewer.TeamViewer",
        name="TeamViewer",
        publisher="TeamViewer Germany GmbH",
        category="Utilities",
        version="15.62.4",
        notes="Fast and secure all-in-one solution for remote access and support.",
    ),
    CatalogEntry(
        id="AnyDeskSoftwareGmbH.AnyDesk",
        name="AnyDesk",
        publisher="AnyDesk Software GmbH",
        category="Utilities",
        version="9.0.2",
        notes="Fast remote desktop software for remote work and technical support.",
    ),

    # --- Media, Audio & Video ---
    CatalogEntry(
        id="VideoLAN.VLC",
        name="VLC Media Player",
        publisher="VideoLAN",
        category="Media",
        version="3.0.21",
        notes="Free and open source cross-platform multimedia player for all formats.",
    ),
    CatalogEntry(
        id="Spotify.Spotify",
        name="Spotify",
        publisher="Spotify AB",
        category="Media",
        version="1.2.56.502",
        notes="Millions of songs and podcasts at your fingertips.",
    ),
    CatalogEntry(
        id="OBSProject.OBSStudio",
        name="OBS Studio",
        publisher="OBS Project",
        category="Media",
        version="31.0.2",
        notes="Free and open source software for video recording and live streaming.",
    ),
    CatalogEntry(
        id="BlenderFoundation.Blender",
        name="Blender",
        publisher="Blender Foundation",
        category="Media",
        version="4.3.2",
        notes="Open source 3D creation suite: modeling, rigging, animation, rendering.",
    ),
    CatalogEntry(
        id="GIMP.GIMP",
        name="GIMP",
        publisher="The GIMP Team",
        category="Media",
        version="2.10.38",
        notes="GNU Image Manipulation Program for high-quality image manipulation.",
    ),
    CatalogEntry(
        id="Audacity.Audacity",
        name="Audacity",
        publisher="Audacity Team",
        category="Media",
        version="3.7.1",
        notes="Easy-to-use, multi-track audio editor and recorder for Windows.",
    ),
    CatalogEntry(
        id="HandBrake.HandBrake",
        name="HandBrake",
        publisher="The HandBrake Team",
        category="Media",
        version="1.9.1",
        notes="Open source video transcoder to convert video from nearly any format.",
    ),
    CatalogEntry(
        id="CodecGuide.K-LiteCodecPack.Full",
        name="K-Lite Codec Pack Full",
        publisher="Codec Guide",
        category="Media",
        version="18.8.5",
        notes="Comprehensive collection of DirectShow filters, VFW/ACM codecs, and tools.",
    ),
    CatalogEntry(
        id="dotPDNLLC.paint.net",
        name="Paint.NET",
        publisher="dotPDN LLC",
        category="Media",
        version="5.1.4",
        notes="Image and photo editing software with intuitive layers and special effects.",
    ),

    # --- Communication & Chat ---
    CatalogEntry(
        id="Discord.Discord",
        name="Discord",
        publisher="Discord Inc.",
        category="Communication",
        version="1.0.9184",
        notes="Voice, video and text chat service for gaming, communities, and friends.",
    ),
    CatalogEntry(
        id="Telegram.TelegramDesktop",
        name="Telegram Desktop",
        publisher="Telegram FZ-LLC",
        category="Communication",
        version="5.10.7",
        notes="Fast, synchronized, and secure cloud-based messaging app.",
    ),
    CatalogEntry(
        id="WhatsApp.WhatsApp",
        name="WhatsApp",
        publisher="WhatsApp LLC",
        category="Communication",
        version="2.2450.6.0",
        notes="Simple, reliable, private messaging and calling across devices.",
    ),
    CatalogEntry(
        id="Zoom.Zoom",
        name="Zoom Workplace",
        publisher="Zoom Video Communications, Inc.",
        category="Communication",
        version="6.3.10",
        notes="Modern video meetings, team chat, phone, whiteboard, and workspace.",
    ),
    CatalogEntry(
        id="SlackTechnologies.Slack",
        name="Slack",
        publisher="Slack Technologies",
        category="Communication",
        version="4.41.105",
        notes="Productivity platform for team messaging, channels, and workflows.",
    ),
    CatalogEntry(
        id="Signal.Signal",
        name="Signal",
        publisher="Signal Messenger LLC",
        category="Communication",
        version="7.42.0",
        notes="State-of-the-art end-to-end encryption for private messaging.",
    ),

    # --- Productivity & Office ---
    CatalogEntry(
        id="TheDocumentFoundation.LibreOffice",
        name="LibreOffice",
        publisher="The Document Foundation",
        category="Productivity",
        version="25.2.0",
        notes="Free and powerful open source office suite (Writer, Calc, Impress).",
    ),
    CatalogEntry(
        id="Obsidian.Obsidian",
        name="Obsidian",
        publisher="Dynalist Inc.",
        category="Productivity",
        version="1.8.4",
        notes="Sharpen your thinking. Extensible markdown knowledge base on local files.",
    ),
    CatalogEntry(
        id="Notion.Notion",
        name="Notion",
        publisher="Notion Labs, Incorporated",
        category="Productivity",
        version="4.2.1",
        notes="A connected workspace for wiki, docs, projects, and notes.",
    ),
    CatalogEntry(
        id="Adobe.Acrobat.Reader.64-bit",
        name="Adobe Acrobat Reader (64-bit)",
        publisher="Adobe Systems Incorporated",
        category="Productivity",
        version="24.004.20243",
        notes="The free global standard for reliably viewing, printing, and sharing PDFs.",
    ),
    CatalogEntry(
        id="Foxit.FoxitReader",
        name="Foxit PDF Reader",
        publisher="Foxit Software Inc.",
        category="Productivity",
        version="2024.3.0.26795",
        notes="Fast, feature-rich PDF viewer and editor for viewing and annotating.",
    ),

    # --- Gaming & Store Launchers ---
    CatalogEntry(
        id="Valve.Steam",
        name="Steam",
        publisher="Valve Corporation",
        category="Gaming",
        version="2.10.91.91",
        notes="The ultimate entertainment platform. Play, connect, create, and more.",
    ),
    CatalogEntry(
        id="EpicGames.EpicGamesLauncher",
        name="Epic Games Launcher",
        publisher="Epic Games, Inc.",
        category="Gaming",
        version="1.3.109.0",
        notes="Official game launcher and Unreal Engine hub by Epic Games.",
    ),
    CatalogEntry(
        id="GOG.Galaxy",
        name="GOG GALAXY",
        publisher="GOG sp. z o.o.",
        category="Gaming",
        version="2.0.76.6",
        notes="Combine your game libraries from all PC and console platforms into one.",
    ),
    CatalogEntry(
        id="Blizzard.BattleNet",
        name="Battle.net",
        publisher="Blizzard Entertainment, Inc.",
        category="Gaming",
        version="2.38.0.15082",
        notes="Blizzard launcher connecting players with World of Warcraft, Overwatch, etc.",
    ),

    # --- Gaming & System Runtimes ---
    CatalogEntry(
        id="Microsoft.VCRedist.2015+.x64",
        name="Microsoft Visual C++ 2015–2022 Redistributable (x64)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="14.51.36247.0",
        notes="Essential Visual C++ runtime required by 95% of modern 64-bit PC games and apps.",
    ),
    CatalogEntry(
        id="Microsoft.VCRedist.2015+.x86",
        name="Microsoft Visual C++ 2015–2022 Redistributable (x86)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="14.51.36247.0",
        notes="Essential Visual C++ runtime for 32-bit games, launchers, and Discord/Steam overlays.",
    ),
    CatalogEntry(
        id="Microsoft.VCRedist.2013.x64",
        name="Microsoft Visual C++ 2013 Redistributable (x64)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="12.0.40664.0",
        notes="Required for 2013–2016 games (Battlefield 4, GTA V, Witcher 3, etc.).",
    ),
    CatalogEntry(
        id="Microsoft.VCRedist.2013.x86",
        name="Microsoft Visual C++ 2013 Redistributable (x86)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="12.0.40664.0",
        notes="Required for 32-bit games and utilities compiled with Visual C++ 2013.",
    ),
    CatalogEntry(
        id="Microsoft.VCRedist.2012.x64",
        name="Microsoft Visual C++ 2012 Redistributable (x64)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="11.0.61030.0",
        notes="Required for 2012-era games, emulators, and graphics software.",
    ),
    CatalogEntry(
        id="Microsoft.VCRedist.2010.x64",
        name="Microsoft Visual C++ 2010 Redistributable (x64)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="10.0.40219",
        notes="Required for classic titles like Skyrim LE, Fallout New Vegas, and Unreal Engine 3 games.",
    ),
    CatalogEntry(
        id="Microsoft.DotNet.DesktopRuntime.8",
        name="Microsoft .NET Desktop Runtime 8.0 (LTS)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="8.0.33",
        notes="Modern Long-Term Support desktop runtime for game launchers, emulators, and tools.",
    ),
    CatalogEntry(
        id="Microsoft.DotNet.DesktopRuntime.9",
        name="Microsoft .NET Desktop Runtime 9.0",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="9.0.22",
        notes="Latest high-performance .NET runtime for next-generation Windows software.",
    ),
    CatalogEntry(
        id="Microsoft.DotNet.DesktopRuntime.6",
        name="Microsoft .NET Desktop Runtime 6.0 (Legacy LTS)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="6.0.36",
        notes="Required by legacy Unity game modding tools, loaders, and emulators.",
    ),
    CatalogEntry(
        id="Microsoft.DirectX",
        name="DirectX End-User Runtimes (June 2010)",
        publisher="Microsoft Corporation",
        category="Runtimes",
        version="9.29.1974.0",
        notes="Installs legacy d3dx9, d3dx10, and d3dx11 DLLs to fix missing DirectX errors in games.",
    ),
    CatalogEntry(
        id="CreativeTechnology.OpenAL",
        name="OpenAL 3D Audio Library",
        publisher="Creative Technology Ltd.",
        category="Runtimes",
        version="1.1",
        notes="Positional 3D audio runtime required by Minecraft, Source engine, and simulation titles.",
    ),
    CatalogEntry(
        id="KhronosGroup.VulkanRT",
        name="Vulkan Runtime",
        publisher="Khronos Group",
        category="Runtimes",
        version="1.4.363.0",
        notes="High-performance low-overhead 3D graphics runtime for modern gaming and emulation.",
    ),
]


def _match_installed(
    item_id: str,
    item_name: str,
    installed_map: Dict[str, ProgramItem],
) -> Optional[ProgramItem]:
    """Finds an existing installed application matching the catalog ID or name."""
    clean_id = (item_id or "").strip().lower()
    clean_name = (item_name or "").strip().lower()

    if clean_id in installed_map:
        return installed_map[clean_id]

    # Try matching without version suffixes or matching name
    for k, inst in installed_map.items():
        if inst.name and inst.name.strip().lower() == clean_name:
            return inst
        if clean_id and inst.id and clean_id == inst.id.strip().lower():
            return inst

    return None


def get_popular_catalog(installed_programs: Optional[List[ProgramItem]] = None) -> List[ProgramItem]:
    """Returns the full curated popular catalog, annotated with local installation state."""
    installed_map: Dict[str, ProgramItem] = {}
    if installed_programs:
        for p in installed_programs:
            if p.id:
                installed_map[p.id.strip().lower()] = p

    items: List[ProgramItem] = []
    for entry in CURATED_CATALOG:
        matched = _match_installed(entry.id, entry.name, installed_map)
        if matched:
            # Already installed on this PC
            inst_v = matched.installed_version or "Installed"
            is_up = matched.action == UpdateAction.UP_TO_DATE
            it = ProgramItem(
                name=entry.name,
                id=entry.id,
                publisher=entry.publisher,
                installed_version=inst_v,
                latest_version=entry.version or matched.latest_version or "Latest",
                package_type=entry.package_type,
                source=entry.source,
                action=UpdateAction.UP_TO_DATE if is_up else UpdateAction.AVAILABLE,
                notes=f"Installed ({inst_v}) • {entry.notes}",
                is_verified_winget=True,
            )
        else:
            it = ProgramItem(
                name=entry.name,
                id=entry.id,
                publisher=entry.publisher,
                installed_version="Not Installed",
                latest_version=entry.version,
                package_type=entry.package_type,
                source=entry.source,
                action=UpdateAction.AVAILABLE,
                notes=entry.notes or f"Official {entry.category} package ready to install",
                is_verified_winget=True,
            )
        items.append(it)

    return items


def search_catalog_packages(
    query: str,
    winget_entries: Optional[List] = None,
    installed_programs: Optional[List[ProgramItem]] = None,
    secondary_items: Optional[List[ProgramItem]] = None,
) -> List[ProgramItem]:
    """Filters curated catalog and merges live winget search results and secondary managers."""
    q = (query or "").strip().lower()
    terms = q.split()

    installed_map: Dict[str, ProgramItem] = {}
    if installed_programs:
        for p in installed_programs:
            if p.id:
                installed_map[p.id.strip().lower()] = p

    seen_ids = set()
    results: List[ProgramItem] = []

    # 1. Filter curated catalog
    for entry in CURATED_CATALOG:
        searchable = f"{entry.name} {entry.id} {entry.publisher} {entry.category} {entry.notes}".lower()
        if not terms or all(t in searchable for t in terms):
            matched = _match_installed(entry.id, entry.name, installed_map)
            if matched:
                inst_v = matched.installed_version or "Installed"
                is_up = matched.action == UpdateAction.UP_TO_DATE
                it = ProgramItem(
                    name=entry.name,
                    id=entry.id,
                    publisher=entry.publisher,
                    installed_version=inst_v,
                    latest_version=entry.version or matched.latest_version or "Latest",
                    package_type=entry.package_type,
                    source=entry.source,
                    action=UpdateAction.UP_TO_DATE if is_up else UpdateAction.AVAILABLE,
                    notes=f"Installed ({inst_v}) • {entry.notes}",
                    is_verified_winget=True,
                )
            else:
                it = ProgramItem(
                    name=entry.name,
                    id=entry.id,
                    publisher=entry.publisher,
                    installed_version="Not Installed",
                    latest_version=entry.version,
                    package_type=entry.package_type,
                    source=entry.source,
                    action=UpdateAction.AVAILABLE,
                    notes=entry.notes or "Official catalog package ready to install",
                    is_verified_winget=True,
                )
            results.append(it)
            seen_ids.add(entry.id.lower())

    # 2. Merge secondary package managers (pip, npm, scoop, choco)
    if secondary_items:
        for s_item in secondary_items:
            s_key = (s_item.id or s_item.name).lower()
            if s_key not in seen_ids:
                seen_ids.add(s_key)
                results.append(s_item)

    # 3. Merge live winget search entries
    if winget_entries:
        for entry in winget_entries:
            eid = getattr(entry, "id", "")
            if not eid:
                continue
            if eid.lower() in seen_ids:
                continue
            seen_ids.add(eid.lower())

            matched = _match_installed(eid, getattr(entry, "name", ""), installed_map)
            inst_v = matched.installed_version if matched else "Not Installed"
            act = UpdateAction.UP_TO_DATE if (matched and matched.action == UpdateAction.UP_TO_DATE) else UpdateAction.AVAILABLE

            it = ProgramItem(
                name=getattr(entry, "name", eid),
                id=eid,
                publisher=getattr(entry, "publisher", "Official Publisher"),
                installed_version=inst_v,
                latest_version=getattr(entry, "version", "Latest") or "Latest",
                package_type=PackageType.WIN32_EXE,
                source=getattr(entry, "source", "winget") or "winget",
                action=act,
                notes=f"Discovered via repository search ({eid})",
                is_verified_winget=True,
            )
            results.append(it)

    return results

