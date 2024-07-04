from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

df = pd.read_csv(r"CPU_tournament_data_1-11.csv")
df["Fight ID"] = range(1, df.shape[0]+1)
p1 = df[["Fight ID", "Player 1", "Player 1 Slot", "Character 1", "Character 1 Alt", "Winner", "Tournament No.",
         "Round No."]].rename(columns = {"Player 1": "Player", "Player 1 Slot": "Player Slot",
                                         "Character 1": "Character", "Character 1 Alt": "Character Alt"})
p2 = df[["Fight ID", "Player 2", "Player 2 Slot", "Character 2", "Character 2 Alt", "Winner", "Tournament No.",
         "Round No."]].rename(columns = {"Player 2": "Player", "Player 2 Slot": "Player Slot",
                                         "Character 2": "Character", "Character 2 Alt": "Character Alt"})

df = pd.concat([p1, p2], ignore_index=True)


# Create a new column "Winner" with boolean values
df["Winner"] = df.apply(lambda row: row["Player"] == df.loc[row["Fight ID"] - 1, "Winner"], axis = 1)

df = df.sort_values(by="Fight ID").reset_index(drop = True)
df.rename(columns = {"Tournament No.": "Tournament", "Round No.": "Round"}, inplace = True)


@app.route('/')
def index():  # put application's code here
    return render_template('index.html')


@app.route('/get_columns')
def get_columns():
    excluded_columns = ["Player Slot", "Character Alt"]
    columns = [col for col in df.columns if col not in excluded_columns]
    return jsonify(columns)


@app.route('/get_unique_values')
def get_unique_values():
    column = request.args.get("column")
    if column in ['Player', 'Character', 'Tournament', 'Fight ID']:
        unique_values = sorted(df[column].unique().tolist())
        return jsonify(unique_values)
    return jsonify([])


@app.route('/filter')
def filter_data():
    column = request.args.get("column")
    value = request.args.get("value")

    if column and value:
        if column in ["Player", "Character", "Tournament", "Fight ID"]:
            filtered_df = df[df[column].astype(str) == value]
        else:
            filtered_df = df[df[column].astype(str).str.contains(value, case=False)]
    else:
        filtered_df = df

    html = filtered_df.to_html(classes = "table table-striped", index=False)

    return jsonify({'html': html})


if __name__ == '__main__':
    app.run(port=8000, debug=True)
