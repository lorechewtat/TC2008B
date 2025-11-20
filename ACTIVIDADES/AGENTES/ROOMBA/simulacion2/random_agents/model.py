from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.datacollection import DataCollector

from .agent import Roomba, ObstacleAgent, TrashAgent, StationAgent, EmptyAgent

class RandomModel(Model):
    """
    Creates a new model with random agents.
    Args:
        num_agents: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, num_agents=1, rate_obstacles=0.1, rate_trash=0.2, max_steps=3000, width=8, height=8, seed=42):

        super().__init__(seed=seed)

        # Initialize model parameters
        self.num_agents = num_agents
        self.num_obstacles = int(rate_obstacles * (width - 2) * (height - 2))
        self.num_trash = int(rate_trash * (width - 2) * (height - 2))
        self.max_steps = max_steps
        self.seed = seed
        self.width = width
        self.height = height

        # Initialize grid
        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        # Setup data collection
        model_reporters = {
            "Battery %": lambda m: sum(agent.battery for agent in m.agents_by_type[Roomba]) / len(m.agents_by_type[Roomba]) if len(m.agents_by_type[Roomba]) > 0 else 0,
            "Trash Collected %": lambda m: (m.num_trash - len(m.agents_by_type[TrashAgent])) / m.num_trash * 100 if m.num_trash > 0 else 100,
            "Roombas Alive": lambda m: len(m.agents_by_type[Roomba]),
            "Roomba Steps": lambda m: sum(agent.steps for agent in m.agents_by_type[Roomba]) / len(m.agents_by_type[Roomba]) if len(m.agents_by_type[Roomba]) > 0 else 0,
            "Time (Steps)": lambda m: m.steps
        }
        self.datacollector = DataCollector(model_reporters)

        # Identify the coordinates of the border of the grid
        border = [(x,y)
                  for y in range(height)
                  for x in range(width)
                  if y in [0, height-1] or x in [0, width - 1]]

        # Create the border cells
        for _, cell in enumerate(self.grid):
            if cell.coordinate in border:
                ObstacleAgent(self, cell = cell)

        # Create the roombas and stations randomly
        roomba_cells = self.random.choices(self.grid.empties.cells, k=self.num_agents)
        for cell in roomba_cells:
            Roomba(self, cell=cell)
            StationAgent(self, cell=cell)

        # Create the obstacles randomly
        ObstacleAgent.create_agents(
            self,
            self.num_obstacles,
            cell=self.random.choices(self.grid.empties.cells, k=self.num_obstacles)
        )


        TrashAgent.create_agents(
            self,
            self.num_trash,
            cell=self.random.choices(self.grid.empties.cells, k=self.num_trash)
        )

        for _, cell in enumerate(self.grid):
            EmptyAgent(self, cell=cell)


        self.running = True
        self.datacollector.collect(self)


    def step(self):
        '''Advance the model by one step.'''

        # If the model is not running, do nothing
        if not self.running:
            return

        self.agents.shuffle_do("step")
        
        # Collect data
        self.datacollector.collect(self)

        # Stop the model if all trash is collected
        if len(self.agents_by_type[TrashAgent]) == 0 or self.steps >= int(self.max_steps):
            self.running = False

            # Only print the last step
            df = self.datacollector.get_model_vars_dataframe()
            print(df.tail(1))

            # Add steps by each roomba to the output
            for agent in self.agents_by_type[Roomba]:
                print(f"Roomba {agent.unique_id}: Battery {agent.battery}%, Steps {agent.steps}")
