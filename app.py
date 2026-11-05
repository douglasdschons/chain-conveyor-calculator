"""Calculadora de transportadores de correntes com interface em português brasileiro.

As imagens estáticas originais são reutilizadas do diretório assets/.
"""
from __future__ import annotations

from html import escape
from math import pi
from pathlib import Path

import pandas as pd
import streamlit as st

from src.localization import format_number, parse_number

from src.calculations import (
    CompleteGearmotorInput,
    DriveOutput,
    ConveyorInput,
    SecondaryTransmissionInput,
    SeparateDriveInput,
    calculate_conveyor,
    calculate_final_output,
    calculate_secondary_requirement,
    complete_gearmotor_output,
    cv_to_kw,
    cylindrical_mass,
    kw_to_cv,
    rectangular_mass,
    separate_drive_output,
)
from src.ibr_catalog import (
    RATIOS,
    SIZES,
    evaluate_ibr_q,
    get_ibr_q,
    catalogue_radial_force,
    required_service_factor,
)

st.set_page_config(
    page_title="Calculadora de transportadores de correntes",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def find_asset(stem: str) -> Path | None:
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        path = ASSETS_DIR / f"{stem}{extension}"
        if path.is_file():
            return path
    if ASSETS_DIR.exists():
        for path in ASSETS_DIR.iterdir():
            if path.is_file() and path.stem.casefold() == stem.casefold() \
                    and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                return path
    return None


IMG_RETURN = find_asset("return")
IMG_SAG = find_asset("sag")
IMG_DIRECT = find_asset("direct")
IMG_REDUCTION = find_asset("reduction")
IMG_PRISM = find_asset("auxiliary prism")
IMG_CYLINDER = find_asset("auxiliary cylinder")

st.markdown(
    """<style>
    :root { --border:#d9dde4; --header:#eaf2f8; --muted:#667085;
      --ok-bg:#ecfdf3; --ok-fg:#067647; --warn-bg:#fff7ed;
      --warn-fg:#b54708; --bad-bg:#fef3f2; --bad-fg:#b42318; }
    .block-container {max-width:1500px; padding:0.75rem 1rem 1.5rem;}
    header[data-testid="stHeader"] {height:2rem;}
    h1 {font-size:1.38rem!important;line-height:1.15!important;margin:0!important;}
    .section-bar {background:var(--header);border:1px solid var(--border);
      border-radius:5px;padding:.38rem .52rem;margin:.55rem 0 .35rem;
      font-size:.94rem;line-height:1.2rem;font-weight:700;clear:both;}
    .cell-grid {display:grid;border-top:1px solid var(--border);
      border-left:1px solid var(--border);margin-bottom:.3rem;}
    .cell {border-bottom:1px solid var(--border);border-right:1px solid var(--border);
      padding:.34rem .46rem;min-height:52px;min-width:0;background:white;}
    .cell-label {font-size:.78rem;color:var(--muted);line-height:1.04rem;}
    .cell-value {font-size:1rem;font-weight:700;color:#1f2937;
      line-height:1.1rem;margin-top:.06rem;overflow-wrap:anywhere;}
    .status-ok,.status-warn,.status-bad {display:inline-block;border-radius:4px;
      font-size:.76rem;font-weight:700;padding:.08rem .28rem;}
    .status-ok {background:var(--ok-bg);color:var(--ok-fg);}
    .status-warn {background:var(--warn-bg);color:var(--warn-fg);}
    .status-bad {background:var(--bad-bg);color:var(--bad-fg);}
    .tiny-caption {font-size:.78rem;color:var(--muted);margin-top:.1rem;}
    .app-note {font-size:.88rem;color:#344054;}
    div[data-testid="stVerticalBlock"] {gap:.32rem;}
    div[data-testid="stHorizontalBlock"] {gap:.52rem;align-items:flex-start;}
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stToggle"] label {font-size:.76rem!important;
      line-height:.90rem!important;margin-bottom:.05rem!important;}
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {font-size:.86rem!important;
      height:2.18rem!important;min-height:2.18rem!important;
      padding-top:.16rem!important;padding-bottom:.16rem!important;
      background:#f4f6f8!important;}
    div[data-testid="stSelectbox"] > div > div {min-height:2.18rem!important;
      font-size:.86rem!important;background:#f4f6f8!important;}
    div[data-testid="stExpander"] summary {font-size:.82rem!important;font-weight:600!important;}
    .power-label {font-size:.76rem;margin-bottom:.1rem;}
    .schematic-image img {max-height:320px;object-fit:contain;}
    .panel-note {border:1px solid var(--border);padding:.4rem .5rem;
      color:var(--muted);font-size:.82rem;line-height:1.25rem;}
    @media(max-width:900px) {
      .block-container {padding:.45rem .55rem 1rem;}
      .cell-grid {grid-template-columns:repeat(2,minmax(0,1fr))!important;}
      .section-bar {margin-top:.25rem;}
    }
    </style>""",
    unsafe_allow_html=True,
)


def fmt(value: float, decimals: int = 1) -> str:
    return format_number(value, decimals)


def _commit_number(key, integer, minimum, maximum, callback, args):
    try:
        value = parse_number(st.session_state[f"entrada:{key}"], integer)
        if minimum is not None and value < minimum:
            raise ValueError(f"O valor mínimo é {fmt(minimum, 5).rstrip('0').rstrip(',')}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"O valor máximo é {fmt(maximum, 5).rstrip('0').rstrip(',')}.")
    except ValueError as error:
        st.session_state[f"erro:{key}"] = str(error)
        return
    st.session_state.pop(f"erro:{key}", None)
    st.session_state[key] = value
    if callback:
        callback(*args)


def number_input_pt(label, min_value=None, max_value=None, value=None, step=None,
                    format=None, key=None, on_change=None, args=(), help=None):
    """Campo decimal independente do idioma do navegador, com limites validados."""
    key = key or f"numero:{label}"
    if value is None:
        value = min_value if min_value is not None else 0.0
    integer = isinstance(value, int) and (step is None or isinstance(step, int))
    decimals = (int(format.split('.')[1][:-1]) if format else
                max(2, len(str(value).partition('.')[2]), len(str(step or 1).partition('.')[2])))
    if integer:
        decimals = 0
    st.session_state.setdefault(key, value)
    if format is None and not integer:
        decimals = max(decimals, len(str(st.session_state[key]).partition('.')[2]))
    text_key = f"entrada:{key}"
    shown_key = f"exibido:{key}"
    if text_key not in st.session_state or st.session_state.get(shown_key) != st.session_state[key]:
        st.session_state[text_key] = format_number(st.session_state[key], decimals, grouping=False)
        st.session_state[shown_key] = st.session_state[key]
    st.text_input(label, key=text_key, help=help,
                  on_change=_commit_number,
                  args=(key, integer, min_value, max_value, on_change, args))
    if st.session_state.get(f"erro:{key}"):
        st.error(f"{label}: {st.session_state[f'erro:{key}']}")
        st.stop()
    return st.session_state[key]


def section_bar(title: str) -> None:
    st.markdown(f'<div class="section-bar">{escape(title)}</div>', unsafe_allow_html=True)


def cell_grid(items: list[tuple[str, str]], columns: int = 2) -> None:
    cols = " ".join("minmax(0,1fr)" for _ in range(columns))
    parts = [f'<div class="cell-grid" style="grid-template-columns:{cols}">']
    for label, value in items:
        parts.append(f'<div class="cell"><div class="cell-label">{escape(label)}</div>'
                     f'<div class="cell-value">{escape(value)}</div></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {"OK": "status-ok", "ATENÇÃO": "status-warn",
           "EM REVISÃO": "status-warn", "NÃO ATENDE": "status-bad"}.get(status, "status-warn")
    return f'<span class="{cls}">{escape(status)}</span>'


def capacity_status(available: float, required: float) -> tuple[float, str]:
    if required <= 0:
        return 0.0, "EM REVISÃO"
    ratio = available / required
    return ratio, "OK" if ratio >= 1.2 else "ATENÇÃO" if ratio >= 1 else "NÃO ATENDE"


def speed_status(available: float, required: float) -> tuple[float, str]:
    if required <= 0:
        return 0.0, "EM REVISÃO"
    error = (available - required) / required
    return error, "OK" if abs(error) <= 0.05 else "EM REVISÃO"


def render_schematic(path: Path | None, missing_text: str) -> None:
    if path is None:
        st.warning(missing_text)
    else:
        st.image(str(path), width="stretch")


def power_from_kw(prefix: str) -> None:
    st.session_state[f"{prefix}_cv"] = kw_to_cv(st.session_state[f"{prefix}_kw"])


def power_from_cv(prefix: str) -> None:
    st.session_state[f"{prefix}_kw"] = cv_to_kw(st.session_state[f"{prefix}_cv"])


def motor_power_pair(prefix: str, default_kw: float) -> float:
    """Two editable Streamlit widgets with last-edited-unit winning."""
    key_kw = f"{prefix}_kw"
    key_cv = f"{prefix}_cv"
    if key_kw not in st.session_state:
        st.session_state[key_kw] = default_kw
    if key_cv not in st.session_state:
        st.session_state[key_cv] = kw_to_cv(st.session_state[key_kw])
    st.markdown('<div class="power-label">Potência nominal do motor</div>', unsafe_allow_html=True)
    a, b = st.columns(2, gap="small")
    with a:
        number_input_pt("kW", key=key_kw, min_value=0.001 if prefix == "ibr_motor" else 0.0,
                        step=0.1, format="%.3f", on_change=power_from_kw, args=(prefix,))
    with b:
        number_input_pt("cv", key=key_cv, min_value=0.001 if prefix == "ibr_motor" else 0.0,
                        step=0.1, format="%.3f", on_change=power_from_cv, args=(prefix,))
    return float(st.session_state[key_kw])


def _reset_ibr_catalog_motor() -> None:
    """Restore the corresponding catalog maximum commercial motor when the row changes."""
    if "ibr_size" in st.session_state and "ibr_ratio" in st.session_state:
        cv = get_ibr_q(st.session_state["ibr_size"], st.session_state["ibr_ratio"]).catalogue_motor_cv
        st.session_state["ibr_motor_cv"] = cv
        st.session_state["ibr_motor_kw"] = cv_to_kw(cv)


st.title("Calculadora de transportadores de correntes")
st.markdown('<div class="app-note">Demanda do sistema · seleção do acionamento · necessário × disponível</div>',
            unsafe_allow_html=True)
st.caption('Use vírgula nos decimais. Exemplo: 1" = 25,4 mm. O ponto separa milhares: 1.000,50.')

# -----------------------------------------------------------------------------
# 1 — SYSTEM INPUTS
# -----------------------------------------------------------------------------
col_sys, col_scheme = st.columns([1.15, .85], gap="medium")
with col_sys:
    section_bar("1 · DADOS DO SISTEMA")
    r = st.columns(3)
    with r[0]:
        center_distance_m = number_input_pt("Distância entre centros C [m]", min_value=.01,
                                            value=4.15554, step=.1)
    with r[1]:
        conveyor_dp = number_input_pt("Diâmetro primitivo Dp [mm]", min_value=1.,
                                      value=260., step=1.)
    with r[2]:
        use_inclination = st.toggle("Inclinação", value=False)
        inclination_deg = number_input_pt("α [°]", value=0., step=1.) if use_inclination else 0.

    r = st.columns(2)
    with r[0]:
        return_mode = st.selectbox("Tipo de retorno", ["Retorno guiado", "Retorno livre com flecha"])
    with r[1]:
        if return_mode == "Retorno guiado":
            mu_return = number_input_pt("Atrito no retorno μ_ret [-]", min_value=0.,
                                        value=.25, step=.01)
            sag_mm, internal_return_type = 80., "Guiado"
        else:
            sag_mm = number_input_pt("Flecha do retorno s [mm]", min_value=1.,
                                     value=80., step=5.)
            mu_return, internal_return_type = 0., "Livre"

    r = st.columns(3)
    with r[0]:
        strands = number_input_pt("Vias de corrente [-]", min_value=1, value=4, step=1)
    with r[1]:
        chain_mass_per_m = number_input_pt("Massa linear da corrente [kg/m]", min_value=.01,
                                            value=7.30, step=.10,
                                            help="Massa por metro de UMA via completa de corrente, incluindo sua largura e configuração.")
    with r[2]:
        mu_top = number_input_pt("Atrito superior μ_top [-]", min_value=0.,
                                 value=.35, step=.01)
    mass_breakdown_slot = st.empty()

    r = st.columns(3)
    with r[0]:
        load_mass = number_input_pt("Carga transportada [kg]", min_value=.01, value=276., step=10.)
    with r[1]:
        additional_force = number_input_pt("Força adicional F_add [N]", min_value=0.,
                                           value=0., step=10.)
    with r[2]:
        linear_speed = number_input_pt("Velocidade desejada [m/min]", min_value=.01,
                                       value=35., step=1.)

    r = st.columns(3)
    with r[0]:
        consider_acceleration = st.toggle("Aceleração", value=True)
    with r[1]:
        acceleration_time = (number_input_pt("Tempo de aceleração [s]", min_value=.01,
                                             value=3., step=.5)
                             if consider_acceleration else 0.)
    with r[2]:
        design_factor = number_input_pt("Fator de projeto do acionamento [-]", min_value=1.,
                                        value=1.5, step=.05,
                                        help="Aplicado UMA VEZ à demanda de força, torque e potência. Não equivale ao fator de segurança contra ruptura da corrente nem ao fator de serviço do catálogo.")

conveyor = calculate_conveyor(ConveyorInput(
    center_distance_m=center_distance_m,
    strands=int(strands),
    chain_mass_per_m_kg=chain_mass_per_m,
    inclination_deg=inclination_deg,
    conveyor_sprocket_pitch_diameter_mm=conveyor_dp,
    return_type=internal_return_type,
    return_sag_mm=sag_mm,
    mu_top=mu_top,
    mu_return=mu_return,
    load_mass_kg=load_mass,
    linear_speed_m_min=linear_speed,
    additional_process_force_n=additional_force,
    acceleration_time_s=acceleration_time,
    design_factor=design_factor,
))

with mass_breakdown_slot.container():
    cell_grid([
        ("Correntes superiores", f"{fmt(conveyor.top_chain_mass_kg,1)} kg"),
        ("Correntes do retorno", f"{fmt(conveyor.return_chain_mass_kg,1)} kg"),
        ("Correntes nos arcos", f"{fmt(conveyor.arc_chain_mass_kg,1)} kg"),
        ("Massa total das correntes", f"{fmt(conveyor.total_chain_mass_kg,1)} kg"),
    ], columns=4)

with col_scheme:
    section_bar("ESQUEMA DO SISTEMA")
    render_schematic(IMG_RETURN if return_mode == "Retorno guiado" else IMG_SAG,
                     "Imagem do esquema de retorno não encontrada.")
    st.markdown('<div class="tiny-caption">Esquema ilustrativo estático · valores calculados abaixo</div>',
                unsafe_allow_html=True)

section_bar("DEMANDA DO SISTEMA")
demand_items = [
    ("Força de projeto", f"{fmt(conveyor.design_force_n,0)} N"),
    ("Força por via", f"{fmt(conveyor.force_per_strand_n,0)} N"),
    ("Torque no eixo", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m"),
    ("Potência", f"{fmt(conveyor.required_axis_power_kw,2)} kW"),
    ("Potência", f"{fmt(conveyor.required_axis_power_cv,2)} cv"),
    ("Rotação do eixo", f"{fmt(conveyor.required_axis_speed_rpm,1)} rpm"),
    ("Massa apoiada no trecho superior", f"{fmt(conveyor.top_supported_mass_kg,1)} kg"),
    ("Massa total das correntes", f"{fmt(conveyor.total_chain_mass_kg,1)} kg"),
    ("Atrito superior F_top", f"{fmt(conveyor.top_friction_n,0)} N"),
    ("Atrito no retorno F_ret", f"{fmt(conveyor.return_friction_n,0)} N"),
    ("Resistência em regime", f"{fmt(conveyor.regime_force_n,0)} N"),
]
if consider_acceleration:
    demand_items.extend([
        ("Aceleração", f"{fmt(conveyor.acceleration_m_s2,3)} m/s²"),
        ("Força de aceleração", f"{fmt(conveyor.acceleration_force_n,0)} N"),
    ])
cell_grid(demand_items, columns=5)

# -----------------------------------------------------------------------------
# 2 — DRIVE CONNECTION
# -----------------------------------------------------------------------------
col_conn_input, col_conn_img = st.columns([.95, 1.05], gap="medium")
with col_conn_input:
    section_bar("2 · CONEXÃO DO ACIONAMENTO")
    coupling_mode = st.radio("Conexão", ["Direto", "Transmissão secundária por corrente"],
                             horizontal=True)
    if coupling_mode == "Transmissão secundária por corrente":
        internal_coupling = "Transmissão secundária"
        r = st.columns(3)
        with r[0]:
            secondary_dp1 = number_input_pt("Dp1 [mm]", min_value=1., value=170., step=1.)
        with r[1]:
            secondary_dp2 = number_input_pt("Dp2 [mm]", min_value=1., value=202.66, step=1.)
        with r[2]:
            secondary_eff = number_input_pt("η_sec [%]", min_value=1., max_value=100.,
                                            value=98., step=.5)
    else:
        internal_coupling = "Direto"
        secondary_dp1, secondary_dp2, secondary_eff = 1., 1., 100.

transmission = SecondaryTransmissionInput(
    coupling_type=internal_coupling,
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
with col_conn_input:
    cell_grid([
        ("Rotação necessária no redutor", f"{fmt(requirement.required_reducer_speed_rpm,1)} rpm"),
        ("Torque necessário no redutor", f"{fmt(requirement.required_reducer_torque_nm,1)} N·m"),
        ("Potência necessária no redutor", f"{fmt(requirement.required_reducer_power_kw,2)} kW"),
    ], columns=1)
with col_conn_img:
    section_bar("ESQUEMA DO ACIONAMENTO")
    render_schematic(IMG_DIRECT if coupling_mode == "Direto" else IMG_REDUCTION,
                     "Imagem do esquema de acionamento não encontrada.")
    st.markdown('<div class="tiny-caption">Esquema ilustrativo estático</div>',
                unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3 — PROVIDED DRIVE
# -----------------------------------------------------------------------------
col_drive, col_compare = st.columns([1.25, .75], gap="medium")
with col_drive:
    section_bar("3 · ACIONAMENTO DISPONÍVEL")
    supply_mode = st.radio(
        "Tipo de acionamento",
        ["Catálogo IBR Q", "Motoredutor completo", "Redutor e motor separados"],
        horizontal=True,
        index=0,
    )
    ibr_row = None
    ibr_perf = None
    ibr_required_fs = None
    ibr_radial_catalogue = None
    if supply_mode == "Catálogo IBR Q":
        st.caption("Redutor de rosca sem-fim IBR Q · tabela transcrita das páginas 13 e 14 do catálogo · "
                   "tamanhos 075 a 150 e reduções 30, 40 e 50. O trecho não cobre toda a linha.")
        r1 = st.columns([1, 1, 2, 1])
        with r1[0]:
            ibr_size = st.selectbox("Tamanho IBR Q", SIZES, index=1,
                                    key="ibr_size", on_change=_reset_ibr_catalog_motor)
        with r1[1]:
            ibr_ratio = st.selectbox("Redução i [-]", RATIOS, index=1, format_func=lambda value: fmt(value, 0),
                                     key="ibr_ratio", on_change=_reset_ibr_catalog_motor)
        ibr_row = get_ibr_q(ibr_size, ibr_ratio)
        with r1[2]:
            ibr_motor_kw = motor_power_pair("ibr_motor", cv_to_kw(ibr_row.catalogue_motor_cv))
        with r1[3]:
            ibr_motor_rpm = number_input_pt("Rotação do motor [rpm]", min_value=1.0,
                                           value=1700.0, step=10.0, key="ibr_motor_rpm")
        ibr_perf = evaluate_ibr_q(ibr_row, kw_to_cv(ibr_motor_kw), ibr_motor_rpm)
        r2 = st.columns(3)
        with r2[0]:
            ibr_starts = st.selectbox("Partidas por hora", ["<10", ">10"], index=0)
        with r2[1]:
            ibr_duty = st.selectbox("Classificação da carga", ["Carga uniforme", "Choques moderados", "Choques intensos"], index=1)
        with r2[2]:
            ibr_hours = st.selectbox("Operação [horas/dia]", ["<2", "2–10", ">10"], index=1)
        ibr_required_fs = required_service_factor(ibr_starts, {"Carga uniforme": "Uniform load", "Choques moderados": "Moderate shocks", "Choques intensos": "Severe shocks"}[ibr_duty], ibr_hours)
        ibr_service_status = ("OK" if ibr_perf.service_factor_motor >= ibr_required_fs - 1e-6
                              else "EM REVISÃO")
        # Actual-demand diagnostic: base includes acceleration, excludes the explicit design factor.
        ibr_base_torque = requirement.required_reducer_torque_nm / design_factor
        ibr_effective_fs_base = (ibr_row.nominal_torque_nm / ibr_base_torque
                                 if ibr_base_torque > 0 else float('inf'))
        ibr_effective_fs_design = (ibr_row.nominal_torque_nm / requirement.required_reducer_torque_nm
                                   if requirement.required_reducer_torque_nm > 0 else float('inf'))
        cell_grid([
            ("Limite PMot do catálogo", f"{fmt(ibr_row.catalogue_motor_cv,2)} cv"),
            ("M2M com o motor informado", f"{fmt(ibr_perf.output_torque_nm,1)} N·m"),
            ("M2Nom do catálogo", f"{fmt(ibr_row.nominal_torque_nm,0)} N·m"),
            ("Rendimento do redutor η", f"{fmt(ibr_row.efficiency_pct,0)} %"),
            ("fs com potência nominal do motor", f"{fmt(ibr_perf.service_factor_motor,2)} ({ibr_service_status})"),
            ("fs necessário para o regime", f"{fmt(ibr_required_fs,2)}"),
            ("fs em relação à carga base calculada", f"{fmt(ibr_effective_fs_base,2)}"),
            ("M2Nom / torque de projeto", f"{fmt(ibr_effective_fs_design,2)}"),
            ("FR2 admissível na saída", f"{fmt(ibr_row.admissible_radial_output_n,0)} N"),
            ("PNom do catálogo", f"{fmt(ibr_row.nominal_input_cv,2)} cv"),
        ], columns=4)
        if not (ibr_perf.within_catalogue_motor_limit and ibr_perf.within_nominal_input_limit
                and ibr_perf.within_nominal_torque_limit):
            st.error("O motor informado excede um limite do catálogo. Selecione um motor menor ou um redutor maior.")
        if ibr_service_status != "OK":
            st.warning("O fator de serviço do catálogo com o torque nominal pleno do motor está abaixo do "
                       "valor exigido pelo regime selecionado. O fator efetivo em relação à "
                       "carga base calculada pode ser maior, pois o motor não está em plena carga. "
                       "O fator de projeto já está incluído no torque necessário. "
                       "Confirme com a IBR o critério de seleção e a combinação das margens.")
        if coupling_mode == "Transmissão secundária por corrente":
            st.caption("Verificação preliminar da força radial IBR para corrente secundária: "
                       "FR ≈ 2000 × M2M × 1,25 × p / Dp1. O fator p depende do ponto de aplicação da força.")
            ibr_p = st.selectbox("Fator do ponto de aplicação p", [1.0, 1.5], index=0, format_func=lambda value: fmt(value, 1),
                                 help="No catálogo, p = 1 ou 1,5 depende da distância de aplicação da força em relação "
                                      "ao comprimento do eixo de saída. Verifique o ponto real de aplicação antes de adotar p = 1.")
            ibr_radial_catalogue = catalogue_radial_force(
                ibr_perf.output_torque_nm, secondary_dp1, 1.25, ibr_p)
            _, radial_catalogue_status = capacity_status(
                ibr_row.admissible_radial_output_n, ibr_radial_catalogue)
            cell_grid([
                ("FR estimada IBR com o motor nominal", f"{fmt(ibr_radial_catalogue,0)} N"),
                ("FR2 admissível IBR", f"{fmt(ibr_row.admissible_radial_output_n,0)} N"),
                ("Verificação radial do catálogo", "ATENDE" if ibr_radial_catalogue <= ibr_row.admissible_radial_output_n else "NÃO ATENDE"),
            ], columns=3)
            st.caption("Esta é a estimativa simplificada de carga radial do catálogo IBR para a potência nominal selecionada. "
                       "A análise vetorial das tensões dos ramos ainda é necessária. A situação radial final permanece EM REVISÃO.")
        st.caption("O catálogo utiliza n1 = 1700 rpm como referência para motor de 4 polos. A rotação informada altera a rotação de saída "
                   "e o M2M calculado. Como aproximação, o rendimento e o limite de torque permanecem nos valores do catálogo.")
        if coupling_mode == "Direto":
            with st.expander("Alternativas IBR Q para esta redução e potência do motor"):
                alternatives = []
                for size in SIZES:
                    alt_row = get_ibr_q(size, ibr_ratio)
                    alt_motor_cv = min(ibr_perf.motor_power_cv, alt_row.catalogue_motor_cv)
                    alt_perf = evaluate_ibr_q(alt_row, alt_motor_cv, ibr_motor_rpm)
                    alt_speed = pi * (conveyor_dp / 1000.0) * alt_perf.output_rpm
                    speed_ok = abs(alt_speed / linear_speed - 1.0) <= .05
                    torque_ok = alt_perf.output_torque_nm >= conveyor.required_axis_torque_nm
                    power_ok = alt_perf.output_power_kw >= conveyor.required_axis_power_kw
                    fs_ok = alt_perf.service_factor_motor >= ibr_required_fs
                    alt_status = "ATENDE*" if speed_ok and torque_ok and power_ok and fs_ok else "EM REVISÃO"
                    alternatives.append({
                        "Modelo": f"IBR Q{size}", "i": fmt(ibr_ratio, 0),
                        "Motor [cv]": fmt(alt_motor_cv, 2),
                        "Velocidade [m/min]": fmt(alt_speed, 2),
                        "M2M [N·m]": fmt(alt_perf.output_torque_nm, 1),
                        "M2Nom [N·m]": fmt(alt_row.nominal_torque_nm, 0),
                        "fs com o motor": fmt(alt_perf.service_factor_motor, 2),
                        "fs necessário": fmt(ibr_required_fs, 2),
                        "FR2 [N]": fmt(alt_row.admissible_radial_output_n, 0),
                        "Resultado preliminar": alt_status,
                    })
                st.dataframe(pd.DataFrame(alternatives), hide_index=True, width="stretch")
                st.caption("*ATENDE indica apenas uma verificação numérica preliminar. Verifique o limite térmico, "
                           "a seleção do fabricante, a montagem e o regime real de serviço. "
                           "A potência do motor está limitada ao menor valor entre a potência "
                           "informada e o PMot máximo de cada linha do catálogo. "
                           "O fator de projeto já está incluído no torque e na potência necessários.")
        effective_torque = min(ibr_perf.output_torque_nm, ibr_row.nominal_torque_nm)
        effective_power = effective_torque * 2 * pi * ibr_perf.output_rpm / 60 / 1000
        drive = DriveOutput(
            reducer_output_speed_rpm=ibr_perf.output_rpm,
            reducer_output_torque_nm=effective_torque,
            reducer_output_power_kw=effective_power,
            admissible_radial_force_n=ibr_row.admissible_radial_output_n,
        )
    elif supply_mode == "Motoredutor completo":
        r1 = st.columns([1, 1, 2, 1])
        with r1[0]:
            gm_manufacturer = st.text_input("Fabricante", "SEW-EURODRIVE")
        with r1[1]:
            gm_model = st.text_input("Modelo", "")
        with r1[2]:
            gm_motor_power = motor_power_pair("gearmotor", 15.0)
        with r1[3]:
            gm_motor_speed = number_input_pt("Rotação do motor [rpm]", min_value=.01,
                                             value=1777., step=1., key="gearmotor_rpm")
        r2 = st.columns(4)
        with r2[0]:
            gm_ratio = number_input_pt("Redução", min_value=.001, value=22.37, step=.01)
        with r2[1]:
            gm_output_speed = number_input_pt("Rotação de saída [rpm]", min_value=.01,
                                              value=79., step=1.)
        with r2[2]:
            gm_output_torque = number_input_pt("Torque de saída [N·m]", min_value=.01,
                                               value=1790., step=10.)
        with r2[3]:
            gm_radial = number_input_pt("Limite radial [N]", min_value=0.,
                                        value=15600., step=100., key="gearmotor_radial")
        gm_service_factor = number_input_pt(
            "Fator de serviço do fabricante [-]", min_value=0., value=1.50, step=.05,
            help="Fator específico do catálogo do fabricante, apresentado como referência. Não multiplica a potência nem o torque disponíveis.",
        )
        drive = complete_gearmotor_output(CompleteGearmotorInput(
            manufacturer=gm_manufacturer, model=gm_model,
            motor_power_kw=gm_motor_power, motor_speed_rpm=gm_motor_speed,
            output_speed_rpm=gm_output_speed, total_ratio=gm_ratio,
            output_torque_nm=gm_output_torque, admissible_radial_force_n=gm_radial,
            manufacturer_service_factor=gm_service_factor,
        ))
    else:
        section_bar("REDUTOR")
        r1 = st.columns(4)
        with r1[0]:
            reducer_manufacturer = st.text_input("Fabricante do redutor", "Geremia")
        with r1[1]:
            reducer_model = st.text_input("Modelo do redutor", "GD30/2R")
        with r1[2]:
            reducer_ratio = number_input_pt("Redução do redutor", min_value=.001,
                                             value=35., step=.01)
        with r1[3]:
            reducer_eff = number_input_pt("Rendimento do redutor η [%]", min_value=.01,
                                          max_value=100., value=96., step=.5)
        r2 = st.columns(3)
        with r2[0]:
            reducer_max_torque = number_input_pt("Torque máximo [N·m]", min_value=0.,
                                                 value=370., step=10.)
        with r2[1]:
            reducer_radial = number_input_pt("Limite radial [N]", min_value=0.,
                                             value=6300., step=100., key="separate_radial")
        with r2[2]:
            reducer_max_power = number_input_pt("Potência máxima de entrada [kW]", min_value=0.,
                                                value=1.50, step=.10)
        section_bar("MOTOR")
        r3 = st.columns([1, 1, 2, 1])
        with r3[0]:
            motor_manufacturer = st.text_input("Fabricante do motor", "WEG")
        with r3[1]:
            motor_model = st.text_input("Modelo do motor", "")
        with r3[2]:
            motor_power = motor_power_pair("separate_motor", 1.50)
        with r3[3]:
            motor_speed = number_input_pt("Rotação do motor [rpm]", min_value=.01,
                                          value=1745., step=1., key="separate_rpm")
        r4 = st.columns(3)
        with r4[0]:
            motor_eff = number_input_pt("Rendimento do motor η [%]", min_value=.01,
                                        max_value=100., value=86.5, step=.1)
        with r4[1]:
            nominal_freq = number_input_pt("Frequência nominal [Hz]", min_value=.01,
                                           value=60., step=1.)
        with r4[2]:
            operating_freq = number_input_pt("Frequência de operação [Hz]", min_value=.01,
                                             value=60., step=1.)
        drive = separate_drive_output(SeparateDriveInput(
            reducer_manufacturer=reducer_manufacturer, reducer_model=reducer_model,
            reducer_ratio=reducer_ratio, reducer_efficiency_pct=reducer_eff,
            reducer_max_torque_nm=reducer_max_torque,
            reducer_admissible_radial_force_n=reducer_radial,
            reducer_max_input_power_kw=reducer_max_power,
            motor_manufacturer=motor_manufacturer, motor_model=motor_model,
            motor_power_kw=motor_power, motor_speed_rpm=motor_speed,
            motor_efficiency_pct=motor_eff, nominal_frequency_hz=nominal_freq,
            operating_frequency_hz=operating_freq,
        ))

final_output = calculate_final_output(drive, transmission, conveyor_dp)

# -----------------------------------------------------------------------------
# 4 — REQUIRED VS AVAILABLE
# -----------------------------------------------------------------------------
with col_compare:
    section_bar("4 · NECESSÁRIO × DISPONÍVEL")
    _, speed_state = speed_status(final_output.linear_speed_m_min, linear_speed)
    power_ratio, power_state = capacity_status(final_output.axis_power_kw,
                                               conveyor.required_axis_power_kw)
    torque_ratio, torque_state = capacity_status(final_output.axis_torque_nm,
                                                 conveyor.required_axis_torque_nm)
    rows = [
        ("Velocidade", f"{fmt(linear_speed,1)} m/min",
         f"{fmt(final_output.linear_speed_m_min,1)} m/min", speed_state),
        ("Potência", f"{fmt(conveyor.required_axis_power_kw,2)} kW",
         f"{fmt(final_output.axis_power_kw,2)} kW", power_state),
        ("Torque", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m",
         f"{fmt(final_output.axis_torque_nm,1)} N·m", torque_state),
    ]
    if supply_mode == "Catálogo IBR Q" and ibr_row is not None:
        # Catalog duty screening is distinct from the force/torque design margin.
        rows.append(("Fator de serviço IBR com motor nominal",
                     f"{fmt(ibr_required_fs,2)} mínimo",
                     f"{fmt(ibr_perf.service_factor_motor,2)}",
                     "OK" if ibr_perf.service_factor_motor >= ibr_required_fs else "EM REVISÃO"))
        if not (ibr_perf.within_catalogue_motor_limit
                and ibr_perf.within_nominal_input_limit
                and ibr_perf.within_nominal_torque_limit):
            rows.append(("Limites de entrada e saída do catálogo", "Dentro dos limites", "Excedidos", "NÃO ATENDE"))
    if coupling_mode == "Transmissão secundária por corrente":
        # Actual radial loading depends on tight/slack tensions and geometry.
        # Ft alone cannot prove radial compliance.
        rows.append(("Carga radial", "Não determinada",
                     f"{fmt(drive.admissible_radial_force_n,0)} N", "EM REVISÃO"))

    html = ['<div class="cell-grid" style="grid-template-columns:1.1fr .95fr .95fr .62fr">']
    for label in ("Parâmetro", "Necessário", "Disponível", "Situação"):
        html.append(f'<div class="cell"><div class="cell-value">{escape(label)}</div></div>')
    for label, req_value, avail_value, status in rows:
        for caption, value in (("Parâmetro", escape(label)),
                               ("Necessário", escape(req_value)),
                               ("Disponível", escape(avail_value)),
                               ("Situação", status_badge(status))):
            html.append(f'<div class="cell"><div class="cell-label">{caption}</div>'
                        f'<div class="cell-value">{value}</div></div>')
    st.markdown("".join(html) + "</div>", unsafe_allow_html=True)

    cell_grid([
        ("Rotação disponível no eixo", f"{fmt(final_output.axis_speed_rpm,1)} rpm"),
        ("Torque disponível no eixo", f"{fmt(final_output.axis_torque_nm,1)} N·m"),
        ("Potência disponível no eixo", f"{fmt(final_output.axis_power_kw,2)} kW"),
        ("Velocidade linear disponível", f"{fmt(final_output.linear_speed_m_min,1)} m/min"),
    ], columns=2)
    if coupling_mode == "Transmissão secundária por corrente":
        cell_grid([
            ("Força tangencial Ft (não é FR)",
             f"{fmt(final_output.radial_tangential_force_n or 0.,0)} N"),
            ("Carga radial admissível", f"{fmt(drive.admissible_radial_force_n,0)} N"),
            ("Dp1 teórico considerando apenas Ft",
             f"{fmt(final_output.critical_pitch_diameter_mm,1)} mm"
             if final_output.critical_pitch_diameter_mm is not None else "Não se aplica"),
        ], columns=1)
        st.caption("A carga radial permanece EM REVISÃO: Ft = T1 − T2 não é a soma vetorial das tensões nos ramos da corrente.")

# -----------------------------------------------------------------------------
# AUXILIARY MASS CALCULATOR + GLOSSARY — preserved as collapsed sections.
# -----------------------------------------------------------------------------
with st.expander("Calculadora auxiliar de massa transportada"):
    density = number_input_pt("Densidade do material ρ [kg/m³]", min_value=.01,
                              value=600., step=10., key="density")
    c1, c2 = st.columns(2)
    with c1:
        section_bar("PRISMA RETANGULAR")
        if IMG_PRISM:
            st.image(str(IMG_PRISM), width="stretch")
        rr = st.columns(3)
        with rr[0]:
            l1 = number_input_pt("ℓ1 [m]", value=3., step=.1, key="p_l1")
        with rr[1]:
            l2 = number_input_pt("ℓ2 [m]", value=.4, step=.01, key="p_l2")
        with rr[2]:
            l3 = number_input_pt("ℓ3 [m]", value=.2, step=.01, key="p_l3")
        vol, mass = rectangular_mass(l2, l3, l1, density)
        cell_grid([("Volume", f"{fmt(vol,3)} m³"),
                   ("Massa", f"{fmt(mass,1)} kg")], columns=2)
    with c2:
        section_bar("CILINDRO / TORA")
        if IMG_CYLINDER:
            st.image(str(IMG_CYLINDER), width="stretch")
        rr = st.columns(2)
        with rr[0]:
            d = number_input_pt("Ø [m]", value=.4, step=.01, key="c_d")
        with rr[1]:
            l = number_input_pt("ℓ1 [m]", value=3., step=.1, key="c_l")
        vol, mass = cylindrical_mass(d, l, density)
        cell_grid([("Volume", f"{fmt(vol,3)} m³"),
                   ("Massa", f"{fmt(mass,1)} kg")], columns=2)

with st.expander("Notas de engenharia e glossário de variáveis"):
    glossary = pd.DataFrame([
        ["C", "Distância entre centros do transportador", "m"],
        ["Dp", "Diâmetro primitivo da roda do transportador", "mm"],
        ["q", "Massa linear de uma via completa de corrente", "kg/m"],
        ["N", "Quantidade de vias paralelas de corrente", "—"],
        ["m_load", "Massa do material transportado", "kg"],
        ["m_top", "Massa das correntes no trecho reto superior", "kg"],
        ["m_ret", "Massa das correntes no trecho de retorno", "kg"],
        ["m_arc", "Massa das correntes nos dois semiarcos das rodas", "kg"],
        ["F_add", "Força adicional de processo", "N"],
        ["F_top", "Força de atrito superior", "N"],
        ["F_ret", "Força de atrito no retorno guiado", "N"],
        ["s", "Flecha no retorno livre", "mm"],
        ["μ_top", "Coeficiente de atrito superior", "—"],
        ["μ_ret", "Coeficiente de atrito no retorno", "—"],
        ["f_d", "Fator de projeto do acionamento", "—"],
        ["f_B", "Fator de serviço do catálogo do fabricante", "—"],
        ["Dp1", "Diâmetro primitivo da roda do redutor", "mm"],
        ["Dp2", "Diâmetro primitivo da roda no eixo do transportador", "mm"],
        ["α", "Inclinação do transportador", "°"],
        ["T1, T2", "Tensões nos ramos tenso e frouxo da corrente de transmissão", "N"],
        ["F_R", "Força radial resultante na roda do redutor", "N"],
    ], columns=["Variável", "Descrição", "Unidade"])
    st.dataframe(glossary, hide_index=True, width="stretch")
    st.markdown("""<div class="panel-note">
      <b>Correntes paralelas:</b> a força por via pressupõe uma distribuição aproximadamente uniforme da carga.
      Os comprimentos das correntes, as rodas, as guias e o tensionamento devem ser compatíveis.<br>
      <b>Integridade estrutural:</b> a resistência à ruptura da corrente, as cargas nos mancais, o engrenamento dos dentes
      e a carga radial no redutor exigem verificações adicionais. Não há aprovação estrutural.
    </div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FULL EQUATION TRACE — LAST SECTION OF THE APP, COLLAPSED BY DEFAULT.
# -----------------------------------------------------------------------------
with st.expander("Metodologia de cálculo · equações e resultados atuais"):
    st.markdown("Esta sequência utiliza os dados selecionados e um modelo de forças quase estático com aceleração linear uniforme. A inércia das rodas, os choques transitórios, as perdas nas articulações e a resistência estrutural das correntes ainda não são modelados.")
    st.caption('Notação brasileira: vírgula decimal e ponto para milhares. Exemplo: 1" = 25,4 mm.')
    st.markdown("**1. Geometria e massa das correntes**")
    st.latex(r"m_{sup}=NqC \qquad m_{ret}=NqL_{ret} \qquad m_{arcos}=Nq\pi D_p")
    if internal_return_type == "Guiado":
        st.latex(r"L_{ret}=C")
        st.markdown("No retorno guiado, os comprimentos retos superior e inferior são iguais. Portanto, suas massas de corrente também são iguais.")
    else:
        st.latex(r"L_{ret}\approx C+\frac{8s^2}{3C}")
        st.markdown("O comprimento do retorno livre utiliza uma aproximação parabólica. Nas equações, a flecha s e o diâmetro Dp são expressos em metros.")
    st.latex(r"m_{correntes}=m_{sup}+m_{ret}+m_{arcos}")
    st.caption(f"C = {fmt(center_distance_m,5)} m · N = {int(strands)} · q = {fmt(chain_mass_per_m,2)} kg/m · L_ret = {fmt(conveyor.return_length_m,4)} m")
    st.caption(f"Trecho superior = {fmt(conveyor.top_chain_mass_kg,2)} kg · retorno = {fmt(conveyor.return_chain_mass_kg,2)} kg · arcos = {fmt(conveyor.arc_chain_mass_kg,2)} kg · total = {fmt(conveyor.total_chain_mass_kg,2)} kg")
    st.markdown("**2. Massa apoiada no trecho superior e forças de atrito**")
    st.latex(r"m_{apoiada}=m_{carga}+m_{sup} \qquad F_{sup}=\mu_{sup}m_{apoiada}g\cos\alpha")
    if internal_return_type == "Guiado":
        st.latex(r"F_{ret}=\mu_{ret}m_{ret}g\cos\alpha")
    else:
        st.latex(r"F_{ret}=0 \qquad w=qg \qquad H\approx\frac{wC^2}{8s} \qquad V\approx\frac{wC}{2} \qquad T=\sqrt{H^2+V^2}")
        st.markdown("No retorno livre, o modelo não considera atrito de deslizamento nas guias. A corrente continua tracionada pelo próprio peso.")
        st.caption(f"Aproximação por via: H = {fmt(conveyor.catenary_horizontal_n or 0.,1)} N · V = {fmt(conveyor.catenary_vertical_n or 0.,1)} N · T = {fmt(conveyor.catenary_tension_n or 0.,1)} N")
    st.caption(f"Massa apoiada = {fmt(conveyor.top_supported_mass_kg,2)} kg · μ_top = {fmt(mu_top,2)} · μ_ret = {fmt(mu_return,2)} · F_top = {fmt(conveyor.top_friction_n,2)} N · F_ret = {fmt(conveyor.return_friction_n,2)} N")
    st.markdown("**3. Inclinação e resistência em regime**")
    st.latex(r"F_{incl}=m_{carga}g\sin\alpha \qquad F_{regime}=F_{sup}+F_{ret}+F_{incl}+F_{adicional}")
    st.caption(f"F_incl = {fmt(conveyor.inclination_force_n,2)} N · F_adicional = {fmt(additional_force,2)} N · F_regime = {fmt(conveyor.regime_force_n,2)} N")
    st.markdown("**4. Aceleração e massa móvel**")
    st.latex(r"v=\frac{v_{m/min}}{60} \qquad m_{movel}=m_{carga}+m_{correntes} \qquad a=\frac{v}{t_a} \qquad F_a=m_{movel}a")
    st.markdown("Quando a aceleração está desativada, a = 0 e F_a = 0.")
    st.caption(f"v = {fmt(linear_speed/60.,4)} m/s · massa móvel = {fmt(conveyor.moving_mass_kg,2)} kg · a = {fmt(conveyor.acceleration_m_s2,4)} m/s² · F_a = {fmt(conveyor.acceleration_force_n,2)} N")
    st.markdown("**5. Fator de projeto aplicado uma única vez**")
    st.latex(r"F_{base}=F_{regime}+F_a \qquad F_{projeto}=f_dF_{base} \qquad F_{via}=\frac{F_{projeto}}{N}")
    st.caption(f"F_base = {fmt(conveyor.force_before_design_factor_n,2)} N · f_d = {fmt(design_factor,2)} · F_projeto = {fmt(conveyor.design_force_n,2)} N · força por via = {fmt(conveyor.force_per_strand_n,2)} N")
    st.markdown("**6. Rotação, torque e potência no eixo do transportador**")
    st.latex(r"n_{eixo}=\frac{v_{m/min}}{\pi D_p} \qquad M_{eixo}=F_{projeto}\frac{D_p}{2}")
    st.latex(r"P_{eixo,kW}=\frac{F_{projeto}v}{1000} \qquad P_{cv}=\frac{P_{kW}}{0{,}73549875}")
    st.caption(f"n = {fmt(conveyor.required_axis_speed_rpm,2)} rpm · M = {fmt(conveyor.required_axis_torque_nm,2)} N·m · P = {fmt(conveyor.required_axis_power_kw,3)} kW = {fmt(conveyor.required_axis_power_cv,3)} cv")
    st.markdown("**7. Demanda na saída do redutor**")
    if internal_coupling == "Direto":
        st.latex(r"n_{red}=n_{eixo} \qquad M_{red}=M_{eixo} \qquad P_{red}=P_{eixo}")
    else:
        st.latex(r"i_{sec}=\frac{D_{p2}}{D_{p1}} \qquad n_{red}=i_{sec}n_{eixo} \qquad M_{red}=\frac{M_{eixo}}{i_{sec}\eta_{sec}} \qquad P_{red}=\frac{P_{eixo}}{\eta_{sec}}")
    st.caption(f"Redução secundária = {fmt(requirement.ratio,4)} · rotação necessária = {fmt(requirement.required_reducer_speed_rpm,2)} rpm · torque necessário = {fmt(requirement.required_reducer_torque_nm,2)} N·m · potência necessária = {fmt(requirement.required_reducer_power_kw,3)} kW")
    st.markdown("**8. Acionamento disponível e hipóteses**")
    if supply_mode == "Catálogo IBR Q":
        st.latex(r"n_2=\frac{n_1}{i} \qquad M_{2M}=\frac{7022P_{motor,cv}\eta}{n_2} \qquad f_{s,cat}=\frac{M_{2Nom}}{M_{2M}}")
        st.latex(r"P_{saida,kW}=\frac{2\pi n_2M_{2M}}{60000} \qquad f_{s,carga}=\frac{M_{2Nom}}{M_{red,base}} \qquad M_{red,base}=\frac{M_{red}}{f_d}")
        st.caption(f"IBR Q{ibr_row.size} · i = {fmt(ibr_row.ratio,0)} · n1 = {fmt(ibr_motor_rpm,1)} rpm · n2 = {fmt(ibr_perf.output_rpm,2)} rpm · motor = {fmt(ibr_perf.motor_power_cv,3)} cv · η = {fmt(ibr_row.efficiency_pct,0)} %")
        st.caption(f"M2M = {fmt(ibr_perf.output_torque_nm,2)} N·m · M2Nom = {fmt(ibr_row.nominal_torque_nm,1)} N·m · fs com motor nominal = {fmt(ibr_perf.service_factor_motor,3)} · fs necessário = {fmt(ibr_required_fs,2)} · fs da carga base = {fmt(ibr_effective_fs_base,2)} · M2Nom / torque de projeto = {fmt(ibr_effective_fs_design,2)}")
        st.markdown("O fator do catálogo utiliza o torque de saída com potência nominal plena do motor. Os fatores relativos à carga base e à demanda de projeto têm definições distintas. A página 4 do catálogo IBR define fs = M2Nom/M2M. A equação da página 9 está invertida em relação à tabela. Adota-se a definição da página 4. O fator é recalculado para a potência informada, que pode ser inferior ao PMot tabelado.")
        st.markdown("Fonte: PDF fornecido pelo usuário, páginas impressas 4, 5, 13 e 14. Trecho transcrito: IBR Q075 a Q150, reduções 30, 40 e 50.")
    elif supply_mode == "Motoredutor completo":
        st.latex(r"P_{red,kW}=\frac{2\pi n_{saida}M_{saida}}{60000}")
        st.caption(f"Saída do catálogo: n = {fmt(gm_output_speed,2)} rpm · M = {fmt(gm_output_torque,2)} N·m · P = {fmt(drive.reducer_output_power_kw,3)} kW. Motor = {fmt(gm_motor_power,3)} kW = {fmt(kw_to_cv(gm_motor_power),3)} cv")
        st.markdown("A potência disponível é calculada a partir do torque e da rotação de saída do catálogo. Potência nominal do motor, redução e fator de serviço são dados de referência. Verifique sua consistência no catálogo.")
    else:
        st.latex(r"n_m=n_{m,nom}\frac{f_{op}}{f_{nom}} \qquad P_{m,modelo}=P_{m,nom}\min\left(\frac{f_{op}}{f_{nom}},1\right)")
        st.latex(r"P_{m,lim}=\min(P_{m,modelo},P_{red,entrada,max}) \qquad n_{red}=\frac{n_m}{i_{red}}")
        st.latex(r"M_{red}=\min\left(\frac{9550P_{m,lim}}{n_m}i_{red}\eta_{red},M_{red,max}\right)")
        st.markdown("O modelo simplificado do inversor adota torque constante abaixo da frequência nominal e potência constante acima dela. Não representa uma curva de capacidade validada do motor. O rendimento do motor é apenas uma referência, pois a potência nominal é tratada como potência mecânica no eixo.")
        st.caption(f"Motor = {fmt(motor_power,3)} kW = {fmt(kw_to_cv(motor_power),3)} cv · saída do redutor: n = {fmt(drive.reducer_output_speed_rpm,2)} rpm · M = {fmt(drive.reducer_output_torque_nm,2)} N·m · P = {fmt(drive.reducer_output_power_kw,3)} kW")
    st.markdown("**9. Necessário × disponível no eixo do transportador**")
    st.latex(r"\lambda_M=\frac{M_{disponivel}}{M_{projeto}} \qquad \lambda_P=\frac{P_{disponivel}}{P_{projeto}} \qquad \delta_v=\frac{v_{disponivel}-v_{desejada}}{v_{desejada}}")
    st.caption(f"Relação de torque = {fmt(torque_ratio,3)} ({torque_state}) · relação de potência = {fmt(power_ratio,3)} ({power_state}) · desvio de velocidade = {fmt(100*(final_output.linear_speed_m_min-linear_speed)/linear_speed,2)} % ({speed_state})")
    st.markdown("Critérios da interface: relação de capacidade ≥ 1,20 → OK. De 1,00 até menos de 1,20 → ATENÇÃO. Abaixo de 1,00 → NÃO ATENDE. Velocidade dentro de ±5 % → OK. Fora dessa faixa → EM REVISÃO. Esses critérios são verificações preliminares, não uma certificação normativa do equipamento.")
    st.markdown("**10. Fatores de projeto, serviço e segurança**")
    st.latex(r"f_d=\frac{F_{projeto}}{F_{base}} \qquad f_B=\frac{M_{a,max}}{M_a} \qquad FS_{corrente}=\frac{F_{ruptura}}{F_{trabalho}}")
    st.markdown("O fator de projeto amplia a demanda calculada. O fator de serviço do fabricante caracteriza a capacidade do redutor segundo seu catálogo. A expressão f_B acima corresponde à definição SEW. O fator de segurança estrutural da corrente não é calculado, pois a carga de ruptura não foi informada. O fator de catálogo não é multiplicado novamente pelo fator de projeto. A aprovação do fabricante depende do regime, das partidas por hora, da temperatura, dos picos de carga e das condições do catálogo.")
    if supply_mode == "Motoredutor completo":
        st.caption(f"Fator de serviço informado pelo fabricante = {fmt(gm_service_factor,2)}, apenas como referência.")
    elif supply_mode == "Catálogo IBR Q":
        st.caption(f"fs IBR com o motor escolhido = {fmt(ibr_perf.service_factor_motor,2)} · mínimo para o regime = {fmt(ibr_required_fs,2)}. Confirme com a IBR o critério de combinação das margens.")
    st.markdown("**11. Carga radial da transmissão secundária**")
    if internal_coupling == "Direto":
        st.markdown("Não há corrente secundária selecionada. O aplicativo não avalia as cargas do acoplamento direto.")
    else:
        st.latex(r"F_t=T_1-T_2=\frac{2M_{red}}{D_{p1}} \qquad \vec F_R=T_1\hat u_1+T_2\hat u_2 \qquad F_R=\lVert\vec F_R\rVert")
        st.caption(f"Estimativa apenas de Ft = {fmt(final_output.radial_tangential_force_n or 0.,2)} N · limite radial do fabricante = {fmt(drive.admissible_radial_force_n,2)} N")
        st.warning("A carga radial real ainda não é calculada. São necessários a distância entre centros secundária, a geometria dos ramos, suas tensões e a pré-tensão de operação. O Dp1 teórico baseado apenas em Ft não é um diâmetro recomendado nem permite aprovar a carga radial.")
        if supply_mode == "Catálogo IBR Q":
            st.latex(r"F_{R,IBR}=\frac{2000M_{2M}f_kp}{D_{p1,mm}}")
            st.caption(f"Corrente secundária IBR: f_k = 1,25 · p = {fmt(ibr_p,1)} · FR estimada = {fmt(ibr_radial_catalogue,1)} N · limite FR2 = {fmt(ibr_row.admissible_radial_output_n,1)} N")
            st.markdown("A fórmula IBR é uma aproximação de seleção do fabricante. Sua comparação depende do ponto real de aplicação da carga e do arranjo dos mancais. A análise vetorial das tensões dos ramos continua necessária.")
    st.markdown("**Referências:** [Definição do fator de serviço SEW](https://download.sew-eurodrive.com/download/html/33346739/en-EN/38925667595.html) · [Fator de serviço de aplicação SEW](https://download.sew-eurodrive.com/download/html/33346739/en-EN/4007542375551665968267.html)")
