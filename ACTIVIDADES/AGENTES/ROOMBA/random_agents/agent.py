from mesa.discrete_space import CellAgent, FixedAgent

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
        self.state = "init"
        self.battery = 100  

    def checkObstacels(self):
        """Return the cells with obstacles."""
        return (next(obj for obj in self.cell.agents if isinstance(obj, ObstacleAgent)), None)

    def checkTrash(self):
        """Return the cells with trash."""
        return (next(obj for obj in self.cell.agents if isinstance(obj, TrashAgent)), None)

    def move(self):
        """Move to a neighboring cell, preferably one with sheep."""
        cells_with_trash = self.cell.neighborhood.select(
            lambda cell: any(isinstance(obj, TrashAgent) for obj in cell.agents)
        )
        cells_empty = self.cell.neighborhood.select(lambda cell: cell.is_empty)
        target_cells = (
            cells_with_trash if len(cells_with_trash) > 0 else cells_empty
        )
        self.cell = target_cells.select_random_cell()

    def clean(self):
        """If possible, clean the trash in the current cell."""
        trash_cell = next(
            (obj for obj in self.cell.agents if isinstance(obj, TrashAgent)), None
        )
        if trash_cell and trash_cell.with_trash:
            trash_cell.with_trash = False
            trash_cell.remove()

    def step(self):
        """
        Determines the new direction it will take, and then moves
        """
        self.clean()  # Primero limpia si hay basura en la celda actual
        self.move()
        self.battery -= 1

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
