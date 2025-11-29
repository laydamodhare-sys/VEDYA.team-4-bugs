import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

from agents.data_agent import DataAgent
from agents.forecasting_agent import ForecastingAgent
from agents.spike_detection_agent import SpikeDetectionAgent
from agents.explanation_agent import ExplanationAgent
from agents.planner_agent import PlannerAgent
from agents.health_risk_index import HealthRiskIndex

from database import get_db, init_db
from models import AcceptedPlan, RejectedPlan, AlertSent

try:
    init_db()
except Exception as e:
    st.error(f"Database initialization error: {e}")

st.set_page_config(
    page_title="Health Risk Prediction System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_agents():
    data_agent = DataAgent(use_local_data=True)
    forecasting_agent = ForecastingAgent()
    spike_agent = SpikeDetectionAgent()
    explanation_agent = ExplanationAgent()
    planner_agent = PlannerAgent()
    health_index = HealthRiskIndex()
    return data_agent, forecasting_agent, spike_agent, explanation_agent, planner_agent, health_index

def generate_health_response(user_input, current_data):
    """Generate healthcare guidance based on user input"""
    user_input_lower = user_input.lower()
    
    # Symptom-based responses
    symptoms_responses = {
        "fever": "Fever can indicate infection. Monitor your temperature regularly. Stay hydrated and rest. If fever persists >3 days or >101°F, consult a doctor. Current AQI: " + str(int(current_data.get('aqi', 0))),
        "headache": "Headaches can be triggered by stress, dehydration, or air quality. Drink water, rest in a dark room, and avoid screens. High AQI (>100) can worsen symptoms.",
        "cough": "Cough might indicate respiratory issues. Avoid air pollution, use masks outdoors, stay hydrated. If persistent >2 weeks, seek medical advice.",
        "cold": "Common cold typically improves in 7-10 days. Rest, hydrate, use saline drops, and avoid spreading to others. Boost immunity with vitamin C.",
        "allergy": "Allergies worsen with high air pollution. Stay indoors on bad air days, use HEPA filters, and take antihistamines as needed.",
        "covid": "COVID symptoms vary. Get tested if symptomatic. Stay isolated for 5-10 days. Seek emergency care if shortness of breath occurs.",
        "flu": "Flu is serious - get vaccinated annually. Rest, hydrate, and antiviral drugs help. Avoid others for 5 days.",
        "pollution": f"Current AQI is {int(current_data.get('aqi', 0))}. Wear N95 masks outdoors, keep windows closed, use air purifiers, and reduce outdoor activities.",
        "aqi": f"Current AQI in your area: {int(current_data.get('aqi', 0))}. Healthy level is <50. Limit outdoor activities if AQI >100.",
    }
    
    for symptom, response in symptoms_responses.items():
        if symptom in user_input_lower:
            return response
    
    # General health questions
    general_responses = {
        "sleep": "Get 7-8 hours of quality sleep daily. Maintain consistent sleep schedule, avoid screens 1 hour before bed.",
        "exercise": "Aim for 150 mins moderate activity weekly. Avoid outdoor exercise on high pollution days. Indoor workouts are safer alternatives.",
        "diet": "Eat balanced meals: fruits, vegetables, lean proteins. Limit processed foods. Stay hydrated with 2-3 liters water daily.",
        "doctor": "See a doctor for: persistent symptoms >2 weeks, high fever, severe pain, breathing issues, or chronic conditions.",
        "vaccine": "Vaccinations protect you and community. Get annual flu shots and recommended vaccines. Consult your doctor for personalized advice.",
        "prevent": "Prevention tips: wash hands regularly, wear masks in crowds, avoid touching face, maintain distance from sick people, boost immunity.",
    }
    
    for keyword, response in general_responses.items():
        if keyword in user_input_lower:
            return response
    
    # Default response
    return "🤔 I'm here to help with health-related questions! Ask about symptoms, prevention, vaccines, air quality, or general wellness. What's your concern?"

data_agent, forecasting_agent, spike_agent, explanation_agent, planner_agent, health_index = initialize_agents()

st.markdown("""
    <style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    [data-testid="stTabs"] {
        background: transparent;
    }
    
    .stTabs {
        overflow: visible !important;
    }
    
    div[data-testid="column"] {
        min-height: auto;
    }
    
    .main-header {
        font-size: 56px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    
    .sub-header {
        font-size: 22px;
        color: #475569;
        text-align: center;
        margin-bottom: 35px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #e8eef7 0%, #f0f4f8 100%);
        padding: 28px;
        border-radius: 16px;
        color: #1e293b;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        border: 1px solid rgba(102, 126, 234, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.16);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card h3 {
        margin: 0 0 12px 0;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #475569 !important;
    }
    
    .metric-card h1 {
        margin: 8px 0;
        font-size: 42px;
        font-weight: 700;
        color: #0f172a !important;
    }
    
    .metric-card p {
        margin: 8px 0 0 0;
        font-size: 13px;
        font-weight: 500;
        color: #475569 !important;
    }
    
    .risk-severe {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .risk-severe h3, .risk-severe p, .risk-severe h1 {
        color: white;
    }
    
    .risk-high {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .risk-high h3, .risk-high p, .risk-high h1 {
        color: white;
    }
    
    .risk-moderate {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    .risk-moderate h3, .risk-moderate p, .risk-moderate h1 {
        color: white;
    }
    
    .risk-low {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: white;
    }
    
    .risk-low h3, .risk-low p, .risk-low h1 {
        color: white;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 12px 24px;
        background-color: transparent;
        border-radius: 8px;
        border: 2px solid transparent;
        font-weight: 600;
        color: #64748b;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9;
        color: #1e293b;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
    }
    
    .stButton button {
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .stButton button:hover {
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        border-left: 4px solid #667eea;
        padding: 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
        font-weight: 700;
    }
    
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🩺 AI Health Risk Prediction System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Early Warning & Resource Planning Platform</div>', unsafe_allow_html=True)

cities = data_agent.get_all_cities()

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/hospital.png", width=150)
    st.header("⚙️ Control Panel")
    
    selected_city = st.selectbox(
        "🏙️ Select City",
        cities,
        index=0
    )
    
    st.divider()
    
    forecast_days = st.slider(
        "📅 Forecast Period (days)",
        min_value=3,
        max_value=7,
        value=7
    )
    
    st.divider()
    
    st.subheader("📊 Quick Stats")
    current_data = data_agent.get_current_data(selected_city)
    if current_data:
        st.metric("Current AQI", f"{current_data.get('aqi', 0):.0f}")
        st.metric("Active Cases", f"{current_data.get('total_cases', 0):.0f}")
        st.metric("Temperature", f"{current_data.get('temperature', 0):.1f}°C")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Citizen Dashboard", "🏥 Hospital Dashboard", "🗺️ City Heatmap", "📱 Alerts & Notifications", "🤖 Health Assistant"])

with tab1:
    st.header(f"👥 Citizen Dashboard - {selected_city}")
    
    current_data = data_agent.get_current_data(selected_city)
    historical_df = data_agent.get_historical_data(selected_city, days=14)
    events_df = data_agent.fetch_events_data(selected_city)
    
    if not current_data:
        st.error("No data available for selected city")
    else:
        risk_info = health_index.calculate_health_risk_index(current_data, historical_df)
        spike_info = spike_agent.detect_all_spikes(historical_df)
        explanation = explanation_agent.generate_comprehensive_explanation(
            current_data, historical_df, events_df, spike_info
        )
        precautions = explanation_agent.generate_precautions(
            spike_info['overall_severity'], 
            current_data.get('aqi', 0)
        )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card risk-{risk_info['category'].lower()}">
                    <h3>Health Risk Index</h3>
                    <h1>{risk_info['emoji']} {risk_info['index']}</h1>
                    <p>{risk_info['category']} Risk</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            aqi_val = current_data.get('aqi', 0)
            aqi_category = "Good" if aqi_val < 50 else "Moderate" if aqi_val < 100 else "Poor" if aqi_val < 200 else "Very Poor" if aqi_val < 300 else "Severe"
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Air Quality Index</h3>
                    <h1>{aqi_val:.0f}</h1>
                    <p>{aqi_category}</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Active Cases</h3>
                    <h1>{current_data.get('total_cases', 0):.0f}</h1>
                    <p>+{spike_info['case_spike']['ratio']:.1f}x vs avg</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>Weather</h3>
                    <h1>{current_data.get('temperature', 0):.1f}°C</h1>
                    <p>{current_data.get('weather_condition', 'N/A')}</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 7-Day Health Weather Forecast")
            
            forecast_df = forecasting_agent.generate_comprehensive_forecast(historical_df, forecast_days)
            forecast_status = forecasting_agent.get_forecast_status()
            
            if forecast_status == "Fallback":
                st.warning("⚠️ Using simplified forecast model. Prophet ML model unavailable or insufficient data.")
            
            if not forecast_df.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['aqi_forecast'],
                    name='AQI Forecast',
                    line=dict(color='#DC2626', width=3),
                    mode='lines+markers'
                ))
                
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['cases_forecast'],
                    name='Cases Forecast',
                    yaxis='y2',
                    line=dict(color='#2563EB', width=3),
                    mode='lines+markers'
                ))
                
                fig.update_layout(
                    title='AQI & Disease Cases Forecast',
                    xaxis_title='Date',
                    yaxis_title='AQI',
                    yaxis2=dict(
                        title='Cases',
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, width='stretch')
                
                st.subheader("📊 Detailed Forecast")
                forecast_display = forecast_df.copy()
                forecast_display['date'] = forecast_display['date'].dt.strftime('%Y-%m-%d')
                forecast_display['aqi_forecast'] = forecast_display['aqi_forecast'].round(0)
                forecast_display['cases_forecast'] = forecast_display['cases_forecast'].round(0)
                st.dataframe(forecast_display, width='stretch')
        
        with col2:
            st.subheader("⚠️ Risk Explanation")
            for exp in explanation['explanations']:
                st.warning(exp)
            
            st.divider()
            
            st.subheader("✅ Precautions")
            for precaution in precautions:
                st.info(precaution)
        
        st.divider()
        
        st.subheader("📉 Historical Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                historical_df,
                x='date',
                y='aqi',
                title='AQI Trend (14 days)',
                markers=True
            )
            fig.update_traces(line_color='#DC2626')
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            fig = px.line(
                historical_df,
                x='date',
                y='total_cases',
                title='Total Cases Trend (14 days)',
                markers=True
            )
            fig.update_traces(line_color='#2563EB')
            st.plotly_chart(fig, width='stretch')

with tab2:
    st.header(f"🏥 Hospital Dashboard - {selected_city}")
    
    current_data = data_agent.get_current_data(selected_city)
    historical_df = data_agent.get_historical_data(selected_city, days=14)
    
    if not current_data:
        st.error("No data available for selected city")
    else:
        spike_info = spike_agent.detect_all_spikes(historical_df)
        forecast_df = forecasting_agent.generate_comprehensive_forecast(historical_df, forecast_days)
        forecast_status = forecasting_agent.get_forecast_status()
        
        if forecast_status == "Fallback":
            st.warning("⚠️ Using simplified forecast model. Predictions may have limited accuracy.")
        
        hospital_plan = planner_agent.generate_hospital_plan(spike_info['overall_severity'], forecast_df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Overall Risk Level",
                spike_info['overall_severity'],
                delta=f"Level {spike_info['overall_level']}"
            )
        
        with col2:
            next_24h_cases = int(forecast_df.iloc[0]['cases_forecast']) if not forecast_df.empty else 0
            st.metric(
                "Predicted Cases (24h)",
                next_24h_cases,
                delta=f"+{next_24h_cases - current_data.get('total_cases', 0):.0f}"
            )
        
        with col3:
            next_24h_hosp = int(forecast_df.iloc[0]['hosp_forecast']) if not forecast_df.empty else 0
            st.metric(
                "Predicted Hospitalizations (24h)",
                next_24h_hosp,
                delta=f"+{next_24h_hosp - current_data.get('hospitalizations', 0):.0f}"
            )
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Patient Surge Prediction")
            
            if not forecast_df.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=forecast_df['date'],
                    y=forecast_df['cases_forecast'],
                    name='Predicted Cases',
                    marker_color='#3B82F6'
                ))
                
                fig.add_trace(go.Scatter(
                    x=forecast_df['date'],
                    y=forecast_df['hosp_forecast'],
                    name='Predicted Hospitalizations',
                    line=dict(color='#DC2626', width=3),
                    mode='lines+markers',
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Cases',
                    yaxis2=dict(
                        title='Hospitalizations',
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.subheader("🚨 Spike Detection")
            
            st.metric(
                "AQI Spike",
                spike_info['aqi_spike']['severity'],
                delta=f"{spike_info['aqi_spike']['ratio']:.2f}x"
            )
            
            st.metric(
                "Cases Spike",
                spike_info['case_spike']['severity'],
                delta=f"{spike_info['case_spike']['ratio']:.2f}x"
            )
            
            st.metric(
                "Hosp. Spike",
                spike_info['hospitalization_spike']['severity'],
                delta=f"{spike_info['hospitalization_spike']['ratio']:.2f}x"
            )
        
        st.divider()
        
        st.subheader("💡 Resource Recommendations")
        
        if hospital_plan:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 👨‍⚕️ Staff Requirements")
                staff = hospital_plan['staff_requirements']
                st.metric("Nurses", f"+{staff['nurses']}")
                st.metric("Doctors", f"+{staff['doctors']}")
                st.metric("Support Staff", f"+{staff['support_staff']}")
            
            with col2:
                st.markdown("### 🏥 Resource Requirements")
                resources = hospital_plan['resource_requirements']
                st.metric("Beds", f"+{resources['beds']}")
                st.metric("Oxygen Cylinders", f"+{resources['oxygen_cylinders']}")
                st.metric("Ventilators", f"+{resources['ventilators']}")
                st.metric("PPE Kits", f"+{resources['ppe_kits']}")
            
            st.divider()
            
            st.subheader("💊 Medicine Requirements")
            medicines = hospital_plan['resource_requirements']['medicines']
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Respiratory Drugs", medicines['respiratory_drugs'])
            col2.metric("Antibiotics", medicines['antibiotics'])
            col3.metric("Antivirals", medicines['antivirals'])
            col4.metric("General Medicines", medicines['general_medicines'])
            
            st.divider()
            
            st.subheader("📋 Action Recommendations")
            for rec in hospital_plan['recommendations']:
                st.info(rec)
            
            st.divider()
            
            st.subheader("📅 Timeline & Actions")
            timeline_df = pd.DataFrame(hospital_plan['timeline'])
            st.dataframe(timeline_df, width='stretch')
            
            st.divider()
            
            st.subheader("💰 Cost Estimation")
            costs = hospital_plan['estimated_costs']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Staff Cost", f"₹{costs['staff_cost_inr']:,}")
            col2.metric("Resource Cost", f"₹{costs['resource_cost_inr']:,}")
            col3.metric("Total Estimated Cost", f"₹{costs['total_estimated_cost_inr']:,}")
            
            st.caption(f"Period: {costs['period']}")
            
            st.divider()
            
            st.subheader("✅ Plan Approval")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Accept Plan", type="primary", width='stretch'):
                    with get_db() as db:
                        new_plan = AcceptedPlan(
                            city=selected_city,
                            severity=hospital_plan['severity'],
                            plan_data=hospital_plan
                        )
                        db.add(new_plan)
                    st.success("✅ Plan accepted and saved to database!")
                    st.balloons()
            
            with col2:
                if st.button("❌ Reject Plan", width='stretch'):
                    with get_db() as db:
                        new_rejection = RejectedPlan(
                            city=selected_city,
                            severity=hospital_plan['severity'],
                            reason="Manual rejection"
                        )
                        db.add(new_rejection)
                    st.warning("❌ Plan rejected and logged")
            
            with col3:
                if st.button("📥 Download Report", width='stretch'):
                    st.info("Report download feature - Coming soon!")
            
            st.divider()
            st.subheader("✅ Accepted Plans History")
            with get_db() as db:
                recent_plans = db.query(AcceptedPlan).order_by(AcceptedPlan.timestamp.desc()).limit(10).all()
                if recent_plans:
                    for i, plan in enumerate(recent_plans):
                        st.success(f"{i+1}. {plan.city} - {plan.severity} - {plan.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.info("No plans accepted yet")

with tab3:
    st.header("🗺️ City Health Risk Heatmap")
    
    st.info("Interactive map showing health risk levels across multiple cities")
    
    try:
        all_cities_data = []
        for city in cities:
            current_data = data_agent.get_current_data(city)
            historical_df = data_agent.get_historical_data(city, days=7)
            
            if current_data:
                risk_info = health_index.calculate_health_risk_index(current_data, historical_df)
                all_cities_data.append({
                    'city': city,
                    'lat': current_data.get('latitude', 0),
                    'lon': current_data.get('longitude', 0),
                    'risk_index': risk_info['index'],
                    'category': risk_info['category'],
                    'aqi': current_data.get('aqi', 0),
                    'cases': current_data.get('total_cases', 0),
                    'color': risk_info['color']
                })
        
        if all_cities_data:
            df_map = pd.DataFrame(all_cities_data)
            
            try:
                m = folium.Map(
                    location=[df_map['lat'].mean(), df_map['lon'].mean()],
                    zoom_start=5,
                    tiles='OpenStreetMap'
                )
                
                for _, row in df_map.iterrows():
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=max(3, row['risk_index'] / 5),
                        popup=f"<b>{row['city']}</b><br>Risk: {row['risk_index']:.0f}/100<br>AQI: {row['aqi']:.0f}<br>Cases: {row['cases']:.0f}",
                        color=row['color'],
                        fill=True,
                        fillColor=row['color'],
                        fillOpacity=0.6,
                        weight=2
                    ).add_to(m)
                
                st_folium(m, width='stretch', height=600)
            except Exception as e:
                st.error(f"Map rendering error: {str(e)}")
            
            st.divider()
            
            st.subheader("📊 City Risk Comparison")
            
            fig = px.bar(
                df_map,
                x='city',
                y='risk_index',
                color='category',
                title='Health Risk Index by City',
                color_discrete_map={
                    'Severe': '#DC2626',
                    'High': '#F97316',
                    'Moderate': '#FBBF24',
                    'Low': '#10B981'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
            
            st.divider()
            
            st.subheader("📋 City Data Table")
            st.dataframe(df_map[['city', 'risk_index', 'category', 'aqi', 'cases']], width='stretch')
        else:
            st.warning("No city data available to display")
    except Exception as e:
        st.error(f"Error loading heatmap: {str(e)}")

with tab4:
    st.header("📱 Alerts & Notifications")
    
    current_data = data_agent.get_current_data(selected_city)
    historical_df = data_agent.get_historical_data(selected_city, days=7)
    
    if current_data:
        risk_info = health_index.calculate_health_risk_index(current_data, historical_df)
        spike_info = spike_agent.detect_all_spikes(historical_df)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📲 Citizen Alert (SMS/WhatsApp)")
            
            citizen_alert = f"""
🚨 HEALTH ALERT - {selected_city.upper()}

Health Risk: {risk_info['emoji']} {risk_info['category']} ({risk_info['index']}/100)

Current Conditions:
• AQI: {current_data.get('aqi', 0):.0f} ({spike_info['aqi_spike']['severity']})
• Temperature: {current_data.get('temperature', 0):.1f}°C
• Active Cases: {current_data.get('total_cases', 0):.0f}

TAKE ACTION:
• Stay indoors if possible
• Wear N95 masks outside
• Keep windows closed
• Avoid outdoor exercise

Stay safe!
- Health Dept, {selected_city}
            """
            
            st.text_area("Alert Message", citizen_alert, height=300)
            
            if st.button("📤 Send to Citizens", type="primary"):
                with get_db() as db:
                    new_alert = AlertSent(
                        alert_type='Citizen',
                        city=selected_city,
                        severity=risk_info['category'],
                        message=citizen_alert,
                        recipients_count=50000,
                        delivery_status='simulated'
                    )
                    db.add(new_alert)
                st.success(f"✅ Alert sent to 50,000+ citizens in {selected_city}!")
                st.balloons()
        
        with col2:
            st.subheader("🏥 Hospital Alert")
            
            forecast_df = forecasting_agent.generate_comprehensive_forecast(historical_df, 3)
            next_24h_cases = int(forecast_df.iloc[0]['cases_forecast']) if not forecast_df.empty else 0
            next_24h_hosp = int(forecast_df.iloc[0]['hosp_forecast']) if not forecast_df.empty else 0
            
            hospital_alert = f"""
🏥 HOSPITAL PREPAREDNESS ALERT

City: {selected_city}
Risk Level: {spike_info['overall_severity']}

24-Hour Forecast:
• Expected Cases: {next_24h_cases}
• Expected Admissions: {next_24h_hosp}

Recommended Actions:
• Increase staff on duty
• Prepare {next_24h_hosp} additional beds
• Stock oxygen & medicines
• Activate emergency protocols

Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            st.text_area("Hospital Alert", hospital_alert, height=300)
            
            if st.button("📤 Send to Hospitals"):
                with get_db() as db:
                    new_alert = AlertSent(
                        alert_type='Hospital',
                        city=selected_city,
                        severity=spike_info['overall_severity'],
                        message=hospital_alert,
                        recipients_count=20,
                        delivery_status='simulated'
                    )
                    db.add(new_alert)
                st.success(f"✅ Alert sent to all hospitals in {selected_city}!")
        
        st.divider()
        
        st.subheader("📊 Alert Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with get_db() as db:
            total_alerts = db.query(AlertSent).count()
            citizen_alerts = db.query(AlertSent).filter(AlertSent.alert_type == 'Citizen').count()
            hospital_alerts = db.query(AlertSent).filter(AlertSent.alert_type == 'Hospital').count()
        
        col1.metric("Total Alerts Sent", total_alerts)
        col2.metric("Citizen Alerts", citizen_alerts)
        col3.metric("Hospital Alerts", hospital_alerts)
        
        if total_alerts > 0:
            st.divider()
            st.subheader("📜 Alert History")
            
            with get_db() as db:
                alerts = db.query(AlertSent).order_by(AlertSent.timestamp.desc()).limit(20).all()
                alerts_data = [{
                    'Type': a.alert_type,
                    'City': a.city,
                    'Severity': a.severity,
                    'Timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'Recipients': a.recipients_count,
                    'Status': a.delivery_status
                } for a in alerts]
                alerts_df = pd.DataFrame(alerts_data)
                st.dataframe(alerts_df, width='stretch')

with tab5:
    st.header("🤖 Health Assistant Bot")
    st.markdown("**Get personalized health guidance from our AI health assistant**")
    
    # Get current data for this tab
    tab5_current_data = data_agent.get_current_data(selected_city)
    
    st.markdown("""
    <style>
    .chat-message {
        margin: 12px 0;
        padding: 16px;
        border-radius: 12px;
        line-height: 1.6;
        font-size: 15px;
    }
    .bot-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        border-left: 5px solid #667eea;
        color: #1e293b;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 40px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat with MedAssist AI")
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history in a scrollable area
        if len(st.session_state.chat_history) > 0:
            for msg in st.session_state.chat_history:
                if msg["role"] == "bot":
                    st.markdown(f'<div class="chat-message bot-message">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message user-message">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.info("👋 Start by typing a health question or clicking quick questions on the right!")
        
        st.divider()
        
        # Input area
        user_input = st.text_input("Type your health question or symptom...", placeholder="e.g., I have a headache and fever", key="user_input")
        
        col_send, col_clear = st.columns([4, 1])
        with col_send:
            if st.button("📤 Send", width='stretch'):
                if user_input.strip():
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    bot_response = generate_health_response(user_input, tab5_current_data if tab5_current_data else {})
                    st.session_state.chat_history.append({"role": "bot", "content": bot_response})
                    st.rerun()
        
        with col_clear:
            if st.button("🗑️", width='stretch'):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        st.subheader("⚡ Quick Questions")
        
        quick_questions = [
            "What are common COVID symptoms?",
            "How to protect from air pollution?",
            "When should I see a doctor?",
            "What's a healthy AQI level?",
            "Tips for flu prevention?",
            "How to manage allergies?"
        ]
        
        for q in quick_questions:
            if st.button(q, width='stretch'):
                st.session_state.chat_history.append({"role": "user", "content": q})
                bot_response = generate_health_response(q, tab5_current_data if tab5_current_data else {})
                st.session_state.chat_history.append({"role": "bot", "content": bot_response})
                st.rerun()
        
        st.divider()
        
        st.subheader("📋 Health Tips")
        tips = [
            "✓ Wear N95 masks in high pollution",
            "✓ Stay hydrated daily",
            "✓ Exercise for 30 mins",
            "✓ Get 7-8 hours sleep",
            "✓ Avoid crowded places when sick"
        ]
        for tip in tips:
            st.caption(tip)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.info("🤖 **Powered by Agentic AI**\n\n6 autonomous agents working 24/7 to keep you safe")

with col2:
    st.success("📊 **Real-Time Data**\n\nAQI, Weather, and Epidemic data updated continuously")

with col3:
    st.warning("⚡ **Early Warnings**\n\nPredict health risks 3-7 days in advance")

st.caption("© 2025 AI Health Risk Prediction System | Developed for Healthtech Innovation")
