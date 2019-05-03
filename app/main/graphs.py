import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json

def create_plot(x,y):

    data = [
        go.Bar(
            x=x, # assign x as the dataframe column 'x'
            y=y
        )
    ]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON