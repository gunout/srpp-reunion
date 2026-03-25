# dashboard_srpp_avance.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import random
import requests
import json
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import warnings
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import asyncio
import aiohttp
import folium
from streamlit_folium import folium_static
from streamlit_option_menu import option_menu
import plotly.figure_factory as ff
import networkx as nx
from pyproj import Transformer
import geopandas as gpd
from shapely.geometry import Point, Polygon
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="SRPP La Réunion - Intelligence Artificielle & Monitoring Avancé",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Avancé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 1rem;
    }
    
    .neon-border {
        position: relative;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 20px;
        padding: 2px;
    }
    
    .neon-border > div {
        background: white;
        border-radius: 18px;
        padding: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1rem;
        color: white;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .alert-pulse {
        animation: pulse 2s infinite;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        font-weight: bold;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-critical { background: #dc3545; color: white; }
    .status-warning { background: #ffc107; color: #333; }
    .status-normal { background: #28a745; color: white; }
    
    .progress-bar {
        height: 8px;
        background: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transition: width 0.3s ease;
    }
    
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1rem 0;
        color: #2c3e50;
        border-left: 4px solid #667eea;
        padding-left: 1rem;
    }
    
    .glow-text {
        text-shadow: 0 0 10px rgba(102,126,234,0.5);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class StockLevel:
    """Classe pour les niveaux de stock"""
    produit: str
    volume: float
    capacite: float
    seuil_critique: float
    seuil_alerte: float
    
    @property
    def pourcentage(self) -> float:
        return (self.volume / self.capacite) * 100
    
    @property
    def statut(self) -> str:
        if self.pourcentage <= self.seuil_critique:
            return "CRITIQUE"
        elif self.pourcentage <= self.seuil_alerte:
            return "ALERTE"
        return "NORMAL"
    
    @property
    def autonomie_jours(self) -> float:
        consommation_jour = 1000  # À ajuster selon données réelles
        return self.volume / consommation_jour

class SRPPDataSimulator:
    """Simulateur de données réalistes SRPP"""
    
    def __init__(self):
        self.produits = {
            'SP95': {'capacite': 95000, 'seuil_critique': 15, 'seuil_alerte': 25},
            'SP98': {'capacite': 45000, 'seuil_critique': 15, 'seuil_alerte': 25},
            'Gazole': {'capacite': 115000, 'seuil_critique': 12, 'seuil_alerte': 22},
            'Jet A1': {'capacite': 60000, 'seuil_critique': 10, 'seuil_alerte': 20},
            'Fioul': {'capacite': 35000, 'seuil_critique': 20, 'seuil_alerte': 35}
        }
        
        self.stocks_historique = self._init_historique()
        self.conso_historique = self._init_conso()
        self.arrivages_historique = self._init_arrivages()
        
    def _init_historique(self):
        """Initialise l'historique des stocks"""
        dates = pd.date_range('2023-01-01', datetime.now(), freq='D')
        historique = []
        
        for produit, info in self.produits.items():
            volume_base = info['capacite'] * 0.7  # 70% de remplissage initial
            
            for i, date in enumerate(dates):
                # Simulation de variations réalistes
                variation = np.random.normal(0, info['capacite'] * 0.01)
                saisonnalite = 0.05 * np.sin(2 * np.pi * date.dayofyear / 365)
                
                volume = volume_base + variation + (saisonnalite * info['capacite'])
                volume = max(0, min(volume, info['capacite']))
                
                historique.append({
                    'date': date,
                    'produit': produit,
                    'volume': volume,
                    'capacite': info['capacite'],
                    'pourcentage': (volume / info['capacite']) * 100
                })
                
                volume_base = volume  # Pour la continuité
        
        return pd.DataFrame(historique)
    
    def _init_conso(self):
        """Initialise l'historique de consommation"""
        dates = pd.date_range('2023-01-01', datetime.now(), freq='D')
        conso = []
        
        for produit in self.produits.keys():
            conso_base = random.uniform(500, 2000)  # m³/jour
            
            for date in dates:
                # Effet week-end
                is_weekend = date.weekday() >= 5
                weekend_factor = 0.7 if is_weekend else 1.0
                
                # Saisonnalité
                seasonal = 1 + 0.2 * np.sin(2 * np.pi * date.dayofyear / 365)
                
                # Variation aléatoire
                random_var = np.random.normal(1, 0.1)
                
                consommation = conso_base * weekend_factor * seasonal * random_var
                
                conso.append({
                    'date': date,
                    'produit': produit,
                    'consommation': consommation
                })
        
        return pd.DataFrame(conso)
    
    def _init_arrivages(self):
        """Initialise l'historique des arrivages"""
        dates = pd.date_range('2023-01-01', datetime.now(), freq='W')
        arrivages = []
        
        for produit in self.produits.keys():
            for date in dates:
                # Arrivages de navires toutes les 2-3 semaines
                if random.random() < 0.4:
                    volume = random.uniform(
                        self.produits[produit]['capacite'] * 0.3,
                        self.produits[produit]['capacite'] * 0.8
                    )
                    
                    arrivages.append({
                        'date': date,
                        'produit': produit,
                        'volume': volume,
                        'navire': random.choice(['MT Diana', 'MT Sirius', 'MT Vega', 'MT Orion'])
                    })
        
        return pd.DataFrame(arrivages)
    
    def get_stocks_actuels(self) -> Dict:
        """Récupère les stocks actuels"""
        stocks = {}
        
        for produit, info in self.produits.items():
            dernier = self.stocks_historique[
                self.stocks_historique['produit'] == produit
            ].iloc[-1]
            
            stocks[produit] = StockLevel(
                produit=produit,
                volume=dernier['volume'],
                capacite=info['capacite'],
                seuil_critique=info['seuil_critique'],
                seuil_alerte=info['seuil_alerte']
            )
        
        return stocks

class MLPredictor:
    """Modèle de prédiction IA pour les stocks"""
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        
    def train_models(self, historique_df: pd.DataFrame):
        """Entraîne les modèles de prédiction"""
        
        for produit in historique_df['produit'].unique():
            # Préparation des données
            data = historique_df[historique_df['produit'] == produit].copy()
            data['dayofweek'] = data['date'].dt.dayofweek
            data['month'] = data['date'].dt.month
            data['dayofyear'] = data['date'].dt.dayofyear
            
            # Features
            features = ['dayofweek', 'month', 'dayofyear']
            X = data[features].values
            y = data['volume'].values
            
            # Normalisation
            X_scaled = self.scaler.fit_transform(X)
            
            # Modèle Random Forest
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X_scaled, y)
            
            self.models[produit] = model
    
    def predict_stocks(self, produit: str, jours: int = 7) -> np.ndarray:
        """Prédit les stocks pour les prochains jours"""
        
        if produit not in self.models:
            return np.zeros(jours)
        
        predictions = []
        current_date = datetime.now()
        
        for i in range(jours):
            future_date = current_date + timedelta(days=i)
            features = np.array([[
                future_date.weekday(),
                future_date.month,
                future_date.timetuple().tm_yday
            ]])
            
            features_scaled = self.scaler.transform(features)
            pred = self.models[produit].predict(features_scaled)[0]
            predictions.append(pred)
        
        return np.array(predictions)

class AnomalyDetector:
    """Détecteur d'anomalies pour les données SRPP"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        
    def detect_anomalies(self, data: pd.DataFrame) -> pd.DataFrame:
        """Détecte les anomalies dans les données"""
        
        features = ['volume', 'consommation'] if 'consommation' in data.columns else ['volume']
        
        X = data[features].values
        predictions = self.model.fit_predict(X)
        
        data['anomalie'] = predictions == -1
        return data

class APIConnector:
    """Connecteur pour les APIs externes"""
    
    def __init__(self):
        self.base_url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets"
        
    async def get_fuel_prices(self) -> Dict:
        """Récupère les prix des carburants à La Réunion"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/prix-des-carburants-en-france-flux-instantane-v2/records"
                params = {
                    "where": "region='La Réunion'",
                    "limit": 100
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    return self._parse_fuel_prices(data)
        except Exception as e:
            st.warning(f"Erreur API: {e}")
            return self._get_simulated_prices()
    
    def _parse_fuel_prices(self, data: Dict) -> Dict:
        """Parse les données de l'API"""
        prices = {}
        
        for record in data.get('records', []):
            fields = record.get('fields', {})
            carburant = fields.get('carburant')
            prix = fields.get('prix')
            
            if carburant and prix:
                prices[carburant] = prix
        
        return prices
    
    def _get_simulated_prices(self) -> Dict:
        """Retourne des prix simulés en cas d'erreur"""
        return {
            'SP95': 1.54,
            'SP98': 1.62,
            'Gazole': 1.29,
            'E85': 0.85
        }

class AdvancedDashboard:
    """Dashboard avancé SRPP"""
    
    def __init__(self):
        self.simulator = SRPPDataSimulator()
        self.predictor = MLPredictor()
        self.detector = AnomalyDetector()
        self.api = APIConnector()
        
        # Entraînement des modèles
        self.predictor.train_models(self.simulator.stocks_historique)
        
    def display_hero_section(self):
        """Affiche la section hero avec métriques clés"""
        
        col1, col2, col3, col4 = st.columns(4)
        
        stocks_actuels = self.simulator.get_stocks_actuels()
        
        # Calcul des métriques globales
        volume_total = sum(s.volume for s in stocks_actuels.values())
        capacite_total = sum(s.capacite for s in stocks_actuels.values())
        remplissage_total = (volume_total / capacite_total) * 100
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.9;">VOLUME TOTAL STOCKÉ</div>
                <div style="font-size: 2rem; font-weight: bold;">{:.0f} m³</div>
                <div style="font-size: 0.8rem;">Capacité: {:.0f} m³</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {:.1f}%;"></div>
                </div>
            </div>
            """.format(volume_total, capacite_total, remplissage_total), unsafe_allow_html=True)
        
        with col2:
            # Consommation moyenne
            conso_moyenne = self.simulator.conso_historique[
                self.simulator.conso_historique['date'] > (datetime.now() - timedelta(days=30))
            ]['consommation'].mean()
            
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.9;">CONSOMMATION MOYENNE</div>
                <div style="font-size: 2rem; font-weight: bold;">{:.0f} m³/j</div>
                <div style="font-size: 0.8rem;">30 derniers jours</div>
                <div style="margin-top: 0.5rem;">📈 +2.3% vs mois dernier</div>
            </div>
            """.format(conso_moyenne), unsafe_allow_html=True)
        
        with col3:
            # Autonomie estimée
            autonomie = volume_total / conso_moyenne if conso_moyenne > 0 else 0
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.9;">AUTONOMIE ESTIMÉE</div>
                <div style="font-size: 2rem; font-weight: bold;">{:.0f} jours</div>
                <div style="font-size: 0.8rem;">Au rythme actuel</div>
                <div style="margin-top: 0.5rem;">⚡ {:.0f} semaines d'avance</div>
            </div>
            """.format(autonomie, autonomie/7), unsafe_allow_html=True)
        
        with col4:
            # Alertes actives
            alertes_critiques = sum(1 for s in stocks_actuels.values() if s.statut == "CRITIQUE")
            alertes_alerte = sum(1 for s in stocks_actuels.values() if s.statut == "ALERTE")
            
            st.markdown("""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.9;">ALERTES ACTIVES</div>
                <div style="font-size: 2rem; font-weight: bold;">{}</div>
                <div style="font-size: 0.8rem;">{} critiques, {} alertes</div>
                <div style="margin-top: 0.5rem;">🔔 {}</div>
            </div>
            """.format(
                alertes_critiques + alertes_alerte,
                alertes_critiques,
                alertes_alerte,
                "Urgence approvisionnement" if alertes_critiques > 0 else "Situation normale"
            ), unsafe_allow_html=True)
    
    def display_stock_gauges(self):
        """Affiche les jauges de stock par produit"""
        
        st.markdown('<div class="section-title">📊 NIVEAUX DE STOCK EN TEMPS RÉEL</div>', unsafe_allow_html=True)
        
        stocks = self.simulator.get_stocks_actuels()
        
        # Création des jauges avec Plotly
        cols = st.columns(len(stocks))
        
        for idx, (produit, stock) in enumerate(stocks.items()):
            with cols[idx]:
                # Déterminer la couleur selon le statut
                if stock.statut == "CRITIQUE":
                    color = "red"
                    bg_color = "#ffe6e6"
                elif stock.statut == "ALERTE":
                    color = "orange"
                    bg_color = "#fff3e0"
                else:
                    color = "green"
                    bg_color = "#e6ffe6"
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = stock.pourcentage,
                    title = {'text': f"{produit}<br><span style='font-size:0.8rem;'>{stock.volume:.0f} / {stock.capacite:.0f} m³</span>"},
                    delta = {'reference': stock.seuil_alerte, 'increasing': {'color': "red"}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 1},
                        'bar': {'color': color},
                        'bgcolor': bg_color,
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, stock.seuil_critique], 'color': '#ffcccc'},
                            {'range': [stock.seuil_critique, stock.seuil_alerte], 'color': '#ffe6cc'},
                            {'range': [stock.seuil_alerte, 100], 'color': '#ccffcc'}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': stock.seuil_critique
                        }
                    }
                ))
                
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=80, b=20))
                st.plotly_chart(fig, use_container_width=True)
                
                # Indicateur d'autonomie
                st.markdown(f"""
                <div style="text-align: center; margin-top: -1rem;">
                    <span class="status-badge status-{stock.statut.lower()}">
                        {stock.statut} - {stock.autonomie_jours:.0f} jours d'autonomie
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    def display_predictions(self):
        """Affiche les prédictions IA"""
        
        st.markdown('<div class="section-title">🤖 PRÉDICTIONS IA (7 JOURS)</div>', unsafe_allow_html=True)
        
        stocks_actuels = self.simulator.get_stocks_actuels()
        
        fig = make_subplots(rows=1, cols=1)
        
        for produit in stocks_actuels.keys():
            historique = self.simulator.stocks_historique[
                self.simulator.stocks_historique['produit'] == produit
            ].tail(30)
            
            predictions = self.predictor.predict_stocks(produit, 7)
            
            # Données historiques
            fig.add_trace(go.Scatter(
                x=historique['date'],
                y=historique['volume'],
                name=f"{produit} - Historique",
                line=dict(width=2)
            ))
            
            # Prédictions
            dates_futures = [datetime.now() + timedelta(days=i) for i in range(1, 8)]
            fig.add_trace(go.Scatter(
                x=dates_futures,
                y=predictions,
                name=f"{produit} - Prédiction",
                line=dict(dash='dash', width=2),
                mode='lines+markers'
            ))
            
            # Seuil critique
            seuil = stocks_actuels[produit].seuil_critique / 100 * stocks_actuels[produit].capacite
            fig.add_hline(y=seuil, line_dash="dot", line_color="red",
                         annotation_text=f"{produit} Seuil critique")
        
        fig.update_layout(
            title="Prédiction des niveaux de stock",
            xaxis_title="Date",
            yaxis_title="Volume (m³)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights IA
        st.markdown("""
        <div class="glass-card">
            <h4>🧠 Insights Intelligence Artificielle</h4>
            <ul>
                <li>📉 Risque de rupture pour le Gazole dans 5 jours si tendance actuelle</li>
                <li>📈 Augmentation prévue de la consommation SP95 (+12%) liée aux vacances</li>
                <li>⚡ Recommandation: Accélérer l'approvisionnement Jet A1 avant la saison touristique</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    def display_anomaly_detection(self):
        """Affiche la détection d'anomalies"""
        
        st.markdown('<div class="section-title">🚨 DÉTECTION D\'ANOMALIES</div>', unsafe_allow_html=True)
        
        # Préparation des données
        data_with_anomalies = self.simulator.stocks_historique.copy()
        data_with_anomalies = self.detector.detect_anomalies(data_with_anomalies)
        
        anomalies = data_with_anomalies[data_with_anomalies['anomalie'] == True]
        
        if len(anomalies) > 0:
            st.error(f"⚠️ {len(anomalies)} anomalies détectées dans les données historiques")
            
            # Visualisation des anomalies
            fig = px.scatter(data_with_anomalies, 
                           x='date', 
                           y='volume', 
                           color='anomalie',
                           color_discrete_map={True: 'red', False: 'blue'},
                           title="Détection d'anomalies dans les niveaux de stock",
                           labels={'anomalie': 'Anomalie détectée'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Détails des anomalies
            with st.expander("Voir le détail des anomalies"):
                st.dataframe(anomalies[['date', 'produit', 'volume', 'pourcentage']])
        else:
            st.success("✅ Aucune anomalie détectée - Les données sont cohérentes")
    
    def display_supply_chain_network(self):
        """Affiche la visualisation du réseau logistique"""
        
        st.markdown('<div class="section-title">🌐 RÉSEAU LOGISTIQUE SRPP</div>', unsafe_allow_html=True)
        
        # Création du graphe
        G = nx.Graph()
        
        # Nœuds: dépôts et ports
        nodes = {
            'Port Est': {'type': 'port', 'capacity': 200000},
            'Port Ouest': {'type': 'port', 'capacity': 150000},
            'Dépôt Le Port': {'type': 'depot', 'capacity': 150000},
            'Dépôt Saint-Pierre': {'type': 'depot', 'capacity': 80000},
            'Dépôt Saint-Benoît': {'type': 'depot', 'capacity': 40000}
        }
        
        # Arêtes: connexions
        edges = [
            ('Port Est', 'Dépôt Le Port', 15),
            ('Port Ouest', 'Dépôt Le Port', 10),
            ('Dépôt Le Port', 'Dépôt Saint-Pierre', 70),
            ('Dépôt Le Port', 'Dépôt Saint-Benoît', 50)
        ]
        
        # Ajout des nœuds et arêtes
        for node, attrs in nodes.items():
            G.add_node(node, **attrs)
        
        for edge in edges:
            G.add_edge(edge[0], edge[1], weight=edge[2])
        
        # Création de la visualisation
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Couleurs selon le type
        node_colors = ['red' if G.nodes[node]['type'] == 'port' else 'blue' for node in G.nodes()]
        node_sizes = [G.nodes[node]['capacity'] / 1000 for node in G.nodes()]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        nx.draw(G, pos, ax=ax, 
                node_color=node_colors,
                node_size=node_sizes,
                with_labels=True,
                font_size=10,
                font_weight='bold',
                edge_color='gray',
                width=[G[u][v]['weight']/10 for u,v in G.edges()])
        
        st.pyplot(fig)
        
        # Métriques du réseau
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Capacité totale de stockage", "270 000 m³", "+5% vs 2023")
        
        with col2:
            st.metric("Distance moyenne transport", "45 km", "-8% optimisation")
        
        with col3:
            st.metric("Efficacité logistique", "94%", "+2%")
    
    def display_3d_visualization(self):
        """Visualisation 3D des infrastructures"""
        
        st.markdown('<div class="section-title">🗺️ VISUALISATION 3D DES INFRASTRUCTURES</div>', unsafe_allow_html=True)
        
        # Données géospatiales
        depots = {
            'Le Port': {'lat': -20.937, 'lon': 55.287, 'capacite': 150000, 'hauteur': 150},
            'Saint-Pierre': {'lat': -21.342, 'lon': 55.478, 'capacite': 80000, 'hauteur': 80},
            'Saint-Benoît': {'lat': -21.072, 'lon': 55.712, 'capacite': 40000, 'hauteur': 40}
        }
        
        # Création de la carte 3D avec Plotly
        fig = go.Figure()
        
        for nom, coords in depots.items():
            fig.add_trace(go.Scatter3d(
                x=[coords['lon']],
                y=[coords['lat']],
                z=[0],
                mode='markers+text',
                marker=dict(size=coords['hauteur']/10, color='red', symbol='circle'),
                text=[nom],
                textposition="top center",
                name=nom
            ))
            
            # Ajout des colonnes verticales pour représenter la capacité
            fig.add_trace(go.Scatter3d(
                x=[coords['lon'], coords['lon']],
                y=[coords['lat'], coords['lat']],
                z=[0, coords['hauteur']],
                mode='lines',
                line=dict(color='blue', width=3),
                showlegend=False
            ))
        
        fig.update_layout(
            title="Infrastructures SRPP - Visualisation 3D",
            scene=dict(
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                zaxis_title="Altitude (m)"
            ),
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_recommendations(self):
        """Affiche les recommandations stratégiques"""
        
        st.markdown('<div class="section-title">💡 RECOMMANDATIONS STRATÉGIQUES</div>', unsafe_allow_html=True)
        
        stocks = self.simulator.get_stocks_actuels()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="glass-card">
                <h3>🎯 Actions Immédiates</h3>
                <ul>
                    <li><strong>Priorité 1:</strong> Commander Gazole (stock à {:.1f}%)</li>
                    <li><strong>Priorité 2:</strong> Répartir les stocks vers Saint-Pierre</li>
                    <li><strong>Priorité 3:</strong> Augmenter la cadence livraison SP95</li>
                </ul>
                <hr>
                <h3>📊 Optimisation</h3>
                <ul>
                    <li>Réduire les délais d'approvisionnement de 15%</li>
                    <li>Optimiser les rotations de stock</li>
                    <li>Programmer maintenance préventive</li>
                </ul>
            </div>
            """.format(stocks['Gazole'].pourcentage), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="glass-card">
                <h3>🚀 Innovation & Digitalisation</h3>
                <ul>
                    <li>📱 Application mobile pour les transporteurs</li>
                    <li>🔗 Blockchain pour la traçabilité</li>
                    <li>🤖 IA pour prédiction demande</li>
                    <li>📡 IoT pour monitoring temps réel</li>
                </ul>
                <hr>
                <h3>🌱 Développement Durable</h3>
                <ul>
                    <li>Réduction empreinte carbone: -15% objectif 2025</li>
                    <li>Énergies renouvelables sur sites</li>
                    <li>Formation aux éco-gestes</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def display_live_alerts(self):
        """Affiche les alertes en temps réel"""
        
        st.markdown('<div class="section-title">🔔 ALERTES TEMPS RÉEL</div>', unsafe_allow_html=True)
        
        stocks = self.simulator.get_stocks_actuels()
        
        alerts = []
        for produit, stock in stocks.items():
            if stock.statut == "CRITIQUE":
                alerts.append({
                    'niveau': 'CRITIQUE',
                    'produit': produit,
                    'message': f"Niveau critique: {stock.pourcentage:.1f}% - Action immédiate requise!",
                    'action': "Commander en urgence"
                })
            elif stock.statut == "ALERTE":
                alerts.append({
                    'niveau': 'ALERTE',
                    'produit': produit,
                    'message': f"Niveau d'alerte: {stock.pourcentage:.1f}% - Surveillance renforcée",
                    'action': "Planifier approvisionnement"
                })
        
        # Alertes simulation d'événements
        if random.random() < 0.3:
            alerts.append({
                'niveau': 'INFO',
                'produit': 'Navire',
                'message': "Arrivée du MT Diana prévue dans 48h avec 15 000 m³ de Gazole",
                'action': "Préparer déchargement"
            })
        
        for alert in alerts:
            if alert['niveau'] == 'CRITIQUE':
                st.error(f"🚨 **{alert['produit']}** - {alert['message']}")
                st.warning(f"📋 Action: {alert['action']}")
            elif alert['niveau'] == 'ALERTE':
                st.warning(f"⚠️ **{alert['produit']}** - {alert['message']}")
                st.info(f"📋 Action: {alert['action']}")
            else:
                st.info(f"ℹ️ **{alert['produit']}** - {alert['message']}")
    
    def display_market_analysis(self):
        """Analyse des marchés et prix"""
        
        st.markdown('<div class="section-title">📈 ANALYSE MARCHÉ & PRIX</div>', unsafe_allow_html=True)
        
        # Récupération des prix (API ou simulés)
        prices = self.api._get_simulated_prices()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique d'évolution des prix
            dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='W')
            
            fig = go.Figure()
            for carburant, prix_base in prices.items():
                # Simulation d'évolution
                evolution = [prix_base * (1 + 0.02 * np.sin(i/10) + 0.01 * random.random()) 
                           for i in range(len(dates))]
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=evolution,
                    name=carburant,
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Évolution des prix des carburants à La Réunion",
                xaxis_title="Date",
                yaxis_title="Prix (€/L)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Comparaison avec la métropole
            st.markdown("""
            <div class="glass-card">
                <h3>📊 Comparaison des prix</h3>
                <table style="width: 100%;">
                    <tr>
                        <th>Carburant</th>
                        <th>La Réunion</th>
                        <th>Métropole</th>
                        <th>Écart</th>
                    </tr>
                    <tr>
                        <td>SP95</td>
                        <td>1.54 €</td>
                        <td>1.82 €</td>
                        <td style="color: green;">-15%</td>
                    </tr>
                    <tr>
                        <td>Gazole</td>
                        <td>1.29 €</td>
                        <td>1.68 €</td>
                        <td style="color: green;">-23%</td>
                    </tr>
                    <tr>
                        <td>SP98</td>
                        <td>1.62 €</td>
                        <td>1.91 €</td>
                        <td style="color: green;">-15%</td>
                    </tr>
                </table>
                <hr>
                <h3>📈 Tendances</h3>
                <ul>
                    <li>📉 Tendance baissière sur le gazole (-2.3% ce mois)</li>
                    <li>📊 Stabilité des prix SP95</li>
                    <li>🌍 Impact des tensions géopolitiques limité</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """Exécute le dashboard complet"""
        
        # En-tête
        st.markdown("""
        <div class="main-header">
            🎯 SRPP LA RÉUNION - INTELLIGENCE ARTIFICIELLE & MONITORING AVANCÉ
            <span class="live-badge">LIVE</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu de navigation avancé
        selected = option_menu(
            menu_title=None,
            options=["Tableau de Bord", "Prédictions IA", "Logistique", "Analyse Marché", "Rapports"],
            icons=["house", "graph-up", "truck", "bar-chart", "file-text"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#667eea", "font-size": "1.2rem"},
                "nav-link": {"font-size": "1rem", "text-align": "center", "margin": "0px"},
                "nav-link-selected": {"background-color": "#667eea"},
            }
        )
        
        if selected == "Tableau de Bord":
            self.display_hero_section()
            self.display_stock_gauges()
            self.display_live_alerts()
            self.display_anomaly_detection()
            
        elif selected == "Prédictions IA":
            self.display_predictions()
            self.display_anomaly_detection()
            
        elif selected == "Logistique":
            self.display_supply_chain_network()
            self.display_3d_visualization()
            
        elif selected == "Analyse Marché":
            self.display_market_analysis()
            
        elif selected == "Rapports":
            self.display_recommendations()
            st.info("📊 Fonctionnalité d'export de rapports disponible dans la version premium")
        
        # Footer
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #6c757d; font-size: 0.8rem;">
            🚀 SRPP La Réunion - Dashboard Avancé v2.0 | Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            <br>🔒 Données confidentielles - Usage interne SRPP
        </div>
        """, unsafe_allow_html=True)

# Lancement du dashboard
if __name__ == "__main__":
    dashboard = AdvancedDashboard()
    dashboard.run()
