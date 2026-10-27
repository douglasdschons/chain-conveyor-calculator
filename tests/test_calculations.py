import unittest

from src.calculations import (
    ConveyorInput,
    SecondaryTransmissionInput,
    calculate_conveyor,
    calculate_secondary_requirement,
)


class ConveyorCalculationTests(unittest.TestCase):
    def setUp(self):
        self.base = ConveyorInput(
            center_distance_m=4.15554,
            strands=4,
            chain_mass_per_m_kg=7.30,
            inclination_deg=0.0,
            conveyor_sprocket_pitch_diameter_mm=260.0,
            return_type="Guiado",
            return_sag_mm=80.0,
            mu_top=0.40,
            mu_return=0.25,
            load_mass_kg=276.0,
            linear_speed_m_min=32.0,
            additional_process_force_n=0.0,
            acceleration_time_s=3.0,
            design_factor=1.50,
        )

    def test_guided_return_has_return_friction(self):
        result = calculate_conveyor(self.base)
        self.assertGreater(result.return_friction_n, 0.0)
        self.assertIsNone(result.catenary_tension_n)

    def test_free_return_has_catenary_and_no_return_friction(self):
        free = ConveyorInput(**{**self.base.__dict__, "return_type": "Livre"})
        result = calculate_conveyor(free)
        self.assertEqual(result.return_friction_n, 0.0)
        self.assertIsNotNone(result.catenary_tension_n)
        self.assertGreater(result.catenary_tension_n, 0.0)

    def test_secondary_requirement(self):
        result = calculate_conveyor(self.base)
        transmission = SecondaryTransmissionInput(
            coupling_type="Transmissão secundária",
            reducer_sprocket_pitch_diameter_mm=170.0,
            shaft_sprocket_pitch_diameter_mm=202.66,
            efficiency_pct=98.0,
        )
        req = calculate_secondary_requirement(
            result.required_axis_speed_rpm,
            result.required_axis_torque_nm,
            result.required_axis_power_kw,
            transmission,
        )
        self.assertGreater(req.ratio, 1.0)
        self.assertGreater(req.required_reducer_speed_rpm, result.required_axis_speed_rpm)
        self.assertLess(req.required_reducer_torque_nm, result.required_axis_torque_nm)


if __name__ == "__main__":
    unittest.main()
