from pydantic import BaseModel, Field
from typing import Optional

class RiderProfile(BaseModel):
    weight_kg: float = Field(80.0, description="Rider weight for tire pressure and energy calculations.")
    fitness_level: str = Field("intermediate", description="Fitness level: 'beginner', 'intermediate', 'pro'.")

class BikeSetup(BaseModel):
    bike_type: str = Field("MTB", description="Type: 'MTB', 'Road', 'Gravel', 'E-MTB', 'Enduro'.")
    tire_size: str = Field("29", description="Wheel size: '29', '27.5', '700c', '650b'.")
    is_ebike: bool = Field(False, description="True if the bike has a motor.")
    battery_wh: Optional[int] = Field(None, description="Battery capacity in Wh (required for E-MTB).")

class MissionConstraints(BaseModel):
    radius_km: int = Field(10, description="Target distance for the loop.")
    profile: str = Field("cycling-mountain", description="ORS profile: cycling-mountain, cycling-road, cycling-regular.")
    surface_preference: str = Field("neutral", description="Preferences: 'neutral', 'prefer_paved', 'avoid_unpaved'.")
    complexity: int = Field(3, alias="points", description="Route shape complexity (3-10).")
    seed: int = Field(42, description="Seed for random route generation.")