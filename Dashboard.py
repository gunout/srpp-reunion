# dashboard_srpp_simple.py - Version sans cartopy
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="SRPP La Réunion - Dashboard Stocks",
    page_icon="⛽",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        background: linear-gradient(45deg, #0055A4, #FF6B00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1rem;
        color: white;
        text-align: center;
    }
    .stock-card {
        background: black;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B00;
    }
    .critical { color: #dc3545; font-weight: bold; }
    .warning { color: #ffc107; font-weight: bold; }
    .normal { color: #28a745; font-weight: bold; }
    .live-badge {
        background-color: #dc3545;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.7rem;
        animation: blink 1s infinite;
        display: inline-block;
        margin-left: 1rem;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

class SRPPDashboard:
    def __init__(self):
        # Données des dépôts SRPP
        self.depots = {
            'Le Port': {'capacite': 150000, 'stocks': 98500, 'coord': [-20.937, 55.287]},
            'Saint-Pierre': {'capacite': 80000, 'stocks': 52300, 'coord': [-21.342, 55.478]},
            'Saint-Benoît': {'capacite': 40000, 'stocks': 28700, 'coord': [-21.072, 55.712]}
        }
        
        # Produits pétroliers
        self.produits = {
            'SP95': {'capacite': 95000, 'stock': 62300, 'seuil_critique': 15},
            'SP98': {'capacite': 45000, 'stock': 29400, 'seuil_critique': 15},
            'Gazole': {'capacite': 115000, 'stock': 78200, 'seuil_critique': 12},
            'Jet A1': {'capacite': 60000, 'stock': 41800, 'seuil_critique': 10}
        }
        
    def get_remplissage(self, stock, capacite):
        return (stock / capacite) * 100
    
    def get_statut(self, pourcentage, seuil):
        if pourcentage <= seuil:
            return "CRITIQUE", "critical"
        elif pourcentage <= seuil + 10:
            return "ALERTE", "warning"
        return "NORMAL", "normal"
    
    def run(self):
        st.markdown('<div class="main-header">⛽ SRPP LA RÉUNION - SUIVI DES STOCKS<span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
        
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        
        volume_total = sum(d['stocks'] for d in self.depots.values())
        capacite_total = sum(d['capacite'] for d in self.depots.values())
        conso_journaliere = 1850  # m³/jour estimé
        
        with col1:
            st.metric("Volume total stocké", f"{volume_total:,.0f} m³", 
                     delta=f"{(volume_total/capacite_total*100):.1f}% remplissage")
        
        with col2:
            st.metric("Capacité totale", f"{capacite_total:,.0f} m³")
        
        with col3:
            st.metric("Consommation journalière", f"{conso_journaliere:,.0f} m³/j")
        
        with col4:
            autonomie = volume_total / conso_journaliere
            st.metric("Autonomie estimée", f"{autonomie:.0f} jours")
        
        # Graphique des stocks par dépôt
        st.subheader("📊 Niveaux de stock par dépôt")
        
        fig = go.Figure()
        
        for depot, data in self.depots.items():
            remplissage = (data['stocks'] / data['capacite']) * 100
            fig.add_trace(go.Bar(
                name=depot,
                x=[depot],
                y=[remplissage],
                text=[f"{remplissage:.1f}%"],
                textposition='auto',
                marker_color='#FF6B00'
            ))
        
        fig.update_layout(
            title="Taux de remplissage des dépôts",
            yaxis_title="Taux de remplissage (%)",
            yaxis_range=[0, 100],
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Produits
        st.subheader("🛢️ Stocks par produit")
        
        cols = st.columns(len(self.produits))
        for idx, (produit, data) in enumerate(self.produits.items()):
            with cols[idx]:
                remplissage = (data['stock'] / data['capacite']) * 100
                statut, classe = self.get_statut(remplissage, data['seuil_critique'])
                
                st.markdown(f"""
                <div class="stock-card">
                    <h3>{produit}</h3>
                    <div style="font-size: 1.5rem; font-weight: bold;">{data['stock']:,.0f} m³</div>
                    <div>Capacité: {data['capacite']:,.0f} m³</div>
                    <div>Taux: {remplissage:.1f}%</div>
                    <div class="{classe}">Statut: {statut}</div>
                    <div style="margin-top: 0.5rem;">
                        <div style="background: #e9ecef; border-radius: 10px; height: 8px;">
                            <div style="background: {'#dc3545' if statut=='CRITIQUE' else '#ffc107' if statut=='ALERTE' else '#28a745'}; 
                                        width: {remplissage}%; height: 8px; border-radius: 10px;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Évolution historique (simulée)
        st.subheader("📈 Évolution des stocks (30 jours)")
        
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        fig = go.Figure()
        for produit in self.produits.keys():
            # Simulation d'évolution
            evolution = [self.produits[produit]['stock'] * (1 + 0.01 * np.sin(i/5) + random.uniform(-0.02, 0.02)) 
                        for i in range(30)]
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=evolution,
                name=produit,
                mode='lines',
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Évolution des stocks",
            xaxis_title="Date",
            yaxis_title="Volume (m³)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Alertes
        st.subheader("🔔 Alertes en temps réel")
        
        alertes = []
        for produit, data in self.produits.items():
            remplissage = (data['stock'] / data['capacite']) * 100
            if remplissage <= data['seuil_critique']:
                alertes.append(f"🚨 **{produit}** - Niveau critique: {remplissage:.1f}%")
            elif remplissage <= data['seuil_critique'] + 10:
                alertes.append(f"⚠️ **{produit}** - Niveau d'alerte: {remplissage:.1f}%")
        
        if alertes:
            for alerte in alertes:
                if "🚨" in alerte:
                    st.error(alerte)
                else:
                    st.warning(alerte)
        else:
            st.success("✅ Aucune alerte - Niveaux de stocks satisfaisants")
        
        # Recommandations
        st.subheader("💡 Recommandations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 Actions prioritaires
            - Planifier l'approvisionnement en Gazole (stock à {:.1f}%)
            - Maintenir la surveillance du Jet A1 pour la saison touristique
            - Optimiser les rotations au dépôt du Port
            """.format((self.produits['Gazole']['stock'] / self.produits['Gazole']['capacite']) * 100))
        
        with col2:
            st.markdown("""
            ### 📊 Données clés
            - **Dernier arrivage:** MT Diana - 12/03/2025
            - **Prochain navire prévu:** MT Sirius - 28/03/2025
            - **Capacité de stockage disponible:** {:.0f} m³
            """.format(capacite_total - volume_total))
        
        # Footer
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #6c757d; font-size: 0.8rem;">
            🚀 SRPP La Réunion - Dashboard v1.0 | Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            <br>🔒 Données internes - Usage professionnel
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard = SRPPDashboard()
    dashboard.run()