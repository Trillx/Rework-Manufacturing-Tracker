import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# Import custom modules
from auth import login, get_company_info
from company import manage_companies
from dashboard import show_dashboard
from part import manage_parts
from rework import manage_rework

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="QTrackPro", page_icon="🏭", layout="wide")
    st.sidebar.title("QTrackPro")

    # Initialize session state variables
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'company_id' not in st.session_state:
        st.session_state.company_id = None
    if 'company_name' not in st.session_state:
        st.session_state.company_name = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Create placeholders for each page
    dashboard_placeholder = st.empty()
    parts_placeholder = st.empty()
    rework_placeholder = st.empty()

    # Handle user authentication and app flow
    if st.session_state.user is None:
        login(supabase)
    else:
        st.sidebar.write(f"Welcome, {st.session_state.user.email}!")
        
        if st.session_state.company_id is None:
            with st.container():
                manage_companies(supabase)
        else:
            st.sidebar.write(f"Current company: {st.session_state.company_name}")
            if st.sidebar.button("Change Company"):
                st.session_state.company_id = None
                st.session_state.company_name = None
                st.experimental_rerun()
            else:
                pages = ["Dashboard", "Manage Parts", "Manage Rework"]
                st.session_state.current_page = st.sidebar.radio("Go to", pages, index=pages.index(st.session_state.current_page))

                if st.session_state.current_page == "Dashboard":
                    with dashboard_placeholder.container():
                        show_dashboard(supabase)
                elif st.session_state.current_page == "Manage Parts":
                    with parts_placeholder.container():
                        manage_parts(supabase)
                elif st.session_state.current_page == "Manage Rework":
                    with rework_placeholder.container():
                        manage_rework(supabase)

        if st.sidebar.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.company_id = None
            st.session_state.company_name = None
            st.session_state.current_page = "Dashboard"
            st.experimental_rerun()

if __name__ == "__main__":
    main()