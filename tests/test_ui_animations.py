"""Unit tests for desktop UI animation components."""

import tkinter as tk
from unittest.mock import MagicMock
from winget_updater.gui.animations import (
    AnimatedSkeletonOverlay,
    CyberLaserHeaderCanvas,
    DeckCounterAnimator,
    FluentFloatingToast,
    PulsingWarningBeacon,
    ScanningPulseAnimator,
    SmoothLerpProgressBar,
    SoftwareEngineeringHeroScene,
    TimelinePipelineHUD,
    VectorIconDrawer,
)


def test_deck_counter_animator():
    root = tk.Tk()
    root.withdraw()
    targets = {"val": 100}
    captured = []

    def update_fn(vals):
        captured.append(vals["val"])

    DeckCounterAnimator.animate_deck(root, targets, update_fn, duration_ms=50, total_frames=4)
    # Process pending events
    root.update()
    root.destroy()
    assert len(captured) >= 1


def test_scanning_pulse_animator():
    root = tk.Tk()
    root.withdraw()
    lbl = tk.Label(root, text="Init")
    anim = ScanningPulseAnimator(lbl, "Scanning")
    anim.start()
    assert anim.is_active is True
    anim.update_text("Updating")
    assert anim.base_text == "Updating"
    anim.stop("Finished")
    assert anim.is_active is False
    assert lbl.cget("text") == "Finished"
    root.destroy()


def test_cyber_laser_canvas():
    root = tk.Tk()
    root.withdraw()
    laser = CyberLaserHeaderCanvas(root, height=5)
    laser.set_mode("scanning")
    assert laser.mode == "scanning"
    laser.set_mode("updating")
    assert laser.mode == "updating"
    laser._tick()
    laser.stop()
    assert laser.is_animating is False
    root.destroy()


def test_smooth_lerp_progress_bar():
    root = tk.Tk()
    root.withdraw()
    pb = SmoothLerpProgressBar(root, width=200, height=18)
    pb.set_progress(75.0)
    assert pb.target_val == 75.0
    pb._tick()
    assert pb.current_val > 0.0
    root.destroy()


def test_animated_skeleton_overlay():
    root = tk.Tk()
    root.withdraw()
    skel = AnimatedSkeletonOverlay(root)
    skel.start_shimmer()
    assert skel.is_shimmering is True
    skel._tick()
    skel.stop_shimmer()
    assert skel.is_shimmering is False
    root.destroy()


def test_software_engineering_hero_scene():
    root = tk.Tk()
    root.withdraw()
    scene = SoftwareEngineeringHeroScene(root, height=100)
    assert scene.mode == "idle"
    scene.set_mode("scanning")
    assert scene.mode == "scanning"
    scene.set_mode("updating")
    assert scene.mode == "updating"
    scene._tick()
    scene.stop()
    assert scene.is_animating is False
    root.destroy()


def test_timeline_pipeline_hud():
    root = tk.Tk()
    root.withdraw()
    timeline = TimelinePipelineHUD(root, height=30)
    assert timeline.current_stage == 0
    timeline.set_stage(2)
    assert timeline.current_stage == 2
    timeline._tick()
    timeline.set_stage(4)
    assert timeline.current_stage == 4
    root.destroy()


def test_vector_icon_drawer():
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root, width=32, height=32)
    VectorIconDrawer.draw_cpu_chip(canvas, 16, 16)
    VectorIconDrawer.draw_rocket_box(canvas, 16, 16)
    VectorIconDrawer.draw_shield_check(canvas, 16, 16)
    VectorIconDrawer.draw_storage_drive(canvas, 16, 16)
    VectorIconDrawer.draw_gpu_module(canvas, 16, 16)
    root.destroy()


def test_theme_system():
    from winget_updater.gui.theme import DARK_THEME, LIGHT_THEME, get_theme
    assert get_theme("dark").name == "dark"
    assert get_theme("light").name == "light"
    assert get_theme("invalid").name == "light"

    root = tk.Tk()
    root.withdraw()

    # Test hero scene apply_theme
    hero = SoftwareEngineeringHeroScene(root, height=100)
    hero.apply_theme(LIGHT_THEME)
    assert hero.theme.name == "light"
    hero.apply_theme(DARK_THEME)
    assert hero.theme.name == "dark"
    hero.stop()

    # Test timeline apply_theme
    timeline = TimelinePipelineHUD(root, height=30)
    timeline.apply_theme(LIGHT_THEME)
    assert timeline.theme.name == "light"
    timeline.apply_theme(DARK_THEME)
    assert timeline.theme.name == "dark"

    # Test vector icons in light mode
    canvas = tk.Canvas(root, width=32, height=32)
    VectorIconDrawer.draw_cpu_chip(canvas, 16, 16, is_light=True)
    VectorIconDrawer.draw_rocket_box(canvas, 16, 16, is_light=True)
    VectorIconDrawer.draw_shield_check(canvas, 16, 16, is_light=True)
    VectorIconDrawer.draw_storage_drive(canvas, 16, 16, is_light=True)
    VectorIconDrawer.draw_gpu_module(canvas, 16, 16, is_light=True)

    root.destroy()


def test_main_window_theme_toggle():
    from winget_updater.gui.app import MainWindow
    from winget_updater.config import ConfigManager
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = ConfigManager(base_dir=Path(tmp_dir))
        app = MainWindow(config_manager=cfg)
        app.withdraw()

        assert app.current_theme.name == "light"
        app.toggle_theme()
        assert app.current_theme.name == "dark"
        assert cfg.theme == "dark"

        app.toggle_theme()
        assert app.current_theme.name == "light"
        assert cfg.theme == "light"

        app.destroy()


def test_rounded_button_and_badge():
    import tkinter as tk
    from winget_updater.gui.rounded_widgets import (
        RoundedButton,
        RoundedPillBadge,
        apply_native_window_styling,
        draw_rounded_rect,
    )

    root = tk.Tk()
    root.withdraw()

    # Native window styling
    apply_native_window_styling(root)

    # Canvas rounded rect
    c = tk.Canvas(root, width=100, height=100)
    poly = draw_rounded_rect(c, 10, 10, 90, 90, radius=8, fill="#ffffff")
    assert poly is not None

    # RoundedButton
    clicked = []
    btn = RoundedButton(
        root,
        text="Click Me",
        command=lambda: clicked.append(True),
        bg_color="#881337",
        fg_color="#ffffff",
        radius=8,
    )
    assert btn.text == "Click Me"
    assert btn["text"] == "Click Me"

    # Hover and press events
    btn._on_enter(None)
    assert btn._is_hovered is True
    btn._on_press(None)
    btn._on_release(None)
    assert clicked == [True]
    btn._on_leave(None)
    assert btn._is_hovered is False

    # Config state changes
    btn.config(state="disabled")
    assert btn._state == "disabled"
    assert btn["state"] == "disabled"
    # Clicking while disabled should do nothing
    btn._on_release(None)
    assert len(clicked) == 1

    btn.config(state="normal", text="Updated")
    assert btn.text == "Updated"

    # RoundedPillBadge
    badge = RoundedPillBadge(root, text="Verified", bg_color="#f1f5f9", fg_color="#0f172a")
    assert badge.text == "Verified"
    badge.set_badge("Pending", bg_color="#fef3c7", fg_color="#92400e")
    assert badge.text == "Pending"

    root.destroy()


def test_exclusion_dialog():
    import tempfile
    from pathlib import Path
    import tkinter as tk
    from winget_updater.config import ConfigManager
    from winget_updater.gui.dialogs import ExclusionManagerDialog

    root = tk.Tk()
    root.withdraw()

    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = ConfigManager(base_dir=Path(tmp_dir))
        cfg.add_exclusion("TestApp*", "Testing exclusion")
        dlg = ExclusionManagerDialog(root, cfg)
        dlg.withdraw()

        assert len(dlg.tree.get_children()) >= 1
        dlg.destroy()

    root.destroy()


def test_bind_winget_source_dialog_and_drawer(monkeypatch):
    import tempfile
    from pathlib import Path
    import tkinter as tk
    from tkinter import messagebox
    from winget_updater.config import ConfigManager
    from winget_updater.gui.components import DetailsDrawer
    from winget_updater.gui.dialogs import BindWingetSourceDialog
    from winget_updater.models import ProgramItem, UpdateAction

    monkeypatch.setattr(messagebox, "showinfo", lambda *args, **kwargs: True)
    monkeypatch.setattr(messagebox, "showwarning", lambda *args, **kwargs: True)

    root = tk.Tk()
    root.withdraw()

    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = ConfigManager(base_dir=Path(tmp_dir))
        item = ProgramItem(name="Unverified Tool", installed_version="1.0", action=UpdateAction.UNVERIFIED)

        # 1. Test Details Drawer with diagnostic box
        drawer = DetailsDrawer(root)
        drawer.set_item(item)
        assert drawer.lbl_diag_text.cget("text") != ""

        # 2. Test BindWingetSourceDialog
        bound_id_received = []
        dlg = BindWingetSourceDialog(
            root,
            item,
            cfg,
            on_bound=lambda b: bound_id_received.append(b),
        )
        dlg.withdraw()

        # Simulate typing an ID and binding
        dlg.entry_manual_id.delete(0, tk.END)
        dlg.entry_manual_id.insert(0, "ToolVendor.UnverifiedTool")
        dlg._apply_binding()

        assert "unverified tool" in cfg.custom_mappings
        assert cfg.custom_mappings["unverified tool"] == "ToolVendor.UnverifiedTool"
        assert bound_id_received == ["ToolVendor.UnverifiedTool"]

    root.destroy()





