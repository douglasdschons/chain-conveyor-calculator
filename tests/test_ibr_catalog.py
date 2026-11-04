import unittest
from math import pi

from src.ibr_catalog import (
    CATALOG, SERVICE_FACTORS, candidates_for_speed, catalogue_radial_force,
    evaluate_ibr_q, get_ibr_q, required_service_factor,
)
from src.calculations import ConveyorInput, calculate_conveyor


class IBRCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.q090 = get_ibr_q('090', 40)
        self.system = calculate_conveyor(ConveyorInput(
            center_distance_m=4.15554, strands=4, chain_mass_per_m_kg=7.3,
            inclination_deg=0, conveyor_sprocket_pitch_diameter_mm=260,
            return_type='Guiado', return_sag_mm=80, mu_top=.35,
            mu_return=.25, load_mass_kg=276,
            linear_speed_m_min=35, additional_process_force_n=0,
            acceleration_time_s=3, design_factor=1.5,
        ))

    def test_q090_catalogue_row_page14(self):
        r = self.q090
        self.assertEqual(r.catalogue_motor_cv, 3)
        self.assertEqual(r.catalogue_output_rpm, 42.5)
        self.assertEqual(r.catalogue_output_torque_nm, 366.8)
        self.assertEqual(r.nominal_torque_nm, 403)
        self.assertEqual(r.efficiency_pct, 74)
        self.assertEqual(r.admissible_radial_output_n, 4580)

    def test_motor_torque_matches_catalogue(self):
        p = evaluate_ibr_q(self.q090, 3.0, 1700)
        self.assertAlmostEqual(p.output_rpm, 42.5)
        self.assertAlmostEqual(p.output_torque_nm, 366.8, delta=.15)
        self.assertAlmostEqual(p.service_factor_motor, 403/366.8, delta=.002)
        self.assertTrue(p.within_catalogue_motor_limit)

    def test_35m_min_demand_and_direct_selection(self):
        p = evaluate_ibr_q(self.q090, 3., 1700)
        v = pi * .26 * p.output_rpm
        self.assertAlmostEqual(v, 34.7145988, places=4)
        self.assertAlmostEqual(self.system.required_axis_torque_nm, 344.6345, delta=.01)
        self.assertGreater(p.output_torque_nm, self.system.required_axis_torque_nm)
        self.assertGreater(p.output_power_kw, self.system.required_axis_power_kw)
        self.assertLess(abs(v / 35 - 1), .01)

    def test_duty_table(self):
        self.assertEqual(len(SERVICE_FACTORS), 18)
        self.assertEqual(required_service_factor('<10', 'Moderate shocks', '2–10'), 1.25)
        self.assertEqual(required_service_factor('>10', 'Severe shocks', '>10'), 2.0)
        self.assertLess(evaluate_ibr_q(self.q090, 3).service_factor_motor, 1.25)

    def test_q110_3cv_as_service_alternative(self):
        perf = evaluate_ibr_q(get_ibr_q('110', 40), 3, 1700)
        self.assertAlmostEqual(perf.output_torque_nm, 391.55, delta=.4)
        self.assertGreater(perf.output_torque_nm, self.system.required_axis_torque_nm)
        self.assertGreater(perf.service_factor_motor, 1.25)
        self.assertTrue(perf.within_catalogue_motor_limit)

    def test_catalogue_radial_coefficient_chain(self):
        # 3 cv Q090, output sprocket 170 mm, p=1; catalog estimate > FR2.
        radial = catalogue_radial_force(366.8, 170, 1.25, 1.0)
        self.assertAlmostEqual(radial, 5394.117647, places=4)
        self.assertGreater(radial, self.q090.admissible_radial_output_n)
        self.assertAlmostEqual(catalogue_radial_force(366.8,170,1.25,1.5), 1.5*radial)

    def test_direct_speed_candidates_include_q090(self):
        options = candidates_for_speed(35, 260)
        self.assertIn(self.q090, options)
        self.assertNotIn(get_ibr_q('090', 30), options)

    def test_user_provided_catalogue_excerpt_is_partial(self):
        self.assertEqual(len(CATALOG),15)


if __name__ == '__main__':
    unittest.main()
