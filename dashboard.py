import streamlit as st
from supabase import create_client, Client

def show_dashboard(supabase: Client):
    st.title("Dashboard")
    st.write("Welcome to the QTrackPro dashboard!")

    # Fetch all parts for the current company
    company_id = st.session_state.get('company_id')
    if not company_id:
        st.error("No company selected.")
        return

    parts_result = supabase.table("parts").select("part_number,description,customer").eq("company_id", company_id).execute()
    all_parts = {part['part_number']: {'description': part['description'], 'customer': part['customer']} for part in parts_result.data}

    # Reworked Part Entry
    st.subheader("Enter Reworked Part")
    with st.form("rework_entry"):
        # Autocomplete for part number
        part_number = st.selectbox(
            "Part Number",
            options=list(all_parts.keys()),
            key="part_number_select"
        )

        # Display part description and customer
        if part_number:
            st.write(f"Description: {all_parts[part_number]['description']}")
            st.write(f"Customer: {all_parts[part_number]['customer']}")

        quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
        
        # Updated rework types
        rework_types = [
            "LASER - REMAKE",
            "LASER - SCRAP",
            "FOD - MISSING PART",
            "FOD - REWORK",
            "PRESS BREAK - REMAKE",
            "PRESS BREAK - SCRAP",
            "PRESS BREAK - PART PROOFING",
            "FOD2 - NON-CONFROMACE",
            "FOD2 - MISSING PART"
        ]
        rework_type = st.selectbox("Rework Type", rework_types)
        
        notes = st.text_area("Notes")
        
        submit_button = st.form_submit_button("Submit Rework")
        
        if submit_button:
            if part_number and quantity > 0:
                try:
                    result = supabase.table("rework_parts").insert({
                        "part_number": part_number,
                        "part_description": all_parts[part_number]['description'],
                        "customer": all_parts[part_number]['customer'],
                        "quantity": quantity,
                        "rework_type": rework_type,
                        "notes": notes,
                        "company_id": company_id
                    }).execute()
                    
                    if result.data:
                        st.success(f"Rework entry for {quantity} {part_number}(s) submitted successfully!")
                    else:
                        st.error("Failed to submit rework entry. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.warning("Please enter a valid part number and quantity.")

    # Add more dashboard content here