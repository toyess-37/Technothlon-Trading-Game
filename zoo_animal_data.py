"""
    Data models for the Fauna Fantastico game.
    This file contains the data structures for zoos, animals, and game mechanics.
"""

import math
import csv

# ----------------------------------------------------------------------------------------------------
# CONTINENT AND ZOO DATA

# Default biome assignment for continents
CONTINENT_BIOMES = {
    'A': 'tundra',
    'B': 'wetland',
    'C': 'ocean',
    'D': 'forest',
    'E': 'desert'
}

# Default zoo biomes
# Each continent has 5 zoos, each with a different biome
ZOO_BIOMES = {
    1: 'forest',
    2: 'tundra',
    3: 'ocean',
    4: 'desert',
    5: 'wetland'
}

""" 
    Multiplier table for zoo based on continent and biome
    The multiplier is used to calculate the final score of the zoo
    The multiplier is the highest for zoos in their native biome and lower for others
"""

MULTIPLIER_TABLE = {
    'A': [1.1, 1.25, 1.2, 1.2, 1.1], # A1->x1.1, A2->x1.25, A3->x1.2, A4->x1.2, A5->x1.1
    'B': [1.2, 1.2, 1.1, 1.1, 1.25], # B1->x1.2, B2->x1.2, B3->x1.1, B4->x1.1, B5->x1.25
    'C': [1.1, 1.1, 1.25, 1.2, 1.2], # C1->x1.1, C2->x1.1, C3->x1.25, C4->x1.2, C5->x1.2
    'D': [1.25, 1.2, 1.2, 1.1, 1.1], # D1->x1.25, D2->x1.2, D3->x1.2, D4->x1.1, D5->x1.1
    'E': [1.2, 1.1, 1.1, 1.25, 1.2]  # E1->x1.2, E2->x1.1, E3->x1.1, E4->x1.25, E5->x1.2
}

# Zoo template
def create_zoo(zoo_id, continent, biome_index):
    """Create a zoo with the specified attributes"""
    biome_type = ZOO_BIOMES[biome_index]
    
    # Calculate the multiplier based on the following table:
    multiplier = MULTIPLIER_TABLE[continent][biome_index-1]
    
    return {
        'id': zoo_id,
        'continent_index': continent,
        'continent': CONTINENT_BIOMES[continent],
        'biome_index': biome_index,
        'biome': biome_type,
        'owner': None,
        'animals': [],
        'coins': 100,
        'multiplier': multiplier
    }

# Initialize all 25 zoos

def initialize_zoos():
    zoos = {}

    for continent in 'ABCDE':
        for i in range(1, 6):
            zoo_id = f"{continent}{i}"
            zoos[zoo_id] = create_zoo(zoo_id, continent, i)

    return zoos
# ----------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------
# ANIMAL DATA

# Biome preferences (order of preference for animals in each biome)
PREFERENCE_ORDER = {
    'forest': ['ocean', 'desert', 'wetland', 'tundra', 'forest'],
    'tundra': ['wetland', 'forest', 'ocean', 'desert', 'tundra'],
    'ocean': ['desert', 'tundra', 'forest', 'wetland', 'ocean'],
    'desert': ['forest', 'ocean', 'tundra', 'desert', 'wetland'],
    'wetland': ['tundra', 'wetland', 'desert', 'forest', 'ocean']
}

# Default auction base prices
AUCTION_BASE_PRICES = {
    1: 30,  # Tier 1
    2: 20,  # Tier 2
    3: 7,  # Tier 3
    4: 3   # Tier 4
}

# Default audience income by tier
AUDIENCE_INCOME = {
    1: [30, 26, 24, 22, 20],  # Tier 1
    2: [20, 19, 18, 17, 16],  # Tier 2
    3: [7, 6, 5, 4, 3],  # Tier 3
    4: [5, 4, 3, 2, 1]   # Tier 4
}

# Default maintenance cost by tier and preference order
# The maintenance cost is higher for animals that are not in their preferred biome
MAINTENANCE_COST = {
    1: [12, 10, 9, 7, 6],       # Tier 1
    2: [8, 6, 5, 4, 3],         # Tier 2
    3: [3, 2.5, 2, 1.5, 1],     # Tier 3
    4: [1, 1, 1, 1, 1]          # Tier 4
}

# Tier limits per zoo
TIER_LIMITS = {
    1: 2,                       # Max 2 Tier 1 animals
    2: 2,                       # Max 2 Tier 2 animals
    3: 3,                       # Max 3 Tier 3 animals
    4: float('inf')             # No limit for Tier 4 animals
}

def count_animals_by_tier(zoo):
    """Count animals by tier in a zoo"""
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for animal_id in zoo['animals']:
        tier = int(animal_id[0])
        tier_counts[tier] += 1
    return tier_counts

def get_native_biome (animal):
    # The native biome is the last in the preference order (index 4, preference 5)
    return animal['preference_order'][4]

def get_animal_in_native_biome(animal, zoo):
    """Check if an animal is in its native biome"""
    native_biome = get_native_biome(animal)
    return zoo['biome'] == native_biome

def get_animal_biome_pref_index(animal, zoo):
    """Get the preference index (0-4) for the animal in the zoo's biome"""
    return animal['preference_order'].index(zoo['biome'])

# Animal template
def create_animal(animal_id, name):
    """
    Create an animal with the specified attributes
    Example: "1101" -> Tier 1, biome index 1 (forest), serial 01
    """

    tier = int(animal_id[0])
    biome_index = int(animal_id[1])
    serial_number = int(animal_id[2:])
    biome = ZOO_BIOMES[biome_index]
 
    if name is None:
        name = f"Tier {tier} {biome.capitalize()} Animal {serial_number}"
    
    return {
        'id': animal_id,
        'name': name,
        'tier': tier,
        'biome': biome,
        'biome_index': biome_index,
        'serial_number': serial_number,
        'base_price': AUCTION_BASE_PRICES[tier],
        'preference_order': PREFERENCE_ORDER[biome],
        'audience_income': AUDIENCE_INCOME[tier],
        'maintenance_cost': MAINTENANCE_COST[tier],
        'owner': None,
        'unhealthy': False
    }

# Initialize animals for a game
def initialize_animals(count_per_tier={1: 2, 2: 4, 3: 7, 4: 11}, csv_file_path=None):
    """
        Initialize animals for the game
        Parameters:
            - count_per_tier: Dictionary mapping tier numbers to number of animals per tier and biome
            - csv_file_path: Optional path to CSV file containing animal data
    """
    
    # Initialize animals dictionary
    animals: dict[str, dict] = {}

    # Read animal data from CSV if provided
    animal_data_from_csv: dict[str, str] = {}
    if csv_file_path:
        try:
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                for row in reader:
                    # Assuming the CSV has columns: id, name
                    animal_id = row.get('Animal ID', '').strip()
                    animal_name = row.get('Animal Name', '').strip()

                    if animal_id:
                        animal_data_from_csv[animal_id] = animal_name
        except Exception as e:
            print(f"Error reading animal data from CSV: {e}")
    
    # Create animals for each tier and biome
    for biome_index, biome in ZOO_BIOMES.items():
        for tier, count in count_per_tier.items():
            for serial_number in range(1, count + 1):
                animal_id = f"{tier}{biome_index}{serial_number:02d}"
                if animal_id in animal_data_from_csv.keys():
                    name = animal_data_from_csv[animal_id]
                else:
                    name = f"Tier {tier} {biome.capitalize()} Animal {serial_number}"

                # Create the animal
                animals[animal_id] = create_animal(animal_id, name)
    
    return animals
# ----------------------------------------------------------------------------------------------------

animal_database = initialize_animals(count_per_tier={1: 2, 2: 4, 3: 7, 4: 11}, csv_file_path=None) # replace with CSV file path

# -----------------------------------------------------------------------------------------------------
# PERKS CHECK
# Tier 1 perks are included in the animal income calculation
# Tier 2 perks are calculated here

# Tier 1 and Tier 2 of the same native biome in the same zoo with a different biome
def check_tier1_tier2_same_biome(zoo, animal_database):
    # to be used for the 5% bonus
    tier1_natives = set()
    tier2_natives = set()

    # to be used for the 10% bonus
    tier1_biomes = set()
    tier2_biomes = set()
    
    for animal_id in zoo['animals']:
        animal = animal_database[animal_id]
        native_biome = get_native_biome(animal)
        
        # Only consider non-native biomes
        if zoo['biome'] != native_biome:
            if animal['tier'] == 1:
                tier1_biomes.add(native_biome)
            elif animal['tier'] == 2:
                tier2_biomes.add(native_biome)
        else:
            if animal['tier'] == 1:
                tier1_natives.add(native_biome)
            elif animal['tier'] == 2:
                tier2_natives.add(native_biome)
    
    # Check for common non-native biomes
    common_biomes = tier1_biomes.intersection(tier2_biomes)
    common_natives = tier1_natives.intersection(tier2_natives)

    # return the counts of common biomes and natives for the 10% and 5% bonus respectively
    if not common_biomes and not common_natives:
        return {"non_native_match": 0, "native_match": 0}  # No bonus if no common biomes or natives
    return {"non_native_match": len(common_biomes), "native_match": len(common_natives)}

# Calculate the 10% or 5% bonus income from Tier 1 and Tier 2 animals
def calculate_tier1_tier2_bonus(zoo, animal_database):
    # Check if we have Tier 1 and Tier 2 animals of the same non-native biome
    has_same_biome = check_tier1_tier2_same_biome(zoo, animal_database)
    
    # Calculate total base income from Tier 1 and Tier 2 animals only
    tier1_tier2_income = 0.0
    
    for animal_id in zoo['animals']:
        animal = animal_database[animal_id]
        
        # Only consider Tier 1 and Tier 2 animals
        if animal['tier'] in [1, 2]:
            # Calculate this animal's base income (without the 5%/10% bonus)
            animal_income = calculate_animal_income(animal, zoo)
            tier1_tier2_income += animal_income
    
    bonus_rate = 0
    if has_same_biome["non_native_match"] > 0:
        # 10% bonus for common non-native biomes
        bonus_rate += ((1.1 ** has_same_biome["non_native_match"]) - 1) # 1.1 * 1.1 * ... - 1
    if has_same_biome["native_match"] > 0:
        bonus_rate += ((1.05 ** has_same_biome["native_match"]) - 1) # 1.05 * 1.05 * ... - 1
    
    # Calculate the bonus amount
    bonus_amount = tier1_tier2_income * bonus_rate
    
    return bonus_amount
# ----------------------------------------------------------------------------------------------------
def calculate_animal_income(animal, zoo):
    """Calculate the income an animal generates in a specific zoo"""
    if animal['unhealthy'] and animal['tier'] == 1:
        # Unhealthy Tier-1 animals have reduced income (0.75x)
        income_factor = 0.75
    elif animal['unhealthy'] and animal['tier'] == 2:
        # Unhealthy Tier-2 animals have reduced income (0.8x)w
        income_factor = 0.8
    else:
        # Healthy and Tier-3, 4 animals have full income
        income_factor = 1.0
        
    # Get preference index (0-4)
    pref_index = get_animal_biome_pref_index(animal, zoo)
    
    # Base income based on tier and biome preference
    base_income = AUDIENCE_INCOME[animal['tier']][pref_index]
    
    # Apply multipliers from perks
    multipliers = 1.0
    
    # Tier 1 special perks
    if animal['tier'] == 1:
        # If Tier 1 animal is in a non-native biome
        if not get_animal_in_native_biome(animal, zoo):
            # All animals get 1.4x audience income
            multipliers *= 1.4
        # If Tier 1 animal is in its native biome
        else:
            # All animals get 1.2x audience income
            multipliers *= 1.2
    
    # Tier 2 special perks
    # the bonus of Tier 2 is linked with Tier 1 and Tier 2's total income
    # hence this bonus is calculated differently and not here
    
    # Apply zoo multiplier from the continent-biome relationship
    multipliers *= zoo['multiplier']
    
    # Final income calculation
    return base_income * multipliers * income_factor

# Calculate animal maintenance cost in a specific zoo
def calculate_animal_maintenance(animal, zoo):
    # Base maintenance cost
    pref_index = get_animal_biome_pref_index(animal, zoo)
    cost = animal['maintenance_cost'][pref_index]

    if animal['tier'] == 1 and animal['unhealthy']:
        if get_animal_in_native_biome(animal, zoo):
            cost *= 2
        else:
            cost *= 4
    elif animal['tier'] == 2 and animal['unhealthy']:
        cost *= 2
    
    return cost
# ----------------------------------------------------------------------------------------------------
# FINAL SCORE CALCULATION

def calculate_final_score(zoo, animals):
    # Calculate total income from animals
    total_income = 0.0
    for animal_id in zoo['animals']:
        animal = animals[animal_id]
        income = calculate_animal_income(animal, zoo)
        cost = calculate_animal_maintenance(animal, zoo)
        total_income += (income - cost)
    
    # Final amount includes coins plus income
    final_amount = zoo['coins'] + total_income
    
    # Count different biomes (a biome is established if there are at least 2 animals)
    biome_counts = {}
    for animal_id in zoo['animals']:
        animal_biome = animals[animal_id]['biome']
        if animal_biome not in biome_counts:
            biome_counts[animal_biome] = 0
        biome_counts[animal_biome] += 1
    
    # A biome is established if there are at least 2 animals of that type
    biomes_established = sum(1 for count in biome_counts.values() if count >= 2)
    n = biomes_established + 1  # +1 for the zoo's native biome
    
    # Apply the scoring formula: |log2(A)|^(n-0.5) * multiplier
    if final_amount <= 0:
        return 0
    else:
        log_amount = math.log2(final_amount)
        return (abs(log_amount) ** (n - 0.5)) * zoo['multiplier']
# ----------------------------------------------------------------------------------------------------