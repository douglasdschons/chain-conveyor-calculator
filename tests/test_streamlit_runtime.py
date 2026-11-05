"""Exercise imports, widgets and reruns with the installed Streamlit runtime."""
import importlib.util
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Install requirements.txt")
class StreamlitRuntimeTests(unittest.TestCase):
    def test_drive_and_return_modes(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.run(timeout=30)
        self.assertFalse(app.exception)
        for supply in ("IBR Q catalogue", "Complete gearmotor", "Separate gearbox + motor"):
            for connection in ("Direct", "Secondary chain transmission"):
                for return_mode in ("Guided return", "Sag return"):
                    with self.subTest(supply=supply, connection=connection, return_mode=return_mode):
                        next(r for r in app.radio if r.label == "Supply mode").set_value(supply)
                        next(r for r in app.radio if r.label == "Connection").set_value(connection)
                        next(s for s in app.selectbox if s.label == "Return type").set_value(return_mode)
                        app.run(timeout=30)
                        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
