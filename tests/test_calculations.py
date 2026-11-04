"""Regression and unit tests for Chain Conveyor Calculator."""
import unittest
from dataclasses import replace
from math import pi

from src.calculations import (
    ConveyorInput,
    SecondaryTransmissionInput,
    CompleteGearmotorInput,
    SeparateDriveInput,
    calculate_conveyor,
    calculate_secondary_requirement,
    calculate_final_output,
    complete_gearmotor_output,
    separate_drive_output,
    return_length,
    kw_to_cv,
    cv_to_kw,
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
            mu_top=0.35,
            mu_return=0.25,
            load_mass_kg=276.0,
            linear_speed_m_min=32.0,
            additional_process_force_n=0.0,
            acceleration_time_s=3.0,
            design_factor=1.50,
        )

    def test_guided_mass_balance_and_equal_straight_spans(self):
        v = calculate_conveyor(self.base)
        self.assertAlmostEqual(v.top_chain_mass_kg, 121.341768, places=5)
        self.assertAlmostEqual(v.return_chain_mass_kg, v.top_chain_mass_kg)
        self.assertAlmostEqual(v.arc_chain_mass_kg, pi*.26*7.3*4)
        self.assertAlmostEqual(v.total_chain_mass_kg, 266.5345074, places=5)
        self.assertAlmostEqual(v.top_supported_mass_kg, 397.341768, places=5)
        self.assertAlmostEqual(v.total_chain_mass_kg,
                               v.top_chain_mass_kg + v.return_chain_mass_kg + v.arc_chain_mass_kg)

    def test_guided_friction_is_distinct_and_correct(self):
        v = calculate_conveyor(self.base)
        self.assertAlmostEqual(v.top_friction_n, 1364.2729604, places=4)
        self.assertAlmostEqual(v.return_friction_n, 297.59068602, places=4)
        self.assertAlmostEqual(v.regime_force_n, 1661.8636464, places=4)
        self.assertNotEqual(v.top_friction_n, v.return_friction_n)
        self.assertIsNone(v.catenary_tension_n)

    def test_case_regression_force_torque_power_speed(self):
        v = calculate_conveyor(self.base)
        self.assertAlmostEqual(v.acceleration_force_n, 96.4505791, places=4)
        self.assertAlmostEqual(v.design_force_n, 2637.4713383, places=4)
        self.assertAlmostEqual(v.force_per_strand_n, 659.3678345, places=4)
        self.assertAlmostEqual(v.required_axis_torque_nm, 342.8712740, places=4)
        self.assertAlmostEqual(v.required_axis_power_kw, 1.40665138, places=5)
        self.assertAlmostEqual(v.required_axis_speed_rpm, 32/(pi*.26), places=5)

    def test_sag_return_increases_mass_but_no_guided_return_friction(self):
        v = calculate_conveyor(replace(self.base, return_type="Livre"))
        self.assertGreater(v.return_length_m, self.base.center_distance_m)
        self.assertGreater(v.return_chain_mass_kg, v.top_chain_mass_kg)
        self.assertEqual(v.return_friction_n, 0.0)
        self.assertIsNotNone(v.catenary_tension_n)
        self.assertGreater(v.catenary_tension_n, 0.0)
        self.assertAlmostEqual(v.top_friction_n, 1364.2729604, places=4)

    def test_no_acceleration_and_design_factor_applied_once(self):
        normal = calculate_conveyor(replace(self.base, acceleration_time_s=0.0, design_factor=1.0))
        amplified = calculate_conveyor(replace(self.base, acceleration_time_s=0.0, design_factor=1.5))
        self.assertEqual(normal.acceleration_force_n, 0.0)
        self.assertAlmostEqual(amplified.design_force_n, 1.5 * normal.design_force_n)
        self.assertAlmostEqual(amplified.required_axis_torque_nm, 1.5 * normal.required_axis_torque_nm)
        self.assertAlmostEqual(amplified.required_axis_power_kw, 1.5 * normal.required_axis_power_kw)

    def test_secondary_requirement(self):
        v = calculate_conveyor(self.base)
        sec = SecondaryTransmissionInput("Transmissão secundária", 170., 202.66, 98.)
        req = calculate_secondary_requirement(v.required_axis_speed_rpm,
                                               v.required_axis_torque_nm,
                                               v.required_axis_power_kw, sec)
        self.assertAlmostEqual(req.ratio, 202.66/170)
        self.assertGreater(req.required_reducer_speed_rpm, v.required_axis_speed_rpm)
        self.assertLess(req.required_reducer_torque_nm, v.required_axis_torque_nm)
        self.assertAlmostEqual(req.required_reducer_power_kw, v.required_axis_power_kw/.98)

    def test_direct_requirement(self):
        v = calculate_conveyor(self.base)
        sec = SecondaryTransmissionInput("Direto", 1., 1., 100.)
        req = calculate_secondary_requirement(v.required_axis_speed_rpm,
                                               v.required_axis_torque_nm,
                                               v.required_axis_power_kw, sec)
        self.assertEqual(req.ratio, 1)
        self.assertAlmostEqual(req.required_reducer_torque_nm, v.required_axis_torque_nm)

    def test_kw_cv_bidirectional_roundtrip(self):
        for kw in (0, .75, 1.5, 15, 75):
            self.assertAlmostEqual(cv_to_kw(kw_to_cv(kw)), kw, places=12)
        self.assertAlmostEqual(cv_to_kw(1.), .73549875, places=8)
        self.assertAlmostEqual(kw_to_cv(1.), 1.3596216, places=6)

    def test_complete_gearmotor_available_power_from_output_rpm_torque(self):
        drive = complete_gearmotor_output(CompleteGearmotorInput(
            "SEW", "example", 15., 1777., 79., 22.37, 1790., 15600., 1.50))
        self.assertAlmostEqual(drive.reducer_output_power_kw, 2*pi*79*1790/60000)

    def test_secondary_tangential_force_is_not_labelled_radial_result(self):
        drive = complete_gearmotor_output(CompleteGearmotorInput(
            "SEW", "example", 15., 1777., 79., 22.37, 1790., 15600., 1.50))
        sec = SecondaryTransmissionInput("Transmissão secundária", 170., 202.66, 98.)
        out = calculate_final_output(drive, sec, 260.)
        self.assertAlmostEqual(out.radial_tangential_force_n, 2*1790/.170)
        self.assertGreater(out.radial_tangential_force_n, 0)

    def test_invalid_efficiency(self):
        sec = SecondaryTransmissionInput("Transmissão secundária", 170., 202.66, 120.)
        with self.assertRaises(ValueError):
            calculate_secondary_requirement(39., 343., 1.4, sec)


if __name__ == "__main__":
    unittest.main()
