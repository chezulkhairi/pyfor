from plotly import offline
from plotly.graph_objs import graph_objs as go
import numpy as np

def iplot3d(las, max_points, point_size, dim, colorscale):
    """
    Plots the 3d point cloud in a compatible version for Jupyter notebooks.
    :return:
    """
    # Check if in iPython notebook
    try:
        cfg = get_ipython().config
        if 'jupyter' in cfg['IPKernelApp']['connection_file']:
            if las.header.count > max_points:
                print("Point cloud too large, down sampling for plot performance.")
                rand = np.random.randint(0, las.count, 30000)
                x = las.points.x.iloc[rand]
                y = las.points.y.iloc[rand]
                z = las.points.z.iloc[rand]
                color_var = las.points[dim].values[rand]

                trace1 = go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode='markers',
                    marker=dict(
                        size=point_size,
                        color=color_var,
                        colorscale=colorscale,
                        opacity=1
                    )
                )

                data = [trace1]
                layout = go.Layout(
                    margin=dict(
                        l=0,
                        r=0,
                        b=0,
                        t=0
                    ),
                    scene=dict(
                        aspectmode="data"
                    )
                )
                offline.init_notebook_mode(connected=True)
                fig = go.Figure(data=data, layout=layout)
                offline.iplot(fig)
        else:
            print("This function can only be used within a Jupyter notebook.")
            return(False)
    except NameError:
        return(False)

def iplot3d_surface(array, colorscale):
    data = [
        go.Surface(
            z=array,
            colorscale=colorscale
        )
    ]

    layout = go.Layout(
        autosize=False,

        width=600,
        height=600,
        margin=dict(
            l=65,
            r=50,
            b=65,
            t=90
        ),
        scene=dict(
            aspectmode="data"
        )
    )
    offline.init_notebook_mode(connected=True)
    fig = go.Figure(data=data, layout=layout)
    offline.iplot(fig)

