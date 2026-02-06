import streamlit as st
from groq import Groq
import PyPDF2
import json
import io
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="Professional Concours Quiz Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .topic-tag {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        background-color: #e3f2fd;
        border-radius: 15px;
        font-size: 0.9rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'topics_extracted' not in st.session_state:
    st.session_state.topics_extracted = []
if 'selected_topics' not in st.session_state:
    st.session_state.selected_topics = []

# Title
st.markdown('<p class="main-header">🎓 Professional Concours Quiz Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload your exam syllabus and generate professional-level questions in any domain</p>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key
    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Get your API key from console.groq.com"
    )
    
    st.markdown("---")
    
    # Quiz Settings
    st.subheader("📋 Quiz Settings")
    num_questions = st.slider(
        "Number of Questions",
        min_value=5,
        max_value=30,
        value=15,
        step=5
    )
    
    difficulty = st.select_slider(
        "Difficulty Level",
        options=["Beginner", "Intermediate", "Advanced", "Expert"],
        value="Intermediate"
    )
    
    question_language = st.selectbox(
        "Language",
        ["English", "French", "Arabic", "Spanish", "German"]
    )
    
    question_type = st.selectbox(
        "Question Type",
        ["Multiple Choice (QCM)", "True/False", "Mixed"]
    )
    
    st.markdown("---")
    
    # Advanced Settings
    with st.expander("🔧 Advanced Settings"):
        include_explanations = st.checkbox("Include detailed explanations", value=True)
        randomize_options = st.checkbox("Randomize answer options", value=True)
        time_limit = st.number_input("Time limit per question (seconds)", min_value=10, max_value=300, value=60)
    
    st.markdown("---")
    
    # Instructions
    st.markdown("### 📖 Instructions")
    st.markdown("""
    1. Enter your Groq API key
    2. Upload exam syllabus/curriculum PDF
    3. Review and select topics
    4. Configure quiz settings
    5. Generate professional quiz
    6. Take the test and get results
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Tip")
    st.info("Upload a detailed syllabus or curriculum PDF for best results. The AI will identify all topics and generate questions based on professional standards.")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return None

def extract_topics_and_domains(text, api_key):
    """Extract academic topics and domains from the PDF"""
    try:
        client = Groq(api_key=api_key)
        
        prompt = f"""Analyze this exam syllabus/curriculum document and extract all academic topics, domains, and subjects mentioned.

Text:
{text[:10000]}

IMPORTANT: Identify the FIELDS OF STUDY mentioned (e.g., Mathematics, Physics, Law, Economics, etc.), not just topics from the document.

Return a JSON object with:
1. "domains": List of main academic fields (e.g., Mathematics, Physics, Chemistry, Law, etc.)
2. "topics": Detailed list of specific topics within each domain
3. "exam_type": Type of exam (e.g., "Engineering Entrance", "Medical School", "Civil Service", etc.)
4. "level": Academic level (e.g., "Undergraduate", "Graduate", "Professional", etc.)

Format:
{{
    "exam_type": "exam type here",
    "level": "academic level",
    "domains": [
        {{
            "name": "Domain Name",
            "topics": ["topic1", "topic2", "topic3"]
        }}
    ]
}}
"""
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=2000,
        )
        
        response_text = response.choices[0].message.content
        
        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        topics_data = json.loads(response_text)
        return topics_data
        
    except Exception as e:
        st.error(f"❌ Error extracting topics: {str(e)}")
        return None

def generate_professional_quiz(api_key, domains_topics, num_questions, difficulty, language, question_type, include_explanations):
    """Generate professional quiz questions based on selected domains and topics"""
    try:
        client = Groq(api_key=api_key)
        
        # Format selected topics
        topics_text = "\n".join([
            f"- {domain['name']}: {', '.join(domain['topics'])}"
            for domain in domains_topics
        ])
        
        prompt = f"""You are a professional exam question writer. Generate {num_questions} high-quality {question_type} questions for a {difficulty} level examination in {language}.

CRITICAL INSTRUCTIONS:
- Generate questions about the ACADEMIC FIELDS themselves, NOT about the syllabus document
- Questions should test ACTUAL KNOWLEDGE in these domains
- Use professional exam standards
- Questions should be clear, unambiguous, and academically rigorous
- Avoid trick questions or overly complex wording

Academic Domains and Topics to cover:
{topics_text}

Difficulty Level: {difficulty}
- Beginner: Basic concepts and definitions
- Intermediate: Application and understanding
- Advanced: Analysis and synthesis
- Expert: Complex problem-solving and critical thinking

Question Type: {question_type}

Requirements:
1. Distribute questions across all selected domains
2. Each question should have 4 options (A, B, C, D) for Multiple Choice
3. Only ONE correct answer per question
4. Include field/topic tag for each question
5. {"Include detailed explanations for correct answers" if include_explanations else "Brief explanations only"}
6. Questions should test REAL knowledge, not document recall

Return JSON format:
{{
    "exam_info": {{
        "title": "Exam title",
        "total_questions": {num_questions},
        "difficulty": "{difficulty}",
        "estimated_time_minutes": calculated_time
    }},
    "questions": [
        {{
            "id": 1,
            "domain": "Domain name",
            "topic": "Specific topic",
            "question": "Question text?",
            "type": "multiple_choice" or "true_false",
            "options": {{
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            }},
            "correct_answer": "A",
            "explanation": "Detailed explanation",
            "difficulty": "intermediate",
            "points": 1
        }}
    ]
}}
"""
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=8000,
        )
        
        response_text = response.choices[0].message.content
        
        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        quiz_data = json.loads(response_text)
        return quiz_data
        
    except Exception as e:
        st.error(f"❌ Error generating quiz: {str(e)}")
        return None

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload & Extract Topics", "🎯 Generate Quiz", "📊 Results"])

with tab1:
    st.header("Step 1: Upload Exam Syllabus")
    
    uploaded_file = st.file_uploader(
        "Upload PDF (Exam syllabus, curriculum, or study guide)",
        type=['pdf'],
        help="Upload a document containing the exam topics and domains"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            with st.expander("📄 View PDF Content Preview"):
                pdf_text = extract_text_from_pdf(uploaded_file)
                if pdf_text:
                    st.text_area("Content Preview", pdf_text[:2000] + "...", height=300, disabled=True)
        
        with col2:
            if st.button("🔍 Extract Topics", type="primary", use_container_width=True):
                if not groq_api_key:
                    st.error("⚠️ Please enter your Groq API key in the sidebar!")
                else:
                    with st.spinner("🤖 AI is analyzing the document and extracting topics..."):
                        pdf_text = extract_text_from_pdf(uploaded_file)
                        if pdf_text:
                            topics_data = extract_topics_and_domains(pdf_text, groq_api_key)
                            if topics_data:
                                st.session_state.topics_extracted = topics_data
                                st.success("✅ Topics extracted successfully!")
                                st.rerun()
        
        # Display extracted topics
        if st.session_state.topics_extracted:
            st.markdown("---")
            st.header("📚 Extracted Academic Domains")
            
            if 'exam_type' in st.session_state.topics_extracted:
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Exam Type:** {st.session_state.topics_extracted.get('exam_type', 'N/A')}")
                with col2:
                    st.info(f"**Level:** {st.session_state.topics_extracted.get('level', 'N/A')}")
            
            st.markdown("### Select domains for your quiz:")
            
            selected_domains = []
            for domain in st.session_state.topics_extracted.get('domains', []):
                with st.expander(f"🎯 {domain['name']}", expanded=True):
                    include_domain = st.checkbox(
                        f"Include {domain['name']} in quiz",
                        value=True,
                        key=f"domain_{domain['name']}"
                    )
                    
                    if include_domain:
                        st.markdown("**Topics:**")
                        selected_topics = st.multiselect(
                            "Select specific topics:",
                            domain['topics'],
                            default=domain['topics'][:5],  # Select first 5 by default
                            key=f"topics_{domain['name']}"
                        )
                        
                        if selected_topics:
                            selected_domains.append({
                                'name': domain['name'],
                                'topics': selected_topics
                            })
            
            if selected_domains:
                st.session_state.selected_topics = selected_domains
                st.success(f"✅ Selected {len(selected_domains)} domains with {sum(len(d['topics']) for d in selected_domains)} topics")

with tab2:
    st.header("Step 2: Generate Professional Quiz")
    
    if not st.session_state.selected_topics:
        st.warning("⚠️ Please upload a PDF and select topics first (Tab 1)")
    else:
        st.markdown("### Selected Domains:")
        for domain in st.session_state.selected_topics:
            st.markdown(f"**{domain['name']}:** {', '.join(domain['topics'])}")
        
        st.markdown("---")
        
        if st.button("🎯 Generate Professional Quiz", type="primary", use_container_width=True):
            if not groq_api_key:
                st.error("⚠️ Please enter your Groq API key!")
            else:
                with st.spinner("🤖 AI is generating professional-level questions... This may take 1-2 minutes."):
                    quiz_data = generate_professional_quiz(
                        groq_api_key,
                        st.session_state.selected_topics,
                        num_questions,
                        difficulty,
                        question_language,
                        question_type,
                        include_explanations
                    )
                    
                    if quiz_data:
                        st.session_state.quiz_data = quiz_data
                        st.session_state.user_answers = {}
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_generated = True
                        st.session_state.start_time = datetime.now()
                        st.success("✅ Professional quiz generated successfully!")
                        st.rerun()
        
        # Display Quiz
        if st.session_state.quiz_generated and 'quiz_data' in st.session_state:
            quiz_data = st.session_state.quiz_data
            
            # Exam Info
            if 'exam_info' in quiz_data:
                st.markdown("---")
                info = quiz_data['exam_info']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📝 Total Questions", info.get('total_questions', num_questions))
                with col2:
                    st.metric("⏱️ Estimated Time", f"{info.get('estimated_time_minutes', 'N/A')} min")
                with col3:
                    st.metric("📊 Difficulty", info.get('difficulty', difficulty))
            
            st.markdown("---")
            st.header("📝 Quiz Questions")
            
            # Progress bar
            answered = len(st.session_state.user_answers)
            total = len(quiz_data['questions'])
            progress = answered / total if total > 0 else 0
            st.progress(progress, text=f"Progress: {answered}/{total} questions answered")
            
            # Display questions
            for idx, q in enumerate(quiz_data['questions']):
                with st.container():
                    st.markdown(f"### Question {idx + 1}")
                    
                    # Tags
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Domain:** {q.get('domain', 'General')} | **Topic:** {q.get('topic', 'N/A')}")
                    with col2:
                        st.markdown(f"**Points:** {q.get('points', 1)}")
                    
                    st.markdown(f"**{q['question']}**")
                    
                    if not st.session_state.quiz_submitted:
                        # Answer selection
                        if q.get('type') == 'true_false':
                            options_list = ["True", "False"]
                        else:
                            options_list = [f"{key}: {value}" for key, value in q['options'].items()]
                        
                        answer = st.radio(
                            "Select your answer:",
                            options_list,
                            key=f"q_{idx}",
                            index=None
                        )
                        
                        if answer:
                            if q.get('type') == 'true_false':
                                st.session_state.user_answers[idx] = answer
                            else:
                                st.session_state.user_answers[idx] = answer[0]
                    else:
                        # Show results
                        user_answer = st.session_state.user_answers.get(idx, "Not answered")
                        correct_answer = q['correct_answer']
                        
                        if user_answer == correct_answer:
                            st.success(f"✅ **Correct!** Your answer: {user_answer}")
                        elif user_answer == "Not answered":
                            st.warning(f"⚠️ **Not answered** | Correct answer: {correct_answer}")
                        else:
                            st.error(f"❌ **Incorrect** | Your answer: {user_answer} | Correct answer: {correct_answer}")
                        
                        if include_explanations and 'explanation' in q:
                            st.info(f"💡 **Explanation:** {q['explanation']}")
                    
                    st.markdown("---")
            
            # Submit button
            if not st.session_state.quiz_submitted:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📤 Submit Quiz", type="primary", use_container_width=True):
                        st.session_state.quiz_submitted = True
                        st.session_state.end_time = datetime.now()
                        st.rerun()

with tab3:
    st.header("📊 Quiz Results")
    
    if not st.session_state.quiz_submitted:
        st.info("Complete and submit the quiz to view your results")
    else:
        quiz_data = st.session_state.quiz_data
        
        # Calculate score
        correct_count = 0
        total_points = 0
        earned_points = 0
        domain_stats = {}
        
        for idx, q in enumerate(quiz_data['questions']):
            points = q.get('points', 1)
            total_points += points
            domain = q.get('domain', 'General')
            
            if domain not in domain_stats:
                domain_stats[domain] = {'correct': 0, 'total': 0}
            
            domain_stats[domain]['total'] += 1
            
            if st.session_state.user_answers.get(idx) == q['correct_answer']:
                correct_count += 1
                earned_points += points
                domain_stats[domain]['correct'] += 1
        
        total_questions = len(quiz_data['questions'])
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Time taken
        if 'start_time' in st.session_state and 'end_time' in st.session_state:
            time_taken = st.session_state.end_time - st.session_state.start_time
            minutes = int(time_taken.total_seconds() / 60)
            seconds = int(time_taken.total_seconds() % 60)
        else:
            minutes, seconds = 0, 0
        
        # Display results
        st.markdown("### 🎯 Overall Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Score", f"{correct_count}/{total_questions}")
        with col2:
            st.metric("Percentage", f"{score_percentage:.1f}%")
        with col3:
            st.metric("Points", f"{earned_points}/{total_points}")
        with col4:
            st.metric("Time Taken", f"{minutes}m {seconds}s")
        
        # Grade
        st.markdown("### 📈 Grade")
        if score_percentage >= 90:
            st.success("🌟 **Excellent!** Outstanding performance!")
        elif score_percentage >= 80:
            st.success("🎉 **Very Good!** Strong understanding!")
        elif score_percentage >= 70:
            st.info("👍 **Good!** Solid knowledge!")
        elif score_percentage >= 60:
            st.warning("📚 **Pass** - Review weak areas")
        else:
            st.error("📖 **Need Improvement** - More study required")
        
        # Domain breakdown
        st.markdown("### 📊 Performance by Domain")
        
        for domain, stats in domain_stats.items():
            domain_percentage = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.progress(domain_percentage / 100, text=f"{domain}: {stats['correct']}/{stats['total']} ({domain_percentage:.0f}%)")
            with col2:
                if domain_percentage >= 80:
                    st.markdown("✅ Strong")
                elif domain_percentage >= 60:
                    st.markdown("⚠️ Review")
                else:
                    st.markdown("❌ Weak")
        
        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generate New Quiz", use_container_width=True):
                st.session_state.quiz_generated = False
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}
                if 'quiz_data' in st.session_state:
                    del st.session_state.quiz_data
                st.rerun()
        
        with col2:
            if st.button("📄 Export Results", use_container_width=True):
                st.info("Export feature coming soon!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Professional Concours Quiz Generator</strong></p>
    <p>Mohammed EL Hassani - Anass EL mottaleb</p>
    <p style='font-size: 0.9rem;'>Get your free API key at <a href='https://console.groq.com' target='_blank'>console.groq.com</a></p>
</div>
""", unsafe_allow_html=True)