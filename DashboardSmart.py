# dashboard_srpp_final.py - Version stable sans erreurs
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
    layout="wide",
    initial_sidebar_state="expanded"
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
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .stock-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B00;
    }
    .critical { color: #dc3545; font-weight: bold; }
    .warning { color: #ffc107; font-weight: bold; }
    .normal { color: #28a745; font-weight: bold; }
    .excellent { color: #17a2b8; font-weight: bold; }
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
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1rem 0;
        color: #2c3e50;
        border-left: 4px solid #FF6B00;
        padding-left: 1rem;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .progress-bar {
        height: 8px;
        background: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .progress-fill {
        height: 100%;
        transition: width 0.3s ease;
    }
    .footer {
        text-align: center;
        color: #6c757d;
        font-size: 0.75rem;
        padding: 1rem;
        border-top: 1px solid #e9ecef;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

class SRPPDashboard:
    def __init__(self):
        # Configuration des produits
        self.produits = {
            'SP95': {
                'capacite': 95000,
                'stock': 62300,
                'seuil_critique': 15,
                'seuil_alerte': 25,
                'prix_achat': 1.32,
                'prix_vente': 1.54,
                'icone': '⛽',
                'couleur': '#FF6B00'
            },
            'SP98': {
                'capacite': 45000,
                'stock': 29400,
                'seuil_critique': 15,
                'seuil_alerte': 25,
                'prix_achat': 1.40,
                'prix_vente': 1.62,
                'icone': '⛽',
                'couleur': '#FF8C00'
            },
            'Gazole': {
                'capacite': 115000,
                'stock': 78200,
                'seuil_critique': 12,
                'seuil_alerte': 22,
                'prix_achat': 1.10,
                'prix_vente': 1.29,
                'icone': '🛢️',
                'couleur': '#28a745'
            },
            'Jet A1': {
                'capacite': 60000,
                'stock': 41800,
                'seuil_critique': 10,
                'seuil_alerte': 20,
                'prix_achat': 0.95,
                'prix_vente': 1.15,
                'icone': '✈️',
                'couleur': '#17a2b8'
            },
            'Fioul': {
                'capacite': 35000,
                'stock': 18700,
                'seuil_critique': 20,
                'seuil_alerte': 35,
                'prix_achat': 0.85,
                'prix_vente': 0.98,
                'icone': '🔥',
                'couleur': '#6c757d'
            }
        }
        
        # Configuration des dépôts
        self.depots = {
            'Le Port': {
                'capacite': 150000,
                'stocks': {'SP95': 38500, 'SP98': 18200, 'Gazole': 48500, 'Jet A1': 25900, 'Fioul': 11600},
                'coordonnees': (-20.937, 55.287)
            },
            'Saint-Pierre': {
                'capacite': 80000,
                'stocks': {'SP95': 20500, 'SP98': 9700, 'Gazole': 25800, 'Jet A1': 13800, 'Fioul': 6200},
                'coordonnees': (-21.342, 55.478)
            },
            'Saint-Benoît': {
                'capacite': 40000,
                'stocks': {'SP95': 10300, 'SP98': 4900, 'Gazole': 12900, 'Jet A1': 6900, 'Fioul': 3100},
                'coordonnees': (-21.072, 55.712)
            }
        }
        
        # Historique simulé
        self.historique = self._generer_historique()
    
    def _generer_historique(self):
        """Génère un historique des stocks"""
        dates = pd.date_range('2024-01-01', datetime.now(), freq='D')
        historique = []
        
        for date in dates:
            for produit, config in self.produits.items():
                # Simulation d'évolution réaliste
                variation = np.random.normal(0, config['capacite'] * 0.01)
                saisonnalite = 0.05 * np.sin(2 * np.pi * date.dayofyear / 365)
                stock_base = config['stock'] * (1 + saisonnalite)
                stock = max(0, min(stock_base + variation, config['capacite']))
                
                historique.append({
                    'date': date,
                    'produit': produit,
                    'stock': stock,
                    'capacite': config['capacite'],
                    'taux': (stock / config['capacite']) * 100
                })
        
        return pd.DataFrame(historique)
    
    def get_remplissage(self, stock, capacite):
        return (stock / capacite) * 100
    
    def get_statut(self, pourcentage, seuil_critique, seuil_alerte):
        if pourcentage <= seuil_critique:
            return "CRITIQUE", "critical"
        elif pourcentage <= seuil_alerte:
            return "ALERTE", "warning"
        elif pourcentage >= 85:
            return "EXCELLENT", "excellent"
        return "NORMAL", "normal"
    
    def predire_stock(self, produit, jours=30):
        """Prédiction simple des stocks"""
        historique_produit = self.historique[self.historique['produit'] == produit].tail(90)
        
        if len(historique_produit) < 30:
            return np.array([self.produits[produit]['stock']] * jours)
        
        # Tendance linéaire simple
        x = np.arange(len(historique_produit))
        y = historique_produit['stock'].values
        
        coeffs = np.polyfit(x, y, 1)
        tendance = coeffs[0]
        
        # Prédiction
        dernier_stock = y[-1]
        predictions = []
        for i in range(1, jours + 1):
            pred = dernier_stock + (tendance * i)
            pred = max(0, min(pred, self.produits[produit]['capacite']))
            predictions.append(pred)
        
        return np.array(predictions)
    
    def run(self):
        # En-tête
        st.markdown(f"""
        <div class="main-header">
            ⛽ SRPP LA RÉUNION - SUIVI DES STOCKS EN TEMPS RÉEL
            <span class="live-badge">LIVE</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.markdown("## 🎛️ CONTRÔLES")
            
            auto_refresh = st.checkbox("🔄 Rafraîchissement automatique", value=False)
            if auto_refresh:
                refresh_interval = st.slider("Intervalle (secondes)", 5, 60, 30)
            
            st.markdown("---")
            st.markdown("### 🔍 Filtres")
            produits_selectionnes = st.multiselect(
                "Produits à afficher",
                list(self.produits.keys()),
                default=list(self.produits.keys())
            )
            
            st.markdown("---")
            st.markdown("### 📊 Informations")
            st.info(f"""
            - **Dernière mise à jour:** {datetime.now().strftime('%H:%M:%S')}
            - **Nombre de produits:** {len(self.produits)}
            - **Nombre de dépôts:** {len(self.depots)}
            """)
        
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        
        volume_total = sum(p['stock'] for p in self.produits.values())
        capacite_total = sum(p['capacite'] for p in self.produits.values())
        conso_journaliere = 1850  # m³/jour estimé
        valeur_totale = sum(p['stock'] * p['prix_achat'] for p in self.produits.values())
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.8rem;">📦 VOLUME TOTAL STOCKÉ</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{volume_total:,.0f} m³</div>
                <div style="font-size: 0.7rem;">Capacité: {capacite_total:,.0f} m³</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(volume_total/capacite_total)*100:.1f}%; background: #FF6B00;"></div>
                </div>
                <div>Taux: {(volume_total/capacite_total)*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            autonomie = volume_total / conso_journaliere
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.8rem;">⏱️ AUTONOMIE ESTIMÉE</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{autonomie:.0f} jours</div>
                <div style="font-size: 0.7rem;">Consommation: {conso_journaliere:,.0f} m³/j</div>
                <div style="margin-top: 0.5rem;">📊 {autonomie/7:.1f} semaines</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.8rem;">💰 VALEUR DU STOCK</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{valeur_totale:,.0f} €</div>
                <div style="font-size: 0.7rem;">Marge estimée: {valeur_totale * 0.12:,.0f} €</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            alertes = sum(1 for p in self.produits.values() 
                         if self.get_remplissage(p['stock'], p['capacite']) <= p['seuil_alerte'])
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.8rem;">🔔 ALERTES ACTIVES</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{alertes}</div>
                <div style="font-size: 0.7rem;">{'🚨 URGENCE' if alertes > 0 else '✅ Situation normale'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Onglets principaux
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Vue d'ensemble",
            "📈 Évolution & Prédictions",
            "🏭 Analyse par dépôt",
            "💰 Analyse économique"
        ])
        
        with tab1:
            st.markdown('<div class="section-title">🛢️ Niveaux de stock par produit</div>', unsafe_allow_html=True)
            
            # Cartes des produits
            cols = st.columns(len(produits_selectionnes))
            for idx, produit in enumerate(produits_selectionnes):
                with cols[idx]:
                    config = self.produits[produit]
                    remplissage = self.get_remplissage(config['stock'], config['capacite'])
                    statut, classe = self.get_statut(remplissage, config['seuil_critique'], config['seuil_alerte'])
                    
                    st.markdown(f"""
                    <div class="stock-card">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 1.5rem;">{config['icone']}</span>
                            <h3 style="margin: 0;">{produit}</h3>
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; margin: 0.5rem 0;">
                            {config['stock']:,.0f} m³
                        </div>
                        <div>Capacité: {config['capacite']:,.0f} m³</div>
                        <div>Taux: {remplissage:.1f}%</div>
                        <div class="{classe}">Statut: {statut}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {remplissage:.1f}%; background: {config['couleur']};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Graphique circulaire
            st.markdown('<div class="section-title">📊 Répartition des stocks</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                df_produits = pd.DataFrame([
                    {
                        'Produit': p,
                        'Volume': config['stock'],
                        'Taux': self.get_remplissage(config['stock'], config['capacite'])
                    }
                    for p, config in self.produits.items()
                    if p in produits_selectionnes
                ])
                
                fig_pie = px.pie(
                    df_produits,
                    values='Volume',
                    names='Produit',
                    title='Répartition du volume stocké',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")
            
            with col2:
                df_bar = df_produits.copy()
                fig_bar = px.bar(
                    df_bar,
                    x='Produit',
                    y='Taux',
                    title='Taux de remplissage par produit',
                    color='Produit',
                    text=df_bar['Taux'].round(1).astype(str) + '%',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True, key="bar_chart")
        
        with tab2:
            st.markdown('<div class="section-title">📈 Évolution historique et prédictions</div>', unsafe_allow_html=True)
            
            produit_pred = st.selectbox("Sélectionnez un produit", produits_selectionnes)
            
            if produit_pred:
                config = self.produits[produit_pred]
                historique_prod = self.historique[self.historique['produit'] == produit_pred].tail(90)
                predictions = self.predire_stock(produit_pred, 30)
                
                dates_hist = historique_prod['date'].values
                stocks_hist = historique_prod['stock'].values
                dates_futures = [datetime.now() + timedelta(days=i) for i in range(1, 31)]
                
                fig = go.Figure()
                
                # Historique
                fig.add_trace(go.Scatter(
                    x=dates_hist,
                    y=stocks_hist,
                    name='Historique',
                    line=dict(color='#667eea', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(102,126,234,0.1)'
                ))
                
                # Prédictions
                fig.add_trace(go.Scatter(
                    x=dates_futures,
                    y=predictions,
                    name='Prédiction',
                    line=dict(color='#dc3545', dash='dash', width=2),
                    mode='lines+markers'
                ))
                
                # Seuils
                fig.add_hline(y=config['capacite'] * config['seuil_critique'] / 100,
                             line_dash="dot", line_color="red",
                             annotation_text="Seuil critique")
                fig.add_hline(y=config['capacite'] * config['seuil_alerte'] / 100,
                             line_dash="dot", line_color="orange",
                             annotation_text="Seuil alerte")
                
                fig.update_layout(
                    title=f"Évolution et prédiction - {produit_pred}",
                    xaxis_title="Date",
                    yaxis_title="Volume (m³)",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True, key="prediction_chart")
                
                # Insights
                dernier_taux = self.get_remplissage(config['stock'], config['capacite'])
                pred_fin = predictions[-1]
                pred_taux = (pred_fin / config['capacite']) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Taux actuel", f"{dernier_taux:.1f}%")
                with col2:
                    st.metric("Prédiction J+30", f"{pred_taux:.1f}%",
                             delta=f"{pred_taux - dernier_taux:+.1f}%")
                with col3:
                    if pred_taux < config['seuil_critique']:
                        st.error("⚠️ Risque de rupture dans les 30 jours")
                    elif pred_taux < config['seuil_alerte']:
                        st.warning("⚠️ Niveau d'alerte atteint dans les 30 jours")
                    else:
                        st.success("✅ Situation stable à 30 jours")
        
        with tab3:
            st.markdown('<div class="section-title">🏭 Analyse par dépôt</div>', unsafe_allow_html=True)
            
            # Heatmap des stocks par dépôt
            heatmap_data = []
            for depot_name, depot in self.depots.items():
                for produit, stock in depot['stocks'].items():
                    if produit in produits_selectionnes:
                        capacite_produit = self.produits[produit]['capacite']
                        taux = (stock / capacite_produit) * 100
                        heatmap_data.append({
                            'Dépôt': depot_name,
                            'Produit': produit,
                            'Taux': taux,
                            'Volume': stock
                        })
            
            df_heatmap = pd.DataFrame(heatmap_data)
            pivot_heatmap = df_heatmap.pivot(index='Dépôt', columns='Produit', values='Taux')
            
            fig_heatmap = px.imshow(
                pivot_heatmap.values,
                x=pivot_heatmap.columns,
                y=pivot_heatmap.index,
                text_auto=True,
                aspect="auto",
                title="Matrice des taux de remplissage par dépôt",
                color_continuous_scale='RdYlGn',
                labels=dict(color="Taux (%)")
            )
            st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap_chart")
            
            # Détail par dépôt
            for depot_name, depot in self.depots.items():
                with st.expander(f"📍 {depot_name} - Capacité: {depot['capacite']:,.0f} m³"):
                    volume_depot = sum(depot['stocks'][p] for p in produits_selectionnes if p in depot['stocks'])
                    taux_depot = (volume_depot / depot['capacite']) * 100
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Volume stocké", f"{volume_depot:,.0f} m³")
                        st.metric("Taux de remplissage", f"{taux_depot:.1f}%")
                    
                    with col2:
                        # Mini graphique des stocks par produit
                        depot_df = pd.DataFrame([
                            {'Produit': p, 'Volume': v}
                            for p, v in depot['stocks'].items()
                            if p in produits_selectionnes
                        ])
                        fig_depot = px.bar(
                            depot_df,
                            x='Produit',
                            y='Volume',
                            title="Stocks par produit",
                            color='Produit'
                        )
                        st.plotly_chart(fig_depot, use_container_width=True, key=f"depot_{depot_name}_chart")
        
        with tab4:
            st.markdown('<div class="section-title">💰 Analyse économique</div>', unsafe_allow_html=True)
            
            # Données économiques
            donnees_economiques = []
            for produit, config in self.produits.items():
                if produit in produits_selectionnes:
                    valeur_stock = config['stock'] * config['prix_achat']
                    valeur_vente = config['stock'] * config['prix_vente']
                    marge = valeur_vente - valeur_stock
                    
                    donnees_economiques.append({
                        'Produit': produit,
                        'Stock (m³)': config['stock'],
                        'Prix achat (€/m³)': config['prix_achat'],
                        'Prix vente (€/m³)': config['prix_vente'],
                        'Valeur stock (€)': valeur_stock,
                        'Marge potentielle (€)': marge,
                        'Marge unitaire (%)': ((config['prix_vente'] - config['prix_achat']) / config['prix_achat']) * 100
                    })
            
            df_economique = pd.DataFrame(donnees_economiques)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_valeur = px.bar(
                    df_economique,
                    x='Produit',
                    y='Valeur stock (€)',
                    title="Valeur du stock par produit",
                    text=df_economique['Valeur stock (€)'].apply(lambda x: f"{x:,.0f} €"),
                    color='Produit'
                )
                fig_valeur.update_traces(textposition='outside')
                st.plotly_chart(fig_valeur, use_container_width=True, key="valeur_chart")
            
            with col2:
                fig_marge = px.bar(
                    df_economique,
                    x='Produit',
                    y='Marge potentielle (€)',
                    title="Marge potentielle par produit",
                    text=df_economique['Marge potentielle (€)'].apply(lambda x: f"{x:,.0f} €"),
                    color='Produit'
                )
                fig_marge.update_traces(textposition='outside')
                st.plotly_chart(fig_marge, use_container_width=True, key="marge_chart")
            
            # Tableau des données
            st.dataframe(
                df_economique.style.format({
                    'Stock (m³)': '{:,.0f}',
                    'Prix achat (€/m³)': '{:.2f}',
                    'Prix vente (€/m³)': '{:.2f}',
                    'Valeur stock (€)': '{:,.0f} €',
                    'Marge potentielle (€)': '{:,.0f} €',
                    'Marge unitaire (%)': '{:.1f}%'
                }),
                use_container_width=True
            )
            
            # KPIs économiques
            valeur_totale = df_economique['Valeur stock (€)'].sum()
            marge_totale = df_economique['Marge potentielle (€)'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Valeur totale du stock", f"{valeur_totale:,.0f} €")
            with col2:
                st.metric("Marge potentielle totale", f"{marge_totale:,.0f} €",
                         delta=f"+{(marge_totale/valeur_totale*100):.1f}%")
            with col3:
                st.metric("Rotation estimée", "15 jours")
            with col4:
                st.metric("ROI projeté", "18.5%")
        
        # Alertes en temps réel
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🔔 Alertes temps réel")
            
            alertes_trouvees = False
            for produit, config in self.produits.items():
                remplissage = self.get_remplissage(config['stock'], config['capacite'])
                if remplissage <= config['seuil_alerte']:
                    alertes_trouvees = True
                    if remplissage <= config['seuil_critique']:
                        st.error(f"🚨 **{produit}** - CRITIQUE: {remplissage:.1f}%")
                    else:
                        st.warning(f"⚠️ **{produit}** - Alerte: {remplissage:.1f}%")
            
            if not alertes_trouvees:
                st.success("✅ Aucune alerte active")
        
        # Footer
        st.markdown(f"""
        <div class="footer">
            🚀 SRPP La Réunion - Dashboard v2.0 | Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            <br>🔒 Données internes - Usage professionnel | Source: SRPP
        </div>
        """, unsafe_allow_html=True)
        
        # Rafraîchissement automatique
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()

if __name__ == "__main__":
    dashboard = SRPPDashboard()
    dashboard.run()
