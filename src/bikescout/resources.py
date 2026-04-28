# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from inspect import cleandoc

class BikeScoutResources:
    """Static technical resources and safety protocols for cyclists."""

    BASE_COMMANDS = [
        "Verify helmet integrity",
        "Check GPS battery levels",
        "Sync offline maps"
    ]

    EXTRA_PROTOCOLS = {
        "ebike": [
            "Battery SoC check (>80% recommended)",
            "Power mode functionality test",
            "Speed sensor magnet alignment"
        ],
        "mtb": [
            "Shock and Fork sag/pressure check",
            "Dropper post operation",
            "Inspect knee/elbow pads integrity"
        ],
        "gravel": [
            "Tubeless sealant level check",
            "Frame bag clearance",
            "Flare bar alignment"
        ],
        "road": [
            "Rim brake wear or Disc pad thickness",
            "High-pressure tire integrity",
            "Rear light battery check"
        ]
    }

    SAFETY_CHECKLIST = cleandoc("""
        ### 🛡️ BikeScout Safety Checklist
        1. **M-Check**: Check hubs, bottom bracket, and headset for play.
        2. **Brakes**: Ensure pads have life and levers don't touch the bars.
        3. **Tires**: Check for cuts and ensure correct pressure.
        4. **Chain**: Clean and lubed?
        5. **Emergency**: Do you have a multi-tool, pump, and spare tube?
        6. **Helmet**: Buckle it up!
    """)

    PRESSURE_DATA = {
        "road": {"range": "4.5 - 5.5 Bar", "psi": "65-80 PSI", "width": "28mm"},
        "gravel": {"range": "2.0 - 3.0 Bar", "psi": "30-45 PSI", "width": "40mm"},
        "mtb": {"range": "1.4 - 1.8 Bar", "psi": "20-26 PSI", "width": "2.3\""}
    }

    TIRE_PRESSURE_GUIDE = cleandoc("""
        ### 🚲 Tire Pressure Recommendations (Tubeless)
        - **Road (28mm)**: 4.5 - 5.5 Bar (65-80 PSI)
        - **Gravel (40mm)**: 2.0 - 3.0 Bar (30-45 PSI)
        - **MTB (2.3")**: 1.4 - 1.8 Bar (20-26 PSI)

        *Note: Add 0.3 Bar if using inner tubes.*
    """)

    MECHANICAL_NOTES = "Pressures are for Tubeless. Add 0.3 Bar if using inner tubes."
