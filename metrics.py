import streamlit as st
import plotly.express as px

def show_metrics(supabase):
    st.header("Metrics")

    # Fetch companies for the current user
    companies = supabase.table("companies").select("id").eq("owner_id", st.session_state.user.id).execute()
    company_ids = [company['id'] for company in companies.data]

    # Fetch rework data for the user's companies
    rework_data = supabase.table("rework_parts").select("*").in_("company_id", company_ids).execute()

    if rework_data.data:
        # Rework types distribution
        rework_types = [item['rework_type'] for item in rework_data.data]
        fig_rework_types = px.pie(names=rework_types, title="Rework Types Distribution")
        st.plotly_chart(fig_rework_types)

        # Reworks by customer
        customer_reworks = {}
        for item in rework_data.data:
            customer_reworks[item['customer']] = customer_reworks.get(item['customer'], 0) + 1
        fig_customer_reworks = px.bar(
            x=list(customer_reworks.keys()),
            y=list(customer_reworks.values()),
            title="Reworks by Customer"
        )
        fig_customer_reworks.update_xaxes(title="Customer")
        fig_customer_reworks.update_yaxes(title="Number of Reworks")
        st.plotly_chart(fig_customer_reworks)

        # Reworks over time
        rework_dates = [item['created_at'] for item in rework_data.data]
        fig_reworks_over_time = px.histogram(x=rework_dates, title="Reworks Over Time")
        fig_reworks_over_time.update_xaxes(title="Date")
        fig_reworks_over_time.update_yaxes(title="Number of Reworks")
        st.plotly_chart(fig_reworks_over_time)
    else:
        st.info("No rework data available yet.")