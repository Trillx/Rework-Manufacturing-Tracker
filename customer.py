import streamlit as st

def manage_customers(supabase):
    st.header("Manage Customers")
    
    # Fetch customers for the current user's companies
    companies = supabase.table("companies").select("id").eq("owner_id", st.session_state.user.id).execute()
    company_ids = [company['id'] for company in companies.data]
    
    customers = supabase.table("customers").select("*").in_("company_id", company_ids).execute()
    
    if customers.data:
        st.subheader("Your Customers")
        for customer in customers.data:
            st.write(f"- {customer['name']}")
    
    # Add new customer
    st.subheader("Add New Customer")
    with st.form("add_customer"):
        customer_name = st.text_input("Customer Name")
        company = st.selectbox("Company", [company['name'] for company in companies.data])
        if st.form_submit_button("Add Customer"):
            company_id = next(c['id'] for c in companies.data if c['name'] == company)
            result = supabase.table("customers").insert({
                "name": customer_name,
                "company_id": company_id
            }).execute()
            if result.data:
                st.success("Customer added successfully!")
            else:
                st.error("Failed to add customer.")