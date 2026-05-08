import pytest

@pytest.fixture
def surface_map():
    return {
        "1": "Asphalt",
        "2": "Gravel",
        "3": "Grass",
        "4": "Muddy",
        "5": "Stony",
        "6": "None" 
    }

@pytest.fixture
def sample_extras():
    return {
        'surface': {
            'summary': [
                {'value': '1', 'amount': 70.0},
                {'value': '2', 'amount': 20.0},
                {'value': '6', 'amount': 10.0}
            ]
        }
    }