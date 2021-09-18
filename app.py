'''
TODO:

Make scorecard a class with card, slope, par etc as attributes
'''











import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table
import plotly.express as px

import pandas as pd
import numpy as np 
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
        dcc.Tab(label = "Stats", value = "stats-tab"),
        dcc.Tab(label = "Handicap", value = "handicap-tab")
    ]),
    html.Div(id = "tab-content")
])



@app.callback(Output('tab-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'score-tab':
        return html.Div([
            #html.H5("Warning: Changing tabs will clear an unsubmitted scorecard"),
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
            html.Button("Reload Course Options", id= "course_reset2", style = {"margin-bottom":20, "margin-top":20}),
            html.Div(children = [
                dcc.Dropdown(id = "course_select2", placeholder = "Select Course", multi = True),
                dcc.Dropdown(id = "tee_select2", placeholder = "Select Tees", multi = True)],
                style = {"width": "25%" }
            ),
            html.Div(["Include rounds in the following date range:"], style = {"margin-top":20}),
            dcc.DatePickerRange(
                id='my-date-picker-range',
                min_date_allowed = datetime.date(2000, 1, 1),
                max_date_allowed = datetime.date.today(),
                initial_visible_month = datetime.date.today(),
                minimum_nights=0),
            html.Br(),
            html.Button("Load Scores for Selected Options", id= "scores_button", style = {"margin-bottom":20, "margin-top":20}),
            html.Div(id = "load_scores_error"),
            html.Div(id = "driving_accuracy_bar", style = {"margin-top":20}), 
            html.Div(id = "par3_accuracy_bar", style = {"margin-top":20}), 
            html.Div(id = "gir_bar"),
            html.Div(id = "strokes_by_par_bar"),
            html.Div(id = "putts_by_par_bar"),
            html.Div(id = "course_options2", style = {"display":"none"}),
            html.Div(id = "scores", style = {"display":"none"})
        ], style = {"padding":50})

    elif tab == 'handicap-tab':
        return html.Div([
            html.Button("Reload Scorecards", id= "scorecard_reset", style = {"margin-bottom":20, "margin-top":20}),
            html.Div(id = "handicap_bar")
        ], style = {"padding":50})




                

@app.callback(
    [Output(component_id = "course_select", component_property = "options"),
     Output(component_id = "course_options", component_property = "children")],
     Input(component_id = "course_reset", component_property = "n_clicks")
)
def load_courses(button):
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
                                               [{"name":"Tee Shot", "id":"Tee Shot", 'presentation': 'dropdown'}], 
                                     data = [dict(card.iloc[i,:]) for i in range(len(card))],
                                     editable = True,
                                     dropdown={'Tee Shot': {'options': [{'label': i, 'value': i} for i in ["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"]]}}
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
    State(component_id = "tee_select", component_property = "value"),
    State(component_id = "card", component_property = "data")]
)
def submit(button, card, course, tee, data):
    ctx = dash.callback_context
    if len(ctx.triggered) > 0:
        if ctx.triggered[0]["prop_id"] == "scorecard.children":
            return ""
    if data == []:
        return "No scorecard active. Select a course and tees to enter a card."

    drives = [row["Tee Shot"] for row in data]
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
        directory = f"Recorded/{course}/{tee}"
        os.makedirs(directory, exist_ok = True)
        card_df = pd.DataFrame(columns = data[0].keys(), data = [row.values() for row in data])
        card_df = card_df[["Hole", "Par", "Index", "Yardage", "Strokes", "Putts", "Tee Shot"]]
        card_df.to_csv(directory + "/" + date + ".csv", index = False)
        return f"Card Saved at {time}"





@app.callback(
    [Output(component_id = "course_select2", component_property = "options"),
     Output(component_id = "course_options2", component_property = "children")],
     Input(component_id = "course_reset2", component_property = "n_clicks")
)
def load_courses2(button):
    paths = [glob.glob(f"{folder}/*") for folder in glob.glob("Recorded/*")]
    paths = [path.split("\\")[1:] for sublist in paths for path in sublist]
    courses = {}
    for pair in paths:
        if pair[0] in courses:
            courses[pair[0]].append(pair[1])
        else:
            courses[pair[0]] = [pair[1]]
        
    course_choices = [{"label": c, "value": c} for c in courses.keys()]
    return course_choices, json.dumps(courses)


@app.callback(
    [Output(component_id = "tee_select2", component_property = "options"),
     Output(component_id = "tee_select2", component_property = "value")],
    Input(component_id = "course_select2", component_property = "value"),
    State(component_id = "course_options2", component_property = "children")
)
def load_tees2(courses, all_courses):
    if courses == None:
        return {}, ""
    else:
        return [{"label": f"{t} ({course})", "value": f"{t} ({course})"} for course in courses for t in json.loads(all_courses)[course]], ""


@app.callback(
    [Output(component_id = "scores", component_property = "children"),
    Output(component_id = "load_scores_error", component_property = "children")],
    Input(component_id = "scores_button", component_property = "n_clicks"),
    [State(component_id = "tee_select2", component_property = "value"),
     State(component_id = "my-date-picker-range", component_property = "start_date"),
     State(component_id = "my-date-picker-range", component_property = "end_date")]
    )
def load_scores(button, tees, start, end):
    if (tees != None) & (tees != []) & (tees != "") & (start != None) & (end != None) & (dash.callback_context.triggered[0]["prop_id"] != "."):
        path = "Recorded/course/tee/*.csv"
        start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end, "%Y-%m-%d").date()
        tees = [(tee.split("(")[1].replace(")", ""), tee.split(" ")[0]) for tee in tees]
        files = [glob.glob(path.replace("course", course).replace("tee", tee)) for course, tee in tees]
        files = [file for sublist in files for file in sublist]
        files = [file for file in files if start <= datetime.datetime.strptime(file.split("\\")[1].split(".")[0], "%d%m%Y").date() <= end]
        if files == []:
            return [], "No recorded scores satisfying filters."
        else:    
            scores = [pd.read_csv(file).to_json(orient = "split") for file in files]
            return json.dumps(dict(zip(files,scores))), ""
    elif dash.callback_context.triggered[0]["prop_id"] == ".":
        return [], ""
    else:
        return [], "Incomplete option selections. Please specify course, tees, start date and end date."


@app.callback(
    Output(component_id = "driving_accuracy_bar", component_property = "children"),
    Input(component_id = "scores", component_property = "children")
    )
def driving_accuracy_bar_plot(data):
    if data != []:
        cards = [pd.read_json(df, orient = "split") for df in json.loads(data).values()]
        cards = pd.concat(cards)
        cards = cards[cards["Par"] != 3].groupby("Tee Shot").size().reset_index(name = "%")
        for label in ["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"]:
            if label not in cards["Tee Shot"].values:
                cards = cards.append({"Tee Shot": label, "%": 0}, ignore_index=True)
        cards = cards.set_index("Tee Shot", drop = True).reindex(["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"]).reset_index(drop = False)
        cards["%"] = cards["%"].divide(cards["%"].sum()).multiply(100)
        cards["str"] = cards["%"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(cards, x="Tee Shot", y="%", text = "str")
        fig.update_yaxes(range=[0,100], title_text = "Proportion (%)")
        fig.update_xaxes(title_text = "")
        return [html.H3("Driving Accuracy"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []


@app.callback(
    Output(component_id = "par3_accuracy_bar", component_property = "children"),
    Input(component_id = "scores", component_property = "children")
    )
def par3_accuracy_bar_plot(data):
    if data != []:
        cards = [pd.read_json(df, orient = "split") for df in json.loads(data).values()]
        cards = pd.concat(cards)
        cards = cards[cards["Par"] == 3].groupby("Tee Shot").size().reset_index(name = "%")
        for label in ["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"]:
            if label not in cards["Tee Shot"].values:
                cards = cards.append({"Tee Shot": label, "%": 0}, ignore_index=True)
        cards = cards.set_index("Tee Shot", drop = True).reindex(["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"]).reset_index(drop = False)
        cards["%"] = cards["%"].divide(cards["%"].sum()).multiply(100)
        cards["str"] = cards["%"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(cards, x="Tee Shot", y="%", text = "str")
        fig.update_yaxes(range=[0,100], title_text = "Proportion (%)")
        fig.update_xaxes(title_text = "")
        return [html.H3("Par 3 Accuracy"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []


@app.callback(
    Output(component_id = "gir_bar", component_property = "children"),
    Input(component_id = "scores", component_property = "children")
    )
def gir_plot(data):
    if data != []:
        cards = pd.concat([pd.read_json(df, orient = "split")[["Par", "Strokes", "Putts"]] for df in json.loads(data).values()])
        cards["GIR"] = cards["Par"]-(cards["Strokes"]-cards["Putts"]) == 2 
        GIR = 100*cards["GIR"].sum()/len(cards)
        cards = cards[["Par", "GIR"]].groupby("Par").sum().divide(cards[["Par", "GIR"]].groupby("Par").size(), axis = 0).multiply(100).reset_index(drop = False)
        cards["Par"] = cards["Par"].apply(lambda x: f"Par {x:.0f}")
        cards = cards.append({"Par": "Overall", "GIR": GIR}, ignore_index = True).sort_values("Par")
        cards["str"] = cards["GIR"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(cards, x="Par", y="GIR", text = "str")
        fig.update_yaxes(range=[0,100], title_text = "GIR Proportion (%)")
        fig.update_xaxes(title_text = "")
        return [html.H3("Greens in Regulation"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []


@app.callback(
    Output(component_id = "strokes_by_par_bar", component_property = "children"),
    Input(component_id = "scores", component_property = "children")
    )
def par_plot(data):
    if data != []:
        cards = pd.concat([pd.read_json(df, orient = "split")[["Par", "Strokes"]] for df in json.loads(data).values()])
        cards["Par"] = cards["Par"].apply(lambda x: f"Par {x:.0f}")
        overall = cards.Strokes.mean()
        cards = cards.groupby("Par").mean().reset_index(drop = False)
        cards = cards.append({"Par":"Overall", "Strokes":overall}, ignore_index = True).sort_values("Par")
        fig = px.bar(cards, x="Par", y="Strokes", text = "Strokes")
        fig.update_xaxes(title_text = "")
        fig.update_yaxes(title_text = "Average Strokes", range = [0, 2*cards.Strokes.max()])
        return [html.H3("Average Strokes"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []
    

@app.callback(
    Output(component_id = "putts_by_par_bar", component_property = "children"),
    Input(component_id = "scores", component_property = "children")
    )
def putts_plot(data):
    if data != []:
        cards = pd.concat([pd.read_json(df, orient = "split")[["Par", "Putts"]] for df in json.loads(data).values()])
        cards["Par"] = cards["Par"].apply(lambda x: f"Par {x:.0f}")
        overall = cards.Putts.mean()
        cards = cards.groupby("Par").mean().reset_index(drop = False)
        cards = cards.append({"Par":"Overall", "Putts":overall}, ignore_index = True).sort_values("Par")
        fig = px.bar(cards, x="Par", y="Putts", text = "Putts")
        fig.update_xaxes(title_text = "")
        fig.update_yaxes(title_text = "Average Putts", range = [0, 2*cards.Putts.max()])
        return [html.H3("Average Putts"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []



def whs_cards(n):
    if n < 2:
        return None,None
    elif n in [3,4,5]:
        return 1, n-5
    elif n in [6,7,8]:
        return 2, np.min(n-7,0)
    elif n in [9,10,11]:
        return 3, 0
    elif n in [12,13,14]:
        return 4, 0
    elif n in [15,16]:
        return 5, 0
    elif n in [17,18]:
        return 6, 0
    elif n == 19:
        return 7, 0
    elif n == 20:
        return 8, 0 
    else:
        raise ValueError("More than 20 scorecards returned")



    
@app.callback(
    Output(component_id = "handicap_bar", component_property = "children"),
    Input(component_id = "scorecard_reset", component_property = "n_clicks")
    )
def handicap_cards(button):
    all_cards = sorted(glob.glob("Recorded/*/*/*"), key = lambda x: datetime.datetime.strptime(x.split("\\")[-1].split(".")[0], "%d%m%Y").date(), reverse = True)[:20]
    n_lowest, adjustment = whs_cards(len(all_cards))
    return f"{len(all_cards)} cards returned. Handicap will be average of lowest {n_lowest} plus adjustment of {adjustment:.0f}"


 


if __name__ == "__main__":
    app.run_server()



