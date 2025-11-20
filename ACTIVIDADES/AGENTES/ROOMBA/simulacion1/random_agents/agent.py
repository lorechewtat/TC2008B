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
        self.stationCell = self.cell

        self.visited_cells = set(self.cell.coordinate)
        self.trash_known_cells = set()

        self.path_back_to_station = []
        self.distance_to_station = 0
        self.steps = 0
        self.hasBattery = True

    # Action methods that allow the agent to check its environment and change its state

    def checkBattery(self):
        """Check if the battery is low and decide the next action."""

        step_margin = 5 
        total_distance = self.distance_to_station + step_margin

        if self.battery <= total_distance:
            self.hasBattery = False
            self.state = "returning" #change state to returning to station if battery is low
        else:
            self.state = "ready" #change state to ready if battery is sufficient


    def checkTrash(self):
        """Return the cells with trash."""
        trash_cell = next(
            (obj for obj in self.cell.agents if isinstance(obj, TrashAgent)), None
        )

        # Add trash cell to known trash cells for future reference
        if (self.state == "returning") and trash_cell is not None:
            self.trash_known_cells.add(self.cell.coordinate)

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
        if self.cell == self.stationCell and not self.hasBattery:
            self.state = "recharging"  #change state to recharging when at station
            self.path_back_to_station = [] #clear path back to station
        else:
            self.distanceToStation()
            self.state = "idle"  #change state to idle after moving
            

    def clean(self, trash_cell):
        """Clean the trash cell that is in the current cell."""
        trash_cell.with_trash = False
        trash_cell.remove()
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
    
    def distanceToStation(self):
        """Calculate the distance to the nearest station using Chebyshev distance."""
        # We use Chebyshev distance so that it doesn't have to calculate a_star every step 
        x1, y1 = self.stationCell.coordinate
        x2, y2 = self.cell.coordinate

        self.distance_to_station = max(abs(x2 - x1), abs(y2 - y1))
        return self.distance_to_station

    def calculateReturnPath(self):
        """Calculate the path back to the station using A* algorithm."""
        start = self.cell.coordinate
        goal = self.stationCell.coordinate
        path = self.a_star(start, goal)
        self.path_back_to_station = path

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
        
        if self.state == "returning":
            self.checkTrash()
            next_cell = self.getNextReturnStep()
            if next_cell is not None and self.state == "moving":
                self.move(next_cell)
        elif self.state == "recharging":
            self.recharge()
        elif self.state == "ready":
            trash_cell = self.checkTrash()
            if self.state == "cleaning":
                self.clean(trash_cell)
            elif self.state == "checkObstacles":
                next_cell = self.checkObstacles()
                if self.state == "moving":
                    self.move(next_cell)

        # Decrease battery after each action
        if self.state != "recharging": # Battery does not decrease while recharging
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
