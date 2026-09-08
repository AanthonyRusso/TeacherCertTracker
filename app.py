import streamlit as st
import pandas as pd
from datetime import date
import utils
import qtpy
import PyQt5

import db

st.set_page_config(page_title="Certification Reminder", layout="wide")

db.create_database()

st.title("Teacher Certification Reminder")

top_left, top_right = st.columns([3, 1])

with top_right:
    csv_name = st.text_input("CSV name", value="teachers", label_visibility="collapsed")
    export_col, import_col = st.columns(2)

    with export_col:
        if st.button("Export CSV", use_container_width=True):
            try:
                db.export_to_csv(csv_name)
                st.success(f"Exported to {csv_name}.csv")
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    with import_col:
        if st.button("Import CSV", use_container_width=True):
            try:
                db.import_from_csv(csv_name)
                st.success(f"Imported from {csv_name}.csv")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
                


with st.expander("Add a teacher", expanded=False):
    with st.form("add_teacher_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("Name")
        email = col2.text_input("Email")
        due_date = col3.date_input("Certification due date", value=date.today())
        submitted = st.form_submit_button("Add teacher")

        if submitted:
            if not name or not email:
                st.error("Name and email are required")
            else:
                try:
                    db.add_teacher(name, email, due_date.isoformat())
                except Exception as e:
                    st.error(f"Could not add teacher: {e}")

def reminder_status(row, due_ids):
    if row["id"] in due_ids:
        return f"Due now ({due_ids[row['id']].replace('_', ' ')})"
    d = date.fromisoformat(row["due_date"])
    days_left = (d - date.today()).days
    if days_left < 0:
        return f"Overdue by {abs(days_left)} days"
    return f"{days_left} days left"

teachers = db.get_all_teachers()
due_ids = db.get_teachers_due_for_reminders()

st.subheader("Teachers")

if not teachers:
    st.info("No teachers have beena added")

else:
    df = pd.DataFrame(dict(t) for t in teachers)
    df["status"] = [reminder_status(t, due_ids) for t in teachers]

    df = df.rename(columns = {  
        "id": "ID",
        "name": "Name",
        "email": "Email",
        "due_date": "Due Date",
        "status": "Status",
        "reminder_3_month_sent": "3mo Sent",
        "reminder_1_month_sent": "1mo Sent",
        "reminder_1_week_sent": "1wk Sent",
        "reminder_2_week_after_sent": "2wk-after Sent"
    })

    display_cols = ["ID", "Name", "Email", "Due Date", "Status", "3mo Sent", "1mo Sent", "1wk Sent", "2wk-after Sent"]

    edited_df = st.data_editor(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        disabled=["ID", "Status", "3mo Sent", "1mo Sent", "1wk Sent", "2wk-after Sent"],
        key="teacher_editor",
    )
    
    if st.button("Save change"):
        original = df[display_cols].set_index("ID")
        edited = edited_df.set_index("ID")
        changed_ids = original.index[(original[["Name", "Email", "Due Date"]] != edited[["Name", "Email", "Due Date"]]).any(axis=1)]

        for tid in changed_ids:
            db.update_teacher(int(tid), edited.loc[tid, "Name"], edited.loc[tid,"Email"], edited.loc[tid, "Due Date"])

        if len(changed_ids) > 0:
            st.success(f"Updated {len(changed_ids)} teacher(s)")
            st.rerun()

    #st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    with st.expander("Remove a teacher"):
        options = {f"{t['name']} ({t['email']})": t["id"] for t in teachers}
        choice = st.selectbox("Select teacher", list(options.keys()))
        if st.button("Delete selected teacher"):
            db.delete_teacher(options[choice])
            st.success("Deleted")
            st.rerun()

st.subheader("Reminders")

if due_ids:
    st.warning(f"{len(due_ids)} teacher(s) are due for a reminder.")
    for tid, stage in due_ids.items():
        t = db.get_teacher(tid)
        st.write(f"- **{t['name']}** ({t['email']}) → `{stage.replace('_', ' ')}` reminder")
 
    if st.button("Send all due reminders", type="primary"):
        db.send_reminders(due_ids)
        st.success("Reminders sent and marked.")
        st.rerun()
else:
    st.success("No reminders due right now.")
