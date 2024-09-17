import streamlit as st
import pandas as pd
from supabase import create_client, Client
from auth import is_admin

def manage_parts(supabase: Client):
    st.title("Manage Parts")

    user = supabase.auth.get_user()
    if not user:
        st.error("You must be logged in to manage parts.")
        return

    company_id = st.session_state.get('company_id')
    if not company_id:
        st.error("No company selected.")
        return

    # Specify the columns we want to work with
    db_columns = ["customer", "part_number", "description"]

    if is_admin(supabase, user.user.id, company_id):
        st.subheader("Admin Options")
        
        # CSV Upload
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            # Read CSV file, skipping empty columns
            df = pd.read_csv(uploaded_file, usecols=lambda x: x.strip() != '')
            st.write("Preview of uploaded data:")
            st.dataframe(df.head())

            # Column mapping
            st.subheader("Map CSV columns to database fields")
            column_mapping = {}
            for db_col in db_columns:
                column_mapping[db_col] = st.selectbox(f"Select column for {db_col}", [""] + list(df.columns), key=db_col)

            if st.button("Upload Parts"):
                mapped_df = df.rename(columns={v: k for k, v in column_mapping.items() if v})
                total_rows = len(mapped_df)
                
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                error_count = 0
                for index, row in mapped_df.iterrows():
                    try:
                        # Ensure all required fields are present and not empty
                        part_data = {k: v.strip() if isinstance(v, str) else v for k, v in row.to_dict().items() if k in db_columns and pd.notna(v)}
                        if all(field in part_data for field in db_columns):
                            part_data["company_id"] = company_id
                            result = supabase.table("parts").insert(part_data).execute()
                            if result.data:
                                success_count += 1
                            else:
                                error_count += 1
                                st.error(f"Failed to insert row: {part_data}")
                        else:
                            error_count += 1
                            st.warning(f"Skipped row due to missing required fields: {row.to_dict()}")
                    except Exception as e:
                        error_count += 1
                        st.error(f"Error inserting row: {str(e)}")
                    
                    # Update progress bar and status text
                    progress = (index + 1) / total_rows
                    progress_bar.progress(progress)
                    status_text.text(f"Processed {index + 1} of {total_rows} rows")
                
                progress_bar.empty()
                status_text.empty()
                st.success(f"Upload complete. Successfully inserted {success_count} parts. Encountered {error_count} errors.")

    # Display all parts in table format
    st.subheader("All Parts")
    parts = supabase.table("parts").select(",".join(db_columns + ["company_id"])).eq("company_id", company_id).execute()
    if parts.data:
        df_parts = pd.DataFrame(parts.data)
        
        # Allow sorting
        sort_column = st.selectbox("Sort by", db_columns)
        sort_order = st.radio("Sort order", ["Ascending", "Descending"])
        df_parts = df_parts.sort_values(by=sort_column, ascending=(sort_order == "Ascending"))
        
        # Allow filtering
        filter_column = st.selectbox("Filter by", ["None"] + db_columns)
        if filter_column != "None":
            filter_value = st.text_input("Filter value")
            if filter_value:
                df_parts = df_parts[df_parts[filter_column].astype(str).str.contains(filter_value, case=False)]
        
        # Display the table
        st.dataframe(df_parts[db_columns])
        
        # Download CSV option
        csv = df_parts[db_columns].to_csv(index=False)
        st.download_button(
            label="Download parts as CSV",
            data=csv,
            file_name="parts.csv",
            mime="text/csv",
        )
    else:
        st.info("No parts found for this company.")