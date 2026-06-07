import streamlit as st
import pandas as pd
import fitz
import re
from datetime import datetime
from pathlib import Path

# -----------------------------------
# Configuration
# -----------------------------------

EXCEL_FILE = "homework.xlsx"

# -----------------------------------
# Page Setup
# -----------------------------------

st.set_page_config(
    page_title="Homework AI",
    layout="wide"
)

st.title("🤖 Homework AI")

# -----------------------------------
# Excel Functions
# -----------------------------------

def load_homework():

    if Path(EXCEL_FILE).exists():

        try:
            return pd.read_excel(EXCEL_FILE)

        except:
            pass

    return pd.DataFrame(
        columns=[
            "Done",
            "Date",
            "Subject",
            "Homework",
            "Due Date"
        ]
    )


def save_homework(df):

    df.to_excel(
        EXCEL_FILE,
        index=False
    )

# -----------------------------------
# Homework Extraction
# -----------------------------------

def extract_homework(text, filename):

    rows = []
    additional_info = ""

    # -----------------------------------
    # Date From Filename
    # Example:
    # 6G 5th June.pdf
    # -----------------------------------

    pdf_date = ""

    filename_match = re.search(
        r'(\d+)(st|nd|rd|th)\s+([A-Za-z]+)',
        filename
    )

    if filename_match:

        day = int(filename_match.group(1))
        month_name = filename_match.group(3)

        year = datetime.now().year

        pdf_date = datetime.strptime(
            f"{day} {month_name} {year}",
            "%d %B %Y"
        ).strftime("%d-%b-%y")

    # -----------------------------------
    # Split Text
    # -----------------------------------

    lines = [line.strip() for line in text.splitlines()]

    current_subject = None

    # -----------------------------------
    # Homework Extraction
    # -----------------------------------

    for i in range(len(lines)):

        line = lines[i]

        if line == "Subject":

            if i + 1 < len(lines):
                current_subject = lines[i + 1]

        if line == "Reinforcement":

            reinforcement = ""

            if i + 1 < len(lines):
                reinforcement = lines[i + 1]

            submission_date = ""

            for j in range(i, min(i + 10, len(lines))):

                if lines[j] == "Submission date":

                    if j + 1 < len(lines):
                        submission_date = lines[j + 1]

                    break

            if (
                reinforcement
                and reinforcement.lower() != "nil"
                and reinforcement.upper() != "na"
            ):

                rows.append(
                    {
                        "Done": False,
                        "Date": pdf_date,
                        "Subject": current_subject,
                        "Homework": reinforcement,
                        "Due Date": submission_date
                    }
                )

    # -----------------------------------
    # Additional Information
    # -----------------------------------

    if "Additional Information" in text:

        additional_info = text.split(
            "Additional Information"
        )[-1].strip()

        additional_info = re.sub(
            r'\d{1,2}/\d{1,2}/\d{4}.*',
            '',
            additional_info,
            flags=re.DOTALL
        ).strip()

    return rows, additional_info

# -----------------------------------
# Load Existing Homework
# -----------------------------------

existing_df = load_homework()

# -----------------------------------
# Upload PDFs
# -----------------------------------

uploaded_files = st.file_uploader(
    "Upload Homework PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

all_additional_info = []

# -----------------------------------
# Process Uploaded PDFs
# -----------------------------------

if uploaded_files:

    all_rows = []

    for uploaded_file in uploaded_files:

        pdf_bytes = uploaded_file.read()

        doc = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        full_text = ""

        for page in doc:
            full_text += page.get_text()

        rows, additional_info = extract_homework(
            full_text,
            uploaded_file.name
        )

        all_rows.extend(rows)

        if additional_info:

            all_additional_info.append(
                {
                    "File": uploaded_file.name,
                    "Information": additional_info
                }
            )

    new_df = pd.DataFrame(all_rows)

    if not new_df.empty:

        combined_df = pd.concat(
            [existing_df, new_df],
            ignore_index=True
        )

        combined_df = combined_df.drop_duplicates(
            subset=[
                "Date",
                "Subject",
                "Homework"
            ]
        )

        save_homework(combined_df)

        existing_df = combined_df

# -----------------------------------
# Homework Table
# -----------------------------------

st.subheader("📚 Homework")

edited_df = st.data_editor(
    existing_df,
    use_container_width=True,
    hide_index=True
)

save_homework(edited_df)

st.write(
    f"Total Homework Items: {len(edited_df)}"
)

# -----------------------------------
# Additional Information
# -----------------------------------

st.subheader("📌 Additional Information")

if all_additional_info:

    addl_df = pd.DataFrame(
        all_additional_info
    )

    st.dataframe(
        addl_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No Additional Information for uploaded PDFs"
    )