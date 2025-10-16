import streamlit as st
import time
import base64
import google.generativeai as genai
import re
import json
import sqlite3 # <-- 1. IMPORTED SQLITE

# --- App Configuration ---
st.set_page_config(
    page_title="DataPath AI Tutor",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- WARNING: Hardcoded API Key for Immediate Launch (As requested) ---
HARDCODED_API_KEY = "AIzaSyACmRDzniS_OTkEtT39kfVWMSiY5ZBal_U"

# --- AI Model Configuration ---
model = None
try:
    genai.configure(api_key=HARDCODED_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash') # Using the requested Flash model
except Exception as e:
    st.error(f"AI model initialization failed. Error: {e}")
    model = None

# --- Dark Theme Color Palette ---
BACKGROUND_COLOR = "#0E1117"
PRIMARY_TEXT_COLOR = "#FAFAFA"
SECONDARY_TEXT_COLOR = "#AFB8C1"
BUTTON_COLOR = "#262730"
ACCENT_COLOR = "#3C3F4A"
HEADER_COLOR = "#007BFF" # A bright, visible blue for headers

# --- Custom CSS for Dark Theme ---
st.markdown(f"""
    <style>
        .stApp, .reportview-container {{ background-color: {BACKGROUND_COLOR}; }}
        
        /* General text colors */
        h1, h3, h4, h5, h6 {{ color: {PRIMARY_TEXT_COLOR}; }}
        p, li, .stMarkdown {{ color: {PRIMARY_TEXT_COLOR}; }}
        .stRadio div[role="radiogroup"] label {{ color: {PRIMARY_TEXT_COLOR} !important; }}

        /* Force the specific header (h2) to be bright blue */
        h2 {{
            color: {HEADER_COLOR} !important;
        }}
        
        /* Button Styles for Dark Theme */
        .stButton>button {{
            background-color: {BUTTON_COLOR};
            color: {PRIMARY_TEXT_COLOR};
            border: 1px solid {ACCENT_COLOR};
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: bold;
            width: 100%;
            transition: all 0.2s ease-in-out;
        }}
        .stButton>button:hover {{
            background-color: {ACCENT_COLOR};
            border-color: {PRIMARY_TEXT_COLOR};
        }}
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_image_as_base64(path):
    try:
        with open(path, "rb") as image_file: return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError: return None

# --- 2. NEW: DATABASE INITIALIZATION ---
def init_db():
    with sqlite3.connect('datapath.db') as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        # Create user_progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        conn.commit()

LOGO_BASE_64 = get_image_as_base64("DataPath_Logo.png")
LOGO_EMBED_HTML = f'<img src="data:image/png;base64,{LOGO_BASE_64}" style="max-width: 250px; display: block; margin-left: auto; margin-right: auto;">' if LOGO_BASE_64 else ""

def init_session_state():
    if 'page' not in st.session_state: st.session_state.page = 'splash'
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'messages' not in st.session_state: st.session_state.messages = []
    
    st.session_state.beginner_topics = [
        "What are Data Structures?", "Big O Notation (Introduction)", "Arrays (Static vs Dynamic)", 
        "Strings", "Stacks (LIFO)", "Queues (FIFO)", "Singly Linked Lists"
    ]
    st.session_state.intermediate_topics = [
        "Doubly Linked Lists", "Circular Linked Lists", "Hash Tables (Hashing & Collisions)", 
        "Sets", "Introduction to Trees", "Binary Search Trees (BST)",
        "Heaps (Min/Max Heap)", "Introduction to Graphs (Representation)", "Graph Traversal (BFS & DFS)"
    ]
    st.session_state.pro_topics = [
        "Self-Balancing Trees (AVL Trees)", "Red-Black Trees", "Tries (Prefix Trees)", 
        "Advanced Graph Algorithms (Dijkstra's)", "Advanced Graph Algorithms (A* Search)",
        "Disjoint Set Union (DSU) / Union-Find", "Segment Trees", "Bit Manipulation"
    ]

# Run the database setup
init_db()
# Initialize session state
init_session_state()

# --- Page Functions ---

def splash_screen():
    if not LOGO_BASE_64: st.warning("`DataPath_Logo.png` not found. Please ensure it is in the same directory as `app.py`.")
    st.markdown(f"<div style='text-align: center; padding-top: 5rem;'>{LOGO_EMBED_HTML}<h2 style='color: {PRIMARY_TEXT_COLOR}; margin-top: 1rem;'>Loading DataPath...</h2></div>", unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.page = 'login'
    st.rerun()

# --- 3. MODIFIED LOGIN PAGE ---
def login_page():
    st.markdown(f"<h1 style='text-align: center;'>Welcome Back to DataPath</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: {SECONDARY_TEXT_COLOR};'>Login to continue your journey</h3>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                with sqlite3.connect('datapath.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                    user = cursor.fetchone()
                
                if user:
                    st.session_state.logged_in, st.session_state.username = True, username
                    st.session_state.page = 'skill_level_selection'
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    st.markdown("---")
    if st.button("Create a new account"):
        st.session_state.page = 'signup'
        st.rerun()

# --- 4. MODIFIED SIGNUP PAGE ---
def signup_page():
    if st.button("⬅️ Back to Login", key="back_to_login"):
        st.session_state.page = 'login'
        st.rerun()

    st.markdown(f"<h1 style='text-align: center;'>Create Your DataPath Account</h1>", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Create Account"):
            if not username or not password or not confirm_password:
                st.error("Please fill out all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    with sqlite3.connect('datapath.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                        conn.commit()
                    
                    st.session_state.logged_in, st.session_state.username = True, username
                    st.session_state.page = 'skill_level_selection'
                    st.success("Account created successfully! Logging in...")
                    time.sleep(1)
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already exists. Please choose a different one.")


def skill_level_selection_page():
    if st.button("⬅️ Logout", key="back_logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page = 'login'
        st.rerun()

    st.markdown(f"<h2 style='text-align: center;'>Hello, {st.session_state.username}!</h2>", unsafe_allow_html=True)
    level_choice = st.radio("To personalize your learning path, please choose your current level:", ('Beginner', 'Intermediate', 'Pro'), horizontal=True)
    if st.button("Start Learning"):
        st.session_state.level = level_choice
        st.session_state.page = 'topic_selection'
        st.rerun()

def topic_selection_page():
    if st.button("⬅️ Back to Skill Selection", key="back_to_skill_selection"):
        st.session_state.page = 'skill_level_selection'
        st.rerun()

    st.markdown(f"<h2 style='text-align: center;'>Your {st.session_state.level} Learning Path</h2>", unsafe_allow_html=True)
    if st.button("🚀 Guide me from Scratch"):
        st.session_state.guided_mode = True
        st.session_state.current_topic_index = 0
        st.session_state.page = 'chat_tutor'
        st.rerun()
    st.markdown("---")
    
    topics_for_level = st.session_state.get(f"{st.session_state.level.lower()}_topics", [])
    
    for topic in topics_for_level:
        if st.button(topic, key=f"topic_{topic}"):
            st.session_state.guided_mode = False
            st.session_state.selected_topic = topic
            st.session_state.page = 'chat_tutor'
            st.rerun()

# --- CONVERSATIONAL TUTOR PAGE (Lesson Page) ---
def chat_tutor_page():
    if st.button("⬅️ Back to Topics", key="back_to_topics"):
        st.session_state.page = 'topic_selection'
        st.session_state.pop('lesson_bundle', None)
        st.session_state.pop('current_topic', None)
        st.rerun()

    if st.session_state.get('guided_mode', False):
        level_topics = st.session_state.get(f"{st.session_state.level.lower()}_topics", [])
        topic_index = st.session_state.get('current_topic_index', 0)
        if topic_index >= len(level_topics):
            st.success("Congratulations! You've completed the guided path for your level.")
            if st.button("Back to Topics"):
                st.session_state.guided_mode = False
                st.session_state.page = 'topic_selection'
                st.rerun()
            return
        st.session_state.selected_topic = level_topics[topic_index]

    st.header(f"DataPath Tutor: {st.session_state.selected_topic}")

    initial_prompt = f"""
    You are DataPath, an expert Data Structures tutor. A student at the '{st.session_state.level}' level wants to learn about '{st.session_state.selected_topic}'.
    Your FIRST response MUST be a complete lesson bundle. Use Markdown for formatting. The bundle MUST include these sections separated by '---':
    ## Concept
    [A clear, concise explanation using simple analogies.]
    ---
    ## Diagram Description
    [A short, simple description of a diagram that illustrates the core concept.]
    ---
    ## Code Examples
    [Provide complete, simple, runnable code examples in three separate, labeled code blocks for Python, Java, and C++.]
    ---
    ## LeetCode Practice
    [Suggest 2-3 relevant LeetCode problems (Name and Number) with their direct URLs.]
    ---
    ## Quiz Questions
    [Create exactly 5 multiple-choice quiz questions with 4 options each. Format them as a JSON list of objects inside a markdown code block labeled json. Each object should have "q" for the question, "o" for a list of options, and "a" for the correct answer text.]
    """
    
    if 'lesson_bundle' not in st.session_state or st.session_state.get('current_topic') != st.session_state.selected_topic:
        st.session_state.lesson_bundle = None
        with st.spinner(f"DataPath AI is preparing your comprehensive lesson on {st.session_state.selected_topic}..."):
            if model:
                try:
                    response = model.generate_content(initial_prompt)
                    st.session_state.lesson_bundle = response.text
                    st.session_state.current_topic = st.session_state.selected_topic
                    st.session_state.messages = [{"role": "assistant", "content": f"I've prepared a lesson on **{st.session_state.selected_topic}** for you. Feel free to ask me anything about it!"}]
                except Exception as e:
                    st.error(f"AI Generation Failed: {e}")
                    return 
            else:
                st.error("AI model is unavailable. Cannot generate content.")
                return

    st.subheader("Comprehensive Lesson")
    try:
        parts = st.session_state.lesson_bundle.split('---')
        concept, diagram_desc_text, code_examples = parts[0], parts[1], parts[2]
        st.markdown(concept)
        diagram_desc = re.search(r"## Diagram Description\s*(.*)", diagram_desc_text, re.DOTALL).group(1).strip()
        diagram_url = f"https://via.placeholder.com/600x250.png?text={diagram_desc.replace(' ', '+')}"
        st.image(diagram_url, caption=f"Visualizing: {st.session_state.selected_topic}")
        st.markdown(code_examples)
    except Exception as e:
        st.error("Failed to parse the initial lesson from the AI's response.")
        st.code(st.session_state.get('lesson_bundle', 'No content generated.'))
        st.markdown("---")
        pass

    st.markdown("---")
    st.subheader("Need More Help? Ask the Tutor!")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(f"Ask about {st.session_state.selected_topic}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("DataPath AI is thinking..."):
            if model:
                try:
                    history_for_model = [f"Initial Lesson:\n{st.session_state.lesson_bundle}"]
                    for msg in st.session_state.messages:
                        history_for_model.append(f"{msg['role']}: {msg['content']}")
                    
                    response = model.generate_content("\n".join(history_for_model))
                    response_text = response.text
                except Exception as e:
                    response_text = f"Sorry, I encountered an error. Please try again. Error: {e}"
            else:
                response_text = "The AI is currently offline."
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()

    st.markdown("---")
    if st.button("I'm ready for the practice!", key="ready_to_practice_btn"):
        st.session_state.page = 'leetcode_practice'
        st.rerun()

def leetcode_practice_page():
    if st.button("⬅️ Back to Lesson", key="back_to_lesson"):
        st.session_state.page = 'chat_tutor'
        st.rerun()

    st.header(f"Practice: {st.session_state.selected_topic}")
    st.markdown("Time to apply what you've learned! Click a problem to open it on LeetCode.")
    
    try:
        parts = st.session_state.lesson_bundle.split('---')
        st.markdown(parts[3])
    except (IndexError, AttributeError): st.info("No LeetCode problems were generated for this topic.")
    st.markdown("---")
    if st.button("I've practiced, proceed to Quiz!"):
        st.session_state.page = 'mcq_test'
        st.session_state.current_question = 0
        st.session_state.quiz_finished = False
        st.rerun()

# --- 5. MODIFIED MCQ TEST PAGE ---
def mcq_test_page():
    if st.button("⬅️ Back to Practice", key="back_to_practice"):
        st.session_state.page = 'leetcode_practice'
        st.rerun()

    st.header(f"Quiz: {st.session_state.selected_topic}")
    
    try:
        parts = st.session_state.lesson_bundle.split('---')
        json_string_match = re.search(r"```json\n(.*?)\n```", parts[4], re.DOTALL)
        if json_string_match:
            json_string = json_string_match.group(1)
            questions = json.loads(json_string)
        else:
            raise ValueError("JSON block for quiz questions not found in AI response.")
            
        if 'user_answers' not in st.session_state or len(st.session_state.user_answers) != len(questions):
            st.session_state.user_answers = [None] * len(questions)

    except Exception as e:
        st.error(f"Failed to load quiz questions from the AI's response. Error: {e}")
        if st.button("Back to Topics"): st.session_state.page = 'topic_selection'; st.rerun()
        return

    if st.session_state.quiz_finished:
        st.balloons()
        score = sum(1 for i, q in enumerate(questions) if st.session_state.user_answers[i] == q["a"])
        st.success(f"Quiz Complete! Your score: {score} / {len(questions)}")
        
        # --- SAVE PROGRESS TO DB ---
        try:
            with sqlite3.connect('datapath.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_progress (username, topic, score) VALUES (?, ?, ?)",
                    (st.session_state.username, st.session_state.selected_topic, score)
                )
                conn.commit()
            st.info("Your progress has been saved!")
        except sqlite3.Error as e:
            st.error(f"Failed to save your progress: {e}")
        
        st.markdown("---")
        if st.session_state.get('guided_mode', False):
            st.session_state.current_topic_index += 1
            if st.button("Continue to Next Lesson"): st.session_state.page = 'chat_tutor'; st.rerun()
        else:
            if st.button("Back to Topic Selection"): st.session_state.page = 'topic_selection'; st.rerun()
        return

    q_index = st.session_state.current_question
    q_data = questions[q_index]
    st.write(f"**Question {q_index + 1} of {len(questions)}**")
    
    st.session_state.user_answers[q_index] = st.radio(q_data['q'], q_data['o'], key=f"q{q_index}")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Previous", disabled=(q_index == 0)): st.session_state.current_question -= 1; st.rerun()
    with col3:
        if q_index < len(questions) - 1:
            if st.button("Next ➡️"): st.session_state.current_question += 1; st.rerun()
        else:
            if st.button("✨ Submit Quiz"): st.session_state.quiz_finished = True; st.rerun()

# --- Main Page Router ---
if st.session_state.page == 'splash': 
    splash_screen()
elif not st.session_state.logged_in:
    if st.session_state.page == 'signup':
        signup_page()
    else:
        login_page()
else:
    page_functions = {
        'skill_level_selection': skill_level_selection_page, 
        'topic_selection': topic_selection_page, 
        'chat_tutor': chat_tutor_page, 
        'leetcode_practice': leetcode_practice_page, 
        'mcq_test': mcq_test_page
    }
    
    if st.session_state.page in page_functions:
        if st.session_state.page in ['chat_tutor', 'leetcode_practice', 'mcq_test'] and not ('selected_topic' in st.session_state or st.session_state.get('guided_mode', False)):
            st.session_state.page = 'topic_selection'
            st.rerun()
        else:
            page_functions[st.session_state.page]()
    else: 
        skill_level_selection_page()