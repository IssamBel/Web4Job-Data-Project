
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

st.set_page_config(page_title="Nigerian E-Commerce ETL Dashboard", layout="centered")
st.markdown("""
    <h1 style='text-align: center;'>🇳🇬 Nigerian E-Commerce ETL & Insights Platform</h1>
    <br>
""", unsafe_allow_html=True)

if 'df' not in st.session_state:
    st.session_state.df = None

page = st.sidebar.radio("📚 Navigate", ["Upload File", "Business Insights", "Load to SQL", "Visualization"])

if page == "Upload File":
    st.markdown("<h3 style='text-align: center;'>📤 Step 1: Upload Raw CSV/XLSX File</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your raw sales file (CSV, XLSX, TXT)", type=['csv', 'xlsx', 'xls', 'txt'])
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        try:
            if file_ext in ['xlsx', 'xls']:
                import openpyxl
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            elif file_ext == 'txt':
                df = pd.read_csv(uploaded_file, sep='\t')
            else:
                df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            df = None

        if df is not None:
            st.markdown("<h3 style='text-align: center;'>🧹 Step 2: Data Cleaning and Transformation</h3>", unsafe_allow_html=True)
            df.drop_duplicates(inplace=True)
            df.fillna(0, inplace=True)

            if 'Item Price' in df.columns and 'Quantity' in df.columns:
                df['Item Price'] = pd.to_numeric(df['Item Price'], errors='coerce').fillna(0)
                df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
                df['Total'] = df['Item Price'] * df['Quantity']

            if 'Order Date' in df.columns:
                df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')

            st.session_state.df = df
            st.success("✅ File cleaned and stored. Now proceed to 'Business Insights' tab.")

            clean_filename = uploaded_file.name.rsplit('.', 1)[0] + "_cleaned.csv"
            st.download_button("⬇️ Download Cleaned File", df.to_csv(index=False).encode('utf-8'), file_name=clean_filename, mime='text/csv')

elif page == "Business Insights":
    st.markdown("<h3 style='text-align: center;'>📊 Step 3: Business Insights</h3>", unsafe_allow_html=True)
    df = st.session_state.get('df', None)
    if df is not None and 'Total' in df.columns:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Sales", f"₦{df['Total'].sum():,.2f}")
        with col2:
            st.metric("📦 Total Orders", df['Order ID'].nunique())
        with col3:
            top_item = df.groupby('Item Name')['Total'].sum().idxmax()
            st.metric("🏆 Top Item", top_item)

        st.markdown("---")
        st.markdown("### 🧮 Additional Insights")

        top_branch = df.groupby('Branch Name')['Total'].sum().idxmax()
        top_region = df.groupby('Order Region')['Total'].sum().idxmax()
        avg_order_value = df['Total'].sum() / df['Order ID'].nunique()

        st.write(f"🔝 **Top Performing Branch**: {top_branch}")
        st.write(f"🌍 **Top Sales Region**: {top_region}")
        st.write(f"📊 **Average Order Value**: ₦{avg_order_value:,.2f}")

        monthly_sales = df.groupby(df['Order Date'].dt.to_period('M'))['Total'].sum().reset_index()
        monthly_sales['Order Date'] = monthly_sales['Order Date'].astype(str)
        fig = px.line(monthly_sales, x='Order Date', y='Total', title='📅 Monthly Sales Trend')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Please upload and clean data first.")

elif page == "Load to SQL":
    st.markdown("<h3 style='text-align: center;'>🗃️ Step 4: Load Data into Local PostgreSQL</h3>", unsafe_allow_html=True)
    df = st.session_state.get('df', None)
    if df is not None:
        db_user = st.text_input("PostgreSQL Username", "postgres")
        db_pass = st.text_input("PostgreSQL Password", type="password")
        db_name = st.text_input("Database Name", "ecommercedb")
        db_host = st.text_input("Host", "localhost")
        db_port = st.text_input("Port", "5432")

        if st.button("🚀 Load into PostgreSQL"):
            try:
                engine = create_engine(f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')
                df.to_sql('ecommerce_sales', engine, if_exists='replace', index=False)
                st.success("✅ Data loaded into PostgreSQL successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ Please upload and clean data first.")

elif page == "Visualization":
    st.markdown("<h3 style='text-align: center;'>📈 Step 5: Custom Visualization</h3>", unsafe_allow_html=True)
    df = st.session_state.get('df', None)
    if df is not None:
        chart_type = st.selectbox("Choose chart type", ["Line", "Bar", "Pie"])

        x_axis = st.selectbox("Select X-axis", options=df.columns)
        y_axis = st.selectbox("Select Y-axis", options=df.columns)

        if chart_type == "Line":
            fig = px.line(df, x=x_axis, y=y_axis, title=f"📈 Line Chart: {y_axis} over {x_axis}")
        elif chart_type == "Bar":
            fig = px.bar(df, x=x_axis, y=y_axis, title=f"📊 Bar Chart: {y_axis} by {x_axis}")
        elif chart_type == "Pie":
            fig = px.pie(df, names=x_axis, values=y_axis, title=f"🥧 Pie Chart: {y_axis} distribution by {x_axis}")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Please upload and clean data first.")
