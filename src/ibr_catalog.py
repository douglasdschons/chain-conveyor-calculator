"""IBR Q reducer selection — curated catalog excerpt provided by the user.

Source: 'IBR pgs.pdf', printed catalog pages 4, 5, 9, 13 and 14.
Only frame sizes 075/090/110/130/150 and ratios 30/40/50 have been
transcribed. These values must NOT be treated as the full manufacturer range.

The catalog's printed page 9 accidentally inverts its service-factor equation:
page 4 defines fs=M2Nom/M2M, consistent with all tabulated data.
The printed linear-power 'cv' equation on page 5 is dimensionally kW; use SI.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import pi

from .calculations import CV_TO_KW


@dataclass(frozen=True)
class IBRQRow:
    size: str
    ratio: float
    catalogue_motor_cv: float
    catalogue_output_rpm: float
    catalogue_output_torque_nm: float
    catalogue_service_factor: float
    nominal_input_cv: float
    nominal_torque_nm: float
    efficiency_pct: float
    admissible_radial_input_n: float
    admissible_radial_output_n: float


@dataclass(frozen=True)
class IBRQPerformance:
    output_rpm: float
    motor_power_cv: float
    motor_power_kw: float
    output_torque_nm: float
    output_power_kw: float
    nominal_torque_nm: float
    service_factor_motor: float
    admissible_radial_output_n: float
    within_catalogue_motor_limit: bool
    within_nominal_input_limit: bool
    within_nominal_torque_limit: bool


# size ratio PMot n2 M2M fs PNom M2Nom eta FR1 FR2
# Comma decimal separators converted to standard Python decimal points.
_TABLE = '''
075 30 2 56.7 193.2 1.4 2.86 276 78 830 3740
075 40 2 42.5 241.2 1.1 2.20 265 73 830 4120
075 50 1.5 34.0 216.9 1.1 1.64 238 70 830 4380
090 30 4 56.7 396.5 1.05 4.22 418 80 1010 4100
090 40 3 42.5 366.8 1.1 3.29 403 74 1010 4580
090 50 2 34.0 297.4 1.2 2.42 360 72 1010 4900
110 30 6 56.7 601.9 1.2 7.35 737 81 1350 5100
110 40 5 42.5 652.6 1.1 5.48 715 79 1350 5630
110 50 3 34.0 477.1 1.4 4.18 664 77 1350 6120
130 30 10 56.7 1015.5 1.1 11.01 1118 82 1820 7580
130 40 7.5 42.5 991.3 1.2 9.07 1199 80 1820 8300
130 50 6 34.0 941.8 1.1 6.59 1035 76 1820 8880
150 30 12.5 56.7 1253.9 1.2 15.13 1518 81 2620 10770
150 40 10 42.5 1305.3 1.2 12.09 1579 79 2620 11820
150 50 7.5 34.0 1146.2 1.3 9.90 1513 74 2620 12790
'''.strip()


def _parse() -> dict[tuple[str, float], IBRQRow]:
    result: dict[tuple[str, float], IBRQRow] = {}
    for line in _TABLE.splitlines():
        fields = line.split()
        size = fields[0]
        numbers = [float(x) for x in fields[1:]]
        row = IBRQRow(size, *numbers)
        result[(size, row.ratio)] = row
    return result


CATALOG = _parse()
SIZES = tuple(sorted({size for size, _ in CATALOG}))
RATIOS = (30.0, 40.0, 50.0)

# IBR printed page 4, rows=starts/hour, duty type; cols=operating hours/day
SERVICE_FACTORS: dict[tuple[str, str, str], float] = {}
for starts, duty, ratings in (
    ('<10', 'Uniform load', (0.9, 1.0, 1.25)),
    ('<10', 'Moderate shocks', (1.0, 1.25, 1.5)),
    ('<10', 'Severe shocks', (1.25, 1.5, 1.75)),
    ('>10', 'Uniform load', (1.0, 1.25, 1.5)),
    ('>10', 'Moderate shocks', (1.25, 1.5, 1.75)),
    ('>10', 'Severe shocks', (1.5, 1.75, 2.0)),
):
    for hours, factor in zip(('<2', '2–10', '>10'), ratings):
        SERVICE_FACTORS[(starts, duty, hours)] = factor


def get_ibr_q(size: str, ratio: float) -> IBRQRow:
    return CATALOG[(size, float(ratio))]


def required_service_factor(starts: str, duty: str, hours: str) -> float:
    return SERVICE_FACTORS[(starts, duty, hours)]


def evaluate_ibr_q(row: IBRQRow, motor_cv: float, motor_rpm: float = 1700.0) -> IBRQPerformance:
    """Evaluate selected motor against a catalog gearbox.

    Per IBR p.5: M2M=7022 * PMot(cv) * eta_fraction / n2(rpm).
    Model assumes nominal steady output and fixed catalog efficiency;
    efficiency/thermal/transient behavior must be confirmed with the maker.
    """
    if motor_cv <= 0 or motor_rpm <= 0:
        raise ValueError('Motor power and speed must be positive.')
    n2 = motor_rpm / row.ratio
    power_kw = motor_cv * CV_TO_KW
    torque = 7022.0 * motor_cv * (row.efficiency_pct / 100.0) / n2
    output_kw = 2 * pi * n2 * torque / 60 / 1000
    return IBRQPerformance(
        output_rpm=n2,
        motor_power_cv=motor_cv,
        motor_power_kw=power_kw,
        output_torque_nm=torque,
        output_power_kw=output_kw,
        nominal_torque_nm=row.nominal_torque_nm,
        service_factor_motor=row.nominal_torque_nm / torque,
        admissible_radial_output_n=row.admissible_radial_output_n,
        within_catalogue_motor_limit=motor_cv <= row.catalogue_motor_cv + 1e-8,
        within_nominal_input_limit=motor_cv <= row.nominal_input_cv + 1e-8,
        within_nominal_torque_limit=torque <= row.nominal_torque_nm + 1e-8,
    )


def catalogue_radial_force(
    output_torque_nm: float,
    sprocket_pitch_mm: float,
    transmission_factor: float = 1.25,
    application_point_factor: float = 1.0,
) -> float:
    """IBR p.5 radial *estimate* for output sprocket; not a vectorial solution.

    Defaults: secondary chain and centered manufacturer load application.
    Check geometric definition of application point vs keyway center.
    """
    if sprocket_pitch_mm <= 0 or output_torque_nm < 0:
        raise ValueError('Sprocket diameter must be positive and torque non-negative.')
    if transmission_factor <= 0 or application_point_factor <= 0:
        raise ValueError('Radial factors must be positive.')
    return (2000.0 * output_torque_nm / sprocket_pitch_mm
            * transmission_factor * application_point_factor)


def candidates_for_speed(
    speed_m_min: float,
    conveyor_pitch_mm: float,
    motor_rpm: float = 1700.0,
    tolerance_fraction: float = 0.05,
) -> list[IBRQRow]:
    """Return catalog entries meeting the nominated shaft speed, direct drive ONLY."""
    if speed_m_min <= 0 or conveyor_pitch_mm <= 0 or motor_rpm <= 0:
        raise ValueError('Positive desired speed, diameter and motor rpm required.')
    target_rpm = speed_m_min / (pi * conveyor_pitch_mm / 1000.0)
    return [row for row in CATALOG.values()
            if abs(motor_rpm / row.ratio / target_rpm - 1) <= tolerance_fraction]
