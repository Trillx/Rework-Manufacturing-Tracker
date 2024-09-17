import streamlit as st
from supabase import create_client, Client

def manage_companies(supabase: Client):
    st.title("Your Companies")

    # Get the current user
    user = supabase.auth.get_user()

    if user is None:
        st.error("You must be logged in to view companies.")
        return

    try:
        # Get companies associated with the user
        company_users = supabase.table("company_users")\
            .select("company_id")\
            .eq("user_id", user.user.id)\
            .execute()

        if company_users.data:
            company_ids = [cu['company_id'] for cu in company_users.data]
            companies = supabase.table("companies")\
                .select("*")\
                .in_("id", company_ids)\
                .execute()

            if companies.data:
                for company in companies.data:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{company['name']}**")
                    with col2:
                        if st.button(f"Select", key=company['id']):
                            st.session_state.company_id = company['id']
                            st.session_state.company_name = company['name']
                            st.success(f"Selected company: {company['name']}")
                            st.experimental_rerun()  # Changed from st.rerun()
            else:
                st.info("No companies found.")
        else:
            st.info("You are not associated with any companies.")
    except Exception as e:
        st.error(f"Error fetching companies: {str(e)}")

def add_user_to_company(supabase):
    st.subheader("Add User to Company")
    
    # Fetch companies where the current user is an admin
    admin_companies = supabase.table("company_users").select("company_id").eq("user_id", st.session_state.user.id).eq("role", "admin").execute()
    admin_company_ids = [ac['company_id'] for ac in admin_companies.data]
    admin_companies_data = supabase.table("companies").select("*").in_("id", admin_company_ids).execute()
    
    with st.form("add_user_to_company"):
        email = st.text_input("User Email")
        company = st.selectbox("Company", [company['name'] for company in admin_companies_data.data])
        role = st.selectbox("Role", ["admin", "user"])
        
        if st.form_submit_button("Add User"):
            # Find the user by email
            user = supabase.table("users").select("id").eq("email", email).execute()
            if user.data:
                user_id = user.data[0]['id']
                company_id = next(c['id'] for c in admin_companies_data.data if c['name'] == company)
                
                # Add user-company relationship
                result = supabase.table("company_users").insert({
                    "user_id": user_id,
                    "company_id": company_id,
                    "role": role
                }).execute()
                
                if result.data:
                    st.success(f"User {email} added to {company} as {role}")
                else:
                    st.error("Failed to add user to company")
            else:
                st.error("User not found")