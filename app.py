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


@app.route('/character_vs_character')
def character_vs_character():
    char1 = request.args.get('char1')
    char2 = request.args.get('char2')

    if char1 and char2:
        if char1 == char2:
            # Find fights where this character is present on either side
            fights = df[(df['Character 1'] == char1) | (df['Character 2'] == char1)]

            if fights.empty:
                return jsonify({
                    'summary': f"No matches found for {char1}.",
                    'table': ''
                })

            # Prepare results
            results = []
            for _, fight in fights.iterrows():
                results.append({
                    'Fight ID': fight['Fight ID'],
                    f'{char1} Player 1': fight['Player 1'],
                    f'{char1} Player 2': fight['Player 2'],
                    'Winner': fight['Winner'],
                    'Tournament': fight['Tournament No.'],
                    'Round': fight['Round No.']
                })

            total_fights = len(results)

            # Convert results to HTML
            results_df = pd.DataFrame(results)
            table_html = results_df.to_html(classes='table table-striped', index=False)

            summary_html = f"<p>Total {char1} vs {char1} matches: {total_fights}</p>"

            return jsonify({'summary': summary_html, 'table': table_html})

        else:
            # Find fights where both characters are present
            fights = df[((df['Character 1'] == char1) & (df['Character 2'] == char2)) |
                        ((df['Character 1'] == char2) & (df['Character 2'] == char1))]

            if fights.empty:
                return jsonify({
                    'summary': f"No matches found between {char1} and {char2}.",
                    'table': ''
                })

            # Prepare results
            results = []
            char1_wins = 0
            total_fights = 0
            for _, fight in fights.iterrows():
                total_fights += 1
                if (fight['Character 1'] == char1 and fight['Winner'] == fight['Player 1']) or \
                        (fight['Character 2'] == char1 and fight['Winner'] == fight['Player 2']):
                    char1_wins += 1

                results.append({
                    'Fight ID': fight['Fight ID'],
                    f'{char1} Player': fight['Player 1'] if fight['Character 1'] == char1 else fight['Player 2'],
                    f'{char2} Player': fight['Player 2'] if fight['Character 1'] == char1 else fight['Player 1'],
                    'Winner': fight['Winner'],
                    'Tournament': fight['Tournament No.'],
                    'Round': fight['Round No.']
                })

            # Calculate win percentages
            char1_win_percent = (char1_wins / total_fights) * 100
            char2_win_percent = 100 - char1_win_percent

            # Convert results to HTML
            results_df = pd.DataFrame(results)
            table_html = results_df.to_html(classes='table table-striped', index=False)

            summary_html = f"<p>{char1} has won this matchup {char1_win_percent:.1f}% of the time</p>"
            summary_html += f"<p>{char2} has won this matchup {char2_win_percent:.1f}% of the time</p>"
            summary_html += f"<p>Total matches: {total_fights}</p>"

            return jsonify({'summary': summary_html, 'table': table_html})

    return jsonify({
        'summary': 'Please select two characters.',
        'table': ''
    })


if __name__ == '__main__':
    app.run(port=8000, debug=True)
