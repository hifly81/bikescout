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

import uuid
import time
from pathlib import Path
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

# --- BIKE SCOUT CORE SCHEMAS (PYDANTIC V2) ---

class RiderProfile(BaseModel):
    """
    Physiological data of the user.
    Required fields without defaults to force Agent-User interaction.
    """
    weight_kg: float = Field(
        75.0,
        description="Rider weight in kilograms. Critical for tire pressure and energy modeling.",
        json_schema_extra={"examples": [70.0, 85.5]}
    )
    fitness_level: Literal["beginner", "intermediate", "pro"] = Field(
        "intermediate",
        description="User's athletic preparation level. Affects fatigue and climbing logic.",
        json_schema_extra={"examples": ["intermediate"]}
    )

class BikeSetup(BaseModel):
    """
    Technical configuration of the bicycle.
    Includes cross-validation for electric bike specifications.
    """
    bike_type: Literal['MTB', 'Road', 'Gravel', 'E-MTB', 'Enduro', 'mtb', 'road', 'gravel', 'e-mtb', 'enduro'] = Field(
        "mtb",
        description="The category of the bike, used to filter suitable trail surfaces.",
        json_schema_extra={"examples": ["mtb", "road"]}
    )
    tire_size: Literal["32", "29", "27.5", "700c", "650b"] = Field(
        "29",
        description="Standard wheel diameter.",
        json_schema_extra={"examples": ["29", "700c"]}
    )
    is_ebike: bool = Field(
        False,
        description="Set to True if the bike has an electric motor.",
        json_schema_extra={"examples": [False]}
    )
    battery_wh: int = Field(
        625,
        description="Battery capacity in Watt-hours. Mandatory if is_ebike is True.",
        json_schema_extra={"examples": [625, 750]}
    )

    @model_validator(mode='after')
    def check_ebike_specs(self) -> 'BikeSetup':
        """
        Pydantic V2 model validator.
        Ensures battery data is provided if the bike is electric.
        """
        if self.is_ebike and self.battery_wh is None:
            raise ValueError("battery_wh must be specified for E-MTB setups.")
        return self

class MissionConstraints(BaseModel):
    """
    Tactical constraints for the specific ride/mission.
    """
    radius_km: int = Field(
        30,
        description="The desired search radius or loop length in kilometers.",
        json_schema_extra={"examples": [20, 50]}
    )
    profile: Literal["cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"] = Field(
        "cycling-mountain",
        description="The OpenRouteService routing profile.",
        json_schema_extra={"examples": ["cycling-mountain"]}
    )
    surface_preference: Literal["neutral", "prefer_paved", "avoid_unpaved"] = Field(
        "neutral",
        description="User preference for road vs off-road surfaces.",
        json_schema_extra={"examples": ["neutral"]}
    )
    complexity: int = Field(
        3,
        ge=3,
        le=10,
        serialization_alias="points",
        description="Number of waypoints to generate for the route shape (3-10).",
        json_schema_extra={"examples": [3, 5]}
    )
    seed: int = Field(
        42,
        description="Random seed for reproducibility of generated trails.",
        json_schema_extra={"examples": [11, 42]}
    )
    assist_mode: Literal["Eco", "Trail", "Boost", "eco", "trail", "boost"] = Field(
        "Eco",
        description="E-bike motor assistance level. Influences battery range predictions.",
        json_schema_extra={"examples": ["Trail"]}
    )

class RouteGeometry(BaseModel):
    """
    GeoJSON-compatible geometry container.
    Coordinates format: [longitude, latitude, elevation]
    """
    coordinates: List[List[float]] = Field(
        ...,
        description="A list of coordinate triplets: [lon, lat, ele].",
        json_schema_extra={
            "examples": [
                [[9.1913, 45.4642, 120.0], [9.1915, 45.4645, 122.5]]
            ]
        }
    )

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates_structure(cls, v: List[List[float]]) -> List[List[float]]:
        """
        Pydantic V2 field validator.
        Ensures each point has [lon, lat] and standardizes elevation.
        """
        if not v:
            raise ValueError("Coordinates list cannot be empty.")

        for point in v:
            if len(point) < 2:
                raise ValueError(f"Invalid point structure: {point}. Expected [lon, lat, ele].")
            if len(point) == 2:
                # Standardize to 3D by adding 0.0 elevation if missing
                point.append(0.0)
        return v

    @property
    def has_elevation(self) -> bool:
        """Helper to verify if the dataset contains meaningful vertical data."""
        return any(len(p) > 2 and p[2] != 0 for p in self.coordinates)

    def to_dict(self):
        """Converts the model back to a standard dictionary for MCP transport."""
        return self.model_dump()
