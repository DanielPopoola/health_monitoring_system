import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def plot_heart_rate(df):
    if df.empty:
        st.warning("No heart rate data available")
        return
    
    fig = px.line(
        df,
        x='timestamp',
        y='value',
        title='Heart Rate Over Time',
        labels={'value': 'BPM', 'timestamp': 'Time'}
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def plot_blood_pressure(df):
    if df.empty:
        st.warning("No blood pressure data available")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['systolic'],
        name='Systolic',
        line=dict(color='red')
    ))
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['diastolic'],
        name='Diastolic',
        line=dict(color='blue')
    ))
    fig.update_layout(
        title='Blood Pressure Over Time',
        xaxis_title='Time',
        yaxis_title='mmHg',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_spo2_gauge(df):
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=df['value'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Oxygen level (%)", 'font': {'size':24}},
        gauge={
            'axis':{'range':[0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "blue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 89], 'color': '#ff6b6b'},  # Critical
                {'range': [90, 94], 'color': '#ffe66d'},    # Low-normal
                {'range': [95, 100], 'color': '#4ecdc4'}    # Healthy
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': df['value']
            }
        }
    ))

    fig.update_layout(height=350, margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)