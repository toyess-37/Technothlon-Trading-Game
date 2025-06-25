import random
import time
import threading
from typing import List, Dict, Optional, Any, Tuple, Callable
from collections import defaultdict
import json
import os
import csv

from zoo_animal_data import (
    create_animal, create_zoo, initialize_animals, initialize_zoos,
    calculate_animal_income, calculate_animal_maintenance, calculate_final_score,
    calculate_tier1_tier2_bonus, count_animals_by_tier, TIER_LIMITS,
    ZOO_BIOMES, CONTINENT_BIOMES, AUCTION_BASE_PRICES
)

class Animal:
    def __init__(self, animal_data: dict):
        """
        Initialize an animal from the data structure used in zoo_animal_data.py
        
        Args:
            animal_data: Dictionary containing animal data from create_animal()
        """
        self.id = animal_data['id']
        self.name = animal_data['name']
        self.tier = animal_data['tier']
        self.biome = animal_data['biome']
        self.biome_index = animal_data['biome_index']
        self.serial_number = animal_data['serial_number']
        self.base_price = animal_data['base_price']
        self.preference_order = animal_data['preference_order']
        self.audience_income = animal_data['audience_income']
        self.maintenance_cost = animal_data['maintenance_cost']
        self.owner = animal_data['owner']
        self.unhealthy = animal_data['unhealthy']

    @classmethod
    def from_id(cls, animal_id: str, name: str = ''):
        """Create an Animal instance using the zoo_animal_data functions."""
        animal_data = create_animal(animal_id, name)
        return cls(animal_data)

    def to_dict(self):
        """Convert animal back to dictionary format for compatibility."""
        return {
            'id': self.id,
            'name': self.name,
            'tier': self.tier,
            'biome': self.biome,
            'biome_index': self.biome_index,
            'serial_number': self.serial_number,
            'base_price': self.base_price,
            'preference_order': self.preference_order,
            'audience_income': self.audience_income,
            'maintenance_cost': self.maintenance_cost,
            'owner': self.owner,
            'unhealthy': self.unhealthy
        }
    
    def set_owner(self, player_id: str):
        self.owner = player_id
    
    def set_unhealthy(self, is_unhealthy: bool = True):
        """Set the animal's health status."""
        self.unhealthy = is_unhealthy
    
    def is_healthy(self):
        """Check if the animal is healthy."""
        return not self.unhealthy

class Zoo:
    """
    Class representing a zoo.
    """

    def __init__(self, zoo_data: dict):
        """
        Initialize a zoo from the data structure used in zoo_animal_data.py
        
        Args:
            zoo_data: Dictionary containing zoo data from create_zoo()
        """
        self.id = zoo_data['id']
        self.continent_index = zoo_data['continent_index']
        self.continent = zoo_data['continent']
        self.biome_index = zoo_data['biome_index']
        self.biome = zoo_data['biome']
        self.owner = zoo_data['owner']
        self.animals = zoo_data['animals'].copy()  # List of animal IDs
        self.coins = zoo_data['coins']
        self.multiplier = zoo_data['multiplier']

    @classmethod
    def from_id(cls, zoo_id: str):
        """Create a Zoo instance using the zoo_animal_data functions."""
        continent = zoo_id[0]
        biome_index = int(zoo_id[1])  # Extract from format like "A[1]"
        zoo_data = create_zoo(zoo_id, continent, biome_index)
        return cls(zoo_data)
    
    def to_dict(self):
        """Convert zoo back to dictionary format for compatibility."""
        return {
            'id': self.id,
            'continent_index': self.continent_index,
            'continent': self.continent,
            'biome_index': self.biome_index,
            'biome': self.biome,
            'owner': self.owner,
            'animals': self.animals.copy(),
            'coins': self.coins,
            'multiplier': self.multiplier
        }
    
    def add_animal(self, animal_id: str):
        """Add an animal to this zoo."""
        if animal_id not in self.animals:
            self.animals.append(animal_id)
    
    def remove_animal(self, animal_id: str):
        """Remove an animal from this zoo."""
        if animal_id in self.animals:
            self.animals.remove(animal_id)
    
    def can_add_animal(self, animal: Animal):
        """Check if an animal can be added to this zoo based on tier limits."""
        tier_counts = count_animals_by_tier(self.to_dict())
        current_count = tier_counts.get(animal.tier, 0)
        tier_limit = TIER_LIMITS.get(animal.tier, float('inf'))
        return current_count < tier_limit

    def set_owner(self, player_id: str):
        """Set the owner of this zoo."""
        self.owner = player_id
    
    def add_coins(self, amount: int):
        """Add coins to the zoo."""
        self.coins += amount
    
    def spend_coins(self, amount: int):
        """Spend coins from the zoo. Returns True if successful, False if insufficient funds."""
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False


class Player:
    """Class representing a player (zoo owner) in the game."""
    
    def __init__(self, player_id: str, name: str, zoo: Zoo, money: int = 100):
        """
        Initialize a player.
        
        Args:
            player_id: Unique identifier for the player
            name: Player name
            zoo_biome: Biome type of the player's zoo
            money: Starting money (default 100 coins)
        """
        self.id = player_id
        self.name = name
        self.money = money
        self.zoo = zoo # Assigned Zoo
        self.is_active = True
        self.is_human = False  # Flag to distinguish human vs AI players
        self.owned_animals = []  # List of animal IDs owned by this player
        self.pending_bids = {}  # Track pending bids {animal_id: bid_amount}
        
        # Set zoo owner if zoo is provided
        if self.zoo:
            self.zoo.set_owner(self.id)
    
    def assign_zoo(self, zoo: Zoo):
        """Assign a zoo to this player."""
        self.zoo = zoo
        self.zoo.set_owner(self.id)

    def add_money(self, amount: int):
        """Add money to the player."""
        self.money += amount
    
    def spend_money(self, amount: int):
        """Spend money. Returns True if successful, False if insufficient funds."""
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def get_available_money(self):
        """Get available money (total money minus pending bids)."""
        total_pending = sum(self.pending_bids.values())
        return self.money - total_pending
    
    def can_afford_bid(self, bid_amount: int, animal_id: str):
        """Check if player can afford a bid considering pending bids."""
        # Get current pending bid for this animal (if any)
        current_bid_on_animal = self.pending_bids.get(animal_id, 0)
        # Calculate total pending excluding current animal
        total_pending_others = sum(amount for aid, amount in self.pending_bids.items() if aid != animal_id)
        # Check if new bid is affordable
        return (total_pending_others + bid_amount) <= self.money

    def update_pending_bid(self, animal_id: str, bid_amount: int):
        """Update pending bid for an animal."""
        self.pending_bids[animal_id] = bid_amount
    
    def clear_pending_bid(self, animal_id: str):
        """Clear pending bid for an animal."""
        if animal_id in self.pending_bids:
            del self.pending_bids[animal_id]
    
    def clear_all_pending_bids(self):
        """Clear all pending bids."""
        self.pending_bids.clear()

    def get_zoo_biome(self):
        """Get the biome of the player's zoo."""
        return self.zoo.biome if self.zoo else None

    def get_zoo_continent(self):
        """Get the continent of the player's zoo."""
        return self.zoo.continent_index if self.zoo else None

    def add_animal_to_zoo(self, animal: Animal):
        """Add an animal to the player's zoo."""
        if self.zoo and self.zoo.can_add_animal(animal):
            self.zoo.add_animal(animal.id)
            self.owned_animals.append(animal.id)
            animal.set_owner(self.id)
            return True
        return False
    
    def can_bid_on_tier(self, tier: int):
        """Check if player can bid on animals of a specific tier based on tier limits."""
        if not self.zoo:
            return False
        
        tier_counts = count_animals_by_tier(self.zoo.to_dict())
        current_count = tier_counts.get(tier, 0)
        tier_limit = TIER_LIMITS.get(tier, float('inf'))
        return current_count < tier_limit

    def calculate_zoo_score(self, animal_database: dict):
        """Calculate the final score for this player's zoo."""
        if not self.zoo:
            return 0
    
        # Add Tier 1 & 2 bonus income to zoo coins
        bonus_income = calculate_tier1_tier2_bonus(self.zoo.to_dict(), animal_database)
        self.zoo.add_coins(int(bonus_income))
    
        # Calculate final score
        return calculate_final_score(self.zoo.to_dict(), animal_database)
    
    def to_dict(self):
        """Convert player to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'money': self.money,
            'zoo_id': self.zoo.id if self.zoo else None,
            'zoo': self.zoo.to_dict() if self.zoo else None,
            'owned_animals': self.owned_animals.copy(),
            'is_active': self.is_active,
            'is_human': self.is_human,
            'pending_bids': self.pending_bids.copy()
        }

class AuctionManager:
    """Manages auction logic and state."""
    
    def __init__(self, game_state, socketio_callback=None):
        self.game_state = game_state
        self.socketio_callback = socketio_callback
        self.current_tier = 1
        self.tier_timers = {1: 120, 2: 180, 3: 240, 4: 300}  # seconds
        self.current_timer = 0
        self.auction_active = False
        self.current_animals = []
        self.animal_bids = defaultdict(list)  # animal_id -> list of (bid_amount, player_id)
        self.timer_thread: Optional[threading.Thread] = None
        self.auction_results = {}
    
    def start_tier_auction(self, tier: int):
        """Start auction for a specific tier."""
        self.current_tier = tier
        self.current_timer = self.tier_timers[tier]
        self.auction_active = True
        self.current_animals = self.game_state.get_animals_by_tier(tier)
        self.animal_bids.clear()
        
        # Initialize bids for each animal
        for animal in self.current_animals:
            self.animal_bids[animal.id] = []
        
        print(f"Starting Tier {tier} auction with {len(self.current_animals)} animals")
        print(f"Auction duration: {self.current_timer} seconds")
        
        # Notify clients
        if self.socketio_callback:
            self.socketio_callback('auction_round_start', {
                'tier': tier,
                'duration': self.current_timer,
                'animals': [animal.to_dict() for animal in self.current_animals]
            })
        
        # Start timer
        self.start_timer()
    
    def start_timer(self):
        """Start the auction timer in a separate thread."""
        if self.timer_thread and self.timer_thread.is_alive():
            return
        
        self.timer_thread = threading.Thread(target=self._run_timer)
        self.timer_thread.daemon = True
        if self.timer_thread is not None:
            self.timer_thread.start()
    
    def _run_timer(self):
        """Run the auction timer."""
        while self.current_timer > 0 and self.auction_active:
            if self.socketio_callback:
                self.socketio_callback('auction_timer_update', {
                    'tier': self.current_tier,
                    'time_remaining': self.current_timer
                })
            
            time.sleep(1)
            self.current_timer -= 1
        
        if self.auction_active:
            self.end_tier_auction()
    
    def submit_bid(self, player_id: str, animal_id: str, bid_amount: int):
        """Submit a bid for an animal."""
        if not self.auction_active:
            return {'success': False, 'message': 'No active auction'}
        
        player = self.game_state.get_player_by_id(player_id)
        if not player:
            return {'success': False, 'message': 'Player not found'}
        
        animal = self.game_state.animal_database.get(animal_id)
        if not animal or animal not in self.current_animals:
            return {'success': False, 'message': 'Animal not in current auction'}
        
        # Check if player can afford the bid considering pending bids
        if not player.can_afford_bid(bid_amount, animal_id):
            return {'success': False, 'message': 'Insufficient funds considering your pending bids'}
        
        # Check on how many animals player is leading
        leading_count = 0
        for aid, bids in self.animal_bids.items():
            if bids and aid != animal_id:  # Don't count the current animal
                highest_bid = max(bids, key=lambda x: x[0])
                if highest_bid[1] == player_id:
                # Check if this animal is same tier
                    other_animal = self.game_state.animal_database.get(aid)
                    if other_animal and other_animal.tier == animal.tier:
                        leading_count += 1

        # Checking against tier limit
        tier_limit = TIER_LIMITS.get(animal.tier, float('inf'))
        if leading_count >= tier_limit:
            return {'success': False, 'message': f'You are already leading bids for {tier_limit} Tier {animal.tier} animals (the maximum allowed)'}
        
        # Get current highest bid
        current_bids = self.animal_bids[animal_id]
        min_bid = animal.base_price
        if current_bids:
            highest_bid = max(current_bids, key=lambda x: x[0])
            min_bid = highest_bid[0] + 2  # Minimum increment of 2
        
        if bid_amount < min_bid:
            return {'success': False, 'message': f'Bid must be at least {min_bid}'}

        # Add to pending bids
        player.update_pending_bid(animal_id, bid_amount)
        
        # Add the bid
        self.animal_bids[animal_id].append((bid_amount, player_id))
        
        # Notify all clients of the bid update
        if self.socketio_callback:
            highest_bid = max(self.animal_bids[animal_id], key=lambda x: x[0])
            highest_bidder = self.game_state.get_player_by_id(highest_bid[1])
            highest_bidder_name = highest_bidder.name if highest_bidder else 'Unknown'

            self.socketio_callback('bid_update', {
                'animal_id': animal_id,
                'highest_bid': highest_bid[0],
                'highest_bidder': highest_bidder_name,
                'bid_count': len(self.animal_bids[animal_id])
            })
        
        return {'success': True, 'message': 'Bid submitted successfully'}
    
    def end_tier_auction(self):
        """End the current tier auction and distribute animals."""
        if not self.auction_active:
            return
        
        self.auction_active = False
        print(f"Ending Tier {self.current_tier} auction")
        
        # Process bids and distribute animals
        tier_results = {}
        
        for animal in self.current_animals:
            animal_id = animal.id
            bids = self.animal_bids[animal_id]
            
            if not bids:
                # No bids for this animal
                tier_results[animal_id] = {
                    'winner': None,
                    'winning_bid': 0,
                    'animal': animal.to_dict()
                }
                continue
            
            # Sort bids by amount (highest first)
            sorted_bids = sorted(bids, key=lambda x: x[0], reverse=True)
            
            # Find valid winner (respecting tier limits)
            winner = None
            winning_bid = 0
            
            for bid_amount, player_id in sorted_bids:
                player = self.game_state.get_player_by_id(player_id)
                if player and player.can_bid_on_tier(animal.tier) and player.money >= bid_amount:
                    winner = player
                    winning_bid = bid_amount
                    break
            
            if winner:
                # Transfer animal to winner
                winner.spend_money(winning_bid)
                winner.add_animal_to_zoo(animal)
                winner.clear_pending_bid(animal_id)

                tier_results[animal_id] = {
                    'winner': winner.name,
                    'winner_id': winner.id,
                    'winning_bid': winning_bid,
                    'animal': animal.to_dict()
                }
                print(f"Animal {animal.id} ({animal.name}) acquired by {winner.name} for {winning_bid} coins")
            else:
                # No valid winner
                tier_results[animal_id] = {
                    'winner': None,
                    'winning_bid': 0,
                    'animal': animal.to_dict()
                }
            
        # Clear all pending bids after auction ends
        for player in self.game_state.players:
            player.clear_all_pending_bids()
        
        self.auction_results[self.current_tier] = tier_results
        
        # Notify clients
        if self.socketio_callback:
            self.socketio_callback('auction_round_end', {
                'tier': self.current_tier,
                'results': tier_results
            })
            self.socketio_callback('game_state_update', self.game_state.get_game_state_dict())
        
        # Move to next tier or end auction
        if self.current_tier >= 4:
            # Wait a bit before starting next tier
            # threading.Timer(5.0, lambda: self.start_tier_auction(self.current_tier + 1)).start()
        # else:
            print("All auction rounds completed!")
            self.game_state.start_scoring_phase()
        
    def stop_current_auction(self):
        """Forcefully stops the current auction."""
        if not self.auction_active:
            return

        print("Admin is stopping the current auction.")
        self.auction_active = False
        # The timer thread will see auction_active is False and will exit its loop.
        
        self.current_animals = []
        self.animal_bids.clear()

        # Clear all pending bids
        for player in self.game_state.players:
            player.clear_all_pending_bids()
        
        if self.socketio_callback:
            self.socketio_callback('auction_stopped', {
                'message': 'The auction was stopped by the administrator.'
            })
            self.socketio_callback('game_state_update', self.game_state.get_game_state_dict())
    
    def get_current_highest_bids(self):
        """Get current highest bids for all animals in current auction."""
        highest_bids = {}
        for animal_id, bids in self.animal_bids.items():
            if bids:
                highest_bid = max(bids, key=lambda x: x[0])
                player = self.game_state.get_player_by_id(highest_bid[1])
                highest_bids[animal_id] = {
                    'amount': highest_bid[0],
                    'bidder': player.name if player else 'Unknown',
                    'bidder_id': highest_bid[1]
                }
            else:
                animal = self.game_state.animal_database.get(animal_id)
                highest_bids[animal_id] = {
                    'amount': animal.base_price if animal else 0,
                    'bidder': None,
                    'bidder_id': None
                }
        return highest_bids


class GameState:
    """Class maintaining the overall state of the game."""
    
    def __init__(self, socketio_callback=None):
        """Initialize the game state."""
        self.players: List[Player] = []
        self.available_zoos = {}
        self.animal_database = {}
        self.current_phase = "setup"  # setup, auction, trading, scoring
        self.auction_manager = AuctionManager(self, socketio_callback)
        
        # Initialize game data
        self.initialize_game_data()
        self.initialize_players()

    def initialize_game_data(self):
        """Initialize zoos and animals using the zoo_animal_data functions."""
        # Initialize all 25 zoos
        zoo_data = initialize_zoos()
        for zoo_id, zoo_dict in zoo_data.items():
            self.available_zoos[zoo_id] = Zoo(zoo_dict)
        
        # Initialize animals - generate specified counts per tier
        animal_data = initialize_animals(
            count_per_tier={1: 2, 2: 4, 3: 7, 4: 11}, 
            csv_file_path='zoo_animals.csv'  # Will fall back to default names if file not found
        )
        for animal_id, animal_dict in animal_data.items():
            self.animal_database[animal_id] = Animal(animal_dict)
    
    def initialize_players(self, num_players=25):
        """Initialize AI players for the game."""
        zoo_ids = list(self.available_zoos.keys())

        for i in range(min(num_players, len(zoo_ids))):
            zoo_id = zoo_ids[i]
            zoo = self.available_zoos[zoo_ids[i]]
            player_id = zoo.id
            player_name = str(zoo.id)
            
            player = Player(player_id, player_name, zoo, money=100)
            self.add_player(player)
            del self.available_zoos[zoo_ids[i]]

    def add_player(self, player: Player):
        """Add a player to the game."""
        self.players.append(player)

    def assign_zoo_to_player(self, player: Player, zoo_id: str):
        """Assign a specific zoo to a player."""
        if zoo_id in self.available_zoos:
            zoo = self.available_zoos[zoo_id]
            if zoo.owner is None:  # Zoo is available
                player.assign_zoo(zoo)
                del self.available_zoos[zoo_id]  # Remove from available zoos
                return True
        return False
    
    def get_available_zoos(self):
        """Get list of available zoos for assignment."""
        return list(self.available_zoos.values())
    
    def get_animals_by_tier(self, tier: int):
        """Get all animals of a specific tier."""
        return [animal for animal in self.animal_database.values() 
                if animal.tier == tier and animal.owner is None]
    
    def start_auction_phase(self):
        """Move to the auction phase."""
        self.current_phase = "auction"
        print("Starting Auction Phase")
        self.auction_manager.start_tier_auction(1)  # Start with Tier 1
    
    def start_scoring_phase(self):
        """Move to the scoring phase and calculate final scores."""
        self.current_phase = "scoring"
        print("Moving to Scoring Phase")
        
        # Convert animal database to dictionary format for scoring functions
        animal_dict_db = {
            aid: animal.to_dict() for aid, animal in self.animal_database.items()
        }
        
        # Calculate scores for all players
        scores = {}
        for player in self.players:
            scores[player.id] = player.calculate_zoo_score(animal_dict_db)
        
        return scores
    
    def get_player_by_id(self, player_id: str):
        """Get a player by their ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_game_state_dict(self):
        """Get complete game state as dictionary for JSON serialization."""
        return {
            'phase': self.current_phase,
            'players': [player.to_dict() for player in self.players],
            'auction': {
                'active': self.auction_manager.auction_active,
                'current_tier': self.auction_manager.current_tier,
                'time_remaining': self.auction_manager.current_timer,
                'current_animals': [animal.to_dict() for animal in self.auction_manager.current_animals],
                'highest_bids': self.auction_manager.get_current_highest_bids()
            } if self.current_phase == "auction" else None,
            'available_zoos': [zoo.to_dict() for zoo in self.available_zoos.values()],
            'total_animals': len(self.animal_database),
            'animal_database': {aid: animal.to_dict() for aid, animal in self.animal_database.items()}
        }