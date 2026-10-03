import streamlit as st
import requests
import time
import fitz  # PyMuPDF for PDF parsing

st.set_page_config(page_title="📄 Resume & Job Matcher", layout="centered")

st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(rgba(248, 250, 252, 0.88), rgba(248, 250, 252, 0.94)),
            url("https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=2200&q=85");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    [data-testid="stMainBlockContainer"] {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 18px;
        padding: 2rem 2.5rem 2.5rem;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📄 Resume & Job Matcher")

tabs = st.tabs(["📄 Resume Match", "💼 Portfolio"])


def render_portfolio():
    st.subheader("Portfolio Overview")
    st.markdown(
        """
        I build AI-powered tools and practical automation products that help people work faster,\n        make better decisions, and turn ideas into useful software.
        """
    )

    portfolio_items = [
        {
            "title": "Resume & Job Matcher",
            "description": "A Streamlit app that compares a resume against a job description and explains strengths, gaps, and recommended improvements.",
            "stack": "Python • Streamlit • Ollama • PyMuPDF",
        },
        {
            "title": "AI Agent Apps",
            "description": "Experiments and practical workflows that combine LLMs with tools, memory, and task automation to improve productivity.",
            "stack": "LLMs • Agents • Automation",
        },
        {
            "title": "Workflow Prototyping",
            "description": "Prototype systems for research, summarization, decision support, and domain-specific AI copilots.",
            "stack": "Product Design • Prompt Engineering • Python",
        },
    ]

    cols = st.columns(3)
    for idx, item in enumerate(portfolio_items):
        with cols[idx]:
            st.markdown(
                f"""
                <div style="padding: 1.2rem; border-radius: 16px; background: rgba(248,250,252,0.97); border: 1px solid rgba(148,163,184,0.35); min-height: 210px;">
                    <h4 style="margin-top: 0;">{item['title']}</h4>
                    <p>{item['description']}</p>
                    <small><strong>Stack:</strong> {item['stack']}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    metrics = [
        ("AI Products", "3+ prototypes"),
        ("Focus", "Practical automation"),
        ("Workflow", "Python + LLMs"),
        ("Goal", "Useful software"),
    ]
    metric_cols = st.columns(4)
    for idx, (label, value) in enumerate(metrics):
        with metric_cols[idx]:
            st.metric(label, value)


with tabs[0]:
    with st.sidebar:
        st.header("Analysis Settings")
        model_name = st.selectbox("Ollama model", ["llama3"], index=0)
        analysis_depth = st.selectbox(
            "Analysis depth",
            ["Balanced", "Concise", "Detailed"],
            index=0,
        )
        job_title = st.text_input("Target job title", placeholder="e.g. Data Analyst")

    st.sidebar.info("""
    This app uses a local LLM via **Ollama**.
    1. Install Ollama: https://ollama.ai
    2. Verify the ollama CLI works, by running the below commands in your terminal:
        2.1. Start the Ollama server: `ollama serve` on separate terminal.
        2.2. Run a model (e.g., `ollama pull llama3`).
        2.3. Verify local LLM llama is listed using `ollama list`.
        2.4. Run the streamlit run app.py command to start this app in another terminal.
    3. Upload a Resume + Job Description to get a fit score and suggestions.
    """)

    # Helper: Extract text from PDF
    def extract_pdf_text(file):
        text = ""
        file.seek(0)
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text

    def get_text_from_file(file_name) -> str:
        file_name.seek(0)
        if file_name.type == "application/pdf":
            file_text = extract_pdf_text(file_name)
        else:
            file_text = file_name.read().decode("utf-8")
        return file_text

    # File uploaders
    resume_file = st.file_uploader("Upload Resume (PDF/TXT)", type=["pdf", "txt"])
    job_file = st.file_uploader("Upload Job Description (PDF/TXT)", type=["pdf", "txt"])

    if resume_file and job_file:
        resume_preview = get_text_from_file(resume_file)
        job_preview = get_text_from_file(job_file)
        with st.expander("Preview extracted text", expanded=False):
            preview_col1, preview_col2 = st.columns(2)
            with preview_col1:
                st.caption("Resume")
                st.text_area("Resume preview", resume_preview[:3000], height=220, disabled=True, label_visibility="collapsed")
            with preview_col2:
                st.caption("Job description")
                st.text_area("Job preview", job_preview[:3000], height=220, disabled=True, label_visibility="collapsed")

    button_col1, button_col2 = st.columns([3, 1])
    with button_col1:
        match_clicked = st.button("🔍 Match Resume with Job Description", use_container_width=True)
    with button_col2:
        clear_clicked = st.button("🗑️ Clear", use_container_width=True)

    if clear_clicked:
        st.session_state.pop("resume_match", None)
        st.rerun()

    if match_clicked:
        if resume_file and job_file:
            resume_text = get_text_from_file(resume_file)
            job_text = get_text_from_file(job_file)

            prompt = f"""
            You are an AI career assistant.

            Target job title: {job_title or "Not provided"}
            Analysis depth: {analysis_depth}

            Resume:
            {resume_text}

            Job Description:
            {job_text}

            Please analyze and return:
            1. A **Fit Score** (0-100%) of how well this resume matches the job.
            2. Key strengths (resume areas that align well).
            3. Specific recommendations to improve the resume to better fit the job.
            Format neatly in Markdown.
            """

            try:
                with st.spinner("⏳ Analyzing Resume vs Job Description..."):
                    for attempt in range(3):
                        try:
                            response = requests.post(
                                "http://127.0.0.1:11434/api/generate",
                                json={"model": model_name, "prompt": prompt, "stream": False},
                                timeout=180,
                            )
                            response.raise_for_status()
                            break
                        except requests.RequestException:
                            if attempt == 2:
                                raise
                            time.sleep(5)
                    data = response.json()
                    output = data.get("response", "⚠️ No response from model.")

                st.subheader("📌 Match Analysis")
                st.markdown(output)
                st.session_state["resume_match"] = output

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

        else:
            st.warning("⚠️ Please upload both Resume and Job Description.")

    if "resume_match" in st.session_state:
        st.download_button(
            "💾 Download Match Report",
            st.session_state["resume_match"],
            file_name="resume_match_report.md",
            mime="text/markdown",
        )

with tabs[1]:
    render_portfolio()
