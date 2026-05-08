## 2. Mechanical Setup & Tire Pressure
The agent must provide pressure recommendations based on a standard 75kg rider baseline.

### Tubeless Pressure Reference Table
| Discipline | Width Reference | Bar Range | PSI Range |
| :--- | :--- | :--- | :--- |
| **Road** | 28mm | 4.5 - 5.5 | 65 - 80 |
| **Gravel** | 40mm | 2.0 - 3.0 | 30 - 45 |
| **MTB** | 2.3" | 1.4 - 1.8 | 20 - 26 |

### Pressure Adjustment Logic
- **Inner Tubes**: If the rider is NOT using tubeless, **ADD 0.3 Bar (approx. 5 PSI)** to the values above to prevent pinch flats.
- **Payload**: Increase pressure by 5-10% if the bike is loaded with heavy bikepacking bags.

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
2. **Retrieve** the corresponding `EXTRA_PROTOCOLS`.
3. **Calculate** the tire pressure using the `PRESSURE_DATA` and apply the `MECHANICAL_NOTES` regarding inner tubes.
4. **Output** a consolidated "Mission Readiness Report."