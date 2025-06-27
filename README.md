# Technothlon 2024 Final Round Trading Game

## Game Description
Five continents $(A, B, C, D, E)$, each favors a unique type of biodiversity: (1) forest, (2) tundra, (3) ocean, (4) desert, or (5) wetland. 
In each continent, there are five different zoos, each zoo favoring a specific type of biodiversity (which may not be the same as its respective continent).
So, there are 25 zoos: $A1-A5, B1-B5, C1-C5, D1-D5, E1-E5$ ($A1$ is in continent $A$ and of the forest biome). 
In addition, the continent as a whole predominantly favors exactly one of the types of biodiversity (in the event, we let $A$ align with tundra, $B$ with wetland, $C$ with ocean, $D$ with forest, and $E$ with desert).

Each player is the _owner_ of a zoo (to be selected by the player) and is given **100** coins to spend. They have to acquire animals to their zoos, through auction or trading (during sessions). Each animal comes with its own set of traits and perks, which will be explained in greater detail later. In the end, an objective scoring system quantitatively determines the winner.

We've attached the development report (discussions, insights and challenges faced). The bottle-neck in the execution was: an online interface for timed conduction of the auction. We have developed an interface for the same (we had to slightly modify the auction rules for this online implementation because of several redundancies in the offline one).

Future challenge will be to create a trading interface to automate the complete project.

### Auction Segment

A real-time multiplayer zoo auction game built with Flask, SocketIO, and modern web technologies. Players bid on animals to build their zoos while an admin manages auction rounds. The live website can be found at https://web-production-dafc.up.railway.app/.

#### Key Features

- **Real-time Multiplayer**: Up to 25 players can participate simultaneously
- **Live Auction System**: Tier-based auctions with countdown timers
- **Dynamic Scoring**: Complex scoring system based on biome diversity and animal synergies
- **Admin Dashboard**: Complete game management interface
- **WebSocket Communication**: Real-time updates for all players

#### Quick Start

##### Prerequisites

- Python 3.11 or higher
- Git

##### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/toyess-37/Technothlon-Trading-Game.git
   cd fauna-fantastico
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export ADMIN_PASSWORD="your-admin-password"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the game**
   - Open your browser to `http://localhost:5000`
   - Admin login: username `admin`, password from environment variable
   - Player login: any username from [A1..5, B1..5, C1..5, D1..5, E1..5] (e.g. D2).

#### How to Play

##### For Players

1. **Join Game**: Enter your name on the login page
2. **Wait for Auction**: Admin initializes the game and starts auctions
3. **Bid on Animals**: Place bids during active auctions
4. **Build Your Zoo**: Strategically collect animals to maximize your score
5. **Track Progress**: Monitor your money, animals, and pending bids

##### For Admins

1. **Login**: Use admin credentials to access the dashboard
2. **Initialize Game**: Set up the game with all animals and zoos
3. **Start Auctions**: Begin tier-based auctions (Tier 1-4)
4. **Monitor Progress**: Watch live bidding and player statistics
5. **Manage Game**: Stop auctions or reset as needed

#### Game Architecture

##### Core Components

- **Flask Backend**: Handles HTTP requests and game logic
- **Socket.IO**: Real-time bidirectional communication
- **Game State**: Centralized state management for all game data
- **Auction Manager**: Handles auction timing and bid processing
- **Zoo System**: Complex scoring based on animal combinations

#### File Structure

```
fauna-fantastico/
├── app.py                 # Main Flask application
├── zoo_auction_system.py  # Core game logic and classes
├── zoo_animal_data.py     # Game data and calculations
├── zoo_animals.csv        # Animal names database
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── runtime.txt           # Python version specification
└── templates/            # HTML templates
    ├── login.html        # Login page
    ├── admin.html        # Admin dashboard
    └── player.html       # Player interface
```

#### Game Rules

##### Animal Tiers

- **Tier 1**: High-value animals (2 per zoo limit)
- **Tier 2**: Medium-value animals (2 per zoo limit) 
- **Tier 3**: Common animals (3 per zoo limit)
- **Tier 4**: Basic animals (unlimited)

##### Biomes

Animals belong to five biomes, each with different characteristics:
**Forest**, **Tundra**, **Ocean**, **Desert**, **Wetland**

##### Scoring System

Final score is calculated based on:
- Animal income vs. maintenance costs
- Zoo biome multipliers
- Biome diversity bonuses
- Special tier combinations

For complete details, kindly go through the `Report_Zoo_Game_Technothlon.pdf`.

#### 🛠️ Development

##### Technology Stack

- **Backend**: Python, Flask, Socket.IO
- **Frontend**: HTML5, CSS3, JavaScript
- **Real-time**: WebSocket connections
- **Deployment**: Gunicorn, WSGI

##### API Endpoints

###### Admin Endpoints
- `POST /api/admin/game/initialize` - Initialize new game
- `POST /api/admin/game/start_auction_tier` - Start tier auction
- `POST /api/admin/game/stop_auction` - Stop current auction

###### Game Endpoints
- `GET /api/game/status` - Get current game state
- `POST /login` - Handle user login
- `GET /logout` - User logout

###### Socket Events
- `game_state_update` - Broadcast game state changes
- `bid_update` - Real-time bid updates
- `auction_timer_update` - Auction countdown
- `place_bid` - Submit bid (client to server)


### Common Issues

**Game won't initialize**
- Check that all CSV files are present
- Verify environment variables are set
- Check server logs for detailed errors

**Players can't connect**
- Ensure SocketIO is working (check browser console)
- Verify firewall/proxy settings
- Check CORS configuration

**Bidding not working**
- Confirm auction is active
- Check player has sufficient funds
- Verify tier limits aren't exceeded

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for educational game development
- Inspired by classic auction and strategy games
- Uses modern web development best practices
