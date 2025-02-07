from flask import Flask, render_template,request
import pyodbc
import joblib
import pandas as pd

app = Flask(__name__)

model_path = "fake_news.pkl"
vectorizer_path = "vectorize.pkl"

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

def get_db_connection():
    return pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=DESKTOP-0RNC19U;'
                          'DATABASE=seneweb;'
                          'Trusted_Connection=yes;')

def fetch_articles_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""SELECT id, category, title, link, meta FROM Articles ORDER BY id DESC""")
        rows = cursor.fetchall()
        articles = []
        seen_titles = set()

        for row in rows:
            title = row[2]
            if title not in seen_titles:
                seen_titles.add(title)
                articles.append({
                    "id": row[0],
                    "category": row[1],
                    "title": title,
                    "link": row[3],
                    "meta": row[4]
                })
        return articles
    finally:
        cursor.close()
        conn.close()



def fetch_articles_from_csv():
    df = pd.read_csv('SenePlus.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "SenePlus",
                "title": title,
                "link": row['like_lien'],
                "meta": "Source: SenePlus"
            })

    return articles


def fetch_articles_from_csv_seneco():
    df = pd.read_csv('seneco.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "Seneco",
                "title": title,
                "link": row['Lien_du_titre'],
                "meta": "Source: seneco"
            })

    return articles


def fetch_articles_from_csv_senewebs():
    df = pd.read_csv('senewebs.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "Seneweb",
                "title": title,
                "link": row['Lien_du_titre'],
                "meta": "Source: seneweb"
            })

    return articles



def fetch_articles_from_csv_walfadjri():
    df = pd.read_csv('walfadjri.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "Walfadjri",
                "title": title,
                "link": row['Lien_du_titre'],
                "meta": "Source: Walfadjri"
            })

    return articles



def predict_truthfulness(title):
    title_vectorized = vectorizer.transform([title])
    prediction = model.predict(title_vectorized)
    return "Vrai" if prediction[0] == 1 else "Faux"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/seneweb")
def seneweb_articles():
    db_articles = fetch_articles_from_csv_senewebs()
    for article in db_articles:
        article["prediction"] = predict_truthfulness(article["title"])
    return render_template("articles.html", articles=db_articles, source="Seneweb")

@app.route("/senplus")
def senplus_articles():
    csv_articles = fetch_articles_from_csv()
    for article in csv_articles:
        article["prediction"] = predict_truthfulness(article["title"])
    return render_template("articles.html", articles=csv_articles, source="Senplus")

@app.route("/seneco")
def seneco_articles():
    csv_articles = fetch_articles_from_csv_seneco()
    for article in csv_articles:
        article["prediction"] = predict_truthfulness(article["title"])
    return render_template("articles.html", articles=csv_articles, source="Seneco")


@app.route("/walfadjri")
def walfadjri_articles():
    csv_articles = fetch_articles_from_csv_walfadjri()
    for article in csv_articles:
        article["prediction"] = predict_truthfulness(article["title"])
    return render_template("articles.html", articles=csv_articles, source="walfadjri")


@app.route('/predict', methods=['POST'])
def predict():
    title = request.form['title']
    # Appeler le modèle de prédiction ici
    predicted_category = model.predict([title])[0]
    return f"La catégorie prédite est : {predicted_category}"


@app.route("/autres-sources", methods=["GET", "POST"])
def autres_sources():
    if request.method == "POST":
        user_text = request.form.get("user_text")
        if user_text:
            prediction = predict_truthfulness(user_text)
            return render_template("prediction.html", user_text=user_text, prediction=prediction)
        else:
            return render_template("autres_sources.html", error="Veuillez saisir du texte.")
    return render_template("autres_sources.html")

@app.route("/prediction", methods=["POST"])
def prediction():
    user_text = request.form.get("user_text")
    if user_text:
        prediction = predict_truthfulness(user_text)
        return render_template("prediction.html", user_text=user_text, prediction=prediction)
    else:
        return redirect(url_for("autres_sources"))

if __name__ == "__main__":
    app.run(debug=True)



