from game_of_life.model import ConwaysGameOfLife
from mesa.visualization import (
    SolaraViz,
    make_space_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def agent_portrayal(agent): #con esto podemos visualizar como queremos que se vean los diferentes agentes
    return AgentPortrayalStyle(
        color="white" if agent.state == 0 else "black",
        marker="s",
        size=30,
    )

def post_process(ax): #esto se hace con matplotlib, y aqui decido como quiero que se vea la grafica
    ax.set_aspect("equal")

model_params = { #diccionario en python, es como un json
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": {
        "type": "SliderInt",
        "value": 50,
        "label": "Width",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 50,
        "label": "Height",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "initial_fraction_alive": {
        "type": "SliderFloat",
        "value": 0.2,
        "label": "Cells initially alive",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
}

# Create initial model instance 
gof_model = ConwaysGameOfLife() #creo el modelo

space_component = make_space_component( #creo el componente visual que va a mostrar el modelo
        agent_portrayal,
        draw_grid = False,
        post_process=post_process
)

page = SolaraViz( #recibo que modelo uso, que componente dibujo y con que parametros
    gof_model,
    components=[space_component],
    model_params=model_params,
    name="Game of Life",
)
