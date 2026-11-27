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

from __future__ import annotations

import pytest


@pytest.fixture
def surface_map():
    return {"1": "Asphalt", "2": "Gravel", "3": "Grass", "4": "Muddy", "5": "Stony", "6": "None"}


@pytest.fixture
def sample_extras():
    return {
        "surface": {
            "summary": [
                {"value": "1", "amount": 70.0},
                {"value": "2", "amount": 20.0},
                {"value": "6", "amount": 10.0},
            ]
        }
    }
