"""
utils/ai_utils.py - Mock AI Features for Project Hub
Replace these with actual OpenAI API calls if available.
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
    Mock AI function to suggest project ideas.
    Returns a list of project suggestions with details.
    """
    # Map department to category
    dept_map = {
        'CSE': 'Computer Science', 'IT': 'Computer Science',
        'ECE': 'Electronics', 'EEE': 'Electronics',
        'MECH': 'Mechanical', 'CIVIL': 'Civil'
    }
    dept_category = dept_map.get(department, 'Computer Science')

    ideas_pool = PROJECT_IDEAS.get(dept_category, PROJECT_IDEAS['Computer Science'])
    domain_ideas = ideas_pool.get(domain, ideas_pool.get('General', []))
    # Also include general ideas
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
            'difficulty': random.choice(['Beginner', 'Intermediate', 'Advanced']),
            'duration': random.choice(['1 month', '2 months', '3 months', '6 months']),
        })
    return results


def generate_description(title, domain, tech_stack):
    """
    Mock AI function to generate project description, problem statement, and tech stack.
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
    Mock AI resume analyzer.
    Returns a score, strengths, weaknesses, and suggestions.
    """
    score = random.randint(55, 95)

    strengths = [
        'Clear and organized layout',
        'Relevant technical skills listed',
        'Educational background is well-presented',
        'Projects demonstrate practical experience',
    ]
    weaknesses = [
        'Missing a strong professional summary',
        'No quantifiable achievements mentioned',
        'Limited internship or work experience',
        'Skills section could be more specific',
    ]
    suggestions = [
        'Add a compelling professional summary at the top',
        'Use action verbs and quantify your achievements (e.g., "improved performance by 40%")',
        'Include relevant certifications and online courses',
        'Add GitHub/LinkedIn profile links',
        'Tailor your resume for each specific job application',
        'Keep the resume to 1–2 pages maximum',
        'Use consistent formatting throughout',
    ]

    random.shuffle(strengths)
    random.shuffle(weaknesses)
    random.shuffle(suggestions)

    return {
        'score': score,
        'grade': 'A' if score >= 85 else ('B' if score >= 70 else ('C' if score >= 55 else 'D')),
        'strengths': strengths[:3],
        'weaknesses': weaknesses[:3],
        'suggestions': suggestions[:5],
    }
