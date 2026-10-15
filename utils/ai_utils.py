"""
utils/ai_utils.py - Simulated / Rule-Based Helper Features for Project Hub
Provides template-based suggestions, descriptions, and resume checklists
without requiring external paid AI APIs.
"""
import random


# ─────────────────────────────────────────────
# PROJECT IDEA SUGGESTIONS
# ─────────────────────────────────────────────
PROJECT_IDEAS = {
    'Computer Science': {
        'AI/ML': [
            'Emotion Detection System using Deep Learning',
            'Fake News Detection using NLP',
            'AI-powered Resume Screening Tool',
            'Predictive Student Performance Analytics',
            'Sign Language Recognition using CNN',
            'Medical Diagnosis Assistant using Machine Learning',
            'Smart Traffic Management with Computer Vision',
        ],
        'Web Development': [
            'Freelance Marketplace Platform',
            'Online Learning Management System',
            'Community Event Management App',
            'Real-time Collaborative Whiteboard',
            'AI-powered Job Portal',
        ],
        'Cybersecurity': [
            'Network Intrusion Detection System',
            'Password Strength Analyzer Tool',
            'Phishing URL Detector',
            'Secure File Sharing Application',
        ],
        'General': [
            'Smart Attendance System using Face Recognition',
            'Campus Navigation App',
            'Library Management System with Recommendations',
            'Student Complaint Portal',
        ]
    },
    'Electronics': {
        'IoT': [
            'Smart Home Automation System',
            'IoT-Based Health Monitoring Device',
            'Automated Irrigation System with Sensors',
            'Smart Parking Management System',
        ],
        'General': [
            'Obstacle Avoiding Robot',
            'Voice-Controlled Home Appliances',
            'Solar Energy Tracker',
        ]
    },
    'Mechanical': {
        'General': [
            'Automated Conveyor Belt System',
            'Drone-based Delivery System',
            'Waste Sorting Machine using AI',
            'Solar-Powered Vehicle Prototype',
        ]
    },
    'Civil': {
        'General': [
            'Smart Bridge Health Monitoring System',
            'Earthquake-Resistant Structure Design',
            'Water Quality Analysis System',
        ]
    }
}

TECH_STACKS = {
    'AI/ML': 'Python, TensorFlow, Keras, OpenCV, Scikit-learn, Pandas, NumPy',
    'Web Development': 'Flask/Django, React/Vue, PostgreSQL, HTML/CSS/JS, Bootstrap',
    'IoT': 'Arduino/Raspberry Pi, Python, MQTT, Firebase, C++',
    'Cybersecurity': 'Python, Wireshark, Kali Linux, Flask, SQLite',
    'Mobile': 'Flutter/React Native, Firebase, REST APIs',
    'General': 'Python, Flask, SQLite, HTML/CSS/JS, Bootstrap',
}


def suggest_projects(department, year, domain):
    """
    Rule-based suggestion function returning curated project ideas.
    """
    dept_map = {
        'CSE': 'Computer Science', 'IT': 'Computer Science',
        'ECE': 'Electronics', 'EEE': 'Electronics',
        'MECH': 'Mechanical', 'CIVIL': 'Civil'
    }
    dept_category = dept_map.get(department, 'Computer Science')

    ideas_pool = PROJECT_IDEAS.get(dept_category, PROJECT_IDEAS['Computer Science'])
    domain_ideas = ideas_pool.get(domain, ideas_pool.get('General', []))
    general_ideas = ideas_pool.get('General', [])
    combined = list(set(domain_ideas + general_ideas))
    suggestions = random.sample(combined, min(5, len(combined)))

    tech = TECH_STACKS.get(domain, TECH_STACKS['General'])
    results = []
    for idea in suggestions:
        results.append({
            'title': idea,
            'description': f"This project focuses on {idea.lower()} and is well-suited for {year} year {dept_category} students.",
            'tech_stack': tech,
            'difficulty': 'Intermediate',
            'duration': '3 months',
        })
    return results


def generate_description(title, domain, tech_stack):
    """
    Template-based description generator for project proposals.
    """
    description = (
        f"{title} is an innovative {domain} project designed to solve real-world challenges using modern technology. "
        f"The system leverages {tech_stack} to deliver a scalable, efficient, and user-friendly solution. "
        f"By automating key processes and integrating intelligent features, the project aims to improve productivity "
        f"and provide meaningful insights to its users."
    )

    problem_statement = (
        f"In today's fast-paced environment, the existing approaches to {domain.lower()} problems lack automation, "
        f"scalability, and intelligent decision-making capabilities. {title} addresses these gaps by providing "
        f"a comprehensive solution built on {tech_stack}. The system eliminates manual effort, reduces errors, "
        f"and empowers users with data-driven insights to make better decisions."
    )

    suggested_stack = tech_stack if tech_stack else TECH_STACKS.get(domain, TECH_STACKS['General'])

    return {
        'description': description,
        'problem_statement': problem_statement,
        'tech_stack': suggested_stack,
    }


def analyze_resume(filename):
    """
    Heuristic rule-based resume reviewer and readiness checklist.
    Provides standardized suggestions without sending files to third-party APIs.
    """
    ext = (filename or '').rsplit('.', 1)[-1].lower() if '.' in (filename or '') else ''
    # Heuristic scoring based on preferred standard document format
    score = 85 if ext == 'pdf' else 75

    strengths = [
        'Clear, industry-standard document format submitted',
        'Structured section headers and organized presentation',
        'Technical profile aligned with engineering domain expectations',
        'Project portfolio included for practical demonstration',
    ]
    weaknesses = [
        'Ensure measurable outcome metrics (e.g. % speedup, user volume) are highlighted',
        'Verify contact details and active repository / portfolio links are up-to-date',
        'Tailor core technical keywords specifically to target project requirements',
    ]
    suggestions = [
        'Add a concise 2-3 sentence executive summary tailored to your focus area',
        'Use strong action verbs (e.g., "Engineered", "Optimized", "Architected") for bullet points',
        'Include verifiable GitHub repository links and deployment URLs for submitted projects',
        'Add relevant technical certifications and course milestones',
        'Ensure formatting is clean, single/dual column, and easily parseable by ATS scanners',
    ]

    return {
        'score': score,
        'grade': 'A' if score >= 85 else 'B',
        'strengths': strengths,
        'weaknesses': weaknesses,
        'suggestions': suggestions,
    }
