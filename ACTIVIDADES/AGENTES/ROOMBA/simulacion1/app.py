from random_agents.agent import Roomba, ObstacleAgent, TrashAgent, StationAgent, EmptyAgent
from random_agents.model import RandomModel

import solara
from solara import Text

from mesa.visualization import (
    CommandConsole,
    Slider,
    SolaraViz,
    SpaceRenderer,
    make_plot_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, Roomba):
        portrayal.color = "#007AFF"
        portrayal.marker = "o"
        portrayal.size = 60

    elif isinstance(agent, StationAgent):
        portrayal.color = "#FFC107"
        portrayal.marker = "v"
        portrayal.size = 55

    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "#8C8888"
        portrayal.marker = "s"
        portrayal.size = 50

    elif isinstance(agent, TrashAgent):
        portrayal.color = "#FF0000"
        portrayal.marker = "x"
        portrayal.size = 35

    elif isinstance(agent, EmptyAgent):
        if agent.visited:
            portrayal.color = "lightgray"
            portrayal.marker = "."
            portrayal.size = 50
        else:
            portrayal.color = "white"
            portrayal.marker = "."
            portrayal.size = 0.0001

    return portrayal

def get_roomba(model):
    # Busca el primer agente que sea instancia de Roomba
    for agent in model.agents_by_type[Roomba]:
        return agent
    return None

def info_component(model):
    roomba = get_roomba(model)

    # Texto plano con saltos de línea
    return Text(
        f"Battery: {roomba.battery}%\n"
        f"State: {roomba.state}\n"
        f"Trash Known: {len(roomba.trash_known_cells)}\n"
        f"Visited Cells: {len(roomba.visited_cells)}"
    )



model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "max_steps": {
        "type": "InputText",
        "value": 3000,
        "label": "Maximum Steps",
    },
    "width": Slider("Grid width", 28, 1, 50),
    "height": Slider("Grid height", 28, 1, 50),
    "rate_obstacles": Slider("Obstacle Rate", 0.1, 0, 0.9, 0.05),
    "rate_trash": Slider("Trash Rate", 0.2, 0, 0.9, 0.05),
}

# Create the model using the initial parameters from the settings
model = RandomModel(
    seed=model_params["seed"]["value"],
    max_steps=model_params["max_steps"]["value"],
    width=model_params["width"].value,
    height=model_params["height"].value,
    rate_obstacles=model_params["rate_obstacles"].value,
    rate_trash=model_params["rate_trash"].value,
)

def post_process(ax):
    ax.set_aspect("equal")

def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))

lineplot_component = make_plot_component(
    {"Battery %": "tab:blue", "Trash Collected %": "tab:green"},
    post_process=post_process_lines,
)

renderer = SpaceRenderer(
    model,
    backend="matplotlib",
)
renderer.draw_agents(random_portrayal)
renderer.post_process = post_process

page = SolaraViz(
    model,
    renderer,
    components=[lineplot_component, info_component,CommandConsole],
    model_params=model_params,
    name="Roomba Simulation",
)
