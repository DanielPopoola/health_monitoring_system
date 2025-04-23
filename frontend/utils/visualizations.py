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