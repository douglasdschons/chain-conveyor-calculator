"""Smoke tests without installing Streamlit (fake UI facade)."""
from __future__ import annotations

import runpy
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FakeContext:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def container(self):
        return self


class FakeStreamlit(types.ModuleType):
    def __init__(self, return_mode="Retorno guiado", coupling_mode="Direto",
                 supply_mode="Motoredutor completo"):
        super().__init__("streamlit")
        self.session_state = {}
        self.return_mode = return_mode
        self.coupling_mode = coupling_mode
        self.supply_mode = supply_mode
        self.html = []
        self.radio_options = {}
        self.text_labels = []

    def columns(self, spec, **_):
        n = spec if isinstance(spec, int) else len(spec)
        return [FakeContext() for _ in range(n)]

    def empty(self):
        return FakeContext()

    def expander(self, *_args, **_kwargs):
        return FakeContext()

    def toggle(self, _label, *_, **kwargs):
        return kwargs.get("value", False)

    def selectbox(self, label, options, *_, **kwargs):
        if label == "Tipo de retorno":
            return self.return_mode
        value = options[kwargs.get("index", 0)]
        key = kwargs.get("key")
        if key:
            return self.session_state.setdefault(key, value)
        return value

    def radio(self, label, options, *_, **__):
        self.radio_options[label] = options
        return {"Conexão": self.coupling_mode,
                "Tipo de acionamento": self.supply_mode}.get(label, options[0])

    def text_input(self, label, value="", *_, **kwargs):
        self.text_labels.append(label)
        key = kwargs.get("key")
        return self.session_state.get(key, value) if key else value

    def markdown(self, content, *_, **__):
        self.html.append(content)

    def __getattr__(self, name):
        if name in {"title", "set_page_config", "image", "warning", "error", "caption", "stop"}:
            return lambda *_, **__: None
        raise AttributeError(name)


class AppSmokeTests(unittest.TestCase):
    def run_fake(self, return_mode="Retorno guiado", coupling_mode="Direto",
                 supply_mode="Motoredutor completo"):
        original = sys.modules.get("streamlit")
        fake = FakeStreamlit(return_mode, coupling_mode, supply_mode)
        try:
            sys.modules["streamlit"] = fake
            env = runpy.run_path(str(ROOT / "app.py"))
            return fake, env
        finally:
            if original is None:
                sys.modules.pop("streamlit", None)
            else:
                sys.modules["streamlit"] = original

    def test_all_eight_modes(self):
        for ret in ("Retorno guiado", "Retorno livre com flecha"):
            for connection in ("Direto", "Transmissão secundária por corrente"):
                for supply in ("Motoredutor completo", "Redutor e motor separados"):
                    with self.subTest(ret=ret, connection=connection, supply=supply):
                        fake, env = self.run_fake(ret, connection, supply)
                        conveyor = env["conveyor"]
                        self.assertGreater(conveyor.total_chain_mass_kg, 0)
                        self.assertGreater(env["drive"].reducer_output_power_kw, 0)
                        self.assertIn("gearmotor_kw" if supply == "Motoredutor completo"
                                      else "separate_motor_kw", fake.session_state)
                        self.assertEqual(fake.radio_options["Tipo de acionamento"],
                                         ["Motoredutor completo", "Redutor e motor separados"])
                        self.assertNotIn("4 · NECESSÁRIO × DISPONÍVEL", "".join(fake.html))
                        self.assertNotIn("Metodologia de cálculo", "".join(fake.html))
                        self.assertNotIn("Notas de engenharia e glossário", "".join(fake.html))

    def test_mass_friction_logic_and_layout(self):
        guided, env = self.run_fake()
        c = env["conveyor"]
        self.assertEqual(env["center_distance_m"], 4.5)
        self.assertEqual(env["conveyor_dp"], 202.66)
        self.assertAlmostEqual(c.top_chain_mass_kg, 131.4, places=5)
        self.assertAlmostEqual(c.return_chain_mass_kg, 131.4, places=5)
        self.assertAlmostEqual(c.top_supported_mass_kg, 407.4, places=5)
        self.assertAlmostEqual(c.top_friction_n, .35 * 407.4 * 9.81, places=5)
        self.assertAlmostEqual(c.return_friction_n, .25 * 131.4 * 9.81, places=5)
        html = "".join(guided.html)
        for label in ("Carga transportada", "Correntes superiores", "Massa apoiada",
                      "Atrito superior", "Correntes do retorno", "Atrito do retorno"):
            self.assertIn(label, html + " ".join(guided.text_labels))
        free, env_free = self.run_fake("Retorno livre com flecha")
        self.assertEqual(env_free["conveyor"].return_friction_n, 0)
        self.assertNotIn("Atrito do retorno μ_ret [-]", free.text_labels)
        self.assertNotIn("Atrito do retorno F_ret [N]", "".join(free.html))

    def test_two_way_motor_power(self):
        fake, env = self.run_fake()
        fake.session_state["gearmotor_kw"] = 11.
        env["power_from_kw"]("gearmotor")
        self.assertAlmostEqual(fake.session_state["gearmotor_cv"], 11 / .73549875)
        fake.session_state["gearmotor_cv"] = 2.5
        env["power_from_cv"]("gearmotor")
        self.assertAlmostEqual(fake.session_state["gearmotor_kw"], 2.5 * .73549875)


if __name__ == "__main__":
    unittest.main()
