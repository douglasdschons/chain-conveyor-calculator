from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from src.calculations import (
    CompleteGearmotorInput,
    ConveyorInput,
    SecondaryTransmissionInput,
    SeparateDriveInput,
    calculate_conveyor,
    calculate_final_output,
    calculate_secondary_requirement,
    complete_gearmotor_output,
    cylindrical_mass,
    rectangular_mass,
    separate_drive_output,
)


st.set_page_config(
    page_title="Calculadora de Transportador por Correntes",
    page_icon="⚙️",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {max-width: 1500px; padding-top: 1.5rem; padding-bottom: 3rem;}
        h1 {margin-bottom: 0.15rem;}
        .app-subtitle {color: #667085; margin-bottom: 1.2rem; font-size: 0.98rem;}
        .section-kicker {color: #667085; font-size: 0.80rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; margin-bottom: .1rem;}
        .section-title {font-size: 1.45rem; font-weight: 700; margin: 0 0 .65rem 0;}
        .engineering-card {border: 1px solid #E4E7EC; border-radius: 10px; padding: .9rem 1rem; background: #FFFFFF; margin-bottom: .75rem;}
        .engineering-card .label {color: #667085; font-size: .80rem; margin-bottom: .1rem;}
        .engineering-card .value {color: #101828; font-size: 1.30rem; font-weight: 700;}
        .engineering-card .sub {color: #667085; font-size: .78rem; margin-top: .15rem;}
        .status-ok {color: #067647; background: #ECFDF3; border: 1px solid #ABEFC6; border-radius: 999px; padding: .20rem .55rem; font-weight: 700; font-size: .78rem;}
        .status-warn {color: #B54708; background: #FFFAEB; border: 1px solid #FEDF89; border-radius: 999px; padding: .20rem .55rem; font-weight: 700; font-size: .78rem;}
        .status-bad {color: #B42318; background: #FEF3F2; border: 1px solid #FECDCA; border-radius: 999px; padding: .20rem .55rem; font-weight: 700; font-size: .78rem;}
        .soft-note {background: #F8FAFC; border-left: 4px solid #98A2B3; padding: .75rem .9rem; border-radius: 4px; color: #475467; font-size: .88rem;}
        div[data-testid="stMetric"] {border: 1px solid #E4E7EC; padding: .8rem .9rem; border-radius: 10px; background: #FFFFFF;}
        div[data-testid="stMetricLabel"] {color: #667085;}
        hr {margin-top: 1.4rem; margin-bottom: 1.4rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def status_for_capacity(ratio: float) -> tuple[str, str]:
    if ratio >= 1.20:
        return "OK", "status-ok"
    if ratio >= 1.00:
        return "ATENÇÃO", "status-warn"
    return "REPROVADO", "status-bad"


def status_for_speed(error: float) -> tuple[str, str]:
    if abs(error) <= 0.05:
        return "OK", "status-ok"
    return "REVER", "status-warn"


def conveyor_svg(
    center_distance_m: float,
    strands: int,
    conveyor_dp_mm: float,
    return_type: str,
    sag_mm: float,
    coupling_type: str,
    secondary_dp1_mm: float,
    secondary_dp2_mm: float,
) -> str:
    """Desenho esquemático paramétrico; não representa escala CAD."""
    width, height = 920, 430
    x1, x2 = 185, 725
    y_top, y_return = 175, 270
    r = 48
    load_x, load_y, load_w, load_h = 335, 92, 250, 58

    n_lines = max(1, min(int(strands), 6))
    offsets = [0] if n_lines == 1 else [-18 + (36 * i / (n_lines - 1)) for i in range(n_lines)]
    chain_lines = "".join(
        f'<line x1="{x1}" y1="{y_top + off}" x2="{x2}" y2="{y_top + off}" stroke="#344054" stroke-width="4" stroke-linecap="round"/>'
        for off in offsets
    )

    if return_type == "Livre":
        sag_px = max(18, min(65, 18 + sag_mm * 0.20))
        return_path = (
            f'<path d="M {x2} {y_return} Q {(x1+x2)/2} {y_return+sag_px} {x1} {y_return}" '
            'fill="none" stroke="#667085" stroke-width="5" stroke-linecap="round"/>'
        )
        return_label = f"Retorno livre · flecha {fmt(sag_mm,0)} mm"
    else:
        return_path = (
            f'<line x1="{x1}" y1="{y_return}" x2="{x2}" y2="{y_return}" stroke="#667085" stroke-width="5" stroke-linecap="round"/>'
            f'<line x1="{x1+15}" y1="{y_return+12}" x2="{x2-15}" y2="{y_return+12}" stroke="#98A2B3" stroke-width="5" stroke-dasharray="12 8"/>'
        )
        return_label = "Retorno guiado"

    if coupling_type == "Direto":
        drive = f"""
        <rect x="35" y="128" width="92" height="66" rx="8" fill="#D1E9FF" stroke="#1570EF" stroke-width="2"/>
        <text x="81" y="153" text-anchor="middle" font-size="14" font-weight="700" fill="#175CD3">MOTOR</text>
        <text x="81" y="173" text-anchor="middle" font-size="13" fill="#175CD3">+ REDUTOR</text>
        <line x1="127" y1="161" x2="{x1-r}" y2="{y_top}" stroke="#1570EF" stroke-width="7"/>
        <text x="80" y="215" text-anchor="middle" font-size="13" fill="#475467">Acionamento direto</text>
        """
    else:
        dp1 = max(18, min(40, secondary_dp1_mm * 0.12))
        dp2 = max(22, min(52, secondary_dp2_mm * 0.12))
        gx1, gy1 = 85, 310
        gx2, gy2 = 185, 310
        drive = f"""
        <rect x="24" y="218" width="122" height="58" rx="8" fill="#D1E9FF" stroke="#1570EF" stroke-width="2"/>
        <text x="85" y="242" text-anchor="middle" font-size="14" font-weight="700" fill="#175CD3">MOTORREDUTOR</text>
        <text x="85" y="261" text-anchor="middle" font-size="12" fill="#175CD3">ou redutor + motor</text>
        <circle cx="{gx1}" cy="{gy1}" r="{dp1}" fill="#F2F4F7" stroke="#344054" stroke-width="4"/>
        <circle cx="{gx2}" cy="{gy2}" r="{dp2}" fill="#F2F4F7" stroke="#344054" stroke-width="4"/>
        <line x1="{gx1}" y1="{gy1-dp1}" x2="{gx2}" y2="{gy2-dp2}" stroke="#475467" stroke-width="4"/>
        <line x1="{gx1}" y1="{gy1+dp1}" x2="{gx2}" y2="{gy2+dp2}" stroke="#475467" stroke-width="4"/>
        <line x1="{gx2}" y1="{gy2-dp2-2}" x2="{x1}" y2="{y_top+r}" stroke="#1570EF" stroke-width="6"/>
        <text x="{gx1}" y="{gy1+dp1+26}" text-anchor="middle" font-size="12" fill="#475467">Dp1 {fmt(secondary_dp1_mm,0)} mm</text>
        <text x="{gx2+30}" y="{gy2+dp2+26}" text-anchor="middle" font-size="12" fill="#475467">Dp2 {fmt(secondary_dp2_mm,0)} mm</text>
        """

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg" role="img">
        <rect width="{width}" height="{height}" rx="14" fill="#FCFCFD" stroke="#EAECF0"/>
        <text x="26" y="35" font-size="17" font-weight="700" fill="#101828">Esquema do transportador</text>
        <text x="26" y="57" font-size="12" fill="#667085">Representação funcional — não usar como desenho de fabricação</text>

        <rect x="{load_x}" y="{load_y}" width="{load_w}" height="{load_h}" rx="5" fill="#E9D7B7" stroke="#8A5A2B" stroke-width="2"/>
        <text x="{load_x + load_w/2}" y="{load_y + 34}" text-anchor="middle" font-size="15" font-weight="700" fill="#5D3A1A">MADEIRA</text>

        <circle cx="{x1}" cy="{y_top}" r="{r}" fill="#F2F4F7" stroke="#344054" stroke-width="5"/>
        <circle cx="{x2}" cy="{y_top}" r="{r}" fill="#F2F4F7" stroke="#344054" stroke-width="5"/>
        <circle cx="{x1}" cy="{y_top}" r="8" fill="#344054"/>
        <circle cx="{x2}" cy="{y_top}" r="8" fill="#344054"/>
        {chain_lines}
        {return_path}
        {drive}

        <line x1="{x1}" y1="360" x2="{x2}" y2="360" stroke="#98A2B3" stroke-width="2"/>
        <line x1="{x1}" y1="350" x2="{x1}" y2="370" stroke="#98A2B3" stroke-width="2"/>
        <line x1="{x2}" y1="350" x2="{x2}" y2="370" stroke="#98A2B3" stroke-width="2"/>
        <text x="{(x1+x2)/2}" y="388" text-anchor="middle" font-size="14" font-weight="700" fill="#475467">C = {fmt(center_distance_m,3)} m</text>

        <text x="{x1}" y="113" text-anchor="middle" font-size="13" fill="#475467">Motriz</text>
        <text x="{x2}" y="113" text-anchor="middle" font-size="13" fill="#475467">Movida</text>
        <text x="{x2+60}" y="{y_top+5}" font-size="13" fill="#475467">Dp = {fmt(conveyor_dp_mm,0)} mm</text>
        <text x="{(x1+x2)/2}" y="{y_top+42}" text-anchor="middle" font-size="13" fill="#475467">{strands} vias de corrente</text>
        <text x="{(x1+x2)/2}" y="{y_return+45}" text-anchor="middle" font-size="13" fill="#475467">{html.escape(return_label)}</text>
        <polygon points="{x2-35},{y_top-27} {x2-10},{y_top-27} {x2-10},{y_top-37} {x2+12},{y_top-20} {x2-10},{y_top-3} {x2-10},{y_top-13} {x2-35},{y_top-13}" fill="#1570EF"/>
        <text x="{x2-55}" y="{y_top-42}" text-anchor="end" font-size="12" fill="#1570EF">movimento</text>
    </svg>
    """


st.title("Calculadora de Transportador por Correntes")
st.markdown(
    '<div class="app-subtitle">Dimensionamento do sistema, seleção do acionamento e comparação direta entre o que a esteira exige e o que o conjunto fornece.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-kicker">Etapa 1</div><div class="section-title">Sistema a dimensionar</div>', unsafe_allow_html=True)
sys_left, sys_right = st.columns([1.15, 0.85], gap="large")

with sys_left:
    row1 = st.columns(3)
    with row1[0]:
        center_distance_m = st.number_input("Distância entre centros [m]", min_value=0.01, value=4.15554, step=0.10)
        strands = st.number_input("Quantidade de vias", min_value=1, value=4, step=1)
        chain_mass_per_m = st.number_input("Massa linear da corrente [kg/m]", min_value=0.01, value=7.30, step=0.10)
    with row1[1]:
        conveyor_dp = st.number_input("Ø primitivo das rodas [mm]", min_value=1.0, value=260.0, step=1.0)
        inclination_deg = st.number_input("Inclinação [°]", value=0.0, step=1.0)
        return_type = st.selectbox("Tipo de retorno", ["Guiado", "Livre"])
    with row1[2]:
        if return_type == "Livre":
            return_sag_mm = st.number_input("Flecha do retorno [mm]", min_value=1.0, value=80.0, step=5.0)
            mu_return = 0.0
        else:
            return_sag_mm = 80.0
            mu_return = st.number_input("Atrito do retorno μret", min_value=0.0, value=0.25, step=0.01)
        mu_top = st.number_input("Atrito superior μsup", min_value=0.0, value=0.40, step=0.01)
        load_mass = st.number_input("Massa transportada [kg]", min_value=0.01, value=276.0, step=10.0)

    row2 = st.columns(4)
    with row2[0]:
        linear_speed = st.number_input("Velocidade desejada [m/min]", min_value=0.01, value=32.0, step=1.0)
    with row2[1]:
        additional_force = st.number_input("Força adicional [N]", min_value=0.0, value=0.0, step=10.0)
    with row2[2]:
        acceleration_time = st.number_input("Tempo de aceleração [s]", min_value=0.0, value=3.0, step=0.5, help="Use 0 para ignorar a aceleração.")
    with row2[3]:
        design_factor = st.number_input(
            "Fator de projeto do acionamento", min_value=1.0, value=1.50, step=0.05,
            help="Margem aplicada ao requisito calculado de força, torque e potência. Não é o fator de segurança estrutural da corrente.",
        )

conveyor = calculate_conveyor(
    ConveyorInput(
        center_distance_m=center_distance_m,
        strands=int(strands),
        chain_mass_per_m_kg=chain_mass_per_m,
        inclination_deg=inclination_deg,
        conveyor_sprocket_pitch_diameter_mm=conveyor_dp,
        return_type=return_type,
        return_sag_mm=return_sag_mm,
        mu_top=mu_top,
        mu_return=mu_return,
        load_mass_kg=load_mass,
        linear_speed_m_min=linear_speed,
        additional_process_force_n=additional_force,
        acceleration_time_s=acceleration_time,
        design_factor=design_factor,
    )
)

with sys_right:
    st.markdown("**Arquitetura do acionamento**")
    coupling_type = st.radio("Ligação ao eixo da esteira", ["Direto", "Transmissão secundária"], horizontal=True, label_visibility="collapsed")
    if coupling_type == "Transmissão secundária":
        s1, s2, s3 = st.columns(3)
        with s1:
            secondary_dp1 = st.number_input("Dp1 redutor [mm]", min_value=1.0, value=170.0, step=1.0)
        with s2:
            secondary_dp2 = st.number_input("Dp2 eixo [mm]", min_value=1.0, value=202.66, step=1.0)
        with s3:
            secondary_eff = st.number_input("η secundária [%]", min_value=1.0, max_value=100.0, value=98.0, step=0.5)
    else:
        secondary_dp1 = 1.0
        secondary_dp2 = 1.0
        secondary_eff = 100.0

    st.markdown(
        conveyor_svg(center_distance_m, int(strands), conveyor_dp, return_type, return_sag_mm, coupling_type, secondary_dp1, secondary_dp2),
        unsafe_allow_html=True,
    )

transmission = SecondaryTransmissionInput(
    coupling_type=coupling_type,
    reducer_sprocket_pitch_diameter_mm=secondary_dp1,
    shaft_sprocket_pitch_diameter_mm=secondary_dp2,
    efficiency_pct=secondary_eff,
)

requirement = calculate_secondary_requirement(
    conveyor.required_axis_speed_rpm,
    conveyor.required_axis_torque_nm,
    conveyor.required_axis_power_kw,
    transmission,
)

st.divider()
st.markdown('<div class="section-kicker">Etapa 2</div><div class="section-title">O que o sistema exige</div>', unsafe_allow_html=True)
req_cols = st.columns(6)
req_cols[0].metric("Força de projeto", f"{fmt(conveyor.design_force_n,0)} N")
req_cols[1].metric("Força por via", f"{fmt(conveyor.force_per_strand_n,0)} N")
req_cols[2].metric("Torque no eixo", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m")
req_cols[3].metric("Potência", f"{fmt(conveyor.required_axis_power_kw,2)} kW")
req_cols[4].metric("Potência comercial", f"{fmt(conveyor.required_axis_power_cv,2)} cv")
req_cols[5].metric("Rotação do eixo", f"{fmt(conveyor.required_axis_speed_rpm,1)} rpm")

st.markdown(
    f'<div class="soft-note">Massa total das correntes: <b>{fmt(conveyor.total_chain_mass_kg,1)} kg</b> · '
    f'Força resistente em regime: <b>{fmt(conveyor.regime_force_n,0)} N</b> · '
    f'Requisito na saída do redutor: <b>{fmt(requirement.required_reducer_speed_rpm,1)} rpm</b>, '
    f'<b>{fmt(requirement.required_reducer_torque_nm,1)} N·m</b> e <b>{fmt(requirement.required_reducer_power_kw,2)} kW</b>.</div>',
    unsafe_allow_html=True,
)

st.divider()
st.markdown('<div class="section-kicker">Etapa 3</div><div class="section-title">Acionamento fornecido</div>', unsafe_allow_html=True)
supply_mode = st.radio("Como o acionamento será informado?", ["Motoredutor completo", "Redutor + motor separados"], horizontal=True)
drive_input_col, drive_summary_col = st.columns([1.25, 0.75], gap="large")

with drive_input_col:
    if supply_mode == "Motoredutor completo":
        st.markdown("#### Motoredutor completo")
        st.caption("Use diretamente os dados de saída do fabricante do conjunto, como nos configuradores SEW, NORD ou Bonfiglioli.")
        a, b = st.columns(2)
        with a:
            gm_manufacturer = st.text_input("Fabricante", value="SEW-EURODRIVE")
            gm_model = st.text_input("Modelo / designação", value="")
            gm_motor_power = st.number_input("Potência do motor [kW]", value=15.0, step=0.5)
            gm_motor_speed = st.number_input("Rotação nominal do motor [rpm]", value=1777.0, step=1.0)
            gm_ratio = st.number_input("Redução total", value=22.37, step=0.01)
        with b:
            gm_output_speed = st.number_input("Velocidade de saída [rpm]", value=79.0, step=1.0)
            gm_output_torque = st.number_input("Torque de saída [N·m]", value=1790.0, step=10.0)
            gm_radial = st.number_input("Força radial admissível [N]", value=15600.0, step=100.0)
            gm_service_factor = st.number_input("Fator de serviço do fabricante", value=1.50, step=0.05, help="Dado comercial do fabricante; não substituir pelo fator de projeto da aplicação.")

        drive = complete_gearmotor_output(
            CompleteGearmotorInput(
                manufacturer=gm_manufacturer,
                model=gm_model,
                motor_power_kw=gm_motor_power,
                motor_speed_rpm=gm_motor_speed,
                output_speed_rpm=gm_output_speed,
                total_ratio=gm_ratio,
                output_torque_nm=gm_output_torque,
                admissible_radial_force_n=gm_radial,
                manufacturer_service_factor=gm_service_factor,
            )
        )
    else:
        st.markdown("#### Redutor")
        r1, r2 = st.columns(2)
        with r1:
            reducer_manufacturer = st.text_input("Fabricante do redutor", value="Geremia")
            reducer_model = st.text_input("Modelo do redutor", value="GD30/2R")
            reducer_ratio = st.number_input("Redução do redutor", value=35.0, step=0.01)
            reducer_eff = st.number_input("Rendimento do redutor [%]", value=96.0, step=0.5)
        with r2:
            reducer_max_torque = st.number_input("Torque máximo [N·m]", value=370.0, step=10.0)
            reducer_radial = st.number_input("Força radial admissível [N]", value=6300.0, step=100.0)
            reducer_max_power = st.number_input("Potência máxima de entrada [kW]", value=1.50, step=0.10)

        st.markdown("#### Motor")
        m1, m2 = st.columns(2)
        with m1:
            motor_manufacturer = st.text_input("Fabricante do motor", value="WEG")
            motor_model = st.text_input("Modelo do motor", value="")
            motor_power = st.number_input("Potência nominal [kW]", value=1.50, step=0.10)
            motor_speed = st.number_input("Rotação nominal [rpm]", value=1745.0, step=1.0)
        with m2:
            motor_eff = st.number_input("Rendimento do motor [%]", value=86.5, step=0.1)
            nominal_freq = st.number_input("Frequência nominal [Hz]", value=60.0, step=1.0)
            operating_freq = st.number_input("Frequência de operação [Hz]", value=60.0, step=1.0)

        drive = separate_drive_output(
            SeparateDriveInput(
                reducer_manufacturer=reducer_manufacturer,
                reducer_model=reducer_model,
                reducer_ratio=reducer_ratio,
                reducer_efficiency_pct=reducer_eff,
                reducer_max_torque_nm=reducer_max_torque,
                reducer_admissible_radial_force_n=reducer_radial,
                reducer_max_input_power_kw=reducer_max_power,
                motor_manufacturer=motor_manufacturer,
                motor_model=motor_model,
                motor_power_kw=motor_power,
                motor_speed_rpm=motor_speed,
                motor_efficiency_pct=motor_eff,
                nominal_frequency_hz=nominal_freq,
                operating_frequency_hz=operating_freq,
            )
        )

final_output = calculate_final_output(drive, transmission, conveyor_dp)

with drive_summary_col:
    st.markdown("#### O que estou fornecendo")
    st.metric("Velocidade linear disponível", f"{fmt(final_output.linear_speed_m_min,1)} m/min")
    st.metric("Torque disponível no eixo", f"{fmt(final_output.axis_torque_nm,1)} N·m")
    st.metric("Potência disponível no eixo", f"{fmt(final_output.axis_power_kw,2)} kW")
    st.metric("Rotação disponível no eixo", f"{fmt(final_output.axis_speed_rpm,1)} rpm")
    if coupling_type == "Transmissão secundária":
        st.markdown("##### Transmissão secundária")
        st.metric("Força tangencial na roda do redutor", f"{fmt(final_output.radial_tangential_force_n or 0,0)} N")
        st.metric("Força radial admissível", f"{fmt(drive.admissible_radial_force_n,0)} N")
        if final_output.critical_pitch_diameter_mm is not None:
            st.metric("Ø primitivo crítico teórico", f"{fmt(final_output.critical_pitch_diameter_mm,1)} mm")
        st.caption("O Ø crítico é um limite teórico sem fator de segurança; não é um diâmetro recomendado.")

st.divider()
st.markdown('<div class="section-kicker">Etapa 4</div><div class="section-title">Requerido × disponível</div>', unsafe_allow_html=True)


def capacity_ratio(available: float, required: float) -> float:
    return available / required if required > 0 else 0.0


speed_error = (final_output.linear_speed_m_min - linear_speed) / linear_speed if linear_speed > 0 else 0.0
power_ratio = capacity_ratio(final_output.axis_power_kw, conveyor.required_axis_power_kw)
torque_ratio = capacity_ratio(final_output.axis_torque_nm, conveyor.required_axis_torque_nm)
speed_status, speed_class = status_for_speed(speed_error)
power_status, power_class = status_for_capacity(power_ratio)
torque_status, torque_class = status_for_capacity(torque_ratio)

comparison_rows = [
    {"Grandeza": "Velocidade linear", "Requerido": round(linear_speed, 2), "Disponível": round(final_output.linear_speed_m_min, 2), "Unidade": "m/min", "Margem / desvio": f"{speed_error*100:+.1f}%", "Status": speed_status},
    {"Grandeza": "Potência", "Requerido": round(conveyor.required_axis_power_kw, 3), "Disponível": round(final_output.axis_power_kw, 3), "Unidade": "kW", "Margem / desvio": f"{power_ratio:.2f}x", "Status": power_status},
    {"Grandeza": "Torque", "Requerido": round(conveyor.required_axis_torque_nm, 2), "Disponível": round(final_output.axis_torque_nm, 2), "Unidade": "N·m", "Margem / desvio": f"{torque_ratio:.2f}x", "Status": torque_status},
]

radial_status = None
radial_class = None
if coupling_type == "Transmissão secundária":
    radial_force = final_output.radial_tangential_force_n or 0.0
    radial_ratio = capacity_ratio(drive.admissible_radial_force_n, radial_force)
    radial_status = "OK" if radial_ratio >= 1.0 else "REPROVADO"
    radial_class = "status-ok" if radial_ratio >= 1.0 else "status-bad"
    comparison_rows.append({"Grandeza": "Força radial / tangencial", "Requerido": round(radial_force, 1), "Disponível": round(drive.admissible_radial_force_n, 1), "Unidade": "N", "Margem / desvio": f"{radial_ratio:.2f}x", "Status": radial_status})

summary_cols = st.columns(4 if coupling_type == "Transmissão secundária" else 3)
summary_cols[0].markdown(f'<div class="engineering-card"><div class="label">Velocidade</div><div class="value">{fmt(linear_speed,1)} → {fmt(final_output.linear_speed_m_min,1)} m/min</div><div class="sub"><span class="{speed_class}">{speed_status}</span></div></div>', unsafe_allow_html=True)
summary_cols[1].markdown(f'<div class="engineering-card"><div class="label">Potência</div><div class="value">{fmt(conveyor.required_axis_power_kw,2)} → {fmt(final_output.axis_power_kw,2)} kW</div><div class="sub"><span class="{power_class}">{power_status}</span></div></div>', unsafe_allow_html=True)
summary_cols[2].markdown(f'<div class="engineering-card"><div class="label">Torque</div><div class="value">{fmt(conveyor.required_axis_torque_nm,1)} → {fmt(final_output.axis_torque_nm,1)} N·m</div><div class="sub"><span class="{torque_class}">{torque_status}</span></div></div>', unsafe_allow_html=True)
if coupling_type == "Transmissão secundária":
    radial_force = final_output.radial_tangential_force_n or 0.0
    summary_cols[3].markdown(f'<div class="engineering-card"><div class="label">Carga no eixo do redutor</div><div class="value">{fmt(radial_force,0)} → {fmt(drive.admissible_radial_force_n,0)} N</div><div class="sub"><span class="{radial_class}">{radial_status}</span></div></div>', unsafe_allow_html=True)

st.dataframe(pd.DataFrame(comparison_rows), hide_index=True, use_container_width=True)
st.markdown('<div class="soft-note"><b>Hipótese de distribuição entre vias:</b> a força por via pressupõe correntes com comprimentos compatíveis, rodas dentadas sincronizadas no eixo, guias niveladas, tensionamento equivalente e desgaste semelhante entre as vias.</div>', unsafe_allow_html=True)

with st.expander("Detalhes das forças e memória intermediária"):
    force_rows = [
        ("Atrito — ramo superior", conveyor.top_friction_n, "N"),
        ("Inclinação da carga", conveyor.inclination_force_n, "N"),
        ("Aceleração", conveyor.acceleration_force_n, "N"),
        ("Força resistente em regime", conveyor.regime_force_n, "N"),
        ("Força total antes do fator de projeto", conveyor.force_before_design_factor_n, "N"),
    ]
    if return_type == "Guiado":
        force_rows.insert(1, ("Atrito — retorno", conveyor.return_friction_n, "N"))
    else:
        force_rows.insert(1, ("Tensão estática de catenária", conveyor.catenary_tension_n or 0.0, "N"))
    st.dataframe(pd.DataFrame(force_rows, columns=["Grandeza", "Valor", "Unidade"]), hide_index=True, use_container_width=True)

with st.expander("Auxílio para calcular a massa da madeira"):
    density = st.number_input("Densidade [kg/m³]", min_value=1.0, value=1150.0, step=10.0)
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Bloco retangular**")
        base = st.number_input("Base [m]", value=0.40, step=0.01, key="rect_base")
        height = st.number_input("Altura [m]", value=0.20, step=0.01, key="rect_height")
        length = st.number_input("Comprimento [m]", value=3.00, step=0.10, key="rect_length")
        vol, mass = rectangular_mass(base, height, length, density)
        st.write(f"Volume: **{fmt(vol,3)} m³**")
        st.write(f"Massa: **{fmt(mass,1)} kg**")
    with g2:
        st.markdown("**Bloco cilíndrico**")
        diameter = st.number_input("Diâmetro [m]", value=0.40, step=0.01, key="cyl_d")
        cyl_length = st.number_input("Comprimento [m]", value=3.00, step=0.10, key="cyl_l")
        vol, mass = cylindrical_mass(diameter, cyl_length, density)
        st.write(f"Volume: **{fmt(vol,3)} m³**")
        st.write(f"Massa: **{fmt(mass,1)} kg**")

st.caption("O fator de projeto do acionamento é aplicado ao requisito calculado de força, torque e potência. A verificação estrutural da corrente contra ruptura deve ser realizada separadamente.")
