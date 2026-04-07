import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ---------- PAGE ----------
st.set_page_config(page_title="Smart Exam Performance Analyzer", layout="wide")

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align: center;
background: linear-gradient(to right, #1e3c72, #2a5298);
padding: 15px;
border-radius: 10px;
color: white;'>
📊 Smart Exam Performance Analyzer
</h1>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.header("Upload Dataset")
file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if file is None:
    st.warning("Please upload a CSV file")
    st.stop()

df = pd.read_csv(file)
df.columns = df.columns.str.strip().str.lower()

# ---------- AUTO DETECT ----------
def find_column(possible):
    for p in possible:
        for col in df.columns:
            if p in col:
                return col
    return None

name_col = find_column(["name"])
id_col = find_column(["id", "roll"])

# ---------- SUBJECT DETECTION ----------
non_subject_keywords = ["age", "id", "roll", "phone"]

subject_cols = [
    col for col in df.columns
    if col not in [name_col, id_col]
    and pd.api.types.is_numeric_dtype(df[col])
    and not any(k in col for k in non_subject_keywords)
]

if not name_col or not id_col or len(subject_cols) < 2:
    st.error("Dataset format not supported")
    st.stop()

# ---------- CLEAN ----------
def clean_name(col):
    return col.replace("_", " ").title()

# ---------- CALCULATIONS ----------
df["average"] = df[subject_cols].mean(axis=1)
# ---------- PASS STATUS FIX ----------
pass_mark = 60  # you can change threshold if needed

df["pass_status"] = df["average"].apply(
    lambda x: "Pass" if x >= pass_mark else "Fail"
)

# ✅ ADD RANK
df["rank"] = df["average"].rank(ascending=False, method="dense").astype(int)

# ---------- KPI ----------
def card(title, value):
    st.markdown(f"""
    <div style="
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid #e5e7eb;">
    <h4>{title}</h4>
    <h2>{value}</h2>
    </div>
    """, unsafe_allow_html=True)

total = len(df)

# ---------- PASS / FAIL CALCULATION (ADDED) ----------
pass_mark = 60

pass_count = (df["average"] >= pass_mark).sum()
fail_count = (df["average"] < pass_mark).sum()

pass_percentage = (pass_count / total) * 100
fail_percentage = (fail_count / total) * 100

# ---------- KPI DISPLAY (UPDATED) ----------
c1, c2, c3, c4 = st.columns(4)

with c1: card("Students", total)
with c2: card("Class Avg", f"{df['average'].mean():.1f}")
with c3: card("Pass %", f"{pass_percentage:.1f}%")
with c4: card("Fail %", f"{fail_percentage:.1f}%")

# ---------- PIE CHART (ADDED) ----------
# ---------- IMPROVED PIE CHART ----------
import plotly.graph_objects as go

labels = ["Pass", "Fail"]
values = [pass_count, fail_count]

pie_colors = ["#22c55e", "#ef4444"]  # green & red

fig_pf = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    hole=0.55,  # donut style (modern look)
    marker=dict(colors=pie_colors),
    textinfo='percent+label',
    pull=[0.05, 0.08],  # slight pop-out effect
)])

# Center text (dynamic)
fig_pf.update_layout(
    title="Pass vs Fail Distribution",
    annotations=[dict(
        text=f"{pass_percentage:.0f}%<br>Pass",
        x=0.5, y=0.5,
        font_size=20,
        showarrow=False
    )],
    showlegend=True,
    height=450
)

st.plotly_chart(fig_pf, use_container_width=True)

# ---------- CHART ----------
st.subheader("Subject Performance")

avg_marks = [df[c].mean() for c in subject_cols]

fig = px.bar(
    x=[clean_name(c) for c in subject_cols],
    y=avg_marks,
    text=[f"{v:.1f}" for v in avg_marks],  # clean values
    title="Average Marks per Subject"
)

fig.update_layout(
    yaxis_title="Average Marks",
    xaxis_title="Subjects",
    height=400,
    plot_bgcolor="white"
)
fig.update_layout(
    height=400,
    margin=dict(t=40, b=40),
    plot_bgcolor="white",
    paper_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

# ---------- TOPPER ----------
topper = df.loc[df["average"].idxmax()]

st.markdown("## 🏆 Top Performer")

st.markdown(f"""
<div style="
display:flex;
align-items:center;
gap:20px;
padding:25px;
border-radius:15px;
background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
color:white;
box-shadow: 0 10px 25px rgba(0,0,0,0.25);
">

<img src="https://ui-avatars.com/api/?name={topper[name_col]}&background=0D1117&color=fff&size=100"
style="border-radius:50%; border:3px solid white;">

<div>
<h2 style="margin:0;">{topper[name_col]}</h2>
<p style="margin:5px 0;">ID: {topper[id_col]}</p>
<h3 style="margin:5px 0;">{topper['average']:.2f}%</h3>
<p style="opacity:0.8;">Top Ranked Student</p>
</div>

</div>
""", unsafe_allow_html=True)

# ---------- LEADERBOARD ----------
st.subheader("🏅 Leaderboard")

leaderboard = df.sort_values("rank")

styled_df = leaderboard.style \
    .background_gradient(cmap="Blues", subset=["average"]) \
    .set_properties(**{
        "border": "1px solid #ddd",
        "padding": "6px",
        "text-align": "center"
    }) \
    .set_table_styles([
        {"selector": "th",
         "props": [
             ("background-color", "#1e293b"),
             ("color", "white"),
             ("text-align", "center")
         ]}
    ])

st.dataframe(styled_df, use_container_width=True)

# ---------- SEARCH ----------
st.divider()
st.subheader("Student Analysis")

query = st.text_input("Enter Name or ID")

if st.button("Analyze"):

    student = df[
        (df[name_col].astype(str).str.lower() == query.lower()) |
        (df[id_col].astype(str).str.lower() == query.lower())
    ]

    if student.empty:
        st.error("Student not found")
    else:
        student = student.iloc[0]

        marks = {clean_name(col): int(student[col]) for col in subject_cols}
        avg = sum(marks.values()) / len(marks)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write(f"Name: {student[name_col]}")
            st.write(f"ID: {student[id_col]}")
            st.write(f"Average: {avg:.2f}")

        with col2:
            fig2 = px.bar(x=list(marks.keys()), y=list(marks.values()), text=list(marks.values()))
            fig2.update_layout(height=350)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Progress")
        for sub, val in marks.items():
            st.write(f"{sub} ({val})")
            st.progress(val/100)

        weak = min(marks, key=marks.get)
        strong = max(marks, key=marks.get)

        st.warning(f"Needs Improvement: {weak}")
        st.success(f"Strong Subject: {strong}")

        # ---------- PDF ----------
        def generate_pdf():
            doc = SimpleDocTemplate("report.pdf")
            styles = getSampleStyleSheet()
            content = []

            content.append(Paragraph("Student Performance Report", styles['Title']))
            content.append(Spacer(1, 20))

            content.append(Paragraph(f"Name: {student[name_col]}", styles['Normal']))
            content.append(Paragraph(f"ID: {student[id_col]}", styles['Normal']))
            content.append(Paragraph(f"Average: {avg:.2f}%", styles['Normal']))

            content.append(Spacer(1, 20))

            table_data = [["Subject", "Marks"]]
            for k, v in marks.items():
                table_data.append([k, v])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ]))

            content.append(table)
            doc.build(content)

            with open("report.pdf", "rb") as f:
                return f.read()
        pdf = generate_pdf()

        st.download_button(
            label="Download Report",
            data=pdf,
            file_name="Student_Report.pdf",
            mime="application/pdf"
    )