import os
import pickle
from difflib import SequenceMatcher


# ---------------------------------------
# 1. MACHINE LEARNING CLASSIFICATION
# ---------------------------------------

DEPARTMENTS = {
    "Road Infrastructure": "Municipal Roads",
    "Water Supply": "Water Supply Department",
    "Electricity": "Electricity Department",
    "Waste Management": "Sanitation Department",
    "Other": "Public Works Department"
}

# Load trained ML model

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "complaint_model.pkl"
)

with open(MODEL_PATH, "rb") as file:
    ml_model = pickle.load(file)


def classify_complaint(description):

    prediction = ml_model.predict([description])[0]

    return prediction

# ---------------------------------------
# 2. SEVERITY CALCULATION
# ---------------------------------------

def calculate_severity(description):

    text = description.lower()

    severity = 3

    high_risk_words = [
        "accident", "injury", "dangerous",
        "emergency", "collapse", "fire",
        "exposed wire", "electric shock"
    ]

    medium_risk_words = [
        "heavy leakage", "major", "blocked",
        "overflow", "completely broken",
        "severe", "flooding"
    ]

    low_risk_words = [
        "minor", "small", "slight",
        "temporary"
    ]

    for word in high_risk_words:
        if word in text:
            severity += 2

    for word in medium_risk_words:
        if word in text:
            severity += 1

    for word in low_risk_words:
        if word in text:
            severity -= 1

    return max(1, min(severity, 10))


# ---------------------------------------
# 3. PRIORITY DETERMINATION
# ---------------------------------------

def determine_priority(severity):

    if severity >= 7:
        return "High"

    elif severity >= 4:
        return "Medium"

    else:
        return "Low"


# ---------------------------------------
# 4. DEPARTMENT ASSIGNMENT
# ---------------------------------------

def assign_department(category):

    return DEPARTMENTS.get(
        category,
        "Public Works Department"
    )


# ---------------------------------------
# 5. DUPLICATE DETECTION
# ---------------------------------------

def detect_duplicate(connection, description, location, category):

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT complaint_id, description, duplicate_count
        FROM complaints
        WHERE LOWER(TRIM(location)) = LOWER(TRIM(%s))
        AND category = %s
        ORDER BY created_at DESC
        LIMIT 20
    """

    cursor.execute(query, (location, category))

    existing_complaints = cursor.fetchall()

    cursor.close()

    new_text = description.lower().strip()

    for complaint in existing_complaints:

        old_text = complaint["description"].lower().strip()

        similarity = SequenceMatcher(
            None, new_text, old_text
        ).ratio()

        if similarity >= 0.55:

            return {
                "duplicate_of": complaint["complaint_id"],
                "similarity": round(similarity * 100, 2)
            }

    return {
        "duplicate_of": None,
        "similarity": 0
    }


# ---------------------------------------
# 6. COMPLETE INTELLIGENCE ANALYSIS
# ---------------------------------------

def analyze_complaint(description, location, connection):

    category = classify_complaint(description)

    severity = calculate_severity(description)

    priority = determine_priority(severity)

    department = assign_department(category)

    duplicate = detect_duplicate(
        connection,
        description,
        location,
        category
    )

    return {
        "category": category,
        "severity": severity,
        "priority": priority,
        "department": department,
        "duplicate_of": duplicate["duplicate_of"],
        "similarity": duplicate["similarity"]
    }


# ---------------------------------------
# 7. TESTING
# ---------------------------------------

if __name__ == "__main__":

    test_complaint = (
        "An electrical cable has fallen on the road "
            "and people are at risk of getting injured."
    )

    category = classify_complaint(test_complaint)

    severity = calculate_severity(test_complaint)

    priority = determine_priority(severity)

    department = assign_department(category)

    print("\n--- CITY INTELLIGENCE ENGINE ---")

    print("Complaint:", test_complaint)

    print("Category:", category)

    print("Severity:", severity, "/10")

    print("Priority:", priority)

    print("Assigned Department:", department)