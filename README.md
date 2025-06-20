# Technothlon 2024 Final Round Trading Game

### Game Description
Five continents $(A, B, C, D, E)$, each favors a unique type of biodiversity: (1) forest, (2) tundra, (3) ocean, (4) desert, or (5) wetland. 
In each continent, there are five different zoos, each zoo favoring a specific type of biodiversity (which may not be the same as its respective continent).
So, there are 25 zoos: $A1-A5, B1-B5, C1-C5, D1-D5, E1-E5$ ($A1$ is in continent $A$ and of the forest biome). 
In addition, the continent as a whole predominantly favors exactly one of the types of biodiversity (in the event, we let $A$ align with tundra, $B$ with wetland, $C$ with ocean, $D$ with forest, and $E$ with desert).

Each player is the _owner_ of a zoo (to be selected by the player) and is given **100** coins to spend. They have to acquire animals to their zoos, through auction or trading (during sessions). Each animal comes with its own set of traits and perks, which will be explained in greater detail later. In the end, an objective scoring system quantitatively determines the winner.

We've attached the development report (discussions, insights and challenges faced). The bottle-neck in the execution was: an online interface for timed conduction of the auction. We have developed an interface for the same (we had to slightly modify the auction rules for this online implementation because of several redundancies in the offline one).

Future challenge will be to create a trading interface to completely automate the project.
