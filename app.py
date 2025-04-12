from flask import Flask, render_template, request, redirect, url_for
import pyodbc
import joblib
import pandas as pd
import dateparser
from datetime import datetime

app = Flask(__name__)

# Chargement des modèles
model_path = "fake_news.pkl"
vectorizer_path = "vectorize.pkl"

model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

# Configuration de la connexion SQL Server
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=sqlserver;'  # Remplacez par votre nom de serveur
        'DATABASE=seneweb;'
        'UID=sa;'
        'PWD=Touba2021!;'

    )
    return conn

def get_latest_articles():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
            SELECT TOP 6 
                [id], [category], [title], [link], [meta], [date]
            FROM [seneweb].[dbo].[Articles]
            ORDER BY [date] DESC
            """
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            for article in articles:
                article['prediction'] = predict_truthfulness(article['title'])
            
            return articles
    except Exception as e:
        print(f"Erreur lors de la récupération des articles: {e}")
        return []

def convert_relative_dates(date_string):
    # Utiliser dateparser pour convertir la date relative en une date absolue
    date = dateparser.parse(date_string)
    return date if date else None

def fetch_articles_from_csv():
    df = pd.read_csv('donnee/SenePlus.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        content = row['rightstoryteaser_acontainsclass_blacklink']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "SenePlus",
                "title": title,
                "link": row['like_lien'],
                "meta": "Source: SenePlus",
                "content": content if content else "Contenu non disponible"
            })

    return articles 

def fetch_articles_from_csv_seneco():
    df = pd.read_csv('donnee/seneco.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        postdate = row['postdate']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "Seneco",
                "title": title,
                "link": row['Lien_du_titre'],
                "meta": f"Source: seneco | Publié le {postdate}",
                "postdate": postdate
            })

    return articles

def fetch_articles_from_csv_senewebs():
    df = pd.read_csv('donnee/seneweb.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        date = row['date']  # Cette date peut être relative
        converted_date = convert_relative_dates(date)  # Convertir la date pour le tri

        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "Seneweb",
                "title": title,
                "link": row['meta_item_lien'],
                "meta": f"Source: Seneweb | Publié le {date}",
                "date": date,  # Garder la date d'origine
                "converted_date": converted_date  # Garder la date convertie pour le tri
            })

    # Trier les articles par date convertie (du plus récent au plus ancien)
    articles.sort(key=lambda x: x['converted_date'], reverse=True)
    
    # Retirer la clé 'converted_date' car elle n'est pas nécessaire pour l'affichage
    for article in articles:
        del article['converted_date']

    return articles

def fetch_articles_from_csv_walfadjri():
    df = pd.read_csv('donnee/walfadjri.csv')
    df = df.fillna("")
    articles = []
    seen_titles = set()

    for _, row in df.iterrows():
        title = row['Titre']
        jeg_meta_date = row['jeg_meta_date']
        content = row['champ']
        if title and title not in seen_titles:
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "Walfadjri",
                "title": title,
                "link": row['Lien_du_titre'],
                "meta": f"Source: Walfadjri | Publié le {jeg_meta_date}",
                "jeg_meta_date": jeg_meta_date,
                "content": content if content else "Contenu non disponible"
            })

    return articles

def predict_truthfulness(title):
    title_vectorized = vectorizer.transform([title])
    prediction = model.predict(title_vectorized)
    return "Vrai" if prediction[0] == 1 else "Faux"

@app.route("/")
def index():
    latest_articles = get_latest_articles()
    return render_template("index.html", latest_articles=latest_articles)

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