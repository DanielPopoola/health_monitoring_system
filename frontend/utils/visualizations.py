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
    if df.empty:
        st.warning("No spo2 data available")
        return
    
    latest_value = df['value'].iloc[-1]

    if latest_value < 90:
        color = 'red'
    elif latest_value < 94:
        color = 'yellow'
    else:
        color = 'green'

    fig = go.Figure(go.Pie(
        labels=["Oxygen Level", "Remaining"],
        values=[latest_value, 100 - latest_value],
        hole=0.5,
        textinfo="percent",
        textfont=dict(size=24, color="white"),
        marker=dict(colors=[color, "lightgray"]),
        rotation=90,
        showlegend=False
    ))
     # Add title and adjust layout
    fig.update_layout(
        title=f"SPO2 Level: {latest_value}%",
        height=350,
        margin=dict(t=40, b=0, l=0, r=0)
    )

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)

def plot_daily_steps(df):
    if df.empty:
        st.warning("No daily steps data available")
        return
    
    fig = px.bar(df, 
                x='timestamp',
                 y='count',
                labels={'timestamp': 'Date', 'count': 'Steps Count'},
                title="Daily Steps Over Time")
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)