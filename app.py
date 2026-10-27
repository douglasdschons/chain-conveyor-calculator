from __future__ import annotations

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

st.title("Calculadora de Transportador por Correntes")
st.caption(
    "Dimensionamento do transportador, transmissão e acionamento. "
    "Os cálculos de aplicação são separados dos dados comerciais do motoredutor."
)

with st.sidebar:
    st.header("Configuração")
    supply_mode = st.radio(
        "Como o acionamento será informado?",
        ["Motoredutor completo", "Redutor + motor separados"],
    )
    coupling_type = st.radio(
        "Ligação do acionamento ao eixo",
        ["Direto", "Transmissão secundária"],
    )


tab_transport, tab_drive, tab_results = st.tabs(
    ["1. Transportador", "2. Acionamento", "3. Resultado"]
)

with tab_transport:
    st.subheader("Dados do transportador")

    c1, c2, c3 = st.columns(3)
    with c1:
        center_distance_m = st.number_input(
            "Distância entre centros [m]", min_value=0.01, value=4.15554, step=0.1
        )
        strands = st.number_input(
            "Quantidade de vias", min_value=1, value=4, step=1
        )
        chain_mass_per_m = st.number_input(
            "Massa linear da corrente [kg/m]", min_value=0.01, value=7.30, step=0.1
        )
        conveyor_dp = st.number_input(
            "Ø primitivo das rodas da esteira [mm]",
            min_value=1.0,
            value=260.0,
            step=1.0,
        )

    with c2:
        return_type = st.selectbox("Tipo de retorno", ["Guiado", "Livre"])
        if return_type == "Livre":
            return_sag_mm = st.number_input(
                "Flecha do retorno [mm]", min_value=1.0, value=80.0, step=5.0
            )
            mu_return = 0.0
        else:
            return_sag_mm = 80.0
            mu_return = st.number_input(
                "Coeficiente de atrito do retorno μret",
                min_value=0.0,
                value=0.25,
                step=0.01,
            )

        mu_top = st.number_input(
            "Coeficiente de atrito superior μsup",
            min_value=0.0,
            value=0.40,
            step=0.01,
        )
        inclination_deg = st.number_input(
            "Inclinação [°]", value=0.0, step=1.0
        )

    with c3:
        load_mass = st.number_input(
            "Massa transportada [kg]", min_value=0.01, value=276.0, step=10.0
        )
        linear_speed = st.number_input(
            "Velocidade linear desejada [m/min]",
            min_value=0.01,
            value=32.0,
            step=1.0,
        )
        additional_force = st.number_input(
            "Força adicional do processo [N]", min_value=0.0, value=0.0, step=10.0
        )
        acceleration_time = st.number_input(
            "Tempo de aceleração [s] (0 = ignorar)",
            min_value=0.0,
            value=3.0,
            step=0.5,
        )
        design_factor = st.number_input(
            "Fator de projeto do acionamento",
            min_value=1.0,
            value=1.50,
            step=0.05,
            help=(
                "Margem aplicada ao requisito calculado de força, torque e potência "
                "do acionamento. Não é o fator de segurança estrutural da corrente."
            ),
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

    st.divider()
    st.subheader("Requisito calculado")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Força de projeto", f"{conveyor.design_force_n:,.0f} N")
    r2.metric("Torque no eixo", f"{conveyor.required_axis_torque_nm:,.1f} N·m")
    r3.metric(
        "Potência no eixo",
        f"{conveyor.required_axis_power_kw:.2f} kW",
        f"{conveyor.required_axis_power_cv:.2f} cv",
        delta_color="off",
    )
    r4.metric("Rotação requerida", f"{conveyor.required_axis_speed_rpm:.1f} rpm")

    d1, d2, d3 = st.columns(3)
    d1.metric("Massa total das correntes", f"{conveyor.total_chain_mass_kg:.1f} kg")
    d2.metric("Força por via", f"{conveyor.force_per_strand_n:.0f} N")
    d3.metric("Força em regime", f"{conveyor.regime_force_n:.0f} N")

    with st.expander("Detalhes das forças"):
        rows = [
            ("Atrito — ramo superior", conveyor.top_friction_n, "N"),
            ("Atrito — retorno", conveyor.return_friction_n, "N"),
            ("Inclinação da carga", conveyor.inclination_force_n, "N"),
            ("Aceleração", conveyor.acceleration_force_n, "N"),
        ]
        if return_type == "Livre":
            rows.append(("Tensão estática de catenária", conveyor.catenary_tension_n or 0, "N"))
        st.dataframe(
            pd.DataFrame(rows, columns=["Grandeza", "Valor", "Unidade"]),
            hide_index=True,
            use_container_width=True,
        )

    with st.expander("Auxílio para calcular a massa da madeira"):
        density = st.number_input(
            "Densidade [kg/m³]", min_value=1.0, value=1150.0, step=10.0
        )
        g1, g2 = st.columns(2)

        with g1:
            st.markdown("**Bloco retangular**")
            base = st.number_input("Base [m]", value=0.40, step=0.01, key="rect_base")
            height = st.number_input("Altura [m]", value=0.20, step=0.01, key="rect_height")
            length = st.number_input("Comprimento [m]", value=3.00, step=0.10, key="rect_length")
            vol, mass = rectangular_mass(base, height, length, density)
            st.write(f"Volume: **{vol:.3f} m³**")
            st.write(f"Massa: **{mass:.1f} kg**")

        with g2:
            st.markdown("**Bloco cilíndrico**")
            diameter = st.number_input("Diâmetro [m]", value=0.40, step=0.01, key="cyl_d")
            cyl_length = st.number_input("Comprimento [m]", value=3.00, step=0.10, key="cyl_l")
            vol, mass = cylindrical_mass(diameter, cyl_length, density)
            st.write(f"Volume: **{vol:.3f} m³**")
            st.write(f"Massa: **{mass:.1f} kg**")


with tab_drive:
    st.subheader("Transmissão entre acionamento e eixo")

    if coupling_type == "Transmissão secundária":
        t1, t2, t3 = st.columns(3)
        with t1:
            secondary_dp1 = st.number_input(
                "Ø primitivo da roda no redutor [mm]",
                min_value=1.0,
                value=170.0,
                step=1.0,
            )
        with t2:
            secondary_dp2 = st.number_input(
                "Ø primitivo da roda no eixo [mm]",
                min_value=1.0,
                value=202.66,
                step=1.0,
            )
        with t3:
            secondary_eff = st.number_input(
                "Rendimento da transmissão [%]",
                min_value=1.0,
                max_value=100.0,
                value=98.0,
                step=0.5,
            )
    else:
        secondary_dp1 = 1.0
        secondary_dp2 = 1.0
        secondary_eff = 100.0

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

    if supply_mode == "Motoredutor completo":
        st.subheader("Motoredutor completo")
        st.caption(
            "Use os valores de saída informados pelo fabricante do conjunto, "
            "como em configuradores SEW, NORD, Bonfiglioli etc."
        )

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
            gm_service_factor = st.number_input(
                "Fator de serviço do fabricante", value=1.50, step=0.05,
                help="Dado do fabricante. Não substituir pelo fator de projeto da aplicação."
            )

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
        st.subheader("Redutor")
        r1, r2 = st.columns(2)
        with r1:
            reducer_manufacturer = st.text_input("Fabricante do redutor", value="Geremia")
            reducer_model = st.text_input("Modelo do redutor", value="GD30/2R")
            reducer_ratio = st.number_input("Redução do redutor", value=35.0, step=0.01)
            reducer_eff = st.number_input("Rendimento do redutor [%]", value=96.0, step=0.5)
        with r2:
            reducer_max_torque = st.number_input("Torque máximo [N·m]", value=370.0, step=10.0)
            reducer_radial = st.number_input("Força radial admissível [N]", value=6300.0, step=100.0)
            reducer_max_power = st.number_input("Potência máxima de entrada [kW]", value=1.50, step=0.1)

        st.subheader("Motor")
        m1, m2 = st.columns(2)
        with m1:
            motor_manufacturer = st.text_input("Fabricante do motor", value="WEG")
            motor_model = st.text_input("Modelo do motor", value="")
            motor_power = st.number_input("Potência nominal [kW]", value=1.50, step=0.1)
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

    st.divider()
    st.subheader("Capacidade disponível")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rotação no eixo", f"{final_output.axis_speed_rpm:.1f} rpm")
    c2.metric("Torque no eixo", f"{final_output.axis_torque_nm:.1f} N·m")
    c3.metric("Potência no eixo", f"{final_output.axis_power_kw:.2f} kW")
    c4.metric("Velocidade linear", f"{final_output.linear_speed_m_min:.1f} m/min")

    if coupling_type == "Transmissão secundária":
        st.subheader("Indicador radial")
        q1, q2, q3 = st.columns(3)
        q1.metric(
            "Força tangencial na roda do redutor",
            f"{final_output.radial_tangential_force_n:,.0f} N",
        )
        q2.metric("Força radial admissível", f"{drive.admissible_radial_force_n:,.0f} N")
        q3.metric(
            "Ø primitivo crítico teórico",
            f"{final_output.critical_pitch_diameter_mm:.1f} mm"
            if final_output.critical_pitch_diameter_mm is not None
            else "N/D",
        )
        st.caption(
            "O Ø crítico é um limite teórico sem fator de segurança. "
            "Não deve ser interpretado como diâmetro recomendado."
        )


with tab_results:
    st.subheader("Requerido × disponível")

    final_output = calculate_final_output(drive, transmission, conveyor_dp)

    def ratio(available: float, required: float) -> float:
        return available / required if required > 0 else 0.0

    power_ratio = ratio(final_output.axis_power_kw, conveyor.required_axis_power_kw)
    torque_ratio = ratio(final_output.axis_torque_nm, conveyor.required_axis_torque_nm)
    speed_error = (
        (final_output.linear_speed_m_min - linear_speed)
        / linear_speed
        if linear_speed > 0
        else 0.0
    )

    rows = [
        {
            "Grandeza": "Velocidade linear",
            "Requerido": linear_speed,
            "Disponível": final_output.linear_speed_m_min,
            "Unidade": "m/min",
            "Margem": speed_error,
            "Status": "OK" if abs(speed_error) <= 0.05 else "REVER",
        },
        {
            "Grandeza": "Potência",
            "Requerido": conveyor.required_axis_power_kw,
            "Disponível": final_output.axis_power_kw,
            "Unidade": "kW",
            "Margem": power_ratio,
            "Status": "OK" if power_ratio >= 1.20 else ("ATENÇÃO" if power_ratio >= 1 else "REPROVADO"),
        },
        {
            "Grandeza": "Torque",
            "Requerido": conveyor.required_axis_torque_nm,
            "Disponível": final_output.axis_torque_nm,
            "Unidade": "N·m",
            "Margem": torque_ratio,
            "Status": "OK" if torque_ratio >= 1.20 else ("ATENÇÃO" if torque_ratio >= 1 else "REPROVADO"),
        },
    ]

    if coupling_type == "Transmissão secundária":
        radial_ratio = ratio(
            drive.admissible_radial_force_n,
            final_output.radial_tangential_force_n or 0.0,
        )
        rows.append(
            {
                "Grandeza": "Carga radial / tangencial",
                "Requerido": final_output.radial_tangential_force_n or 0.0,
                "Disponível": drive.admissible_radial_force_n,
                "Unidade": "N",
                "Margem": radial_ratio,
                "Status": "OK" if radial_ratio >= 1 else "REPROVADO",
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.info(
        "A força de projeto por via pressupõe correntes com comprimentos compatíveis, "
        "rodas dentadas sincronizadas no eixo, guias niveladas, tensionamento equivalente "
        "e desgaste semelhante entre as vias."
    )
