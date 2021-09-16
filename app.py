import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table

import pandas as pd
import numpy as np 
import plotly.graph_objects as go
import glob
import re
import json
import datetime
import os

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)










app.layout = html.Div([
    dcc.Tabs(id = "tabs", value = "score-tab", children = [
        dcc.Tab(label = "Enter Score", value = "score-tab"),
        dcc.Tab(label = "Stats", value = "stats-tab")
    ]),
    html.Div(id = "tab-content")
])



@app.callback(Output('tab-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    print(tab)
    if tab == 'score-tab':
        return html.Div([
            html.H5("Warning: Changing tabs will clear an unsubmitted scorecard"),
            html.Button("Reload Course Options", id= "course_reset", style = {"margin-bottom":20, "margin-top":20}),
            html.Div(children = [
                dcc.Dropdown(id = "course_select", placeholder = "Select Course"),
                dcc.Dropdown(id = "tee_select", placeholder = "Select Tees")],
                style = {"width": "25%" }
            ),
            html.Button("Submit Card", id= "score_submit", style = {"margin-top":20}),
            html.Div(id = "Submission"),
            html.Div(id = "scorecard", style = {"padding":100}),
            html.Div(id = "course_options", style = {"display":"none"})
        ], style = {"padding":50})

    elif tab == 'stats-tab':
        return html.Div([
            html.H3('Stats')
        ])




                

@app.callback(
    [Output(component_id = "course_select", component_property = "options"),
     Output(component_id = "course_options", component_property = "children")],
     Input(component_id = "course_reset", component_property = "n_clicks"),
     State(component_id = "tee_select", component_property = "options")
)
def load_courses(button, test):
    courses = {}
    for card in glob.glob("./Courses/*.csv"):
        course = card.split("\\")[1].split("_")
        tees = course[-1].replace(".csv", "")
        course = " ".join(course[:-1])
        if course in courses.keys():
            courses[course].append(tees)
        else:
            courses[course] = [tees]
        
    course_choices = [{"label": c, "value": c} for c in courses.keys()]
    print(course_choices)
    return course_choices, json.dumps(courses)

@app.callback(
    [Output(component_id = "tee_select", component_property = "options"),
     Output(component_id = "tee_select", component_property = "value")],
    Input(component_id = "course_select", component_property = "value"),
    State(component_id = "course_options", component_property = "children")
)
def load_tees(course, all_courses):
    if course == None:
        return {}, ""
    else:
        return [{"label": t, "value": t} for t in json.loads(all_courses)[course]], ""


@app.callback(
    Output(component_id = "scorecard", component_property = "children"),
    Input(component_id = "tee_select", component_property = "value"),
    State(component_id = "course_select", component_property = "value")
)
def show_scorecard(tee, course):
    if isinstance(course, str) & isinstance(tee, str) & (course != "") & (tee != ""):
        course = course.replace(" ", "_")
        path = f"Courses/{course}_{tee}.csv"
        card = pd.read_csv(path).fillna("")
        cols = list(card.columns)
        table = dash_table.DataTable(id = "card", 
                                     columns = [{"name":i, "id":i, "editable": False} for i in cols[0:4]] +\
                                               [{"name":i, "id":i} for i in cols[4:6]] +\
                                               [{"name":"Drive", "id":"Drive", 'presentation': 'dropdown'}], 
                                     data = [dict(card.iloc[i,:]) for i in range(len(card))],
                                     editable = True,
                                     dropdown={'Drive': {'options': [{'label': i, 'value': i} for i in ["Wide Left", "Narrow Left", "Fairway", "Narrow Right", "Wide Right"]]}}
                                     )
        return table
    else:
        table = dash_table.DataTable(id = "card", 
                             columns = [], 
                             data = []
                             )
        return table



@app.callback(
    Output(component_id = "Submission", component_property = "children"),
    [Input(component_id = "score_submit", component_property = "n_clicks"),
     Input(component_id = "scorecard", component_property = "children")],
    [State(component_id = "course_select", component_property = "value"),
    State(component_id = "course_select", component_property = "value"),
    State(component_id = "card", component_property = "data")]
)
def submit(button, card, course, tee, data):
    print("SUBMIT RUNS")
    ctx = dash.callback_context
    if len(ctx.triggered) > 0:
        print(ctx.triggered[0]["prop_id"])
        if ctx.triggered[0]["prop_id"] == "scorecard.children":
            return ""
    if data == []:
        return "No scorecard active. Select a course and tees to enter a card."

    drives = [row["Drive"] for row in data]
    strokes = [row["Strokes"] for row in data]
    putts = [row["Putts"] for row in data]
    if "" in drives + strokes + putts:
        return "Scorecard Incomplete. Please fill in missing fields."
    elif sum([s.isnumeric() for s in strokes]) != len(strokes):
        return "Non-numeric stroke value entered. Please enter only numeric scores."
    elif sum([s.isnumeric() for s in putts]) != len(putts):
        return "Non-numeric putts value entered. Please enter only numeric putts."
    else:
        now = datetime.datetime.now()
        date = now.strftime("%d%m%Y")
        time = now.strftime("%H:%M:%S")
        course = course.replace(" ", "")
        directory = f"Recorded/{course}/{tee}"
        os.makedirs(directory, exist_ok = True)

        return f"Card Saved at {time}"

if __name__ == "__main__":
    app.run_server()



