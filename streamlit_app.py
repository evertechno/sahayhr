import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from docx import Document
import PyPDF2
import io
from googleapiclient.discovery import build

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
google_cse_api_key = st.secrets["GOOGLE_CSE_API_KEY"]
google_cse_engine_id = st.secrets["GOOGLE_CSE_ENGINE_ID"]

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
        
        # Attempt to find job description dynamically
        job_description = ""
        
        # Try to find different possible containers for job description
        description_containers = [
            'div.job-description',
            'div.description',
            'div#job-summary',
            'section.job-details'
        ]
        
        for container in description_containers:
            job_description = soup.select_one(container)
            if job_description:
                return job_description.get_text(strip=True)
        
        # If no description found in common containers, fallback to entire page text
        job_description = soup.get_text(strip=True)
        
        if job_description:
            return job_description
        else:
            return "Job description not found"
    except Exception as e:
        return f"Error scraping job description: {str(e)}"

# Function to search for job descriptions using Google CSE
def search_job_description(query):
    try:
        service = build("customsearch", "v1", developerKey=google_cse_api_key)
        res = service.cse().list(q=query, cx=google_cse_engine_id).execute()

        if "items" in res:
            # Returning the snippet of the first search result
            return res["items"][0]["snippet"]
        else:
            return "No relevant job descriptions found."
    except Exception as e:
        return f"Error searching for job description: {str(e)}"

# Streamlit App UI
st.title("Ever AI - Resume & Job Matching")
st.write("Upload your resume and paste a job link or enter a job title to get AI insights on how well the resume matches the job description.")

# File uploader for resume
resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

# Input for job post URL or job title
job_url = st.text_input("Enter Job Posting URL:")
job_title = st.text_input("Or, Enter Job Title for Google Search:")

# Button to analyze resume and job description
if st.button("Generate Insights"):
    if resume_file:
        try:
            # Extract resume text
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(resume_file)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = extract_text_from_docx(resume_file)
            
            # Check if job URL or title is provided
            if job_url:
                job_description = scrape_job_description(job_url)
            elif job_title:
                job_description = search_job_description(job_title)
            else:
                st.warning("Please provide a job URL or job title.")
                job_description = None  # Explicitly set job_description to None if neither field is filled.
            
            if job_description:
                # Combine resume text and job description for analysis
                analysis_prompt = f"""
                Analyze the following resume against the job description. Provide insights into how well the resume matches the job description, highlighting strengths, skills, and any potential gaps.
                
                Resume: {resume_text}
                
                Job Description: {job_description}
                
                Generate insights on the fit and potential improvements.
                """

                # Generate AI response using the AI model
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(analysis_prompt)

                # Display AI-generated insights
                st.write("Insights and Shortcomings:")
                st.write(response.text)
            else:
                st.warning("No job description found. Please check the URL or job title.")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please upload a resume.")
