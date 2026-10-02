"""GUI routing checks: no real font installation or elevation in tests."""
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from font_fixtures import make_font
from korean_builder import MODERN_HANGUL

if os.name == 'nt':
    import app


@unittest.skipUnless(os.name == 'nt', 'Windows GUI')
class KoreanGuiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Startup backup/config are external user-state effects, not this test.
        self.patches = [patch.object(app.SyrianSegoeApp, name) for name in
                        ('run_backup', 'load_config', 'save_config')]
        for p in self.patches:
            p.start(); self.addCleanup(p.stop)
        self.gui = app.SyrianSegoeApp()
        self.gui.withdraw()
        self.addCleanup(self.close_gui)
        self.gui.update()

    def close_gui(self):
        # CTk/Tk timers belong to this interpreter; cancel before destroying it.
        for timer in self.gui.tk.call('after', 'info'):
            self.gui.tk.call('after', 'cancel', timer)
        self.gui.destroy()

    def run_worker(self, method, *args):
        worker = threading.Thread(target=method, args=args, daemon=True)
        worker.start()
        expired = []
        def poll():
            if worker.is_alive(): self.gui.after(10, poll)
            else: self.gui.quit()
        def timeout():
            expired.append(True); self.gui.quit()
        timer = self.gui.after(5000, timeout)
        self.gui.after(10, poll)
        self.gui.mainloop()
        self.gui.after_cancel(timer)
        self.gui.update()
        self.assertFalse(expired, 'GUI worker did not return through the main event loop')

    def test_variable_selection_enables_build_and_invalidates_old_package(self):
        self.assertTrue(hasattr(self.gui, 'korean_select_btn'), 'Korean GUI controls missing')
        font = self.root / 'PretendardVariable.ttf'
        make_font(font, codepoints=MODERN_HANGUL, variable=True)
        self.gui.korean_build_dir = str(self.root / 'old-build')
        with patch.object(app.filedialog, 'askopenfilename', return_value=str(font)):
            self.gui.korean_select_btn.invoke()
        self.assertEqual(self.gui.korean_source, str(font))
        self.assertIsNone(self.gui.korean_build_dir)
        self.assertEqual(self.gui.korean_build_btn.cget('state'), 'normal')
        self.assertEqual(self.gui.korean_apply_btn.cget('state'), 'disabled')

    def test_static_font_is_rejected_without_enabling_apply(self):
        self.assertTrue(hasattr(self.gui, 'korean_select_btn'), 'Korean GUI controls missing')
        font = self.root / 'Pretendard-Regular.ttf'
        make_font(font, codepoints=MODERN_HANGUL)
        with patch.object(app.filedialog, 'askopenfilename', return_value=str(font)), \
                patch.object(app.messagebox, 'showerror') as error:
            self.gui.korean_select_btn.invoke()
        self.assertIsNone(self.gui.korean_source)
        self.assertEqual(self.gui.korean_apply_btn.cget('state'), 'disabled')
        self.assertTrue(error.called)

    def test_failed_build_never_enables_apply_and_restores_controls(self):
        self.assertTrue(hasattr(self.gui, '_threaded_korean_build'), 'GUI builder missing')
        self.gui.korean_source = 'source.ttf'
        self.gui.set_build_busy(True)
        with patch.object(app, 'build_all', side_effect=ValueError('broken build')), \
                patch.object(app.messagebox, 'showerror') as error:
            self.run_worker(self.gui._threaded_korean_build, 'source.ttf', str(self.root / 'Fonts'), str(self.root / 'out'))
        self.assertIsNone(self.gui.korean_build_dir)
        self.assertFalse(self.gui.build_busy)
        self.assertEqual(self.gui.revert_btn.cget('state'), 'normal')
        self.assertEqual(self.gui.korean_apply_btn.cget('state'), 'disabled')
        self.assertTrue(error.called)

    def test_declined_apply_does_not_elevate_or_install(self):
        self.assertTrue(hasattr(self.gui, 'apply_korean_build'), 'GUI apply missing')
        self.gui.korean_build_dir = str(self.root / 'validated')
        with patch.object(app.messagebox, 'askyesno', return_value=False), \
                patch.object(app, 'is_admin', side_effect=AssertionError('elevation reached')), \
                patch.object(app, 'apply_build', side_effect=AssertionError('install reached')):
            self.gui.apply_korean_build()
        self.assertFalse(self.gui.build_busy)

    def test_source_restore_elevation_keeps_an_absolute_script_path(self):
        with patch.object(app, 'is_admin', return_value=False), \
                patch.object(app.messagebox, 'askyesno', return_value=True), \
                patch.object(app.sys, 'argv', ['src/app.py']), \
                patch.object(app.ctypes.windll.shell32, 'ShellExecuteW', return_value=31) as launch:
            self.gui.restore_system()
        args = launch.call_args.args[3]
        state = args.split('--state "')[1].rstrip('"')
        self.addCleanup(lambda: Path(state).unlink(missing_ok=True))
        self.assertIn(str(Path('src/app.py').resolve()), args)

    def test_cancelled_apply_elevation_keeps_gui_and_never_installs(self):
        self.gui.korean_build_dir = str(self.root / 'validated')
        with patch.object(app, 'is_admin', return_value=False), \
                patch.object(app.messagebox, 'askyesno', return_value=True), \
                patch.object(app.messagebox, 'showerror') as error, \
                patch.object(app.ctypes.windll.shell32, 'ShellExecuteW', return_value=31), \
                patch.object(app, 'apply_build', side_effect=AssertionError('install reached')):
            self.gui.apply_korean_build()
        self.assertTrue(self.gui.winfo_exists())
        self.assertEqual(self.gui.korean_build_dir, str(self.root / 'validated'))
        self.assertTrue(error.called)

    def test_build_success_is_read_only_and_package_survives_state_reload(self):
        self.assertTrue(hasattr(self.gui, '_threaded_korean_build'), 'GUI builder missing')
        from test_install_plan import InstallPlanTests
        from font_transaction import restore_font_set
        from test_rollback import Registry
        build, fonts = InstallPlanTests().fixture(self.root)
        self.gui.korean_source = 'source.ttf'
        self.gui.set_build_busy(True)
        # Real plan validation; only the expensive build is replaced with an existing fixture.
        with patch.object(app, 'build_all'), patch.object(app.messagebox, 'showinfo'):
            self.run_worker(self.gui._threaded_korean_build, 'source.ttf', str(fonts), str(build))
        self.assertEqual(len(list(fonts.iterdir())), 10)
        self.assertEqual(self.gui.korean_build_dir, str(build))
        self.assertEqual(self.gui.korean_apply_btn.cget('state'), 'normal')
        state = self.gui.save_state()
        self.gui.korean_build_dir = None
        self.gui.load_state(state)
        self.assertEqual(self.gui.korean_build_dir, str(build))
        # Reuse production installation and rollback against a temporary Fonts directory.
        registry = Registry(); original = dict(registry.values)
        with patch.object(app, 'persistent_state_dir', return_value=str(self.root / 'state')), \
                patch.object(app, 'WindowsRegistry', return_value=registry), \
                patch.object(app.messagebox, 'showinfo'):
            self.gui.set_build_busy(True)
            self.run_worker(self.gui._threaded_korean_apply, str(build), str(fonts))
        self.assertEqual(registry.get('Malgun Gothic (TrueType)')[0], 'malgun_system_mod.ttf')
        restore_font_set(self.root / 'state', registry, fonts)
        self.assertEqual(registry.values, original)
        self.assertEqual(len(list(fonts.iterdir())), 10)

