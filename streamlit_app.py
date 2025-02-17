import streamlit as st
import google.generativeai as genai
from docx import Document
import PyPDF2
import io
import re
from collections import Counter

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Function to extract text from DOCX file
def extract_text_from_docx(docx_file):
    doc = Document(io.BytesIO(docx_file.read()))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Function to extract text from PDF file
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to clean and extract skills from text (simple example, can be expanded)
def extract_skills(text, skill_list):
    # Convert text to lowercase and split it into words
    text = text.lower()
    words = re.findall(r'\w+', text)
    # Count how many times each skill appears
    skill_count = {skill: words.count(skill) for skill in skill_list}
    return skill_count

# Function to extract experience in years
def extract_experience(text):
    experience = re.findall(r'(\d+)\s?(?:year|yr|yrs)', text, re.IGNORECASE)
    return sum(int(exp) for exp in experience)

# Function to compare job description and resume text for keyword matching
def compare_keywords(job_description, resume_text):
    job_keywords = set(re.findall(r'\w+', job_description.lower()))
    resume_keywords = set(re.findall(r'\w+', resume_text.lower()))
    common_keywords = job_keywords.intersection(resume_keywords)
    return len(common_keywords), common_keywords

# Function to provide actionable feedback
def actionable_feedback(resume_text, job_description, skill_list):
    feedback = []
    
    # Skill extraction
    resume_skills = extract_skills(resume_text, skill_list)
    job_skills = extract_skills(job_description, skill_list)
    
    missing_skills = [skill for skill, count in job_skills.items() if count > 0 and resume_skills[skill] == 0]
    
    if missing_skills:
        feedback.append(f"Consider adding or emphasizing the following missing skills: {', '.join(missing_skills)}.")
    else:
        feedback.append("You have all the key skills listed in the job description.")
    
    # Experience check
    resume_experience = extract_experience(resume_text)
    job_experience = re.findall(r'(\d+)\s?(?:year|yr|yrs)', job_description, re.IGNORECASE)
    job_experience_years = sum(int(exp) for exp in job_experience)
    
    if resume_experience < job_experience_years:
        feedback.append(f"You might want to highlight more experience. The job description asks for {job_experience_years} years of experience.")
    elif resume_experience > job_experience_years:
        feedback.append(f"Your experience exceeds the job requirement of {job_experience_years} years.")
    
    return feedback

# Streamlit App UI
st.title("Ever AI - Resume & Job Matching")
st.write("Upload your resume and provide the job description text to get AI insights on how well the resume matches the job description.")

# File uploader for resume
resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

# Input for job description
job_description = st.text_area("Enter Job Description:")

# Define a list of skills to extract (expand this list as necessary)
skill_list = ['python', 'java', 'javascript', 'c++', 'html', 'css', 'sql', 'machine learning', 'deep learning', 'data analysis', 'communication', 'teamwork']

# Button to analyze resume and job description
if st.button("Generate Insights"):
    if resume_file and job_description:
        try:
            # Extract resume text
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(resume_file)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = extract_text_from_docx(resume_file)

            # Keyword comparison
            keyword_match_count, common_keywords = compare_keywords(job_description, resume_text)

            # Actionable feedback based on skills and experience
            feedback = actionable_feedback(resume_text, job_description, skill_list)

            # Combine resume text and job description for analysis
            analysis_prompt = f"""
            Analyze the following resume against the job description. Provide insights into how well the resume matches the job description, highlighting strengths, skills, and any potential gaps.

            Resume: {resume_text}

            Job Description: {job_description}

            Provide insights into skill match, experience relevance, and any notable gaps in the resume.
            """

            # Generate AI response using the AI model
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(analysis_prompt)

            # Display AI-generated insights
            st.write("Insights and Shortcomings:")
            st.write(response.text)
            
            # Display additional metrics and feedback
            st.write(f"\n### Keyword Match Analysis")
            st.write(f"Keywords matching between the resume and job description: {keyword_match_count} common keywords.")
            st.write(f"Common keywords: {', '.join(common_keywords)}")
            
            st.write(f"\n### Experience Match")
            st.write(f"Your resume mentions {extract_experience(resume_text)} years of experience.")
            
            st.write(f"\n### Actionable Feedback")
            for item in feedback:
                st.write(f"- {item}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please upload a resume and provide a job description.")
