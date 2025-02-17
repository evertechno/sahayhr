import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from docx import Document
import PyPDF2
import io

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

# Function to scrape job description from URL
def scrape_job_description(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Assuming job description is in <div> with class 'job-description', you may need to adjust this
        job_description = soup.find('div', class_='job-description')
        if job_description:
            return job_description.get_text(strip=True)
        else:
            return "Job description not found"
    except Exception as e:
        return f"Error scraping job description: {str(e)}"

# Streamlit App UI
st.title("Ever AI - Resume & Job Matching")
st.write("Upload your resume and paste a job link to get AI insights on how well the resume matches the job description.")

# File uploader for resume
resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

# Input for job post URL
job_url = st.text_input("Enter Job Posting URL:")

# Button to analyze resume and job description
if st.button("Generate Insights"):
    if resume_file and job_url:
        try:
            # Extract resume text
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(resume_file)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = extract_text_from_docx(resume_file)
            
            # Scrape job description
            job_description = scrape_job_description(job_url)

            # Combine resume text and job description for analysis
            analysis_prompt = f"Analyze the following resume against this job description and provide insights:\n\nResume: {resume_text}\n\nJob Description: {job_description}\n\nProvide insights and potential shortcomings."
            
            # Generate AI response
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(analysis_prompt)

            # Display AI-generated insights
            st.write("Insights and Shortcomings:")
            st.write(response.text)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please upload a resume and enter a job URL.")
