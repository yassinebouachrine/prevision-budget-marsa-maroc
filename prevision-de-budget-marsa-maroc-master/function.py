import streamlit as st
import mysql.connector
import subprocess
import pandas as pd 
from PIL import Image
import io
import hashlib
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import uuid


query_params = st.query_params
current_page = query_params.get("page", ["login"])[0]

if not current_page:
    current_page = 'login'


def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="prediction_db"
        )
        if conn.is_connected():
            return conn
    except mysql.connector.Error as e:
        st.error(f"Erreur lors de la connexion à la base de données MySQL : {e}")
        return None


def resize_image(image, target_width):
    aspect_ratio = image.height / image.width
    new_height = round(target_width * aspect_ratio)
    resized_img = image.resize((target_width, new_height))
    return resized_img

def move_image_right(image, pixels_to_move):
    width, height = image.size
    moved_img = image.crop((pixels_to_move, 0, width, height))
    return moved_img


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'prediction_db'
}

def all_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute("SELECT Date, Nom_Marchandise, Volume, Type_Marchandise FROM trafic_port")
        existing_data = cursor.fetchall()
        df = pd.DataFrame(existing_data, columns=[i[0] for i in cursor.description])
        cursor.close()
        connection.close()

        return df
    except mysql.connector.Error as error:
        return f"Erreur lors de la récupération des données depuis la base de données : {error}"



def insert_data(spectra_df):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        for index, row in spectra_df.iterrows():
            sql = "INSERT INTO trafic_port VALUES (%s, %s, %s, %s)"
            values = tuple(row)  
            cursor.execute(sql, values)
            
        connection.commit()
        st.success("Données enregistrées dans la base de données avec succès.")

    except mysql.connector.Error as error:
        connection.rollback()  
        st.error(f"Erreur lors de l'enregistrement des données dans la base de données : {error}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


def delete_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        sql = "DELETE FROM trafic_port"
        cursor.execute(sql)
            
        connection.commit()
        st.success("Données supprimer dans la base de données avec succès.")

    except mysql.connector.Error as error:
        connection.rollback()  
        st.error(f"Erreur lors de la suppression des données dans la base de données : {error}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="prediction_db"
)

def execute_query(query):
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    return pd.DataFrame(result, columns=columns)


def end_of_month(date):
    next_month = date.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def hash_password(password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password


def authenticate_user(conn, username, password):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = %s", (username,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            hashed_password = result[0]
            if hashed_password == hash_password(password):
                print(f"L'utilisateur {username} a été authentifié avec succès.")
                return True
            else:
                print(f"Échec de l'authentification pour l'utilisateur {username}. Mot de passe incorrect.")
                return False
        else:
            print(f"Échec de l'authentification pour l'utilisateur {username}. Nom d'utilisateur inconnu.")
            return False
    except Exception as e:
        st.error(f"Une erreur s'est produite lors de l'authentification de l'utilisateur : {e}")
        return None


reset_email = None

def get_reset_email():
    global reset_email
    return reset_email

def change_password(email, new_password):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    
    hashed_password = hash_password(new_password)
    
    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
    conn.commit()
    cursor.close()
    conn.close()

def change_password_form():
    st.title("Changer le mot de passe")
    new_password = st.text_input("Nouveau mot de passe", type="password")
    confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
    reset_email = get_reset_email()

    if st.button("Changer le mot de passe"):
        if new_password == confirm_password:
            reset_token = st.session_state.get("reset_token")
            if reset_email and reset_token and validate_token(reset_token):
                change_password(reset_email, new_password)
                st.success("Votre mot de passe a été changé avec succès. Vous pouvez maintenant vous connecter.")
            else:
                st.error("Aucune adresse e-mail ou token de réinitialisation valide trouvé dans la session.")
        else:
            st.error("Les mots de passe ne correspondent pas. Veuillez réessayer.")


def generate_reset_link(email):
    reset_token = str(uuid.uuid4())
    reset_link = f"http://localhost:8501/?page=change_password&token={reset_token}"  
    return reset_link


os.environ["SENDER_EMAIL"] = "yassinebouachrine71@gmail.com"
os.environ["SENDER_PASSWORD"] = "wpgn uiso vcap okbz"

def send_password_reset_email(recipient_email):
    global reset_email
    reset_email = recipient_email
    
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    subject = "Réinitialisation de votre mot de passe"
    body = """
    Bonjour,

    Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :

    [Lien de réinitialisation]

    Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

    Merci,
    L'équipe MARSA MAROC
    """

    if not recipient_email:
        print("Erreur: l'adresse email du destinataire est vide.")
        return False

    reset_link = generate_reset_link(recipient_email)
    body = body.replace("[Lien de réinitialisation]", reset_link)

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False
    




def login():
    image_path = "photo/logo_Marsa.png"
    target_width = 300
    pixels_to_move = -100
    img = Image.open(image_path)
    moved_image = move_image_right(img, pixels_to_move)
    resized_image = resize_image(moved_image, target_width)
    with io.BytesIO() as output:
        resized_image.save(output, format="PNG")
        image_data = output.getvalue()
    st.image(image_data, caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto")

    with st.form("Connexion"):
        st.title("Connexion")
        username_login = st.text_input("Nom d'utilisateur (connexion)")
        password_login = st.text_input("Mot de passe (connexion)", type="password")
        submit_button = st.form_submit_button("Se connecter")
        
        if submit_button:
            conn = connect_to_mysql()
            if authenticate_user(conn, username_login, password_login):
                st.session_state.logged_in = True
                st.success("Connexion réussie ! Vous êtes maintenant connecté.")
            else:
                st.error("Échec de la connexion. Veuillez vérifier vos informations d'identification.")
    
    forgot_password = st.checkbox("Mot de passe oublié")
    if forgot_password:
        with st.form("forgot_password_form"):
            email = st.text_input("Entrez votre adresse e-mail pour réinitialiser votre mot de passe")
            submitted = st.form_submit_button("Envoyer")

            if submitted:
                if email:
                    if send_password_reset_email(email):
                        st.success("Email de réinitialisation envoyé avec succès.")
                    else:
                        st.error("Erreur lors de l'envoi de l'email de réinitialisation.")
                else:
                    st.warning("Veuillez entrer votre adresse e-mail.")

 

def logout():
    st.session_state.logged_in = False
    st.session_state.reset_token = None
    st.session_state.token_expiration_time = None
    


def set_page_url(page):
    st.query_params.update(page=page)




import datetime

def validate_token(token):
    expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
    st.session_state.token_expiration_time = expiration_time.timestamp()

    current_time = datetime.datetime.now().timestamp()
    if current_time < st.session_state.token_expiration_time:
        return True
    else:
        return False

