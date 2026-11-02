# Software & Package Updater for Windows 11

<p align="center">
  <img src="assets/social-preview.png" alt="Software & Package Updater for Windows 11" width="100%" />
</p>

<p align="center">
  <a href="https://github.com/rupom787/winget-updater/releases/latest"><img src="https://img.shields.io/github/v/release/rupom787/winget-updater?style=for-the-badge&color=800020&logo=github&label=Release" alt="Latest Release" /></a>
  <img src="https://img.shields.io/badge/Unit%20Tests-59%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white" alt="59 Tests Passing" />
  <img src="https://img.shields.io/badge/Platform-Windows%2011-blue?style=for-the-badge&logo=windows11&logoColor=white" alt="Windows 11" />
  <img src="https://img.shields.io/badge/Architecture-x64%20%7C%2064--bit-success?style=for-the-badge" alt="64-bit Architecture" />
  <img src="https://img.shields.io/badge/Hardware-DirectX%2012%20%2F%20DWM%20Accelerated-orange?style=for-the-badge&logo=nvidia&logoColor=white" alt="DirectX 12 GPU" />
  <img src="https://img.shields.io/badge/License-Proprietary%20(All%20Rights%20Reserved)-red?style=for-the-badge" alt="Proprietary License" />
</p>

<p align="center">
  <a href="https://github.com/rupom787/winget-updater/releases/download/v1.0.0/WingetUpdater.exe">
    <img src="https://img.shields.io/badge/⚡_Direct_Download-WingetUpdater.exe_(13.1_MB)-800020?style=for-the-badge&logo=windows11&logoColor=white" alt="Download Standalone EXE" />
  </a>
</p>

---

## 🚀 Overview

**Software & Package Updater** is a desktop application engineered specifically for **Windows 11**. It audits installed software across all PC subsystems, verifies available updates against official package repositories via the **Windows Package Manager (`winget`)**, evaluates hardware and OS compatibility before each update, and installs verified software securely with Administrator privileges.

Featuring a **Clean White and Velvet Burgundy** aesthetic with anti-aliased rounded canvas controls, native Windows 11 rounded window corners, and **direct GPU hardware acceleration** (NVIDIA GeForce, AMD Radeon, Intel Arc), the application delivers instant responsiveness with zero UI freezing across 300+ item inventories.

---

## 💾 Download Standalone Executable (.exe)

No Python installation, compilers, or complex setup required. Simply download the standalone single-file binary and run:

| Package | Platform | Size | Integrity Check (SHA-256) |
| :--- | :--- | :--- | :--- |
| [**WingetUpdater.exe** (Direct Download)](https://github.com/rupom787/winget-updater/releases/download/v1.0.0/WingetUpdater.exe) | Windows 11 (64-bit) | 13.11 MB | `4F5CF09F96F196C39222B3C7088C2B50DBA2512D4E7F17BC430E7A159ECC59B2` |

### ⚡ Quick Start (Run in 10 Seconds)
1. **Download:** Click [**WingetUpdater.exe**](https://github.com/rupom787/winget-updater/releases/download/v1.0.0/WingetUpdater.exe) (or download from the [Releases](https://github.com/rupom787/winget-updater/releases) page).
2. **Launch:** Double-click `WingetUpdater.exe`.
3. **Approve Elevation:** When prompted by Windows User Account Control (UAC), click **Yes** to grant Administrator rights (required for installing and updating software).
4. **Scan & Update:** Click **"Check for updates"**, select the packages you wish to update, and click **"Update all eligible"**.

---

## ✨ Key Features

### 🖥️ 1. Multi-Subsystem Inventory Discovery
Unlike tools that check only one registry location, Software & Package Updater audits five distinct system subsystems simultaneously:
- **Classic Win32 Applications:** Scans both 64-bit and 32-bit Windows Registry hives (`HKLM\Software`, `HKCU\Software`, `WOW6432Node`).
- **Microsoft Store & MSIX Packages:** Queries official modern Windows packaged applications via AppX manifests.
- **Portable Applications:** Scans user-configured portable directories for standalone executables.
- **Browser Extensions:** Discovers extensions installed across Google Chrome, Microsoft Edge, Brave, and Mozilla Firefox.
- **OEM Device Drivers:** Enumerates third-party device drivers safely (`pnputil /enum-drivers`) in read-only mode.

### ⚡ 2. High-Performance Batched Queries
- Queries repository upgrades (`winget upgrade`) and installed registries (`winget list`) in single batch operations.
- Correlates an entire system inventory of 200–300+ programs in under **3 seconds** without slow, per-item network requests.
- Never skips software silently: programs without public repositories are explicitly marked **"No update source"** rather than hidden.

### 🎮 3. GPU Hardware Acceleration & Telemetry
- **Windows DirectX High-Performance Mode:** Automatically configures Windows 11 graphics preference (`GpuPreference=2;`) in the DirectX runtime.
- **Discrete GPU Routing:** Routes processing and composition through your dedicated graphics card (e.g. **NVIDIA GeForce RTX**, **AMD Radeon**).
- **DirectComposition & Double-Buffering:** Activates Windows 11 DWM hardware composition (`SetProcessDpiAwarenessContext(-4)` and `WS_EX_COMPOSITED`), eliminating canvas tearing and rendering lag.
- **Real-Time Telemetry:** Live GPU model, VRAM capacity, and driver version are displayed directly in the header and status bar.

### 🛡️ 4. Enterprise Safety & Reliability
- **Process Lock Detection & Auto-Close:** Identifies running applications that would lock files during installation and gracefully closes them before updating.
- **System Restore Point Creation:** Optionally creates a Windows System Restore Point prior to commencing batch update routines.
- **Automatic Post-Update Cleanup:** Purges temporary downloaded installer packages and setup caches automatically upon completion.
- **Downgrade Protection:** Automatically detects if your installed application is newer than the repository version, preventing unintended downgrades unless explicitly approved.
- **Exclusion Management (`exclusions.json`):** Easily ignore specific programs from all future scans and updates.
- **Daily Automated Scheduling:** Configure an automated background check via Windows Task Scheduler that runs only on AC power and interactive sign-in sessions.

---

## 🎨 User Interface & Layout

The application utilizes an intuitive **two-column layout with an interactive bottom details drawer**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Software & Package Updater  •  Windows 11  •  Hardware Accelerated (RTX 2050)│
├──────────────┬──────────────────────────────────────────────────────────────┤
│  NAVIGATION  │ [Check for updates]   [Update all eligible]  [Update selected] │
│ • All Apps   ├──────────────────────────────────────────────────────────────┤
│ • Updates    │ Application Name     Installed     Available     Status      │
│ • Up to Date │ ──────────────────────────────────────────────────────────── │
│ • Excluded   │ Git                  2.56.0.4      2.56.0.4      Up to date  │
│ • Catalog    │ VLC media player     3.0.21        3.0.24        Update ready│
│              │ Node.js              26.13.0       26.13.0       Up to date  │
│  CATEGORIES  ├──────────────────────────────────────────────────────────────┤
│ [Dropdown  ] │ [Avatar] VLC media player            [ Update available pill ]│
│              │ Publisher: VideoLAN  •  Package ID: VideoLAN.VLC             │
│  TELEMETRY   │ Installed: 3.0.21  →  Available: 3.0.24  (Source: winget)    │
│ Win 11 (x64) │ [ Update Application ]  [ Exclude ]  [ Open Folder ] [ Copy ]│
└──────────────┴──────────────────────────────────────────────────────────────┘
```

---

## ⚙️ System Requirements

- **Operating System:** Windows 11 (64-bit, Build 22000 or newer)
- **Package Manager:** Windows Package Manager CLI (`winget`), included natively with Windows 11
- **Privileges:** Administrator privileges (the executable self-elevates via Windows UAC upon launch)
- **Graphics:** DirectX 11 / 12 capable GPU (NVIDIA, AMD, Intel, or Qualcomm Adreno)

---

## 🔒 Verification & Security

To verify the integrity of your downloaded `WingetUpdater.exe`, open PowerShell and run:

```powershell
Get-FileHash -Path "WingetUpdater.exe" -Algorithm SHA256
```

Confirm that the output hash exactly matches:
```
4F5CF09F96F196C39222B3C7088C2B50DBA2512D4E7F17BC430E7A159ECC59B2
```

---

## 📄 License & Terms of Use

**Copyright © 2026 rupom. All Rights Reserved.**

This software and its source code are proprietary. **No license is granted to copy, modify, distribute, fork, reverse engineer, or create derivative works from the source code.** 

End users are authorized solely to download and execute the pre-compiled binary (`WingetUpdater.exe`) on personal Windows 11 devices for personal software maintenance. For full terms, please review the [`LICENSE`](LICENSE) file.
