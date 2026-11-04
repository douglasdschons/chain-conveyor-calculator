"""Dependency-free structural smoke check of every major UI branch.

This fake Streamlit facade is not a substitute for running a real Streamlit server;
it catches missing names and wrong control flow even in CI without streamlit.
"""
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
    def __init__(self, return_mode="Guided return", coupling_mode="Direct",
                 supply_mode="Complete gearmotor"):
        super().__init__("streamlit")
        self.session_state = {}
        self.return_mode = return_mode
        self.coupling_mode = coupling_mode
        self.supply_mode = supply_mode

    def columns(self, specs, **_):
        return [FakeContext() for _ in range(specs if isinstance(specs, int) else len(specs))]

    def expander(self, *_, **__):
        return FakeContext()

    def empty(self):
        return FakeContext()

    def number_input(self, label, *_, **kwargs):
        key = kwargs.get("key")
        if key is not None and key in self.session_state:
            return self.session_state[key]
        value = kwargs.get("value", kwargs.get("min_value", 0.0))
        if key is not None:
            self.session_state[key] = value
        return value

    def selectbox(self, label, options, *_, **kwargs):
        if label == "Return type":
            return self.return_mode
        key = kwargs.get("key")
        value = options[kwargs.get("index", 0)]
        if key:
            self.session_state.setdefault(key, value)
            return self.session_state[key]
        return value

    def radio(self, label, options, *_, **__):
        return {"Connection": self.coupling_mode,
                "Supply mode": self.supply_mode}.get(label, options[0])

    def toggle(self, label, *_, **kwargs):
        return kwargs.get("value", False)

    def text_input(self, label, value="", *_, **__):
        return value

    def __getattr__(self, name):
        if name in {"title", "set_page_config", "markdown", "image", "warning",
                    "caption", "latex", "dataframe", "info", "error"}:
            return lambda *_, **__: None
        raise AttributeError(name)


class AppSmokeTests(unittest.TestCase):
    def test_all_four_input_branches(self):
        saved = sys.modules.get("streamlit")
        try:
            for ret in ("Guided return", "Sag return"):
                for coupling in ("Direct", "Secondary chain transmission"):
                    for supply in ("IBR Q catalogue", "Complete gearmotor", "Separate gearbox + motor"):
                        with self.subTest(ret=ret, coupling=coupling, supply=supply):
                            fake = FakeStreamlit(ret, coupling, supply)
                            sys.modules["streamlit"] = fake
                            env = runpy.run_path(str(ROOT / "app.py"))
                            self.assertGreater(env["conveyor"].total_chain_mass_kg, 0)
                            self.assertGreater(env["final_output"].axis_power_kw, 0)
                            prefix = ("ibr_motor" if supply == "IBR Q catalogue" else
                                      "gearmotor" if supply == "Complete gearmotor" else "separate_motor")
                            self.assertIn(prefix + "_kw", fake.session_state)
                            self.assertIn(prefix + "_cv", fake.session_state)
        finally:
            if saved is None:
                sys.modules.pop("streamlit", None)
            else:
                sys.modules["streamlit"] = saved

    def test_bidirectional_callback_state(self):
        saved = sys.modules.get("streamlit")
        try:
            fake = FakeStreamlit()
            sys.modules["streamlit"] = fake
            env = runpy.run_path(str(ROOT / "app.py"))
            fake.session_state["gearmotor_kw"] = 11.0
            env["power_from_kw"]("gearmotor")
            self.assertAlmostEqual(fake.session_state["gearmotor_cv"], 11/.73549875)
            fake.session_state["gearmotor_cv"] = 5.0
            env["power_from_cv"]("gearmotor")
            self.assertAlmostEqual(fake.session_state["gearmotor_kw"], 5*.73549875)
        finally:
            if saved is None:
                sys.modules.pop("streamlit", None)
            else:
                sys.modules["streamlit"] = saved


if __name__ == "__main__":
    unittest.main()
