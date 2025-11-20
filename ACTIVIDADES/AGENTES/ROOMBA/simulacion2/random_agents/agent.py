from mesa.discrete_space import CellAgent, FixedAgent
from collections import deque
import heapq

class Roomba(CellAgent):
    """
    Agent that moves randomly.
    Attributes:
        unique_id: Agent's ID
    """
    def __init__(self, model, cell):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell
        self.state = "idle"
        self.battery = 100  
        self.stationCells = [self.cell.coordinate]
        self.trash_cleaned = 0 

        self.visited_cells =  {self.cell.coordinate}
        self.trash_known_cells = set()

        self.path_back_to_station = []
        self.distance_to_station = 0
        
        self.hasInfo = False
        self.info_timer = 0
        self.steps = 0
        self.hasBattery = True

    # Action methods that allow the agent to check its environment and change its state

    def checkBattery(self):
        """Check if the battery is low and decide the next action."""

        self.distanceToStation() #Calculate distance to nearest station

        step_margin = 10  #Safety margin to avoid running out of battery
        total_distance = self.distance_to_station + step_margin

        if self.battery <= total_distance:
            self.hasBattery = False
            self.state = "returning" #change state to returning to station if battery is low
        else:
            self.state = "ready" #change state to ready if battery is sufficient

    def checkStation(self):
        """Check if an agent is at the station."""
        station_cell = next(
            (cell for cell in self.cell.neighborhood
             if any(isinstance(obj, StationAgent) for obj in cell.agents)), None
        )
        if station_cell:
            occupied = self.stationOccupied(station_cell) #Check if station is occupied
            if not occupied:
                self.state = "recharging" #change state to recharging if station is free
                self.move(station_cell)
            else:
                self.state = "waiting" #change state to waiting if station is occupied


    def checkTrash(self):
        """Return the cells with trash."""
        trash_cell = next(
            (obj for obj in self.cell.agents if isinstance(obj, TrashAgent)), None
        )

        # Add trash cell to known trash cells for future reference
        if (self.state == "returning") and trash_cell is not None:
            self.trash_known_cells.add(self.cell.coordinate)
            return

        if trash_cell is not None:
            self.state = "cleaning" #change state to cleaning if trash is found
        else:
            self.state = "checkObstacles" #change state to checkObstacles if no trash is found
        return trash_cell
        

    def checkObstacles(self):
        """Return the cells with obstacles."""
        # Get neighboring cells that do not contain obstacles
        valid_neighbors = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        )

        # If there are valid neighbors, choose the ones that have trash
        trash_cells = valid_neighbors.select(
            lambda cell: any(isinstance(obj, TrashAgent) for obj in cell.agents)
        )

        # Get neighboring cells that have not been visited yet
        unvisited_cells = valid_neighbors.select(
            lambda cell: cell.coordinate not in self.visited_cells
        )

        # Prioritize cells with trash, then unvisited cells, then any valid neighbor
        if trash_cells:
            next_cell = trash_cells.select_random_cell()
        elif unvisited_cells:
            next_cell = unvisited_cells.select_random_cell()
        else:
            if self.trash_known_cells:
                path = self.pathToNearestKnownTrash()
            else:
                path = self.pathToNearestUnvisited()

            if len(path) > 0:
                next_coord = path[0]
                next_cell = self.model.grid[next_coord ]
            else: #If there are no known trash or unvisited cells, move randomly
                next_cell = valid_neighbors.select_random_cell()

        self.state = "moving" #change state to moving after deciding next cell
        return next_cell
    
    def checkRoombas(self, roomba_cell):
        """Check if another roomba is in the cell."""
        roomba_cells = roomba_cell.neighborhood.select(
            lambda cell: any(isinstance(obj, Roomba) and obj != self for obj in cell.agents)
        ) # Get neighboring cells with other roombas
        roomba_agent = next(
            (obj for cell in roomba_cells for obj in cell.agents if isinstance(obj, Roomba) and obj != self), None
        ) # Get the first roomba agent found that is not self

        #If another roomba is found, set hasInfo to true and start info timer
        if roomba_agent and not self.hasInfo:
            self.state = "communicating"
        else:
            self.state = "checkTrash"
        return roomba_agent

    def a_star(self, start, goal):
        """
        A* pathfinding algorithm adapted for the grid in the model

        This algorithm was adapted from the one made in the advanced algorithm class
        with Lizbeth Peralta. Made by Diego Cordova, Aquiba Benarroch and me.
        """

        # Calculate Manhattan distance
        # We have to estimate heuristic using this distance
        # since it is not given from the model
        # Ref: https://www.geeksforgeeks.org/dsa/a-search-algorithm/
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Initialize variables
        grid = self.model.grid
        stack = [] # Stack of nodes to explore
        c_list = {}  # g values
        visited = set()  # visited nodes

        # Father vector to reconstruct path
        fathers = {}

        # Initialize stack with start node
        # Heap already sorts by smallest f value
        heapq.heappush(stack, (0, start))
        c_list[start] = 0

        # While the stack is not empty
        # Explore neighbors with lowest f value
        while len(stack) > 0:
            
            # Get node with lowest f value
            # This returns f, coordinate
            # but we only need coordinate, so we use _
            _, current = heapq.heappop(stack)

            # If the node hasnt been visited, process it
            if current not in visited:

                # Mark as visited
                visited.add(current)

                # If we reached the goal, finish
                if (current == goal):
                    break

                # Explore neighbors
                # Get valid neighbors (not obstacles)                
                valid_neighbors = grid[current].neighborhood.select(
                    lambda cell: not any(isinstance(a, ObstacleAgent) for a in cell.agents)
                )

                # For each valid neighbor, calculate costs and update structures
                for neighbor_cell in valid_neighbors:
                    neighbor = neighbor_cell.coordinate
                    actual_c = c_list[current] + 1 # Cost between nodes is 1

                    # If the new cost is lower, calculate f and add to stack
                    if (actual_c < c_list.get(neighbor, float('inf'))):
                        c_list[neighbor] = actual_c
                        fathers[neighbor] = current
                        f_value = actual_c + heuristic(neighbor, goal)

                        # Add to stack
                        heapq.heappush(stack, (f_value, neighbor))

        # Reconstruct path
        if goal in fathers:
            path = []
            current = goal
            while current != start:
                path.append(current)
                current = fathers[current]
            path.reverse()
            return path
        
        # If no path found, return empty list
        return []
    

    def move(self, cell):
        """Move to a neighboring cell, prioritizing cells with trash."""

        #If the cell is a station, and is occupied, wait
        if cell.coordinate in self.stationCells and not self.hasBattery and self.stationOccupied(cell):
            self.state = "waiting"
            return
        
        # Move to the cell
        self.cell = cell

        #Add current cell to visited cells 
        self.visited_cells.add(cell.coordinate)
        self.steps += 1

        visited_agent = next(
            (obj for obj in cell.agents if isinstance(obj, EmptyAgent)), None
        )
        if visited_agent:
            visited_agent.visited = True

        #For station, check if reached and recharge battery
        if self.cell.coordinate in self.stationCells and not self.hasBattery:
            occupied = self.stationOccupied(self.cell)
            if not occupied:
                self.state = "recharging"  #change state to recharging when at station
                self.path_back_to_station = [] #clear path back to station
            else:
                self.state = "waiting"  #change state to waiting if station is occupied
        else:
            self.state = "idle"  #change state to idle after moving
            

    def clean(self, trash_cell):
        """Clean the trash cell that is in the current cell."""
        trash_cell.with_trash = False
        trash_cell.remove()
        self.trash_cleaned += 1
        self.state = "idle"  #change state to idle after cleaning


    def getNextReturnStep(self):
        """Get the next step to return to the station using A* algorithm."""
        if not self.path_back_to_station:
            self.calculateReturnPath() # Calculate path if not already done

        if self.path_back_to_station:
            next_coord = self.path_back_to_station.pop(0) # Get next coordinate in path and remove it from the list
            next_cell = self.model.grid[next_coord]
            self.state = "moving"  #change state to moving when returning
            return next_cell
        else:
            self.state = "idle"  #change state to idle if no path back to station
            return None
        
    def pathToNearestUnvisited(self):
        """Find the nearest unvisited cell for the roomba to move to."""
        grid = self.model.grid
        start = self.cell.coordinate

        visited = set(start)
        queue = deque([start]) 

        #while there are cells to explore
        while len(queue) > 0:
            current = queue.popleft()
            cell = grid[current]

            #if the cell has not been visited yet, return path to it
            if cell.coordinate not in self.visited_cells and not any(isinstance(a, ObstacleAgent) for a in cell.agents):
                return self.a_star(start, cell.coordinate)
    
            #explore neighbors
            valid_neighbors = cell.neighborhood.select(
                lambda cell: not any(isinstance(a, ObstacleAgent) for a in cell.agents)
            )

            # For each valid neighbor, add to queue if not visited

            for neighbor_cell in valid_neighbors:
                neighbor = neighbor_cell.coordinate

                #if neighbor has been visited, add to queue for further exploration
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        #if no unvisited cell found, return empty path
        return []
    
    def pathToNearestKnownTrash(self):
        """Find the nearest known trash cell for the roomba to move to."""
        if not self.trash_known_cells: #If no known trash cells, return empty path, just in case
            return []

        trash_cell = self.trash_known_cells.pop() #get the last known trash cell
        return self.a_star(self.cell.coordinate, trash_cell)
    
    def distanceToStation(self, stations=None):
        """Calculate the distance to the nearest station using Chebyshev distance."""
        # We use Chebyshev distance so that it doesn't have to calculate a_star every step 

        if stations is None:
            stations = self.stationCells
        
        if not stations:
            self.distance_to_station = float('inf')
            return None
        
        minimum_distance = float('inf')
        nearest_station = None

        x2, y2 = self.cell.coordinate

        #Find nearest station using Chebyshev distance
        for coord in stations:
            x1, y1 = coord
            distance = max(abs(x2 - x1), abs(y2 - y1))
            if distance < minimum_distance:
                minimum_distance = distance
                nearest_station = coord

        self.distance_to_station = minimum_distance
        return nearest_station

    def calculateReturnPath(self):
        """Calculate the path back to the station using A* algorithm."""
        start = self.cell.coordinate
        available_stations = [
            coord for coord in self.stationCells
            if not self.stationOccupied(self.model.grid[coord])
        ]
        if not available_stations: 
            self.state = "waiting"
            self.path_back_to_station = []
            return
        
        goal = self.distanceToStation(available_stations) #Get nearest available station

        if goal is None:
            self.state = "waiting"
            self.path_back_to_station = []
            return
        
        path = self.a_star(start, goal)

        if path:
            self.path_back_to_station = path
        else:
            self.state = "waiting"
            self.path_back_to_station = []

    def exchangeInfo(self, other_roomba):
        """Exchange visited cells and known stations with another roomba."""
        for cell in other_roomba.visited_cells:
            if cell not in self.visited_cells:
                self.visited_cells.add(cell)

        for station_coord in other_roomba.stationCells:
            if station_coord not in self.stationCells: #Add new station coordinates found by other roomba
                self.stationCells.append(station_coord) 

        # Timer to limit how long the roomba keeps the info
        self.hasInfo = True
        self.info_timer = 5  # Keep info for 5 steps
        self.state = "idle"  #change state to idle after exchanging info

    
    def stationOccupied(self, station_cell):
        """Check if the station cell is occupied by another roomba."""
        occupied = any(
            isinstance(agent, Roomba) and agent != self and agent.state == "recharging"
            for agent in station_cell.agents
        )
        return occupied

    def recharge(self):
        """Recharge the battery when at the station."""
        self.battery += 5
        if self.battery >= 100:
            self.battery = 100
            self.hasBattery = True
            self.state = "idle"  #change state to idle after recharging

    def step(self):
        """
        Determines the next action based on the current state of the agent.

        1. Check battery level.
        2. If battery is low, return to station. 
        3. If battery is enough, check for trash.
        4. If trash is found, clean it.
        5. If there's no trash, check for obstacles and move to a valid cell.
        6. Decrease battery after each action.

        """
        if self.state == "idle":
            self.checkBattery()
        elif self.state == "waiting":
            self.checkStation()
        
        if self.state == "returning":
            self.checkTrash()
            next_cell = self.getNextReturnStep()
            if next_cell is not None and self.state == "moving":
                self.move(next_cell)
        elif self.state == "recharging":
            self.recharge()
        elif self.state == "ready":
            roomba_agent = self.checkRoombas(self.cell)
            if self.state == "communicating":
                self.exchangeInfo(roomba_agent)
            elif self.state == "checkTrash":
                trash_cell = self.checkTrash()
                if self.state == "cleaning":
                    self.clean(trash_cell)
                elif self.state == "checkObstacles":
                    next_cell = self.checkObstacles()
                    if self.state == "moving":
                        self.move(next_cell)

        # Manage info timer
        if self.info_timer > 0:
            self.info_timer -= 1
            if self.info_timer == 0:
                self.hasInfo = False

        # Decrease battery after each action
        if self.state != "recharging" and self.state != "waiting": # Battery does not decrease while recharging or waiting
            self.battery -= 1
            if self.battery <= 0:
                self.remove()  # Remove agent if battery has died

class TrashAgent(FixedAgent):
    @property
    def with_trash(self):
        """Whether the cell has trash."""
        return self._with_trash
    
    @with_trash.setter
    def with_trash(self, value: bool) -> None:
        """Set trash presence state."""
        self._with_trash = value

    def __init__(self, model, cell):
        """Create a new trash object

        Args:
            model: Model instance
            cell: Cell to which this trash object belongs
        """
        super().__init__(model)
        self.cell=cell
        self._with_trash = True

class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class StationAgent(FixedAgent):
    """
    Station agent. Where the Roomba recharges.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell
    def step(self):
        pass

class EmptyAgent(FixedAgent):
    @property
    def visited(self):
        """Whether the cell has been visited by a Roomba."""
        return self._visited
    
    @visited.setter
    def visited(self, value: bool) -> None:
        """Set visited state."""
        self._visited = value

    def __init__(self, model, cell):
        """Create a new trash object

        Args:
            model: Model instance
            cell: Cell that's empty but visited by a Roomba
        """
        super().__init__(model)
        self.cell=cell
        self._visited = False
