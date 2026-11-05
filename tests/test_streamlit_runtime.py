"""Real Streamlit widget tests, automatically skipped if Streamlit is unavailable."""
import importlib.util
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Install requirements.txt")
class StreamlitRuntimeTests(unittest.TestCase):
    @staticmethod
    def create_app():
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))

    def test_decimal_entry_and_power_pair(self):
        app = self.create_app().run(timeout=40)
        self.assertFalse(app.exception)

        def field(label):
            return next(item for item in app.text_input if item.label == label)

        field("Diâmetro primitivo Dp [mm]").set_value("25,4").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["numero:Diâmetro primitivo Dp [mm]"], 25.4)
        field("cv").set_value("2,5").run()
        self.assertFalse(app.exception)
        self.assertAlmostEqual(app.session_state["gearmotor_kw"], 2.5 * .73549875)
        self.assertEqual(field("kW").value, "1,839")
        field("kW").set_value("1,5").run()
        self.assertFalse(app.exception)
        self.assertAlmostEqual(app.session_state["gearmotor_cv"], 1.5 / .73549875)
        self.assertEqual(field("cv").value, "2,039")
        field("Diâmetro primitivo Dp [mm]").set_value("0").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertIn("valor mínimo", app.error[0].value)
        field("Diâmetro primitivo Dp [mm]").set_value("202,66").run()
        self.assertFalse(app.error)
        self.assertFalse(app.exception)

    def test_modes(self):
        app = self.create_app().run(timeout=40)
        self.assertFalse(app.exception)
        for supply in ("Motoredutor completo", "Redutor e motor separados"):
            for connection in ("Direto", "Transmissão secundária por corrente"):
                for return_mode in ("Retorno guiado", "Retorno livre com flecha"):
                    with self.subTest(supply=supply, connection=connection, return_mode=return_mode):
                        next(r for r in app.radio if r.label == "Tipo de acionamento").set_value(supply)
                        next(r for r in app.radio if r.label == "Conexão").set_value(connection)
                        next(s for s in app.selectbox if s.label == "Tipo de retorno").set_value(return_mode)
                        app.run(timeout=40)
                        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
