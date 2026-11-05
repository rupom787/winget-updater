"""Gaming & System Runtimes scanner and orchestrator for Windows 11.
Scans, detects, and automates installation of essential Visual C++ redistributables,
.NET Desktop runtimes, DirectX End-User Runtimes, OpenAL, and Vulkan components.
"""

from dataclasses import dataclass
from enum import Enum
import os
import re
import winreg
from typing import Callable, Dict, List, Optional, Tuple

from winget_updater.models import PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.utils.logger import get_logger
from winget_updater.winget.client import WingetClient

logger = get_logger()


class RuntimeCategory(str, Enum):
    VCREDIST = "Visual C++ Redistributable"
    DOTNET = ".NET Desktop Runtime"
    DIRECTX_GRAPHICS = "DirectX & Graphics"
    AUDIO_MEDIA = "Audio & Multimedia"


class RuntimeState(str, Enum):
    INSTALLED = "INSTALLED"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    MISSING = "MISSING"


@dataclass
class RuntimeDefinition:
    id: str
    name: str
    category: RuntimeCategory
    architecture: str  # "x64", "x86", or "universal"
    description: str
    is_essential: bool
    winget_id: str
    registry_patterns: List[str]
    file_checks: List[str] = None
    min_recommended_version: Optional[str] = None


# Authoritative definition of all critical runtimes required for Windows PC gaming & desktop applications
RECOMMENDED_RUNTIMES: List[RuntimeDefinition] = [
    # --- Microsoft Visual C++ Redistributables ---
    RuntimeDefinition(
        id="vcredist_2015_2022_x64",
        name="Visual C++ 2015–2022 Redistributable (x64)",
        category=RuntimeCategory.VCREDIST,
        architecture="x64",
        description="Core C++ runtime required by 95% of modern 64-bit games and desktop applications.",
        is_essential=True,
        winget_id="Microsoft.VCRedist.2015+.x64",
        registry_patterns=[r"visual c\+\+ (2015|2017|2019|2022|v14).*(x64|64-bit)"],
        file_checks=[r"System32\vcruntime140.dll", r"System32\msvcp140.dll"],
        min_recommended_version="14.40.33810",
    ),
    RuntimeDefinition(
        id="vcredist_2015_2022_x86",
        name="Visual C++ 2015–2022 Redistributable (x86)",
        category=RuntimeCategory.VCREDIST,
        architecture="x86",
        description="Required for 32-bit games, launchers, Discord/Steam game overlays, and mods.",
        is_essential=True,
        winget_id="Microsoft.VCRedist.2015+.x86",
        registry_patterns=[r"visual c\+\+ (2015|2017|2019|2022|v14).*(x86|32-bit)"],
        file_checks=[r"SysWOW64\vcruntime140.dll", r"SysWOW64\msvcp140.dll"],
        min_recommended_version="14.40.33810",
    ),
    RuntimeDefinition(
        id="vcredist_2013_x64",
        name="Visual C++ 2013 Redistributable (x64)",
        category=RuntimeCategory.VCREDIST,
        architecture="x64",
        description="Essential for 2013–2016 games (e.g. Battlefield 4, GTA V, Witcher 3).",
        is_essential=True,
        winget_id="Microsoft.VCRedist.2013.x64",
        registry_patterns=[r"visual c\+\+ 2013.*(x64|64-bit)"],
        file_checks=[r"System32\msvcr120.dll", r"System32\msvcp120.dll"],
        min_recommended_version="12.0.40664",
    ),
    RuntimeDefinition(
        id="vcredist_2013_x86",
        name="Visual C++ 2013 Redistributable (x86)",
        category=RuntimeCategory.VCREDIST,
        architecture="x86",
        description="Required for 32-bit binaries compiled with Visual Studio 2013.",
        is_essential=True,
        winget_id="Microsoft.VCRedist.2013.x86",
        registry_patterns=[r"visual c\+\+ 2013.*(x86|32-bit)"],
        file_checks=[r"SysWOW64\msvcr120.dll", r"SysWOW64\msvcp120.dll"],
        min_recommended_version="12.0.40664",
    ),
    RuntimeDefinition(
        id="vcredist_2012_x64",
        name="Visual C++ 2012 Redistributable (x64)",
        category=RuntimeCategory.VCREDIST,
        architecture="x64",
        description="Required for titles and game engines released around 2012–2014.",
        is_essential=False,
        winget_id="Microsoft.VCRedist.2012.x64",
        registry_patterns=[r"visual c\+\+ 2012.*(x64|64-bit)"],
        file_checks=[r"System32\msvcr110.dll", r"System32\msvcp110.dll"],
        min_recommended_version="11.0.61030",
    ),
    RuntimeDefinition(
        id="vcredist_2012_x86",
        name="Visual C++ 2012 Redistributable (x86)",
        category=RuntimeCategory.VCREDIST,
        architecture="x86",
        description="Required for 32-bit engines, tools, and emulators using MSVC 2012.",
        is_essential=False,
        winget_id="Microsoft.VCRedist.2012.x86",
        registry_patterns=[r"visual c\+\+ 2012.*(x86|32-bit)"],
        file_checks=[r"SysWOW64\msvcr110.dll", r"SysWOW64\msvcp110.dll"],
        min_recommended_version="11.0.61030",
    ),
    RuntimeDefinition(
        id="vcredist_2010_x64",
        name="Visual C++ 2010 Redistributable (x64)",
        category=RuntimeCategory.VCREDIST,
        architecture="x64",
        description="Required for classic titles (Skyrim LE, Fallout: New Vegas, Unreal Engine 3).",
        is_essential=True,
        winget_id="Microsoft.VCRedist.2010.x64",
        registry_patterns=[r"visual c\+\+ 2010.*(x64|64-bit)"],
        file_checks=[r"System32\msvcr100.dll", r"System32\msvcp100.dll"],
        min_recommended_version="10.0.40219",
    ),
    RuntimeDefinition(
        id="vcredist_2010_x86",
        name="Visual C++ 2010 Redistributable (x86)",
        category=RuntimeCategory.VCREDIST,
        architecture="x86",
        description="Required for 32-bit classic games and legacy PC mods.",
        is_essential=True,
        winget_id="Microsoft.VCRedist.2010.x86",
        registry_patterns=[r"visual c\+\+ 2010.*(x86|32-bit)"],
        file_checks=[r"SysWOW64\msvcr100.dll", r"SysWOW64\msvcp100.dll"],
        min_recommended_version="10.0.40219",
    ),
    RuntimeDefinition(
        id="vcredist_2008_x64",
        name="Visual C++ 2008 Redistributable (x64)",
        category=RuntimeCategory.VCREDIST,
        architecture="x64",
        description="Required for legacy games (Crysis, Mass Effect 1/2, GTA IV).",
        is_essential=False,
        winget_id="Microsoft.VCRedist.2008.x64",
        registry_patterns=[r"visual c\+\+ 2008.*(x64|64-bit)"],
        file_checks=[r"System32\msvcr90.dll"],
        min_recommended_version="9.0.30729",
    ),
    RuntimeDefinition(
        id="vcredist_2008_x86",
        name="Visual C++ 2008 Redistributable (x86)",
        category=RuntimeCategory.VCREDIST,
        architecture="x86",
        description="Required for 32-bit 2008–2010 games and retro PC gaming.",
        is_essential=False,
        winget_id="Microsoft.VCRedist.2008.x86",
        registry_patterns=[r"visual c\+\+ 2008.*(x86|32-bit)"],
        file_checks=[r"SysWOW64\msvcr90.dll"],
        min_recommended_version="9.0.30729",
    ),
    RuntimeDefinition(
        id="vcredist_2005_x64",
        name="Visual C++ 2005 Redistributable (x64)",
        category=RuntimeCategory.VCREDIST,
        architecture="x64",
        description="Required for classic 64-bit titles from the mid-2000s era.",
        is_essential=False,
        winget_id="Microsoft.VCRedist.2005.x64",
        registry_patterns=[r"visual c\+\+ 2005.*(x64|64-bit)"],
        file_checks=[r"System32\msvcr80.dll"],
        min_recommended_version="8.0.61000",
    ),
    RuntimeDefinition(
        id="vcredist_2005_x86",
        name="Visual C++ 2005 Redistributable (x86)",
        category=RuntimeCategory.VCREDIST,
        architecture="x86",
        description="Required for 32-bit classic PC gaming releases from 2005–2008.",
        is_essential=False,
        winget_id="Microsoft.VCRedist.2005.x86",
        registry_patterns=[r"visual c\+\+ 2005.*(x86|32-bit)"],
        file_checks=[r"SysWOW64\msvcr80.dll"],
        min_recommended_version="8.0.61001",
    ),

    # --- Microsoft .NET Desktop Runtimes ---
    RuntimeDefinition(
        id="dotnet_desktop_8_x64",
        name="Microsoft .NET Desktop Runtime 8.0 (LTS)",
        category=RuntimeCategory.DOTNET,
        architecture="x64",
        description="Long-Term Support runtime for modern Windows game tools, emulators, and launchers.",
        is_essential=True,
        winget_id="Microsoft.DotNet.DesktopRuntime.8",
        registry_patterns=[r"windows desktop runtime - 8\.", r"\.net.*desktop runtime.*8\."],
        file_checks=[],
        min_recommended_version="8.0.0",
    ),
    RuntimeDefinition(
        id="dotnet_desktop_9_x64",
        name="Microsoft .NET Desktop Runtime 9.0 (Current)",
        category=RuntimeCategory.DOTNET,
        architecture="x64",
        description="Latest high-performance .NET runtime for next-generation Windows utilities.",
        is_essential=False,
        winget_id="Microsoft.DotNet.DesktopRuntime.9",
        registry_patterns=[r"windows desktop runtime - 9\.", r"\.net.*desktop runtime.*9\."],
        file_checks=[],
        min_recommended_version="9.0.0",
    ),
    RuntimeDefinition(
        id="dotnet_desktop_6_x64",
        name="Microsoft .NET Desktop Runtime 6.0 (Legacy LTS)",
        category=RuntimeCategory.DOTNET,
        architecture="x64",
        description="Required by legacy Unity tools, mod loaders, and previous-gen game utilities.",
        is_essential=False,
        winget_id="Microsoft.DotNet.DesktopRuntime.6",
        registry_patterns=[r"windows desktop runtime - 6\.", r"\.net.*desktop runtime.*6\."],
        file_checks=[],
        min_recommended_version="6.0.0",
    ),

    # --- DirectX, Audio & Graphics Runtimes ---
    RuntimeDefinition(
        id="directx_june_2010",
        name="DirectX End-User Runtimes (June 2010)",
        category=RuntimeCategory.DIRECTX_GRAPHICS,
        architecture="universal",
        description="Provides d3dx9, d3dx10, d3dx11, and xinput DLLs missing on clean Windows 10/11 installs.",
        is_essential=True,
        winget_id="Microsoft.DirectX",
        registry_patterns=[r"directx.*9\.0c", r"directx.*extra files", r"directx end-user"],
        file_checks=[r"System32\d3dx9_43.dll", r"SysWOW64\d3dx9_43.dll"],
        min_recommended_version="9.29.1974.0",
    ),
    RuntimeDefinition(
        id="openal_runtime",
        name="OpenAL 3D Audio Library",
        category=RuntimeCategory.AUDIO_MEDIA,
        architecture="universal",
        description="3D spatial audio API used by Minecraft, Source engine, Unreal, and simulation games.",
        is_essential=False,
        winget_id="CreativeTechnology.OpenAL",
        registry_patterns=[r"openal"],
        file_checks=[r"System32\OpenAL32.dll"],
        min_recommended_version="1.1",
    ),
    RuntimeDefinition(
        id="vulkan_runtime",
        name="Vulkan Runtime Library",
        category=RuntimeCategory.DIRECTX_GRAPHICS,
        architecture="universal",
        description="Cross-platform, low-overhead graphics API for modern gaming emulators and AAA titles.",
        is_essential=False,
        winget_id="KhronosGroup.VulkanRT",
        registry_patterns=[r"vulkan.*runtime"],
        file_checks=[r"System32\vulkan-1.dll"],
        min_recommended_version="1.3",
    ),
    RuntimeDefinition(
        id="webview2_runtime",
        name="Microsoft Edge WebView2 Runtime",
        category=RuntimeCategory.DOTNET,
        architecture="universal",
        description="Embedded web view engine used by modern game launchers (EA App, Riot, Battle.net).",
        is_essential=True,
        winget_id="Microsoft.EdgeWebView2Runtime",
        registry_patterns=[r"microsoft edge webview2 runtime"],
        file_checks=[],
        min_recommended_version="120.0",
    ),
]


@dataclass
class RuntimeScanResult:
    definition: RuntimeDefinition
    state: RuntimeState
    installed_version: Optional[str] = None
    latest_version: Optional[str] = None
    status_message: str = ""
    is_missing: bool = False
    is_upgradable: bool = False


class RuntimesManager:
    """Detects, scans, and installs essential gaming and desktop runtimes."""

    def __init__(self, winget_client: Optional[WingetClient] = None):
        self.client = winget_client or WingetClient()

    def get_installed_registry_entries(self) -> List[Tuple[str, str]]:
        """Enumerates DisplayName and DisplayVersion from all Windows uninstall registry subkeys."""
        entries: List[Tuple[str, str]] = []
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for hive, path in keys:
            try:
                with winreg.OpenKey(hive, path) as root:
                    count = winreg.QueryInfoKey(root)[0]
                    for i in range(count):
                        try:
                            subkey_name = winreg.EnumKey(root, i)
                            with winreg.OpenKey(root, subkey_name) as subkey:
                                try:
                                    name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                except Exception:
                                    continue
                                ver = ""
                                try:
                                    ver, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                                except Exception:
                                    pass
                                if name:
                                    entries.append((str(name).strip(), str(ver).strip()))
                        except Exception:
                            continue
            except Exception:
                continue

        return entries

    def get_dotnet_desktop_versions(self) -> List[str]:
        """Discovers installed .NET WindowsDesktop runtimes."""
        versions: List[str] = []
        # Check dotnet shared installation directory
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        desktop_dir = os.path.join(program_files, "dotnet", "shared", "Microsoft.WindowsDesktop.App")
        if os.path.isdir(desktop_dir):
            try:
                for entry in os.listdir(desktop_dir):
                    if os.path.isdir(os.path.join(desktop_dir, entry)) and re.match(r"^\d+\.\d+", entry):
                        versions.append(entry)
            except Exception:
                pass
        return versions

    def scan_all_runtimes(
        self,
        winget_upgrades: Optional[Dict[str, str]] = None,
    ) -> List[RuntimeScanResult]:
        """Performs a comprehensive scan of the local system against the authoritative runtime matrix."""
        registry_entries = self.get_installed_registry_entries()
        dotnet_versions = self.get_dotnet_desktop_versions()
        windir = os.environ.get("WINDIR", r"C:\Windows")
        results: List[RuntimeScanResult] = []

        for rdef in RECOMMENDED_RUNTIMES:
            installed = False
            detected_ver: Optional[str] = None

            # 1. Check registry patterns
            for reg_pat in rdef.registry_patterns:
                regex = re.compile(reg_pat, re.IGNORECASE)
                for name, ver in registry_entries:
                    if regex.search(name):
                        installed = True
                        if ver and not detected_ver:
                            detected_ver = ver
                        break
                if installed:
                    break

            # 2. Check .NET specific versions
            if not installed and rdef.category == RuntimeCategory.DOTNET:
                match = re.search(r"_(\d+)_", rdef.id)
                if match:
                    major = match.group(1)
                    matching_dotnet = [v for v in dotnet_versions if v.startswith(f"{major}.")]
                    if matching_dotnet:
                        installed = True
                        detected_ver = matching_dotnet[0]

            # 3. Check critical DLL file paths
            if not installed and rdef.file_checks:
                file_found = False
                for rel_path in rdef.file_checks:
                    full_p = os.path.join(windir, rel_path)
                    if os.path.isfile(full_p):
                        file_found = True
                        break
                if file_found:
                    installed = True
                    detected_ver = detected_ver or "Installed"

            # 4. Check if an upgrade is available in winget
            winget_id_lower = rdef.winget_id.lower()
            upgrade_avail = False
            latest_version: Optional[str] = None
            if winget_upgrades and winget_id_lower in winget_upgrades:
                upgrade_avail = True
                latest_version = winget_upgrades[winget_id_lower]

            if not installed:
                state = RuntimeState.MISSING
                msg = "Missing from system (Recommended for game compatibility)"
            elif upgrade_avail:
                state = RuntimeState.UPDATE_AVAILABLE
                msg = f"Update available: {latest_version or 'Latest'}"
            else:
                state = RuntimeState.INSTALLED
                ver_label = f"v{detected_ver}" if detected_ver else "Active"
                msg = f"Installed & Healthy ({ver_label})"

            results.append(
                RuntimeScanResult(
                    definition=rdef,
                    state=state,
                    installed_version=detected_ver,
                    latest_version=latest_version,
                    status_message=msg,
                    is_missing=(state == RuntimeState.MISSING),
                    is_upgradable=(state == RuntimeState.UPDATE_AVAILABLE),
                )
            )

        return results

    def install_runtime(
        self,
        runtime_id: str,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """Installs or upgrades a single runtime package via Winget with silent flags."""
        target_def = next((r for r in RECOMMENDED_RUNTIMES if r.id == runtime_id or r.winget_id.lower() == runtime_id.lower()), None)
        pkg_id = target_def.winget_id if target_def else runtime_id

        logger.info(f"RuntimesManager: Installing runtime package {pkg_id}")
        return self.client.install_package(package_id=pkg_id, dry_run=dry_run, source="winget")

    def batch_install_missing(
        self,
        target_results: List[RuntimeScanResult],
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Tuple[bool, str]]:
        """Installs all missing or upgradable runtimes sequentially with progress callbacks."""
        outcomes: Dict[str, Tuple[bool, str]] = {}
        actionable = [r for r in target_results if r.is_missing or r.is_upgradable]
        total = len(actionable)

        for idx, item in enumerate(actionable, 1):
            name = item.definition.name
            if on_progress:
                on_progress(f"Installing {name} ({idx}/{total})...", idx, total)

            success, msg = self.install_runtime(item.definition.winget_id, dry_run=dry_run)
            outcomes[item.definition.id] = (success, msg)
            logger.info(f"Runtime install result for {name}: {success} ({msg})")

        return outcomes
