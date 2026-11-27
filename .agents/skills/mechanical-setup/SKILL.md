## 2. Mechanical Setup & Tire Pressure
Prefer the pressure and compatibility data in `info.surface_analysis.mechanical_setup`
from `trail_scout_simple` (internal service `bikescout.tools.bike_setup.get_tire_setup`);
there is no standalone tire-setup MCP tool. Its volume/load model returns differential
`psi_front` / `psi_rear` values, equipment advice and warnings from rider mass, tire width
squared, rim internal width, casing stiffness and tubeless/tube setup. Ask the rider for
tire width (mm), rim internal width (mm), casing (xc/trail/enduro/dh) and tubeless status.

### Reference Pressures (tubeless, 85kg rider)
| Discipline | Tire Width | Front PSI | Rear PSI |
| :--- | :--- | :--- | :--- |
| **Road** | 25mm | ~80 | ~90 |
| **Gravel** | 40mm | ~33 | ~37 |
| **MTB** | 58mm (2.3") | ~20 | ~25 |
| **Enduro** | 60mm | ~18 | ~23 |
| **E-MTB** | 60mm | ~22 | ~28 |

### Pressure Adjustment Logic
- **Inner Tubes**: Add roughly 18% versus tubeless.
- **Load**: Total system mass (rider + bike) scales pressure with exponent 1.25.
- **Volume**: Wider tires need disproportionately less pressure (width squared).
- **Surface / Terrain**: Mud raises flotation, rocks/roots raise compliance; S3+ or
  high ascent adds a pinch-flat support floor, insert advice and a tubeless check.

---

## 3. Emergency Checklist
Before confirming "Ready to Ride," ensure the following items are logged:
1. **Multi-tool**: Hex keys, Torx, and chain breaker.
2. **Inflation**: Mini-pump or CO2 cartridges.
3. **Repair**: Spare tube, tire levers, and tubeless plugs (anchovies).
4. **Hydration/Nutrition**: Verify the calculated nutrition plan is packed.

---

## 4. Agent Operational Logic
When an user asks for a route or mission prep:
1. **Identify** the `bike_type` from the user profile.
2. **Retrieve** `info.surface_analysis.mechanical_setup` (`bike_type`, `compatible`, `setup_details`, `safety_warnings`) from the mission briefing.
3. **Apply** `setup_details` (front/rear PSI, strategy, casing, inserts) and `safety_warnings`, including the inner-tube correction, to the Mission Readiness Report.
4. **Output** a consolidated "Mission Readiness Report."