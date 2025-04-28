import pandas as pd 
import numpy as np 
import streamlit as st 
import seaborn as sns 
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from sklearn.metrics import r2_score
from streamlit_option_menu import option_menu
import mysql.connector
from function import *
import os
from streamlit_dynamic_filters import DynamicFilters
import altair as alt
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title='Marsa Maroc', page_icon='photo/marsamaroc.jpg')



if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "reset_token" not in st.session_state:
    st.session_state.reset_token = None

if "token_expiration_time" not in st.session_state:
    st.session_state.token_expiration_time = None

reset_token = query_params.get("token", [None])[0]
if reset_token:
    st.session_state.reset_token = reset_token


if st.session_state.logged_in:
    st.sidebar.image("photo/logo_Marsa.png")

    with st.sidebar:
        selected = option_menu("Main Menu", ["Accueil", "Données", "Visualisation", "Prévision"], 
            icons=["house", "journal-album", "clipboard-data", "graph-down"], menu_icon="cast", default_index=1)
        selected

        set_page_url(selected.lower())

        if st.button("Se déconnecter"):
            logout()

    if selected == "Accueil" or current_page == "Accueil":

        st.image("photo/acc1.jpg")
        st.write("""
        **Analyse des données et Prédiction du Budget de Marsa Maroc**

        L'application "Analyse des données et Prédiction du Budget de Marsa Maroc" offre une plateforme interactive pour l'exploration des données financières passées de Marsa Maroc ainsi que la prédiction du budget futur. En tant que l'un des principaux acteurs dans le domaine portuaire au Maroc, Marsa Maroc gère une vaste gamme d'activités, ce qui rend la gestion budgétaire cruciale pour son succès opérationnel.

        **Fonctionnalités :**

        1. **Exploration des Données :** Les utilisateurs peuvent explorer les données historiques financières de Marsa Maroc, y compris les revenus, les dépenses, les bénéfices et d'autres indicateurs pertinents. Des tableaux de bord interactifs, des graphiques et des visualisations permettent une analyse approfondie de ces données.

        2. **Analyse des Tendances :** L'application fournit des outils d'analyse des tendances pour identifier les schémas et les fluctuations dans les finances de Marsa Maroc. Les utilisateurs peuvent examiner les variations saisonnières, les tendances à long terme et les facteurs externes influençant les finances de l'entreprise.

        3. **Prévision du Budget :** En utilisant des modèles de prévision avancés basés sur des techniques d'apprentissage automatique, l'application est capable de prédire le budget futur de Marsa Maroc. Les utilisateurs peuvent ajuster les paramètres et les hypothèses pour obtenir des prévisions personnalisées et fiables.

        4. **Optimisation des Ressources :** En comprenant les tendances passées et en utilisant les prévisions futures, l'application aide Marsa Maroc à optimiser l'allocation des ressources et à prendre des décisions éclairées en matière de planification budgétaire. Cela permet à l'entreprise de mieux gérer les risques et d'atteindre ses objectifs financiers.

        5. **Interface Conviviale :** L'interface utilisateur est intuitive et conviviale, ce qui permet aux utilisateurs de naviguer facilement à travers les fonctionnalités de l'application. Des options de personnalisation sont également disponibles pour répondre aux besoins spécifiques des utilisateurs.

        En combinant l'analyse des données et la prédiction du budget, cette application fournit à Marsa Maroc les outils nécessaires pour prendre des décisions stratégiques informées et maintenir sa position de leader dans le secteur portuaire au Maroc.
        """)



    elif selected == "Données" or current_page == "Données":
        st.title('Importation des données')

        data_trafic = st.file_uploader("Uploader un fichier", type={"csv", "xlsx", "txt"})
        if data_trafic is not None:
            spectra_df = pd.read_csv(data_trafic)
            spectra_df.dropna(inplace=True)
            insert_data(spectra_df)
        
        st.write("Exemple de jeu de données, contenant les champs suivants")
        st.image("photo/table_trafic.png")
        afficher, vider = st.columns(2)

        if afficher.button('Afficher les données existantes'):
            trafic_port = all_data()
            st.write(trafic_port)

        if vider.button('Vider la base de données'):
            delete_data()

            


    elif selected == "Visualisation" or current_page == "Visualisation":
        st.title("Visualisation des données")

        trafic_port = all_data()

        type_marchandise = st.multiselect(
            label="Sélectionnez le type de marchandise",
            options=["TRAFIC CONTENEURISE", "VRAC SOLIDE", "HYDROCARBURES", "TRAFIC CONTENEURS"],
            default=["TRAFIC CONTENEURISE", "VRAC SOLIDE", "HYDROCARBURES", "TRAFIC CONTENEURS"]
        )

        annee = st.multiselect(
            label="Sélectionnez l'année",
            options=["2021", "2022", "2023"],
            default=["2021", "2022", "2023"]
        )

        mois = st.multiselect(
            label="Sélectionnez le mois",
            options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
            default=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        )

        trafic_port["Date"] = pd.to_datetime(trafic_port["Date"])

        filtered_data = trafic_port[trafic_port["Type_Marchandise"].isin(type_marchandise) & trafic_port["Date"].dt.year.isin([int(a) for a in annee]) & trafic_port["Date"].dt.month.isin([int(a) for a in mois])]

        st.write(filtered_data)

        custom_colors = px.colors.qualitative.Plotly
        theme_plotly = None

        fig = px.bar(filtered_data, y="Volume", x="Type_Marchandise", color="Type_Marchandise", title="Volume de marchandises par type en tonnes", color_discrete_sequence=custom_colors)
        fig.update_traces(textfont_size=18, textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

        fig = px.pie(filtered_data, values="Volume", names="Type_Marchandise", title="Répartition du volume de marchandises par type", color_discrete_sequence=custom_colors)
        fig.update_layout(legend_title="Type_Marchandise", legend_y=0.9)
        fig.update_traces(textinfo="percent+label", textposition="inside")
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

        fig = px.bar(filtered_data, y="Volume", x="Nom_Marchandise", color="Nom_Marchandise", title="Volume de marchandises par type en tonnes", color_discrete_sequence=custom_colors)
        fig.update_traces(textfont_size=18, textangle=20, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

        fig = px.pie(filtered_data, values="Volume", names="Nom_Marchandise", title="Répartition du volume de marchandises par type", color_discrete_sequence=custom_colors)
        fig.update_layout(legend_title="Type_Marchandise", legend_y=0.9)
        fig.update_traces(textinfo="percent+label", textposition="inside")
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)


        filtered_data['Années'] = pd.to_datetime(filtered_data['Date']).dt.year
        unique_years = filtered_data['Années'].unique()
        unique_years.sort()
        fig = px.bar(filtered_data, x='Volume', y='Années', color='Type_Marchandise', orientation='h', title="Volume de marchandises en tonnes Annuelle", color_discrete_sequence=custom_colors)
        fig.update_yaxes(tickvals=unique_years, ticktext=unique_years)
        st.plotly_chart(fig, use_container_width=True)


        filtered_data['Mois'] = pd.to_datetime(filtered_data['Date']).dt.month
        unique_years = filtered_data['Mois'].unique()
        unique_years.sort()
        fig = px.bar(filtered_data, x='Volume', y='Mois', color='Type_Marchandise', orientation='h', title="Volume de marchandises en tonnes Mensuelle", color_discrete_sequence=custom_colors)
        fig.update_yaxes(tickvals=unique_years, ticktext=unique_years)
        st.plotly_chart(fig, use_container_width=True)
    


    elif selected == "Prévision" or current_page == "Prévision":

        st.title("Prévision des données")
        selectionne_type, prevision, performance = st.tabs(
            [
                "Sélectionner le type de marchandise", 
                "Prévision",  
                "Performances du modèle"

            ]
        )

        with selectionne_type:
            trafic_port = all_data()

            type_marchandise = st.multiselect(
                label="Sélectionnez le type de marchandise",
                options=["TRAFIC CONTENEURISE", "VRAC SOLIDE", "HYDROCARBURES", "TRAFIC CONTENEURS"],
                default=["TRAFIC CONTENEURISE", "VRAC SOLIDE", "HYDROCARBURES", "TRAFIC CONTENEURS"]
            )

            trafic_port["Date"] = pd.to_datetime(trafic_port["Date"])

            filtered_data = trafic_port[trafic_port["Type_Marchandise"].isin(type_marchandise)]

            st.write(filtered_data)


        with prevision:
            filtered_data['Mois'] = pd.to_datetime(filtered_data['Date']).dt.month
            label_encoders = {}
            categorical_columns = ['Nom_Marchandise', 'Type_Marchandise']
            for col in categorical_columns:
                label_encoders[col] = LabelEncoder()
                filtered_data[col] = label_encoders[col].fit_transform(filtered_data[col])

            X = filtered_data[['Nom_Marchandise', 'Mois', 'Type_Marchandise']]
            y = filtered_data['Volume']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            linear_regression_model = LinearRegression()
            decision_tree_model = DecisionTreeRegressor()
            random_forest_model = RandomForestRegressor()

            linear_regression_model.fit(X_train, y_train)
            decision_tree_model.fit(X_train, y_train)
            random_forest_model.fit(X_train, y_train)

            if filtered_data is not None:
                filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])

                data_next_years = []

                current_year = datetime.datetime.now().year
                next_year = current_year 

                for month in range(1, 13):
                    date = datetime.datetime(next_year, month, 1) + relativedelta(months=1) - relativedelta(days=1)
                    volume_predicted_lr = linear_regression_model.predict([[0, month, 0]])[0]
                    volume_predicted_dt = decision_tree_model.predict([[0, month, 0]])[0]
                    volume_predicted_rf = random_forest_model.predict([[0, month, 0]])[0]
                    volume_predicted_avg = (volume_predicted_lr + volume_predicted_dt + volume_predicted_rf) / 3
                    data_next_years.append({'Date': date, 'Type de marchandise': type_marchandise, 'Volume_Predicted': volume_predicted_avg})

                data_next_years = pd.DataFrame(data_next_years)
                st.write(data_next_years)

                if st.button('Télécharger'):
                    filename = "data_trafic_next_year.xlsx"
                    data_next_years.to_excel(filename, index=False)
                    st.success(f'Le fichier {filename} a été téléchargé avec succès.')

                fig = px.line()
                fig.add_scatter(x=filtered_data['Date'], y=filtered_data['Volume'], mode='lines', name='Données Anciennes')
                fig.add_scatter(x=data_next_years['Date'], y=data_next_years['Volume_Predicted'], mode='lines', name='Données Prévisions')
                fig.update_layout(title='Volume de marchandise en tonne réel vs Prévisions : ' + str(type_marchandise))
                st.plotly_chart(fig)
            else:
                st.write("Aucune donnée ancienne disponible")


        with performance:
            volume_predicted_lr = linear_regression_model.predict(X_test)
            volume_predicted_dt = decision_tree_model.predict(X_test)
            volume_predicted_rf = random_forest_model.predict(X_test)

            mse_linear_regression_model = mean_squared_error(y_test, volume_predicted_lr)
            mse_decision_tree_model = mean_squared_error(y_test, volume_predicted_dt)
            mse_random_forest_model = mean_squared_error(y_test, volume_predicted_rf)

            mae_linear_regression_model = mean_absolute_error(y_test, volume_predicted_lr)
            mae_decision_tree_model = mean_absolute_error(y_test, volume_predicted_dt)
            mae_random_forest_model = mean_absolute_error(y_test, volume_predicted_rf)

            data_performance = pd.DataFrame({
                'Modèle': ['Linear Regression', 'Decision Tree', 'Random Forest'],
                'MSE': [mse_linear_regression_model, mse_decision_tree_model, mse_random_forest_model],
                'MAE': [mae_linear_regression_model, mae_decision_tree_model, mae_random_forest_model]
            })

            fig = px.bar(data_performance, x='Modèle', y=['MSE', 'MAE'], barmode='group',
                        labels={'value': 'Performance', 'variable': 'Type d\'erreur'},
                        color_discrete_sequence=['#636EFA', '#EF553B'])

            fig.update_layout(title='Performance des modèles',
                            xaxis={'title': 'Modèle'},
                            yaxis={'title': 'Performance'},
                            legend={'title': 'Type d\'erreur'})
            st.plotly_chart(fig)

 
else:
    if reset_token and validate_token(reset_token):
        change_password_form()

    elif current_page == "login":
        set_page_url("login")
        login()

