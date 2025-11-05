# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self):
        """Compute if the cell will be dead or alive at the next tick.  This is
        based on the number of alive or dead neighbors.  The state is not
        changed here, but is just computed and stored in self._nextState,
        because our current state may still be necessary for our neighbors
        to calculate their next state.
        """

        #Get the positions of the top, top left and top right neighbors
        left_neighbor_pos = (self.pos[0] - 1) %  50, (self.pos[1] + 1) % 50
        right_neighbor_pos = (self.pos[0] + 1) % 50, (self.pos[1] + 1) % 50
        top_neighbor_pos = self.pos[0], (self.pos[1] + 1) % 50

        #Initialize the neightbors' state
        left = 0
        top = 0
        right = 0

        #Get the states of the neighbors
        for neighbor in self.neighbors:
            if neighbor.pos == left_neighbor_pos:
                left = neighbor.is_alive
            elif neighbor.pos == right_neighbor_pos:
                right = neighbor.is_alive
            elif neighbor.pos == top_neighbor_pos:
                top = neighbor.is_alive


        #Conditions
        #First condition helps the simulation to not run into an infinite loop
        
        if left and top and right: #111
            self._next_state = self.DEAD
        elif left and top and not right: #110
            self._next_state = self.ALIVE
        elif left and not top and right: #101
            self._next_state = self.DEAD
        elif left and not top and not right:#100
            self._next_state = self.ALIVE
        elif not left and top and right: #011
            self._next_state = self.ALIVE
        elif not left and top and not right: #010
            self._next_state = self.DEAD
        elif not left and not top and right: #001
            self._next_state = self.ALIVE
        elif not left and not top and not right: #000
            self._next_state = self.DEAD

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state
