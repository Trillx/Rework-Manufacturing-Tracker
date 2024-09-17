import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from auth import is_admin

def manage_rework(supabase: Client):
    st.title("Manage Rework Parts")

    user = supabase.auth.get_user()
    if not user:
        st.error("You must be logged in to manage rework parts.")
        return

    company_id = st.session_state.get('company_id')
    if not company_id:
        st.error("No company selected.")
        return

    # Fetch rework data
    rework_data = supabase.table("rework_parts").select("*").eq("company_id", company_id).execute()
    
    if rework_data.data:
        df_rework = pd.DataFrame(rework_data.data)
        
        # Display metrics
        st.subheader("Rework Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Reworks", len(df_rework))
        with col2:
            st.metric("Total Quantity Reworked", df_rework['quantity'].sum())
        with col3:
            st.metric("Unique Parts Reworked", df_rework['part_number'].nunique())

        # Rework types distribution
        st.subheader("Rework Types Distribution")
        fig_rework_types = px.pie(df_rework, names='rework_type', title="Rework Types")
        st.plotly_chart(fig_rework_types)

        # Reworks over time
        st.subheader("Reworks Over Time")
        df_rework['created_at'] = pd.to_datetime(df_rework['created_at'])
        fig_reworks_over_time = px.line(df_rework.groupby('created_at').size().reset_index(name='count'), 
                                        x='created_at', y='count', title="Reworks Over Time")
        st.plotly_chart(fig_reworks_over_time)

        # Display table of all reworked parts
        st.subheader("All Reworked Parts")
        
        # Allow sorting
        sort_column = st.selectbox("Sort by", df_rework.columns)
        sort_order = st.radio("Sort order", ["Ascending", "Descending"])
        df_rework = df_rework.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))
        
        # Allow filtering
        filter_column = st.selectbox("Filter by", ["None"] + list(df_rework.columns))
        if filter_column != "None":
            filter_value = st.text_input("Filter value")
            if filter_value:
                df_rework = df_rework[df_rework[filter_column].astype(str).str.contains(filter_value, case=False)]
        
        # Display the table
        st.dataframe(df_rework)
        
        # Download CSV option
        csv = df_rework.to_csv(index=False)
        st.download_button(
            label="Download rework data as CSV",
            data=csv,
            file_name="rework_data.csv",
            mime="text/csv",
        )
    else:
        st.info("No rework data found for this company.")

    if is_admin(supabase, user.user.id, company_id):
        st.subheader("Admin Options")
        # Add any additional admin-specific options here
    else:
        st.subheader("User Options")
        # Add any additional user-specific options here