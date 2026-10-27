# Chain Conveyor Calculator

Streamlit application for sizing and checking multi-strand chain conveyors used in wood handling.

## Scope

The application separates:

1. **Conveyor requirement**
   - chain mass
   - guided or free return
   - friction
   - inclination
   - acceleration
   - process force
   - design factor
   - required force, torque, power and shaft speed

2. **Drive supply mode**
   - complete gearmotor (SEW-style configurator data)
   - reducer + motor selected separately

3. **Connection to conveyor shaft**
   - direct
   - secondary chain/sprocket transmission

4. **Checks**
   - required vs available speed
   - required vs available torque
   - required vs available power
   - tangential load at reducer sprocket
   - theoretical critical pitch diameter based on admissible radial load

## Engineering note

The application design factor is applied to the calculated **drive requirement** (force, torque and power). It is not the structural safety factor of the conveyor chain against breaking load.

The load per strand assumes reasonably uniform load sharing between parallel chains. This requires compatible chain lengths, synchronized sprockets, level guides, equivalent tensioning and similar wear between strands.

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Deploy on Streamlit Community Cloud

After pushing this repository to GitHub:

1. Open Streamlit Community Cloud.
2. Create a new app.
3. Select this GitHub repository.
4. Set the main file path to `app.py`.
5. Deploy.

No secrets are required for the current version.

## Planned next steps

- parametric conveyor schematic
- saved reducer/gearmotor database
- exportable calculation report
- optional chain structural verification
