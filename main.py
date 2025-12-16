import streamlit as st
import pandas as pd
import time
from modules.enrichment import check_scientific_intent, check_funding_signal, get_linkedin_data
from modules.scoring import calculate_propensity_score

st.set_page_config(
    page_title="Bio-Lead Hunter | Sail Nagale",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1231/1231418.png", width=50)
    st.title("Bio-Lead Hunter")
    
    st.markdown("""
    *Developed by:* **Sail Nagale**  
    *VIT Pune | Research Intern*
    """)
    
    st.divider()
    
    st.subheader("1. Input Data")
    uploaded_file = st.file_uploader("Upload CSV File", type="csv")
    
    st.write("") 
    
    run_btn = st.button("🚀 Run Enrichment Agent", type="primary", use_container_width=True)
    
    st.divider()
    st.caption("v1.3.1 | 3D In-Vitro Intelligence")

st.markdown("""
    <h2 style='color: #2E86C1;'>🧬 3D In-Vitro Model Intelligence</h2>
""", unsafe_allow_html=True)

if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None

if uploaded_file:
    input_df = pd.read_csv(uploaded_file)
    
    st.subheader("Data Preview")
    st.dataframe(input_df.head(), use_container_width=True)
    st.divider()
    
    if run_btn:
        st.write("### ⚙️ Agent Processing...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        df = input_df.copy()
        
        required_cols = ['Has_Recent_Paper', 'Paper_Count', 'Recent_Funding', 'Score']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        total_rows = len(df)
        for index, row in df.iterrows():
            status_text.markdown(f"**Scanning:** `{row['Name']}` @ *{row['Company']}*")
            
            has_paper, count, titles = check_scientific_intent(row['Name'], keyword="toxicity")
            df.at[index, 'Has_Recent_Paper'] = has_paper
            df.at[index, 'Paper_Count'] = count
            
            has_funding, snippet = check_funding_signal(row['Company'])
            df.at[index, 'Recent_Funding'] = has_funding
            
            linkedin_data = get_linkedin_data(row['Name'], row['Company'])
            if linkedin_data.get('city') and linkedin_data.get('city') != "Unknown":
                df.at[index, 'Location'] = linkedin_data['city']
            if linkedin_data.get('role') and linkedin_data.get('role') != "Not Found":
                df.at[index, 'Title'] = linkedin_data['role']
            
            progress_bar.progress((index + 1) / total_rows)

        df['Score'] = df.apply(calculate_propensity_score, axis=1)
        df = df.sort_values(by='Score', ascending=False)
        
        st.session_state.processed_df = df
        
        status_text.empty()
        progress_bar.empty()
        st.success("✅ Analysis Complete!")

    if st.session_state.processed_df is not None:
        df = st.session_state.processed_df
        
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Total Leads", len(df))
        with m2: st.metric("🔥 Hot Leads (>60)", len(df[df['Score'] >= 60]))
        with m3: st.metric("🔬 Researchers", len(df[df['Has_Recent_Paper'] == True]))

        st.divider()

        search_query = st.text_input("🔍 Filter Results", placeholder="Search by Name, Company, or Location...")
        
        if search_query:
            filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
        else:
            filtered_df = df

        display_cols = ['Score', 'Name', 'Title', 'Company', 'Location', 'Has_Recent_Paper', 'Recent_Funding']
        
        st.dataframe(
            filtered_df[display_cols].style.background_gradient(subset=['Score'], cmap="Greens", vmin=0, vmax=100),
            use_container_width=True,
            height=500
        )
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name="sail_nagale_leads.csv",
            mime="text/csv",
            type="primary"
        )

else:
    st.info("👈 Please upload a CSV file in the sidebar to begin.")
    st.markdown("#### Expected Format:")
    st.code("Name, Company, Title, Location", language="csv")