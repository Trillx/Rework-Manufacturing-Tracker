from gotrue.errors import AuthApiError
import streamlit as st
from supabase import create_client, Client
from postgrest.exceptions import APIError
import time  # Add this line

def login(supabase: Client):
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = response.user
            st.success("Logged in successfully!")
            st.rerun()  # Changed from st.experimental_rerun()
        except Exception as e:
            st.error(f"Error logging in: {str(e)}")

def signup(supabase: Client):
    st.subheader("Sign Up")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    company = st.text_input("Company Name", key="signup_company")
    col1, col2 = st.columns(2)
    with col1:
        if "last_signup_attempt" not in st.session_state:
            st.session_state.last_signup_attempt = 0
        
        cooldown = 30  # 30 seconds cooldown
        time_since_last_attempt = time.time() - st.session_state.last_signup_attempt
        
        if time_since_last_attempt < cooldown:
            st.button("Sign Up", key="signup_button", disabled=True)
            st.write(f"Please wait {int(cooldown - time_since_last_attempt)} seconds before trying again.")
        elif st.button("Sign Up", key="signup_button"):
            st.session_state.last_signup_attempt = time.time()
            # Check if company name already exists
            existing_company = supabase.table("companies").select("*").eq("name", company).execute()
            if existing_company.data:
                st.error(f"The company name '{company}' is already taken. Please choose a different name.")
            else:
                try:
                    response = supabase.auth.sign_up({"email": email, "password": password})
                    if response.user:
                        if create_company_and_relationship(supabase, response.user.id, company):
                            st.success("Signed up successfully! Please log in.")
                        else:
                            # If company creation fails, delete the user
                            supabase.auth.admin.delete_user(response.user.id)
                            st.error("Error during company creation. Please try again.")
                    else:
                        st.error("Error during sign up")
                except AuthApiError as e:
                    error_msg = str(e)
                    if "email rate limit exceeded" in error_msg.lower():
                        st.error("Too many sign-up attempts. Please wait for 60 minutes before trying again.")
                    elif "for security purposes, you can only request this after" in error_msg.lower():
                        st.error("Please wait a few seconds before trying to sign up again.")
                    else:
                        st.error(f"An error occurred during sign up: {error_msg}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
    with col2:
        if st.button("Sign Up with Google", key="google_signup_button"):
            auth_url = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": "http://localhost:8501"  # Replace with your Streamlit app URL
                }
            })
            st.markdown(f'<a href="{auth_url.url}" target="_self">Sign Up with Google</a>', unsafe_allow_html=True)

def create_company_and_relationship(supabase: Client, user_id: str, company_name: str):
    try:
        company_result = supabase.table("companies").insert({"name": company_name}).execute()
        if company_result.data:
            supabase.table("company_users").insert({
                "user_id": user_id,
                "company_id": company_result.data[0]['id'],
                "role": "admin"
            }).execute()
            return True
        else:
            st.error("Error creating company: No data returned")
            return False
    except APIError as e:
        st.error(f"Error creating company: {str(e)}")
        return False

def get_user_role(supabase: Client, user_id: str, company_id: str):
    result = supabase.table("company_users")\
        .select("role")\
        .eq("user_id", user_id)\
        .eq("company_id", company_id)\
        .execute()
    
    if result.data:
        return result.data[0]['role']
    return None

def is_admin(supabase: Client, user_id: str, company_id: str):
    role = get_user_role(supabase, user_id, company_id)
    return role in ['admin', 'owner']

def get_company_info(supabase: Client, user_id: str):
    result = supabase.table("companies")\
        .select("companies.*")\
        .join("company_users", "companies.id", "company_users.company_id")\
        .eq("company_users.user_id", user_id)\
        .limit(1)\
        .execute()
    
    if result.data:
        return result.data[0]
    return None

def associate_user_with_company(supabase: Client, user_id: str, company_id: str):
    try:
        result = supabase.table("company_users").insert({
            "user_id": user_id,
            "company_id": company_id
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error associating user with company: {str(e)}")
        return False

def get_user_companies(supabase: Client, user_id: str):
    result = supabase.table("company_users").select("company_id").eq("user_id", user_id).execute()
    return [row['company_id'] for row in result.data]