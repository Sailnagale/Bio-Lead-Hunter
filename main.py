import streamlit as st
import pandas as pd
import time


from modules.enrichment import check_scientific_intent, check_funding_signal, get_linkedin_data, discover_new_leads
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
    **Developed by:** ### 👨‍💻 Sail Nagale  
    *VIT Pune | Research Intern*
    """)
    
    st.divider()
    st.info("💡 **New Feature:** Auto-Discovery Mode is now active. No CSV required.")
    st.caption("v2.1 | Science-First Architecture")


st.markdown("""
    <h2 style='color: #2E86C1;'>🧬 3D In-Vitro Model Intelligence</h2>
""", unsafe_allow_html=True)


if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None

tab1, tab2 = st.tabs(["🔍 Option A: Auto-Discovery (Recommended)", "📂 Option B: Upload CSV"])

input_df = None
start_processing = False


with tab1:
    st.markdown("Enter a target audience (e.g., 'Director of Toxicology'), and the Agent will find relevant people.")
    
    c1, c2 = st.columns(2)
    with c1:
        role_input = st.text_input("Target Role", "Director of Toxicology")
    with c2:
        loc_input = st.text_input("Target Location", "Boston, MA")
    
    if st.button("🕵️‍♂️ Find & Rank Leads", type="primary"):
        with st.spinner(f"Scanning for '{role_input}' in '{loc_input}'..."):
            
           
            discovered_data, is_science_fallback = discover_new_leads(role_input, loc_input)
            
            if discovered_data:
                input_df = pd.DataFrame(discovered_data)
                
               
                if is_science_fallback:
                    st.info(f"ℹ️ **Note:** Cloud IP blocking detected on Google Search. Switched to **Science-First Discovery** (OpenAlex API) to find active researchers publishing on '{role_input}'.")
                else:
                    st.success(f"✅ Found {len(input_df)} leads via Web Scraping! Starting enrichment...")
                
                start_processing = True
            else:
                st.error("No leads found. Please try a broader query (e.g., 'Scientist' instead of 'Senior Scientist').")


with tab2:
    uploaded_file = st.file_uploader("Upload CSV File", type="csv")
    if uploaded_file:
        input_df = pd.read_csv(uploaded_file)
        st.dataframe(input_df.head(), use_container_width=True)
        if st.button("🚀 Process Uploaded List"):
            start_processing = True


if start_processing and input_df is not None:
    
    st.divider()
    st.write("### ⚙️ Agent Processing...")
    
   
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    df = input_df.copy()
    
  
    for col in ['Has_Recent_Paper', 'Paper_Count', 'Recent_Funding', 'Score']:
        if col not in df.columns:
            df[col] = None

  
    total_rows = len(df)
    for index, row in df.iterrows():
       
        status_text.markdown(f"**Enriching Lead {index+1}/{total_rows}:** `{row['Name']}` @ *{row['Company']}*")
        
       
        keyword_search = "toxicity" if "toxicity" in role_input.lower() else role_input
        has_paper, count, titles = check_scientific_intent(row['Name'], keyword=keyword_search)
        
        df.at[index, 'Has_Recent_Paper'] = has_paper
        df.at[index, 'Paper_Count'] = count
        
       
        has_funding, snippet = check_funding_signal(row['Company'])
        df.at[index, 'Recent_Funding'] = has_funding
        
       
        if "csv" in str(uploaded_file): 
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
    
    st.divider()
    
   
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Total Leads", len(df))
    with m2: st.metric("🔥 Hot Leads (>60)", len(df[df['Score'] >= 60]))
    with m3: st.metric("🔬 Researchers", len(df[df['Has_Recent_Paper'] == True]))
    
    st.write("") 

    
    st.subheader("🎯 Ranked Lead Dashboard")
    
   
    display_cols = ['Score', 'Name', 'Title', 'Company', 'Location', 'Has_Recent_Paper', 'Recent_Funding']
   
    final_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(
        df[final_cols].style.background_gradient(subset=['Score'], cmap="Greens", vmin=0, vmax=100),
        use_container_width=True,
        height=500
    )
    
   
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Results CSV",
        data=csv,
        file_name="sail_nagale_leads.csv",
        mime="text/csv",
        type="primary"
    )