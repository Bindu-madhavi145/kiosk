from flask import Flask, Response, render_template, request, redirect, url_for, send_from_directory, jsonify, session, flash, send_file
import datetime
import os 
import re
from gsheets_utils import append_to_sheet, get_filtered_data
from functools import wraps
import requests
import json
import webbrowser
import threading
from werkzeug.utils import secure_filename
import pandas as pd
import random
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

@app.route("/")
def home():
    return render_template("index.html")

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.static_folder = STATIC_FOLDER

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "isro2025"

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function
def init_db():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

from datetime import date

def daily_leaderboard_reset():
    today = str(date.today())

    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM meta WHERE key='last_reset'")
    row = cursor.fetchone()

    if row is None or row[0] != today:
        # New day → reset leaderboard
        cursor.execute("DELETE FROM leaderboard")
        cursor.execute(
            "REPLACE INTO meta (key, value) VALUES ('last_reset', ?)",
            (today,)
        )
        conn.commit()

    conn.close()


# ISRO Knowledge Base with expanded topics
ISRO_KNOWLEDGE = {
    "greeting": {
        "pattern": r"\b(hello|hi|hey)\b",
        "response": "Hello! I'm your ISRO Space Assistant. Ask me anything about ISRO or space exploration!"
    },
    'isro': {
        'pattern': r'what.*(isro|indian space research)|about.*isro|tell.*isro',
        'response': '''ISRO (Indian Space Research Organisation) is India's national space agency, established in 1969. 
        It is one of the largest space agencies in the world and has achieved numerous milestones in space exploration. 
        ISRO's primary vision is to "harness space technology for national development while pursuing space science 
        research and planetary exploration".'''
    },
    'chandrayaan': {
        'pattern': r'chandrayaan|moon mission|lunar mission|lunar landing',
        'response': '''The Chandrayaan program represents India's lunar exploration missions:
        - Chandrayaan-1 (2008): First lunar mission that discovered water molecules on the Moon
        - Chandrayaan-2 (2019): Studied the Moon's surface with an orbiter (still operational)
        - Chandrayaan-3 (2023): Achieved historic soft landing on the Moon's south pole region, making India the fourth country to achieve a soft landing on the Moon and the first to land near the lunar south pole.'''
    },
    'mangalyaan': {
        'pattern': r'mangalyaan|mars mission|mars orbiter|mom',
        'response': '''Mangalyaan (Mars Orbiter Mission) was India's first interplanetary mission, launched in 2013. 
        It successfully reached Mars orbit in 2014, making ISRO the fourth space agency to reach Mars. 
        The mission demonstrated India's capability in deep space missions while being the most cost-effective Mars mission globally.'''
    },
    'gaganyaan': {
        'pattern': r'gaganyaan|human spaceflight|manned mission',
        'response': '''Gaganyaan is India's first human spaceflight program, aiming to demonstrate human spaceflight capability. 
        The mission will send astronauts to an orbit of 400km for 3 days. Key features include:
        - Indigenous development of human-rated launch vehicle
        - Life support systems and crew escape mechanisms
        - Extensive astronaut training program
        The first crewed mission is planned for 2025.'''
    },
    'aditya': {
        'pattern': r'aditya|solar mission|sun mission',
        'response': '''Aditya-L1 is India's first solar mission, designed to study the Sun from the Lagrangian point L1. 
        The mission carries various instruments to observe the solar corona, photosphere, and chromosphere. 
        It will help understand solar weather and its impact on Earth.'''
    },
    'pslv': {
        'pattern': r'pslv|polar satellite|launch vehicle',
        'response': '''The Polar Satellite Launch Vehicle (PSLV) is ISRO's reliable workhorse launch vehicle. 
        It has successfully conducted over 50 missions, launching various Indian and international satellites. 
        Known for its versatility and cost-effectiveness, PSLV has launched satellites to various orbits and even to the Moon and Mars.'''
    },
    'satellites': {
        'pattern': r'satellite program|communication satellite|earth observation',
        'response': '''ISRO's satellite program includes:
        - Communication satellites (INSAT/GSAT series)
        - Earth observation satellites (IRS series)
        - Navigation satellites (NavIC/IRNSS)
        - Scientific and planetary observation satellites
        These satellites support telecommunications, broadcasting, weather forecasting, and disaster management.'''
    },
    'achievements': {
        'pattern': r'achievement|success|milestone|recent.*development',
        'response': '''ISRO's notable achievements include:
        - Successful Chandrayaan-3 lunar landing (2023)
        - Mars Orbiter Mission success
        - Development of indigenous cryogenic engine
        - Launch of 104 satellites in a single mission
        - Demonstration of anti-satellite capabilities
        - Successful space capsule recovery experiment
        - Development of NavIC navigation system'''
    },
    'future': {
        'pattern': r'future|upcoming|plan|next mission',
        'response': '''ISRO's future plans include:
        - Gaganyaan human spaceflight mission
        - Shukrayaan Venus mission
        - Space station development
        - Reusable launch vehicle technology
        - Advanced satellite series
        - Deep space exploration missions
        These missions demonstrate ISRO's commitment to advancing India's space capabilities.'''
    },
    'budget': {
        'pattern': r'budget|cost|funding|financial',
        'response': '''ISRO is known for its cost-effective space missions:
        - Annual budget (2023-24): approximately ₹13,700 crore ($1.6 billion)
        - Chandrayaan-3 mission cost: ₹615 crore ($75 million)
        - Mars Orbiter Mission: ₹450 crore ($74 million)
        - Known for achieving complex missions at fraction of international costs
        ISRO's efficient resource utilization has made India a preferred partner for international space projects.'''
    },
    'technology': {
        'pattern': r'technology|innovation|development|indigenous',
        'response': '''Key technologies developed by ISRO:
        - Cryogenic Engine Technology
        - Reusable Launch Vehicle (RLV) Technology
        - Satellite Communication Systems
        - Remote Sensing Technologies
        - Navigation Systems (NavIC)
        - Space-Grade Lithium-Ion Cells
        These developments have made India self-reliant in space technology.'''
    },
    'international': {
        'pattern': r'international|collaboration|partnership|cooperation',
        'response': '''ISRO's International Collaborations:
        - Partnerships with NASA, ESA, JAXA, and other space agencies
        - Commercial launch services for multiple countries
        - Joint satellite missions
        - Technology exchange programs
        - International space research projects
        - Training programs for developing nations'''
    },
    'education': {
        'pattern': r'education|training|learn|study|course',
        'response': '''ISRO's Educational Initiatives:
        - Space Science Research Programs
        - ISRO Young Scientist Programme
        - Space Technology Cells in IITs
        - Training programs at Space Applications Centre
        - Collaborations with universities
        - Online courses and resources
        These programs aim to nurture future space scientists and engineers.'''
    },
    'applications': {
        'pattern': r'application|use|benefit|impact',
        'response': '''ISRO's Technology Applications:
        - Disaster Management
        - Weather Forecasting
        - Agriculture and Crop Monitoring
        - Urban Planning
        - Natural Resource Management
        - Telemedicine and Education
        - Navigation and Location Services
        These applications directly benefit society and economic development.'''
    },
    'history': {
        'pattern': r'history|establishment|origin|begin|start',
        'response': '''ISRO's Historical Journey:
        1962: Indian National Committee for Space Research established
        1969: ISRO formed
        1975: First Indian satellite Aryabhata launched
        1980: First indigenous satellite launch (Rohini)
        1984: First Indian astronaut in space (Rakesh Sharma)
        2008: First lunar mission
        2014: Successful Mars mission
        2023: Soft landing on Moon's south pole'''
    },
    'rockets': {
        'pattern': r'rocket|gslv|slv|launcher',
        'response': '''ISRO's Launch Vehicles:
        - SLV (Satellite Launch Vehicle)
        - ASLV (Augmented Satellite Launch Vehicle)
        - PSLV (Polar Satellite Launch Vehicle)
        - GSLV (Geosynchronous Satellite Launch Vehicle)
        - GSLV Mark III/LVM3 (Human-rated)
        Each vehicle serves specific mission requirements and payload capacities.'''
    },
    'shukrayaan': {
        'pattern': r'shukrayaan|venus mission|venus',
        'response': '''Shukrayaan-1 is ISRO's planned orbital mission to Venus:
        - Launch planned for December 2024
        - Will study Venus' surface and atmosphere
        - Carry 12 scientific instruments
        - Focus on atmospheric chemistry and surface mapping
        - Mission life of 4 years
        The mission aims to understand Venus' geological and atmospheric processes.'''
    },
    'nisar': {
        'pattern': r'nisar|nasa collaboration|earth observation satellite',
        'response': '''NISAR (NASA-ISRO Synthetic Aperture Radar):
        - Joint venture between NASA and ISRO
        - Launch planned for 2024
        - Will map entire Earth in 12 days
        - Monitor ecosystems, ice sheets, and natural hazards
        - Uses advanced radar imaging
        - Cost-effective solution for global earth observation'''
    },
    'space_station': {
        'pattern': r'space station|orbital platform|indian space station',
        'response': '''ISRO's Space Station Plans:
        - Plans for 20-tonne space station
        - To be launched in phases after Gaganyaan
        - Will support microgravity experiments
        - Planned orbit of 400km altitude
        - Focus on space tourism and research
        - Indigenous development and launch capability
        Expected to be operational by 2035.'''
    },
    'commercial': {
        'pattern': r'commercial|business|private sector|space economy',
        'response': '''ISRO's Commercial Activities:
        - NewSpace India Limited (NSIL) commercial arm
        - Launch services for international satellites
        - Technology transfer to industries
        - Satellite data services
        - Private sector participation in space
        - Support for space startups
        Contributing significantly to global space economy.'''
    },
    'scientists': {
        'pattern': r'scientist|vikram sarabhai|abdul kalam|k sivan|director',
        'response': '''Notable ISRO Scientists:
        - Dr. Vikram Sarabhai (Founder)
        - Dr. APJ Abdul Kalam (Missile Man)
        - Dr. Satish Dhawan (Former Chairman)
        - Dr. K Sivan (Former Chairman)
        - Dr. S Somanath (Current Chairman)
        Their contributions shaped India's space program.'''
    },
    'facilities': {
        'pattern': r'facility|center|laboratory|launch pad|sriharikota',
        'response': '''ISRO's Major Facilities:
        - Satish Dhawan Space Centre, Sriharikota (Launch center)
        - Space Applications Centre, Ahmedabad
        - Vikram Sarabhai Space Centre, Thiruvananthapuram
        - ISRO Satellite Centre, Bangalore
        - Liquid Propulsion Systems Centre
        - Physical Research Laboratory, Ahmedabad'''
    },
    'deep_space': {
        'pattern': r'deep space|interplanetary|solar system|exploration',
        'response': '''ISRO's Deep Space Missions:
        - Mars Orbiter Mission (Mangalyaan)
        - Chandrayaan series (Moon missions)
        - Aditya-L1 (Solar mission)
        - Future missions planned:
          * Shukrayaan-1 (Venus)
          * Mars Orbiter Mission 2
          * Jupiter mission studies'''
    },
    'climate': {
        'pattern': r'climate|environment|earth observation|weather',
        'response': '''ISRO's Climate Monitoring:
        - INSAT series for weather monitoring
        - OCEANSAT for ocean and atmospheric studies
        - SCATSAT-1 for weather forecasting
        - SARAL for sea surface studies
        - RESOURCESAT for resource monitoring
        Supporting climate change research and disaster management.'''
    },
    'navigation': {
        'pattern': r'navigation|navic|irnss|gps',
        'response': '''NavIC (Navigation with Indian Constellation):
        - India's indigenous GPS system
        - 8 satellites in orbit
        - Covers India and region up to 1500 km
        - Accuracy better than 20 meters
        - Applications in:
          * Transportation
          * Emergency services
          * Maritime operations
          * Telecommunications'''
    },
    'recovery': {
        'pattern': r'recovery|landing|reusable|return mission',
        'response': '''ISRO's Recovery Programs:
        - Space Capsule Recovery Experiment (SRE)
        - Reusable Launch Vehicle (RLV) program
        - Crew Module Atmospheric Re-entry Experiment
        - Pad Abort Test for Gaganyaan
        - Future plans for reusable rockets
        Developing capabilities for human spaceflight and cost reduction.'''
    }
}

def get_openai_response(query: str) -> str:
    """Get a response from Ollama using streaming mode."""
    try:
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2",  # or "llama3.2:latest"
            "prompt": f"""
You are Outreach Bot, a friendly virtual assistant working for ISRO (Indian Space Research Organisation).
Never call yourself Rohan or any other name. You are always 'Outreach Bot'.
Speak in a helpful tone and answer clearly in either Hindi or English. 
User's query: {query}
""",
            "stream": True
        }

        response = requests.post(ollama_url, json=payload, stream=True)
        response.raise_for_status()

        result = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line.decode("utf-8"))
                    result += json_line.get("response", "")
                except json.JSONDecodeError:
                    continue

        return result.strip()

    except Exception as e:
        return f"Error occurred: {e}"


# def get_openai_response(query: str) -> str:
#     """Use local Ollama LLM to get a response for unknown queries."""
#     try:
#         ollama_url = "http://localhost:11434/api/generate"
#         payload = {
#             "model": "llama3.2",  # change to your model if needed
#             "prompt": f"You are ISRO Space Assistant. {query}",
#             "stream": False
#         }

#         response = requests.post(ollama_url, json=payload)
#         result = response.json()

#         return result.get("response", "I'm sorry, I couldn't fetch a proper response.")
    
#     except Exception as e:
#         return f"Oops! Local LLM failed to respond. Error: {str(e)}"
    
def get_chat_response(message: str) -> str:
    """Get response for user message using knowledge base or OpenAI."""
    message = message.lower().strip()
    
    # Score-based matching for better accuracy
    matches = []
    for topic, data in ISRO_KNOWLEDGE.items():
        pattern = data['pattern']
        # Find all matches in the message
        if re.findall(pattern, message):
            # Calculate match score based on number of words matched
            matched_words = len(re.findall(r'\w+', re.findall(pattern, message)[0]))
            total_words = len(message.split())
            score = matched_words / total_words
            matches.append((topic, score, data['response']))
    
    if matches:
        # Sort by score and get the best match
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][2]
    
    # If no match found in knowledge base, use OpenAI
    return get_openai_response(message)

@app.route('/virtual-tour')
def virtual_tour():
    return render_template('virtual_tour.html')
 
@app.route('/log_entry', methods=['GET', 'POST'])
def log_entry():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        college = request.form['college']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        total_students = request.form['total_students']
        total_faculties = request.form['total_faculties']
        feedback = request.form['feedback']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get feedback ratings
        lecture_rating = request.form.get('Lecture_&_Interaction', '')
        display_rating = request.form.get('Display_&_Explanation', '')
        exhibition_rating = request.form.get('Exhibition_of_Models', '')
        video_rating = request.form.get('Video_Show', '')
        selfie_rating = request.form.get('Selfie_Corner', '')
        overall_rating = request.form.get('Overall_Arrangements', '')
        
        # Handle video feedback if present
        video_feedback_url = ''
        if 'video_feedback' in request.files:
            video_file = request.files['video_feedback']
            if video_file:
                filename = secure_filename(f"video_feedback_{name}_{timestamp.replace(':', '-').replace(' ', '_')}.webm")
                video_path = os.path.join(STATIC_FOLDER, 'video_feedback', filename)
                video_file.save(video_path)
                video_feedback_url = f"/static/video_feedback/{filename}"
        
        # Combine all data
        row = [
            timestamp, name, role, college, mobile_number, email, 
            total_students, total_faculties,
            lecture_rating, display_rating, exhibition_rating,
            video_rating, selfie_rating, overall_rating,
            feedback, video_feedback_url
        ]
        
        # Store in Google Sheets
        if append_to_sheet(row):
            flash('Feedback submitted successfully!', 'success')
        else:
            flash('Error submitting feedback. Please try again.', 'error')

        return redirect('/')
    return render_template('log_entry.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').lower()
    
    # Get response from knowledge base
    reply = get_chat_response(message)
    
    return jsonify({
        'reply': reply
    })

@app.route("/bot", methods=["GET", "POST"])
def chatbot():
    return render_template('chatbot.html')


@app.route("/stream_response", methods=["POST"])
def stream_response():
    if not request.json:
        return jsonify({"error": "No JSON data provided"}), 400
    user_input = request.json.get("message")

    def generate():
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "llama3.2",
            "prompt": f"""
You are Outreach Bot, a friendly virtual assistant working for ISRO (Indian Space Research Organisation).
Never call yourself Rohan or any other name. You are always 'Outreach Bot'.
Respond helpfully and respectfully.

User's message: {user_input}
""",
            "stream": True
        }

        with requests.post(url, json=data, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    try:
                        part = json.loads(line.decode("utf-8"))
                        token = part.get("response", "")
                        yield f"data: {token}\n\n"
                    except Exception as e:
                        yield f"data: [Error parsing response]\n\n"

    return Response(generate(), content_type="text/event-stream")

#game routes
@app.route('/game')
def game():
    return render_template('game.html')


# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/admin/get_data', methods=['POST'])
@login_required
def get_data():
    filters = {}
    
    # Parse date filters
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    if date_from:
        filters['date_from'] = datetime.datetime.strptime(date_from, '%Y-%m-%d')
    if date_to:
        filters['date_to'] = datetime.datetime.strptime(date_to, '%Y-%m-%d')
    
    # Parse other filters
    college = request.form.get('college')
    if college:
        filters['college'] = college.strip()
        
    role = request.form.get('role')
    if role:
        filters['role'] = role.lower().strip()
    
    # Get filtered data
    data = get_filtered_data(filters)
    return jsonify(data)

@app.route('/videos')
def videos():
    video_data = {
        'gsat': {
            'title': 'GSAT-11: High Throughput Satellite',
            'description': 'India\'s Advanced Communications Gateway',
            'video_url': '/static/videos/gsat-11-english.mp4.mp4',
            'thumbnail': '/static/images/gsat-thumb.jpg'
        },
        'mangalyaan': {
            'title': 'Mars Orbiter Mission',
            'description': 'India\'s Journey to Mars',
            'video_url': '/static/videos/Mangalyan-Jan-2017 (1).mp4',
            'thumbnail': '/static/images/mangalyaan-thumb.jpg'
        },
        'adityal1': {
            'title': 'Aditya L1: India\'s Solar Mission',
            'description': 'Journey to Study the Sun',
            'video_url': '/static/videos/Adtiya-L1-17-02-2023 .mp4',
            'thumbnail': '/static/images/adityal1-thumb.jpg'
        },
        'antarctic': {
            'title': 'Bharti Research Station',
            'description': 'ISRO\'s Antarctic Research',
            'video_url': '/static/videos/Antarctica_Bharti_31Jan2016.mp4',
            'thumbnail': '/static/images/antarctic-thumb.jpg'
        }
    }
    return render_template('videos.html', videos=video_data)

@app.route('/future-missions')
def future_missions():
    missions_data = {
        'gaganyaan': {
            'title': 'Gaganyaan',
            'launch': '2026',
            'description': 'India\'s first human spaceflight mission, aiming to demonstrate human spaceflight capability to low Earth orbit.',
            'key_features': [
                'Crew module designed for 3 astronauts',
                'Mission duration of 7 days',
                'Orbital altitude of 400 km',
                'Environmental control and life support systems',
                'Emergency escape system',
                'Real-time health monitoring'
            ],
            'image': '/static/images/future/gaganyaan.jpg'
        },
        'trishna': {
            'title': 'TRISHNA',
            'launch': '2026',
            'description': 'Thermal infraRed Imaging Satellite for High resolution Natural resource Assessment.',
            'key_features': [
                'High-resolution thermal imaging',
                'Water resource monitoring',
                'Agriculture and forestry applications',
                'Urban heat island studies',
                'Climate change impact assessment'
            ],
            'image': '/static/images/future/trishna.jpg'
        },
        'adityal2': {
            'title': 'Aditya-L2',
            'launch': '2026',
            'description': 'Follow-up solar mission to study advanced solar phenomena and space weather.',
            'key_features': [
                'Advanced coronagraph',
                'Solar wind studies',
                'Magnetic field mapping',
                'Space weather prediction',
                'Enhanced solar observation capabilities'
            ],
            'image': '/static/images/future/adityal2.jpg'
        },
        'mangalyaan2': {
            'title': 'Mangalyaan-2',
            'launch': '2027',
            'description': 'Second Mars Orbiter Mission with enhanced capabilities for detailed Mars exploration.',
            'key_features': [
                'Advanced scientific instruments',
                'Higher resolution cameras',
                'Extended mission life',
                'Improved communication capabilities',
                'Focus on Mars atmosphere and surface composition'
            ],
            'image': '/static/images/future/mangalyaan2.jpg'
        },
        'chandrayaan4': {
            'title': 'Chandrayaan-4',
            'launch': '2028',
            'description': 'The next phase of India\'s lunar exploration program, focusing on sample return missions.',
            'key_features': [
                'Lunar sample return capability',
                'Advanced landing technologies',
                'Extended surface operations',
                'Deep drilling equipment',
                'Improved communication systems'
            ],
            'image': '/static/images/future/chandrayaan4.jpg'
        },
        'shukrayaan': {
            'title': 'Shukrayaan',
            'launch': '2028',
            'description': 'India\'s first mission to Venus, designed to study the hottest planet in our solar system.',
            'key_features': [
                'Venus atmospheric studies',
                'Surface mapping radar',
                'Chemical composition analysis',
                'Study of Venus\' super-rotation',
                'Investigation of Venusian atmosphere'
            ],
            'image': '/static/images/future/shukrayaan.jpg'
        },
        'spacestation': {
            'title': 'Bharatiya Antariksh Station',
            'launch': '2035',
            'description': 'India\'s first space station, providing platform for extended microgravity research.',
            'key_features': [
                '20-tonne modular space station',
                'Permanent human presence capability',
                'Scientific research laboratories',
                'Indigenous life support systems',
                'International collaboration opportunities'
            ],
            'image': '/static/images/future/spacestation.jpg'
        }
    }
    return render_template('future_missions.html', missions=missions_data)

@app.route('/nrsc')
def nrsc():
    nrsc_data = {
        'agriculture': {
            'title': 'Agriculture',
            'overview': 'Satellite derived seasonal cropping pattern, experiments on yield estimation, estimation of net-sown crop area and agricultural drought assessment studies are conducted.',            'description': 'Presently, studies are in progress on development of new techniques and methodologies for providing space inputs for Crop Insurance Decision Support System (CIDSS), crop intensification, mapping and inventory and assessment of high value crops, horticulture inventory, agricultural drought vulnerability assessment, soil-vegetation-atmosphere flux studies over different agro-ecosystems, pilot studies on hyper spectral remote sensing applications for crop condition assessment.\n\nThe future vision of agriculture applications are - Crop Surveillance Systems, local to regional scales, customized information through user friendly Dashboards for Multi-purpose Decision Support.',
            'image': '/static/images/nrsc/agriculture.jpg'
        },
        'disaster_management': {
            'title': 'Disaster Management Support',
            'overview': 'As part of Disaster Management Support Programme (DMSP), Decision Support Centre is established at NRSC for monitoring natural disasters.',
            'description': '''Decision Support Centre monitors natural disasters viz. flood, cyclone, agricultural drought, landslides, earthquakes and forest fires in near real-time using space and aerial remote sensing based inputs.
            
            National Database for Emergency Management (NDEM) serves as national repository of GIS based database for entire country coupled with set of Decision Support System tools to assist the State / Central Disaster Management Authorities in decision making during emergency situations.
            
            Current activities include: Near Real Time Flood & Cyclone monitoring & mapping, Flood Hazard/Risk Zonation, Spatial Flood Early Warning, forest fire alerts, landslide zonation and inventory, agricultural drought studies and Capacity Building.''',
            'image': '/static/images/nrsc/disaster.jpg'
        },
        'forestry': {
            'title': 'Forestry and Ecology',
            'overview': 'The forest resources being scarce and under tremendous anthropogenic pressure, focus is on sustainable management and carbon sequestration.',
            'description': '''Forestry and Ecology studies at NRSC focus on development of automated processing of multi-temporal and multi sensor data, three dimensional description of forest structure and distribution.
            
            Key activities include: Analysis of forest cover change, spatial biomass estimation, Community Biodiversity characterization, Forest fire alert system, inputs to working plan and wild life plan preparation, Forest carbon sequestration, Inputs to UNFCCC, etc.''',
            'image': '/static/images/nrsc/forestry.jpg'
        },
        'geosciences': {
            'title': 'Geosciences',
            'overview': 'Geosciences group focuses on groundwater studies, mineral exploration, geoenvironmental studies, and geohazards assessment.',
            'description': '''Major projects include National Geomorphology and Lineament Mapping (NGLM), National Rural Drinking Water Program (NRDWP), Mineral exploration studies for Diamond, Iron, Phosphate Manganese, Bauxite etc., Seasonal Landslide Inventory Mapping (SLIM) and Landslide Susceptibility Zonation (LSZ).
            
            The group also conducts research in earthquake studies, geotechnical studies, coal fire mapping, geoenvironmental zonation and planetary studies.''',
            'image': '/static/images/nrsc/geosciences.jpg'
        },
        'land_use': {
            'title': 'Land Use/Land Cover',
            'overview': 'Provides comprehensive mapping and monitoring of land use and land cover changes at various scales.',
            'description': '''Annual LULC information on national spatial databases enables monitoring of temporal dynamics of agricultural ecosystems, forest conversions, surface water bodies, etc.
            
            Mapping is done at various scales:
            - 1:250000 scale annually
            - 1:50000 scale every 5 years
            - 1:10000 scale for water land resources planning at village/taluk level
            
            Wasteland mapping and monitoring is carried out at 1:50000 and 1:25000 scales.''',
            'image': '/static/images/nrsc/landuse.jpg'
        },
        'rural_development': {
            'title': 'Rural Development',
            'overview': 'Focuses on water and land conservation through systematic planning and implementation of development plans.',
            'description': '''Key initiatives include:
            - Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)
            - Accelerated Irrigation Benefit Programme (AIBP)
            - Integrated Watershed Management Programme (IWMP)
            - On Farm Water Management (OFWM)
            - National Health Resource Repository (NHRR) Project
            
            Applications provide customized near real-time natural resources databases and tools for analytics.''',
            'image': '/static/images/nrsc/rural.jpg'
        },
        'soils': {
            'title': 'Soils',
            'overview': 'Generates comprehensive soil maps and degradation assessments for land management.',
            'description': '''Key activities include:
            - Land degradation mapping for soil conservation/reclamation
            - Mapping of salt affected and water logging areas
            - Soil erosion mapping
            - Preparation of soil maps at various scales (1:25,000, 1:12,500, 1:10K)
            - Studies on Soil Carbon Dynamics
            - Remote sensing based soil mapping through hybrid approach''',
            'image': '/static/images/nrsc/soils.jpg'
        },
        'urban': {
            'title': 'Urban & Infrastructure',
            'overview': 'Provides geospatial technology support for Urban Local Bodies and infrastructure development.',
            'description': '''Applications include:
            - Urban and regional planning
            - Route alignment for road, rail, oil/gas pipeline
            - Site suitability analysis
            - Facility & Utility planning
            - Environmental impact assessment
            
            Major projects:
            - National Urban Information System for 142 towns
            - Regional planning under National Capital Region
            - Monitoring of GAIL pipeline corridor
            - Mapping of 242 cities under AMRUT program''',
            'image': '/static/images/nrsc/urban.jpg'
        },
        'water_resources': {
            'title': 'Water Resources',
            'overview': 'Provides key inputs for planning, monitoring and management of water resources.',
            'description': '''Key activities include:
            - Performance evaluation of irrigation commands
            - Assessment of irrigation infrastructure
            - Feasibility studies for Inter Linking of rivers
            - Reassessment of water resources at river basin level
            - Reservoir sedimentation studies
            - Seasonal snow and water bodies monitoring
            - Snow melt runoff analysis
            
            Develops water resources information systems at state/central level.''',
            'image': '/static/images/nrsc/water.jpg'
        }
    }
    return render_template('nrsc.html', sections=nrsc_data)

@app.route('/working-models')
def working_models():
    models = {
        'demosat': {
            'title': 'DemoSat Educational Model',
            'video': '/static/videos/working_models/demosat.mp4',
            'thumbnail': '/static/images/working_models/demosat-thumb.jpg',
            'description': 'An interactive educational satellite model demonstrating key satellite components and their functions. This model helps understand satellite technology and space operations.'
        },
        'chandrayaan3': {
            'title': 'Chandrayaan-3 Mission Model',
            'video': '/static/videos/working_models/chandrayaan3.mp4',
            'thumbnail': '/static/images/working_models/chandrayaan3-thumb.jpg',
            'description': 'A detailed working model of the Chandrayaan-3 lunar mission, showcasing the lander and rover components, and demonstrating the landing sequence and surface operations.'
        },
        'telescope': {
            'title': 'Advanced Telescope Operations',
            'video': '/static/videos/working_models/telescope.mp4',
            'thumbnail': '/static/images/working_models/telescope-thumb.jpg',
            'description': 'Experience the operation of advanced astronomical telescopes used in space research. This model demonstrates tracking, imaging, and data collection techniques.'
        }
    }
    return render_template('working_models.html', models=models)
questions = [
        {
            'question': 'When was ISRO established?',
            'options': ['1969', '1972', '1975', '1980'],
            'correct': '1969',
            'explanation': 'ISRO was established in 1969 under Dr. Vikram Sarabhai.'
        },
        {
            'question': "Which was India's first satellite?",
            'options': ['Aryabhata', 'Rohini', 'Bhaskara', 'INSAT-1A'],
            'correct': 'Aryabhata',
            'explanation': "Aryabhata was launched in 1975, marking India's entry into space age."
        },
        {
            'question': "What is the name of India's Mars mission?",
            'options': ['Chandrayaan', 'Mangalyaan', 'Aditya', 'Gaganyaan'],
            'correct': 'Mangalyaan',
            'explanation': 'Mangalyaan or Mars Orbiter Mission was launched in 2013.'
        },
        {
            'question': 'Which mission successfully landed near lunar south pole?',
            'options': ['Chandrayaan-1', 'Chandrayaan-2', 'Chandrayaan-3', 'Vikram'],
            'correct': 'Chandrayaan-3',
            'explanation': 'Chandrayaan-3 achieved soft landing near lunar south pole in 2023.'
        },
        {
            'question': 'Which ISRO satellite is used for weather forecasting?',
            'options': ['INSAT-3DR', 'GSAT-10', 'Cartosat-2', 'IRS-1C'],
            'correct': 'INSAT-3DR',
            'explanation': 'INSAT-3DR is used for weather forecasting.'
        },
        {
            'question': 'Which ISRO mission discovered water on the Moon?',
            'options': ['Chandrayaan-1', 'Chandrayaan-2', 'Mangalyaan', 'Cartosat-2'],
            'correct': 'Chandrayaan-1',
            'explanation': 'Chandrayaan-1 discovered water on the moon.'
        },
        {
            'question': "What does the term 'IRNSS' stand for?",
            'options': [
                'Indian Regional Navigation Satellite System',
                'Indian Remote Navigation Satellite System',
                'International Research Navigation Satellite System',
                'Indian Revolutionary Navigation Satellite System'
            ],
            'correct': 'Indian Regional Navigation Satellite System',
            'explanation': 'Indian Regional Navigation Satellite System.'
        },
        {
            'question': 'Which satellite was launched to study the Martian surface?',
            'options': ['Mangalyaan', 'Chandrayaan-1', 'Cartosat-3', 'GSAT-9'],
            'correct': 'Mangalyaan',
            'explanation': 'Mangalyaan was launched to study the Martian surface.'
        },
        {
            'question': "What is the primary use of 'GSAT' satellites?",
            'options': ['Weather monitoring', 'Communication', 'Earth Observation', 'Navigation'],
            'correct': 'Communication',
            'explanation': 'Communication is the main use of GSAT satellites.'
        },
        {
            'question': "Which ISRO launch vehicle is called 'Bahubali'?",
            'options': ['PSLV', 'GSLV Mk III', 'GSLV Mk II', 'SSLV'],
            'correct': 'GSLV Mk III',
            'explanation': 'GSLV Mk III is called Bahubali.'
        },
        {
            'question': 'What type of data does the Cartosat series provide?',
            'options': ['Weather data', 'High-resolution images', 'Communication data', 'Astrophysical data'],
            'correct': 'High-resolution images',
            'explanation': 'Cartosat series provides high-resolution images.'
        },
        {
            'question': "What is Aditya-L1's mission objective?",
            'options': ['Study Sun', 'Study Moon', 'Study Mars', 'Study Venus'],
            'correct': 'Study Sun', 
            'explanation': "Aditya-L1 is India's first solar mission."
        },
        {
            'question': "Which ISRO mission discovered water on the Moon?",
            'options': ['Chandrayaan-1', 'Chandrayaan-2', 'Mangalyaan', 'Cartosat-2'],
            'correct': 'Chandrayaan-1',
            'explanation': 'Chandrayaan-1 discovered the water on Moon.'
            
        },
        {
            'question': "What is the primary function of Cartosat satellites?",
            'options': ['Earth observation', 'Weather forecasting', 'Communication', 'Navigation'],
            'correct': 'Earth observation',
            'explanation': 'Earth observation is the primary function of Cartosat satellite.'
        },
        {
            'question': "Which is the heaviest launch vehicle of ISRO?",
            'options': ['GSLV Mk III', 'PSLV', 'SSLV', 'GSLV Mk II'],
            'correct': 'GSLV Mk III',
            'explanation': 'GSLV Mk III is the heaviest launch vehicle of ISRO .'
            
        },
        {
            'question': "Which Indian scientist is known as the Father of the Indian Space Program?",
            'options': ['Dr. Vikram Sarabhai', 'Dr. APJ Abdul Kalam', 'Dr. Homi Bhabha', 'Dr. Satish Dhawan'],
            'correct': 'Dr. Vikram Sarabhai',
            'explanation': 'Dr. Vikram Sarabhai is known as the Father of the Indian Space Program.'
            
        },
        {
            'question': "Which ISRO satellite is used for ocean observation?",
            'options': ['Oceansat', 'Cartosat', 'INSAT', 'GSAT'],
            'correct': 'Oceansat',
            'explanation': 'Oceansat is used for ocean observation.'
            
        },
        {
            'question': "What is the purpose of the RISAT satellite series?	",
            'options': ['Radar imaging', 'Navigation', 'Weather forecasting', 'Communication'],
            'correct': 'Radar imaging',
            'explanation': 'Radar imaging is the purpose of the RISAT satellite series.'
            
        },
        {
            'question': "Which orbit is used by geostationary satellites?	",
            'options': ['Geostationary orbit', 'Low Earth orbit', 'Medium Earth orbit', 'Polar orbit'],
            'correct': 'Geostationary orbit',
            'explanation': 'Radar imaging is the purpose of the RISAT satellite series.'
        },
        {
            'question': "Which of the following is a satellite navigation system by ISRO?",
            'options': ['NAVIC', 'GPS', 'Galileo', 'GLONASS'],
            'correct': 'NAVIC',
            'explanation': 'NAVIC is a satellite navigation system by ISRO.'
        },
        {
            'question': "Which is the first Indian satellite launched from foreign soil?	",
            'options': ['Aryabhata', 'Bhaskara-I', 'INSAT-1A', 'GSAT-1'],
            'correct': 'Aryabhata',
            'explanation': 'Aryabhata is the first Indian satellite launched from foreign soil.'
        },
        {
            'question': "What is the main role of INSAT satellites?	",
            'options': ['Communication', 'Navigation', 'Weather monitoring', 'Remote sensing'],
            'correct': 'Communication',
            'explanation': 'Communication plays a main role in INSAT satellite.'
        },
        {
            'question': "which ISRO center is responsible for developing launch vehicles?",
            'options': ['VSSC', 'SAC', 'ISTRAC', 'ISAC'],
            'correct': 'VSSC',
            'explanation': 'VSSC ISRO center is responsible for developing launch vehicles'
        },
        {
            'question': "Which is the smallest launch vehicle by ISRO?",
            'options': ['SSLV', 'PSLV', 'GSLV Mk II', 'GSLV Mk III'],
            'correct': 'SSLV',
            'explanation': 'SSLV is the smallest launch vehicle by ISRO'
        },
        {
            'question': "Which Indian spaceport is used for satellite launches?",
            'options': ['Sriharikota', 'Thumba', 'Chennai', 'Mumbai'],
            'correct': 'Sriharikota',
            'explanation': 'Sriharikota Indian spaceport is used for satellite launches '
        },
        {
            'question': "Which type of satellite resolution measures the level of detail in spectral data?",
            'options': ['Spectral resolution', 'Spatial resolution', 'Temporal resolution', 'Radiometric resolution'],
            'correct': 'Spectral resolution',
            'explanation': 'Sriharikota Indian spaceport is used for satellite launches '
        },
        {
            'question': "What is the Kepler telescope known for discovering?",
            'options': ['Exoplanets', 'Black holes', 'Galaxies', 'Supernovae'],
            'correct': 'Exoplanets',
            'explanation': 'Exoplanets is the Kepler telescope known for discovering'
        },
        {
            'question': "Which Indian satellite series is focused on studying Earth’s resources?",
            'options': ['Resourcesat', 'Cartosat', 'Oceansat', 'RISAT'],
            'correct': 'Resourcesat',
            'explanation': 'Resourcesat satellite series is focused on studying Earth’s resources'
        },
        {
            'question': "Which was the first reusable spacecraft?",
            'options': ['Space Shuttle Columbia', 'Apollo 11', 'Soyuz', 'Skylab'],
            'correct': 'Space Shuttle Columbia',
            'explanation': 'Space Shuttle Columbia is first reusable spacecraft'
        },
        {
            'question': "Which satellite launched by ESA maps cosmic microwave background radiation?",
            'options': ['Planck', 'Herschel', 'Gaia', 'Kepler'],
            'correct': 'Planck',
            'explanation': 'Planck launched by ESA maps cosmic microwave background radiation.'
        },
        {
            'question': "What is the orbital inclination of a Sun-synchronous orbit?",
            'options': ['98°', '90°', '51°', '23.5°'],
            'correct': '98°',
            'explanation': '98° is the orbital inclination of a Sun-synchronous orbit.'
        },
        {
            'question': "Which space agency operates the H-IIA rocket?",
            'options': ['JAXA', 'NASA', 'ESA', 'ISRO'],
            'correct': 'JAXA',
            'explanation': 'JAXA space agency operates the H-IIA rocket.'
        },
        {
            'question': "Which space agency launched the Rosetta mission to study a comet?",
            'options': ['ESA', 'NASA', 'ISRO', 'CNSA'],
            'correct': 'ESA',
            'explanation': 'ESA space agency launched the Rosetta mission to study a comet '
        },
        {
            'question': "What is the main purpose of the Sentinel satellites launched by ESA?",
            'options': ['Earth observation', 'Communication', 'Navigation', 'Space exploration'],
            'correct': 'Earth observation',
            'explanation': 'Earth observation is the main purpose of the Sentinel satellites launched by ESA '
        },
        {
            'question': "What is the maximum payload capacity of the SpaceX Falcon Heavy?",
            'options': ['63,800 kg to LEO', '25,000 kg to LEO', '50,000 kg to LEO', '75,000 kg to LEO'],
            'correct': '63,800 kg to LEO',
            'explanation': '63,800 kg to LEO is the maximum payload capacity of the SpaceX Falcon Heavy.'
        },
        {
            'question': "Which satellite orbits at the Earth-Moon Lagrange Point 2 (EML2)?",
            'options': ['James Webb Space Telescope', 'Hubble Space Telescope', 'Gaia', 'Kepler'],
            'correct': 'James Webb Space Telescope',
            'explanation': 'James Webb Space Telescope is the satellite orbits at the Earth-Moon Lagrange Point 2.'
        },
        {
            'question': "Which satellite orbits at the Earth-Moon Lagrange Point 2 (EML2)?",
            'options': ['James Webb Space Telescope', 'Hubble Space Telescope', 'Gaia', 'Kepler'],
            'correct': 'James Webb Space Telescope',
            'explanation': 'James Webb Space Telescope is the satellite orbits at the Earth-Moon Lagrange Point 2.'
        },
        {
            'question': "Which space mission studied Pluto and its moons?",
            'options': ['New Horizons', 'Voyager 2', 'Cassini', 'Galileo'],
            'correct': 'New Horizons',
            'explanation': 'New Horizons space mission studied Pluto and its moons.'
        },
        
    ]

#LEADERBOARD = []


@app.route('/quiz')
def quiz():
    return render_template('quiz_start.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    data = request.json
    session['username'] = data['name']
    session['score'] = 0
    session['current_index'] = 0
    session['score_saved'] = False

    random.shuffle(questions)
    session['quiz_questions'] = questions[:10]  # only 10 questions

    return '', 200

@app.route('/quiz/play')
def quiz_play():
    return render_template('quiz.html')

@app.route('/get_quiz_question', methods=['POST'])
def get_quiz_question():
    index = session.get('current_index', 0)
    questions = session.get('quiz_questions', [])

    if index >= len(questions):
        return jsonify({'quiz_over': True})

    question = questions[index]
    session['current_index'] = index + 1

    return jsonify(question)

    '''question = random.choice(questions)
    return jsonify(question)'''

@app.route('/update_score', methods=['POST'])
def update_score():
    session['score'] += 10
    return '', 200

@app.route('/quiz/result')
def quiz_result():
    daily_leaderboard_reset()

    name = session.get('username')
    score = session.get('score')

    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()

    # ✅ SAVE ONLY ONCE
    if not session.get('score_saved', False):
        cursor.execute(
            "INSERT INTO leaderboard (name, score) VALUES (?, ?)",
            (name, score)
        )
        conn.commit()
        session['score_saved'] = True   # 👈 LOCK IT

    cursor.execute(
        "SELECT name, score FROM leaderboard ORDER BY score DESC"
    )
    leaderboard = cursor.fetchall()

    conn.close()

    return render_template(
        'quiz_result.html',
        name=name,
        score=score,
        leaderboard=leaderboard
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
