'''
TODO:

Use dcc.Store to persist choices instead of html.Div
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
        dcc.Tab(label = "Summary Stats", value = "stats-tab"),
        dcc.Tab(label = "Round-by-Round Stats", value = "round-stats-tab"),
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
        ], style = {"padding":100})

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
            html.Div(id = "scores%_bar"),
            html.Div(id = "strokes_by_par_bar"),
            html.Div(id = "putts_by_par_bar"),
            html.Div(id = "course_options2", style = {"display":"none"}),
            html.Div(id = "scores", style = {"display":"none"})
        ], style = {"padding":100})
    elif tab == 'round-stats-tab':
        return html.Div([
            html.Button("Reload Data", id = "round-stats-reset", style = {"margin-bottom":20, "margin-top":20}),
            dcc.Dropdown(id = "n_rounds", placeholder = "Number of rounds to include"),
            html.Div(id = "driving_accuracy_bar2", style = {"margin-top":20}), 
            html.Div(id = "par3_accuracy_bar2", style = {"margin-top":20}),
            html.Div(id = "gir_bar2", style = {"margin-top":20}),
            html.Div(id = "recent_rounds_data", style = {"display":"none"}),
            html.Div(id = "scores_2", style = {"display":"none"})
        ], style = {"padding":100})
    elif tab == 'handicap-tab':
        return html.Div([
            html.Button("Reload Scorecards", id= "scorecard_reset", style = {"margin-bottom":20, "margin-top":20}),
            html.Div(id = "strokes_bar"),
            html.Div(id = "index_bar")
        ], style = {"padding":100})




                

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
        card = pd.read_csv(path, usecols = ["Hole","Par","Index","Yardage","Strokes","Putts","Tee Shot"]).fillna("")
        cols = list(card.columns)
        print(card)
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
        course = course.replace(" ", "_")
        path = f"Courses/{course}_{tee}.csv"
        ratings = pd.read_csv(path, usecols = ["Slope", "Course"])
        card_df = pd.DataFrame(columns = data[0].keys(), data = [row.values() for row in data])
        card_df = card_df[["Hole", "Par", "Index", "Yardage", "Strokes", "Putts", "Tee Shot"]]
        card_df = pd.concat([card_df, ratings], axis = 1)
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
            scores = [pd.read_csv(file, usecols = ["Hole","Par","Index","Yardage","Strokes","Putts","Tee Shot"]).to_json(orient = "split") for file in files]
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
        cards["GIR"] = cards["Par"]-(cards["Strokes"]-cards["Putts"]) >= 2 
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


score_dict = {-3:"Albatross", -2:"Eagle", -1:"Birdie", 0:"Par", 1:"Bogey", 2:"Double", 3:"Triple", 4:"Worse than triple"}
reverse_dict = {v:k for k,v in score_dict.items()}
def score_map(n):
    if n<=3 in score_dict.keys():
        return score_dict[n]
    elif n > 3: return "Worse than triple"


@app.callback(
    Output(component_id = "scores%_bar", component_property = "children"),
    Input(component_id = "scores", component_property = "children")
    )
def scores_plot(data):
    if data != []:
        cards = pd.concat([pd.read_json(df, orient = "split")[["Par", "Strokes"]] for df in json.loads(data).values()])
        cards["Score"] = cards.apply(lambda x: score_map(x["Strokes"]-x["Par"]), axis = 1)
        cards = cards.groupby("Score").size().reset_index(name = "%")
        cards["%"] = cards["%"].divide(cards["%"].sum()).multiply(100)
        cards["str"] = cards["%"].apply(lambda x: f"{x:.0f}%")
        cards["order"] = cards['Score'].replace(reverse_dict)
        cards = cards.sort_values("order")
        fig = px.bar(cards, x="Score", y="%", text = "str")
        fig.update_xaxes(title_text = "")
        fig.update_yaxes(range=[0,100], title_text = "Proportion (%)")
        return [html.H3("Score Type %"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
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
        cards["str"] = cards["Strokes"].apply(lambda x: f"{x:.2f}")
        fig = px.bar(cards, x="Par", y="Strokes", text = "str")
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
        cards["str"] = cards["Putts"].apply(lambda x: f"{x:.2f}")
        fig = px.bar(cards, x="Par", y="Putts", text = "str")
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
    [Output(component_id = "strokes_bar", component_property = "children"),
     Output(component_id = "index_bar", component_property = "children")],
    Input(component_id = "scorecard_reset", component_property = "n_clicks")
    )
def handicap_cards(button):
    all_cards = sorted(glob.glob("Recorded/*/*/*"), key = lambda x: datetime.datetime.strptime(x.split("\\")[-1].split(".")[0], "%d%m%Y").date(), reverse = True)[:20]
    if len(all_cards)>=3:
        n_lowest, adjustment = whs_cards(len(all_cards))
        cards = [pd.read_csv(card) for card in all_cards[::-1]]
        slopes = [card.Slope.iloc[0] for card in cards]
        ratings = [card.Course.iloc[0] for card in cards]
        scores = [card.Strokes.sum() for card in cards]
        index = [(scores[i]-ratings[i])*113/slopes[i] for i in range(len(scores))]
        results_df = pd.DataFrame({"Strokes":scores, "Index": index})
        cutoff = list(results_df.sort_values("Index").iloc[:n_lowest,:].index)
        results_df["included"] = [x in cutoff for x in results_df.index]
        hcp = results_df.Index[results_df.included == True].mean()+adjustment
        colours = ["green" if x else "blue" for x in results_df.included]
        
        fig1 = px.bar(results_df, x=results_df.index, y="Strokes", text = "Strokes", color = colours, color_discrete_map = "identity")
        fig1.update_xaxes(title_text = "", showticklabels = False)
        fig1.update_yaxes(title_text = "Strokes", range = [0, results_df.Strokes.max()+10])
        fig2 = px.bar(results_df, x=results_df.index, y="Index", text = results_df.Index.apply(lambda x: f"{x:.2f}"), color = colours, color_discrete_map = "identity")
        fig2.update_xaxes(title_text = "", showticklabels = False)
        fig2.update_yaxes(title_text = "Handicap Index", range = [0, results_df.Index.max()+5])        
        return [html.H3(f"Handicap: {hcp:.1f}"), html.Center(dcc.Graph(figure = fig1, style={'width': '80vw'}))],\
                [html.Center(dcc.Graph(figure = fig2, style={'width': '80vw'}))]      
    else:
        return "Not enough scores recorded", []


@app.callback(
    [Output(component_id = "n_rounds", component_property = "options"),
     Output(component_id = "recent_rounds_data", component_property = "children")],
    Input(component_id = "round-stats-reset", component_property = "n_clicks")
    )
def recent_rounds_options(button):
        all_cards = sorted(glob.glob("Recorded/*/*/*"), key = lambda x: datetime.datetime.strptime(x.split("\\")[-1].split(".")[0], "%d%m%Y").date(), reverse = True)
        paths_dict = dict(enumerate(all_cards))
        options = [{"label": i+1, "value": i+1} for i in range(len(all_cards))]
        return options, json.dumps(all_cards)

 

@app.callback(
    Output(component_id = "scores_2", component_property = "children"),
    Input(component_id = "n_rounds", component_property = "value"),
    State(component_id = "recent_rounds_data", component_property = "children")
    )
def load_scores2(num, paths):
    print("new load scores runs")
    if paths != None:
        paths_dict = json.loads(paths)
        chosen_paths = [paths_dict[i] for i in range(num)] 
        scores = [pd.read_csv(file, usecols = ["Hole","Par","Index","Yardage","Strokes","Putts","Tee Shot"]) for file in chosen_paths]
        chosen_paths = ["/".join([path[-12:-10],path[-10:-8],path[-8:-4]]) for path in chosen_paths]
        if scores != []:
            for date, j in zip(chosen_paths, range(len(scores))):
                scores[j]["Round Index"] = date
        if scores != []:
            scores = pd.concat(scores)      
        return json.dumps({"data":scores.to_json(orient = "split")})
    else:
        return []



@app.callback(
    Output(component_id = "driving_accuracy_bar2", component_property = "children"),
    Input(component_id = "scores_2", component_property = "children")
    )
def driving_accuracy_bar_plot2(data):
    if data != []:
        cards = pd.read_json(json.loads(data)["data"], orient = "split")
        cards = cards[cards["Par"] != 3].groupby(["Round Index","Tee Shot"]).size().reset_index(name = "%")
        labels = dict(zip(["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"], [0,1,2,3,4]))
        new_cards = []
        for i in sorted(cards["Round Index"].unique(), key = lambda x: 400*int(x.split("/")[2])+31*int(x.split("/")[1])+int(x.split("/")[0])):
            df = cards[cards["Round Index"] == i]
            for label in labels.keys():
                if label not in df["Tee Shot"].values:
                    df = df.append({"Round Index":i, "Tee Shot": label, "%": 0}, ignore_index=True)
            df = df.sort_values("Tee Shot", key = lambda x: x.apply(lambda y: labels[y]))
            new_cards.append(df)
        cards = pd.concat(new_cards)
        cards["%"] = cards.groupby("Round Index")["%"].transform(lambda df: df.divide(df.sum()).multiply(100)).values
        cards["str"] = cards["%"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(cards, x="Tee Shot", y="%", text = "str",
                 color="Round Index", barmode="group")
        fig.update_yaxes(range=[0,100], title_text = "Proportion (%)")
        fig.update_xaxes(title_text = "")
        return [html.H3("Driving Accuracy"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []


@app.callback(
    Output(component_id = "par3_accuracy_bar2", component_property = "children"),
    Input(component_id = "scores_2", component_property = "children")
    )
def par3_accuracy_bar_plot2(data):
    if data != []:
        cards = pd.read_json(json.loads(data)["data"], orient = "split")
        cards = cards[cards["Par"] == 3].groupby(["Round Index","Tee Shot"]).size().reset_index(name = "%")
        labels = dict(zip(["Wide Left", "Narrow Left", "Straight", "Narrow Right", "Wide Right"], [0,1,2,3,4]))
        new_cards = []
        for i in sorted(cards["Round Index"].unique(), key = lambda x: 400*int(x.split("/")[2])+31*int(x.split("/")[1])+int(x.split("/")[0])):
            df = cards[cards["Round Index"] == i]
            for label in labels.keys():
                if label not in df["Tee Shot"].values:
                    df = df.append({"Round Index":i, "Tee Shot": label, "%": 0}, ignore_index=True)
            df = df.sort_values("Tee Shot", key = lambda x: x.apply(lambda y: labels[y]))
            new_cards.append(df)
        cards = pd.concat(new_cards)
        cards["%"] = cards.groupby("Round Index")["%"].transform(lambda df: df.divide(df.sum()).multiply(100)).values
        cards["str"] = cards["%"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(cards, x="Tee Shot", y="%", text = "str",
                 color="Round Index", barmode="group")
        fig.update_yaxes(range=[0,100], title_text = "Proportion (%)")
        fig.update_xaxes(title_text = "")
        return [html.H3("Par 3 Accuracy"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []



par_sort_dict = {"Overall":0, "3":0.1, "4":0.2, "5":0.3}

def test_sort(x):
    print(x)
    return 1


@app.callback(
    Output(component_id = "gir_bar2", component_property = "children"),
    Input(component_id = "scores_2", component_property = "children")
    )
def gir_plot2(data):
    print("gir_plot2 runs")
    if data != []:
        cards = pd.read_json(json.loads(data)["data"], orient = "split")
        cards["GIR"] = cards["Par"]-(cards["Strokes"]-cards["Putts"]) >= 2 
        GIR_by_round = cards[["Round Index", "GIR"]].groupby("Round Index").apply(lambda x: 100*x.sum()/len(x)).reset_index(drop = False) 
        GIR_by_round["Par"] = "Overall"   
        cards = cards[["Par", "Round Index", "GIR"]].groupby(["Round Index","Par"]).apply(lambda x: 100*x.sum()/len(x)).reset_index(drop = False)
        cards["Par"] = cards["Par"].apply(lambda x: f"Par {x:.0f}")
        cards = pd.concat([GIR_by_round, cards]).sort_values(["Round Index", "Par"], key = lambda x: x.apply(lambda y: par_sort_dict[y] if y in par_sort_dict.keys() else f"{y[-4:]}/{y[3:5]}/{y[0:2]}"))#lambda x: 400*int(x[0].split("/")[2])+31*int(x[0].split("/")[1])+int(x[0].split("/")[0])+par_sort_dict[x[1]])
        cards["str"] = cards["GIR"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(cards, x="Par", y="GIR", color = "Round Index", barmode = "group", text = "str")
        fig.update_yaxes(range=[0,100], title_text = "GIR Proportion (%)")
        fig.update_xaxes(title_text = "")
        return [html.H3("Greens in Regulation"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
    else:
        return []

# @app.callback(
#     Output(component_id = "gir_bar2", component_property = "children"),
#     Input(component_id = "scores_2", component_property = "children")
#     )
# def gir_plot(data):
#     if data != []:
#         cards = pd.read_json(json.loads(data)["data"], orient = "split")[["Par", "Strokes", "Putts"]]
#         cards["GIR"] = cards["Par"]-(cards["Strokes"]-cards["Putts"]) >= 2 
#         GIR = 100*cards["GIR"].sum()/len(cards)
#         cards = cards[["Par", "GIR"]].groupby("Par").sum().divide(cards[["Par", "GIR"]].groupby("Par").size(), axis = 0).multiply(100).reset_index(drop = False)
#         cards["Par"] = cards["Par"].apply(lambda x: f"Par {x:.0f}")
#         cards = cards.append({"Par": "Overall", "GIR": GIR}, ignore_index = True).sort_values("Par")
#         cards["str"] = cards["GIR"].apply(lambda x: f"{x:.0f}%")
#         fig = px.bar(cards, x="Par", y="GIR", text = "str")
#         fig.update_yaxes(range=[0,100], title_text = "GIR Proportion (%)")
#         fig.update_xaxes(title_text = "")
#         return [html.H3("Greens in Regulation"), html.Center(dcc.Graph(figure = fig, style={'width': '80vw'}))]
#     else:
#         return []



if __name__ == "__main__":
    app.run_server()



