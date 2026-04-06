import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------- PAGE ----------
st.set_page_config(page_title="Smart Exam Performance Analyzer", layout="wide")

# ---------- LIGHT UI ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}
h1, h2, h3 { color: #1e293b; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 Smart Exam Performance Analyzer")

# ---------- UPLOAD ----------
file = st.sidebar.file_uploader("📂 Upload CSV", type=["csv"])

if file is None:
    st.info("Upload a CSV file to begin")
    st.stop()

# ---------- LOAD ----------
df = pd.read_csv(file)
df.columns = df.columns.str.strip().str.lower()

subjects = ["mathematics", "science", "english", "history", "computer_science"]

# ---------- FIXED CALCULATIONS ----------
df["calculated_avg"] = df[subjects].mean(axis=1)

df["status"] = df[subjects].apply(
    lambda x: "Fail" if any(m < 35 for m in x) else "Pass", axis=1
)

df["rank"] = df["calculated_avg"].rank(ascending=False)

# ---------- KPIs ----------
total = len(df)
pass_count = (df["status"] == "Pass").sum()
fail_count = total - pass_count

c1, c2, c3 = st.columns(3)
c1.metric("👨‍🎓 Students", total)
c2.metric("✅ Pass %", f"{(pass_count/total)*100:.1f}%")
c3.metric("❌ Fail %", f"{(fail_count/total)*100:.1f}%")

# ---------- FILTER ----------
status_filter = st.selectbox("Filter Students", ["All", "Pass", "Fail"])

if status_filter != "All":
    filtered_df = df[df["status"] == status_filter]
else:
    filtered_df = df

# ---------- CHARTS ----------
col1, col2 = st.columns(2)

with col1:
    fig1 = px.pie(
        names=["Pass", "Fail"],
        values=[pass_count, fail_count],
        hole=0.5
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    subject_avg = {sub: df[sub].mean() for sub in subjects}
    fig2 = px.bar(
        x=list(subject_avg.keys()),
        y=list(subject_avg.values()),
        color=list(subject_avg.values()),
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---------- TOPPER ----------
topper = df.loc[df["calculated_avg"].idxmax()]

st.markdown(f"""
## 🏆 Top Performer

👤 **{topper['name']}**  
🆔 ID: {topper['student_id']}  
📊 Percentage: **{topper['calculated_avg']:.2f}%**  
🏅 Rank: **1**
""")

# ---------- TABLE ----------
st.subheader("📋 Student Leaderboard")
st.dataframe(
    filtered_df.sort_values("calculated_avg", ascending=False),
    use_container_width=True
)

# ---------- STUDENT SEARCH ----------
st.divider()
st.subheader("🔍 Student Analysis")

query = st.text_input("Enter Student ID or Name")

if st.button("Analyze"):

    student = df[
        (df["student_id"].astype(str).str.lower() == query.lower()) |
        (df["name"].astype(str).str.lower() == query.lower())
    ]

    if student.empty:
        st.error("Student not found")
    else:
        student = student.iloc[0]

        marks = {
            "Maths": int(student["mathematics"]),
            "Science": int(student["science"]),
            "English": int(student["english"]),
            "History": int(student["history"]),
            "Computer": int(student["computer_science"])
        }

        avg = sum(marks.values()) / len(marks)

        # ---------- INFO ----------
        col1, col2 = st.columns([1, 2])

        with col1:
            st.write(f"**Name:** {student['name']}")
            st.write(f"**ID:** {student['student_id']}")
            st.write(f"**Average:** {avg:.2f}")

            rank = int(df.loc[df["student_id"] == student["student_id"], "rank"].values[0])
            st.info(f"🏅 Rank: #{rank}")

            # ---------- PERFORMANCE BADGE ----------
            if avg >= 85:
                st.success("🌟 Excellent")
            elif avg >= 60:
                st.info("👍 Good")
            elif avg >= 40:
                st.warning("⚠️ Average")
            else:
                st.error("❌ Poor")

        # ---------- CHART ----------
        with col2:
            fig3 = px.bar(
                x=list(marks.keys()),
                y=list(marks.values()),
                text=list(marks.values()),
                color=list(marks.values()),
                color_continuous_scale="Blues"
            )
            fig3.update_traces(textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)

        # ---------- PROGRESS ----------
        st.subheader("📈 Subject Performance")
        for sub, mark in marks.items():
            st.write(sub)
            st.progress(mark / 100)

        # ---------- INSIGHTS ----------
        weak = min(marks, key=marks.get)
        strong = max(marks, key=marks.get)

        st.subheader("🧠 AI Insights")
        st.warning(f"Focus on: {weak}")
        st.success(f"Strong in: {strong}")

        # ---------- PDF ----------
        def generate_pdf():
            doc = SimpleDocTemplate("report.pdf")
            styles = getSampleStyleSheet()
            content = []

            content.append(Paragraph("Student Report", styles['Title']))
            content.append(Spacer(1, 10))

            content.append(Paragraph(f"Name: {student['name']}", styles['Normal']))
            content.append(Paragraph(f"ID: {student['student_id']}", styles['Normal']))
            content.append(Paragraph(f"Average: {avg:.2f}", styles['Normal']))

            for s, m in marks.items():
                content.append(Paragraph(f"{s}: {m}", styles['Normal']))

            doc.build(content)

            with open("report.pdf", "rb") as f:
                return f.read()

        pdf = generate_pdf()

        st.download_button("📄 Download Report", pdf, "report.pdf")