from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, radians, sin, sqrt


G = 9.81
KW_TO_CV = 1 / 0.7355


@dataclass(frozen=True)
class ConveyorInput:
    center_distance_m: float
    strands: int
    chain_mass_per_m_kg: float
    inclination_deg: float
    conveyor_sprocket_pitch_diameter_mm: float
    return_type: str  # "Guiado" or "Livre"
    return_sag_mm: float
    mu_top: float
    mu_return: float
    load_mass_kg: float
    linear_speed_m_min: float
    additional_process_force_n: float
    acceleration_time_s: float
    design_factor: float


@dataclass(frozen=True)
class ConveyorResult:
    return_length_m: float
    total_chain_mass_kg: float
    top_chain_mass_kg: float
    return_chain_mass_kg: float
    top_friction_n: float
    return_friction_n: float
    inclination_force_n: float
    regime_force_n: float
    moving_mass_kg: float
    acceleration_m_s2: float
    acceleration_force_n: float
    force_before_design_factor_n: float
    design_force_n: float
    force_per_strand_n: float
    required_axis_speed_rpm: float
    required_axis_torque_nm: float
    required_axis_power_kw: float
    required_axis_power_cv: float
    catenary_horizontal_n: float | None
    catenary_vertical_n: float | None
    catenary_tension_n: float | None


@dataclass(frozen=True)
class SecondaryTransmissionInput:
    coupling_type: str  # "Direto" or "Transmissão secundária"
    reducer_sprocket_pitch_diameter_mm: float
    shaft_sprocket_pitch_diameter_mm: float
    efficiency_pct: float


@dataclass(frozen=True)
class SecondaryTransmissionRequirement:
    ratio: float
    required_reducer_speed_rpm: float
    required_reducer_torque_nm: float
    required_reducer_power_kw: float


@dataclass(frozen=True)
class CompleteGearmotorInput:
    manufacturer: str
    model: str
    motor_power_kw: float
    motor_speed_rpm: float
    output_speed_rpm: float
    total_ratio: float
    output_torque_nm: float
    admissible_radial_force_n: float
    manufacturer_service_factor: float


@dataclass(frozen=True)
class SeparateDriveInput:
    reducer_manufacturer: str
    reducer_model: str
    reducer_ratio: float
    reducer_efficiency_pct: float
    reducer_max_torque_nm: float
    reducer_admissible_radial_force_n: float
    reducer_max_input_power_kw: float
    motor_manufacturer: str
    motor_model: str
    motor_power_kw: float
    motor_speed_rpm: float
    motor_efficiency_pct: float
    nominal_frequency_hz: float
    operating_frequency_hz: float


@dataclass(frozen=True)
class DriveOutput:
    reducer_output_speed_rpm: float
    reducer_output_torque_nm: float
    reducer_output_power_kw: float
    admissible_radial_force_n: float


@dataclass(frozen=True)
class FinalOutput:
    axis_speed_rpm: float
    axis_torque_nm: float
    axis_power_kw: float
    linear_speed_m_min: float
    radial_tangential_force_n: float | None
    critical_pitch_diameter_mm: float | None


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} deve ser maior que zero.")


def return_length(center_distance_m: float, return_type: str, sag_mm: float) -> float:
    _validate_positive(center_distance_m, "Distância entre centros")
    if return_type == "Guiado":
        return center_distance_m
    if return_type != "Livre":
        raise ValueError("Tipo de retorno inválido.")
    sag_m = sag_mm / 1000.0
    _validate_positive(sag_m, "Flecha")
    # Aproximação parabólica de pequeno/médio abaulamento.
    return center_distance_m + (8.0 * sag_m**2) / (3.0 * center_distance_m)


def calculate_conveyor(data: ConveyorInput) -> ConveyorResult:
    _validate_positive(data.center_distance_m, "Distância entre centros")
    _validate_positive(data.strands, "Quantidade de vias")
    _validate_positive(data.chain_mass_per_m_kg, "Massa linear da corrente")
    _validate_positive(data.conveyor_sprocket_pitch_diameter_mm, "Diâmetro primitivo")
    _validate_positive(data.load_mass_kg, "Massa transportada")
    _validate_positive(data.linear_speed_m_min, "Velocidade linear")
    _validate_positive(data.design_factor, "Fator de projeto")

    alpha = radians(data.inclination_deg)
    diameter_m = data.conveyor_sprocket_pitch_diameter_mm / 1000.0
    return_len = return_length(data.center_distance_m, data.return_type, data.return_sag_mm)

    top_chain_mass = (
        data.center_distance_m * data.chain_mass_per_m_kg * data.strands
    )
    return_chain_mass = return_len * data.chain_mass_per_m_kg * data.strands
    arc_length_per_strand = pi * diameter_m
    arc_chain_mass = arc_length_per_strand * data.chain_mass_per_m_kg * data.strands
    total_chain_mass = top_chain_mass + return_chain_mass + arc_chain_mass

    top_friction = (
        data.mu_top
        * (data.load_mass_kg + top_chain_mass)
        * G
        * cos(alpha)
    )
    return_friction = 0.0
    if data.return_type == "Guiado":
        return_friction = (
            data.mu_return * return_chain_mass * G * cos(alpha)
        )

    inclination_force = data.load_mass_kg * G * sin(alpha)
    regime_force = (
        top_friction
        + return_friction
        + inclination_force
        + data.additional_process_force_n
    )

    moving_mass = data.load_mass_kg + total_chain_mass
    acceleration = 0.0
    if data.acceleration_time_s > 0:
        acceleration = (data.linear_speed_m_min / 60.0) / data.acceleration_time_s
    acceleration_force = moving_mass * acceleration

    force_before_df = regime_force + acceleration_force
    design_force = force_before_df * data.design_factor
    force_per_strand = design_force / data.strands

    axis_speed = data.linear_speed_m_min / (pi * diameter_m)
    axis_torque = design_force * diameter_m / 2.0
    axis_power = design_force * (data.linear_speed_m_min / 60.0) / 1000.0

    h = v = t = None
    if data.return_type == "Livre":
        sag_m = data.return_sag_mm / 1000.0
        w = data.chain_mass_per_m_kg * G
        h = w * data.center_distance_m**2 / (8.0 * sag_m)
        v = w * data.center_distance_m / 2.0
        t = sqrt(h**2 + v**2)

    return ConveyorResult(
        return_length_m=return_len,
        total_chain_mass_kg=total_chain_mass,
        top_chain_mass_kg=top_chain_mass,
        return_chain_mass_kg=return_chain_mass,
        top_friction_n=top_friction,
        return_friction_n=return_friction,
        inclination_force_n=inclination_force,
        regime_force_n=regime_force,
        moving_mass_kg=moving_mass,
        acceleration_m_s2=acceleration,
        acceleration_force_n=acceleration_force,
        force_before_design_factor_n=force_before_df,
        design_force_n=design_force,
        force_per_strand_n=force_per_strand,
        required_axis_speed_rpm=axis_speed,
        required_axis_torque_nm=axis_torque,
        required_axis_power_kw=axis_power,
        required_axis_power_cv=axis_power * KW_TO_CV,
        catenary_horizontal_n=h,
        catenary_vertical_n=v,
        catenary_tension_n=t,
    )


def calculate_secondary_requirement(
    axis_speed_rpm: float,
    axis_torque_nm: float,
    axis_power_kw: float,
    transmission: SecondaryTransmissionInput,
) -> SecondaryTransmissionRequirement:
    if transmission.coupling_type == "Direto":
        return SecondaryTransmissionRequirement(
            ratio=1.0,
            required_reducer_speed_rpm=axis_speed_rpm,
            required_reducer_torque_nm=axis_torque_nm,
            required_reducer_power_kw=axis_power_kw,
        )

    if transmission.coupling_type != "Transmissão secundária":
        raise ValueError("Tipo de acoplamento inválido.")

    _validate_positive(
        transmission.reducer_sprocket_pitch_diameter_mm,
        "Ø primitivo da roda no redutor",
    )
    _validate_positive(
        transmission.shaft_sprocket_pitch_diameter_mm,
        "Ø primitivo da roda no eixo",
    )
    _validate_positive(transmission.efficiency_pct, "Rendimento da transmissão")

    ratio = (
        transmission.shaft_sprocket_pitch_diameter_mm
        / transmission.reducer_sprocket_pitch_diameter_mm
    )
    eta = transmission.efficiency_pct / 100.0

    return SecondaryTransmissionRequirement(
        ratio=ratio,
        required_reducer_speed_rpm=axis_speed_rpm * ratio,
        required_reducer_torque_nm=axis_torque_nm / (ratio * eta),
        required_reducer_power_kw=axis_power_kw / eta,
    )


def complete_gearmotor_output(data: CompleteGearmotorInput) -> DriveOutput:
    _validate_positive(data.output_speed_rpm, "Rotação de saída")
    _validate_positive(data.output_torque_nm, "Torque de saída")
    power_kw = (
        data.output_torque_nm
        * 2.0
        * pi
        * data.output_speed_rpm
        / 60.0
        / 1000.0
    )
    return DriveOutput(
        reducer_output_speed_rpm=data.output_speed_rpm,
        reducer_output_torque_nm=data.output_torque_nm,
        reducer_output_power_kw=power_kw,
        admissible_radial_force_n=data.admissible_radial_force_n,
    )


def separate_drive_output(data: SeparateDriveInput) -> DriveOutput:
    _validate_positive(data.reducer_ratio, "Redução do redutor")
    _validate_positive(data.reducer_efficiency_pct, "Rendimento do redutor")
    _validate_positive(data.motor_speed_rpm, "Rotação do motor")
    _validate_positive(data.nominal_frequency_hz, "Frequência nominal")
    _validate_positive(data.operating_frequency_hz, "Frequência de operação")

    operating_speed = (
        data.motor_speed_rpm
        * data.operating_frequency_hz
        / data.nominal_frequency_hz
    )

    # Modelo simplificado de VFD:
    # abaixo da frequência base: torque aproximadamente constante;
    # acima da base: potência aproximadamente constante.
    if data.operating_frequency_hz <= data.nominal_frequency_hz:
        motor_power_kw = (
            data.motor_power_kw
            * data.operating_frequency_hz
            / data.nominal_frequency_hz
        )
    else:
        motor_power_kw = data.motor_power_kw

    if data.reducer_max_input_power_kw > 0:
        motor_power_kw = min(motor_power_kw, data.reducer_max_input_power_kw)

    motor_torque_nm = 9550.0 * motor_power_kw / operating_speed
    eta = data.reducer_efficiency_pct / 100.0

    reducer_speed = operating_speed / data.reducer_ratio
    theoretical_torque = motor_torque_nm * data.reducer_ratio * eta
    available_torque = theoretical_torque
    if data.reducer_max_torque_nm > 0:
        available_torque = min(theoretical_torque, data.reducer_max_torque_nm)

    available_power = (
        available_torque
        * 2.0
        * pi
        * reducer_speed
        / 60.0
        / 1000.0
    )

    return DriveOutput(
        reducer_output_speed_rpm=reducer_speed,
        reducer_output_torque_nm=available_torque,
        reducer_output_power_kw=available_power,
        admissible_radial_force_n=data.reducer_admissible_radial_force_n,
    )


def calculate_final_output(
    drive: DriveOutput,
    transmission: SecondaryTransmissionInput,
    conveyor_pitch_diameter_mm: float,
) -> FinalOutput:
    diameter_m = conveyor_pitch_diameter_mm / 1000.0

    if transmission.coupling_type == "Direto":
        axis_speed = drive.reducer_output_speed_rpm
        axis_torque = drive.reducer_output_torque_nm
        axis_power = drive.reducer_output_power_kw
        radial_force = None
        critical_dp = None
    else:
        ratio = (
            transmission.shaft_sprocket_pitch_diameter_mm
            / transmission.reducer_sprocket_pitch_diameter_mm
        )
        eta = transmission.efficiency_pct / 100.0
        axis_speed = drive.reducer_output_speed_rpm / ratio
        axis_torque = drive.reducer_output_torque_nm * ratio * eta
        axis_power = (
            axis_torque * 2.0 * pi * axis_speed / 60.0 / 1000.0
        )

        dp1_m = transmission.reducer_sprocket_pitch_diameter_mm / 1000.0
        radial_force = 2.0 * drive.reducer_output_torque_nm / dp1_m

        critical_dp = None
        if drive.admissible_radial_force_n > 0:
            critical_dp = (
                2.0
                * drive.reducer_output_torque_nm
                / drive.admissible_radial_force_n
                * 1000.0
            )

    linear_speed = pi * diameter_m * axis_speed

    return FinalOutput(
        axis_speed_rpm=axis_speed,
        axis_torque_nm=axis_torque,
        axis_power_kw=axis_power,
        linear_speed_m_min=linear_speed,
        radial_tangential_force_n=radial_force,
        critical_pitch_diameter_mm=critical_dp,
    )


def rectangular_mass(base_m: float, height_m: float, length_m: float, density_kg_m3: float) -> tuple[float, float]:
    volume = base_m * height_m * length_m
    return volume, volume * density_kg_m3


def cylindrical_mass(diameter_m: float, length_m: float, density_kg_m3: float) -> tuple[float, float]:
    volume = pi * diameter_m**2 / 4.0 * length_m
    return volume, volume * density_kg_m3
