from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

import pickle


# ---------------------------------------
# 1. TRAINING DATASET
# ---------------------------------------

complaints = [

    # ROAD INFRASTRUCTURE
    "There is a large pothole on the road",
    "Road is broken and damaged",
    "Multiple cracks on the main road",
    "Footpath is completely damaged",
    "Bridge has developed cracks",
    "Road surface is uneven and unsafe",
    "Vehicles are facing problems due to potholes",
    "The road needs urgent repair",
    "The highway has a deep hole",
    "Broken footpath is creating problems for pedestrians",
    "Road construction work is incomplete",
    "The street is full of potholes",

    # WATER SUPPLY
    "There is no water supply in our area",
    "Water pipeline is leaking",
    "Drinking water is not coming from taps",
    "Water pipe has burst",
    "Heavy water leakage near our house",
    "Drainage system is blocked",
    "Sewage water is overflowing",
    "Dirty water is coming from the tap",
    "Water supply has stopped",
    "Main pipeline is damaged",
    "Flooding due to water leakage",
    "Water is continuously leaking from the pipe",

    # ELECTRICITY
    "Street light is not working",
    "There is a power outage in our area",
    "Electric wire is hanging dangerously",
    "Transformer is damaged",
    "Electric pole is broken",
    "No electricity in our locality",
    "Streetlights are not functioning",
    "Exposed electrical wires are dangerous",
    "Frequent power cuts in our area",
    "Electric shock risk due to damaged wire",
    "The electricity supply has stopped",
    "A street light needs repair",

    # WASTE MANAGEMENT
    "Garbage is scattered on the road",
    "Dustbin is overflowing",
    "Waste has not been collected",
    "There is a lot of rubbish in our area",
    "The streets are dirty due to garbage",
    "Garbage collection has not happened",
    "Trash is lying everywhere",
    "Sanitation workers are not cleaning the area",
    "The public dustbin is full",
    "Bad smell is coming from accumulated waste",
    "Litter is spread across the street",
    "Waste disposal is not happening properly",

    # OTHER
    "Public park equipment is damaged",
    "There is a problem with public facilities",
    "A public building needs maintenance",
    "The community hall is damaged",
    "There is a broken bench in the park",
    "Public property needs repair",
    "The playground equipment is broken",
    "There is an issue with a public facility",

    # ADDITIONAL ROAD COMPLAINTS
    "The road surface has become rough and uneven",
    "A deep hole has appeared near the market",
    "Vehicles cannot pass because the road is damaged",
    "There are cracks in the newly constructed road",
    "The pavement is broken near the school",
    "A damaged bridge is creating traffic problems",
    "The road is full of broken patches",
    "Repair work is required on the main street",

    # ADDITIONAL WATER COMPLAINTS
    "Water is not reaching houses in our locality",
    "A pipe is leaking continuously near the market",
    "There is a shortage of drinking water",
    "The drainage channel is overflowing",
    "Dirty sewage is spreading in the street",
    "The underground water pipe is damaged",
    "Tap water has stopped coming since morning",
    "A broken pipeline is wasting water",

    # ADDITIONAL ELECTRICITY COMPLAINTS
    "There is no power in the neighbourhood",
    "The lamp post is not illuminating the street",
    "An electrical cable has fallen on the road",
    "The power transformer is making unusual noises",
    "Electricity keeps going off repeatedly",
    "A damaged electric pole is leaning dangerously",
    "The street lamps have stopped functioning",
    "Sparks are coming from an electrical wire",

    # ADDITIONAL WASTE COMPLAINTS
    "The garbage truck has not visited our street",
    "Waste is piling up outside the houses",
    "The municipal dustbin has not been emptied",
    "The public area is covered with litter",
    "Rotting garbage is causing a foul smell",
    "The garbage collection service is irregular",
    "Plastic waste is scattered around the park",
    "The roadside dumping area needs cleaning",

    # ADDITIONAL OTHER COMPLAINTS
    "The public garden bench is broken",
    "Playground facilities need maintenance",
    "The community centre requires repairs",
    "Public toilet facilities are damaged",
    "The park gate is broken",
    "A public building has damaged windows",
    "The public seating area needs repair",
    "A community facility is not maintained"
]

labels = [

    # ORIGINAL 56 COMPLAINTS
    *["Road Infrastructure"] * 12,
    *["Water Supply"] * 12,
    *["Electricity"] * 12,
    *["Waste Management"] * 12,
    *["Other"] * 8,

    # ADDITIONAL 40 COMPLAINTS
    *["Road Infrastructure"] * 8,
    *["Water Supply"] * 8,
    *["Electricity"] * 8,
    *["Waste Management"] * 8,
    *["Other"] * 8

]
if len(complaints) != len(labels):
    raise ValueError(
        f"Dataset mismatch! Complaints: {len(complaints)}, "
        f"Labels: {len(labels)}"
    )

print("Total complaints:", len(complaints))
print("Total labels:", len(labels))



# ---------------------------------------
# 2. SPLIT TRAINING AND TEST DATA
# ---------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    complaints,
    labels,
    test_size=0.25,
    random_state=42,
    stratify=labels
)


# ---------------------------------------
# 3. CREATE ML PIPELINE
# ---------------------------------------

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            stop_words="english"
        )
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        )
    )
])


# ---------------------------------------
# 4. TRAIN MODEL
# ---------------------------------------

model.fit(X_train, y_train)


# ---------------------------------------
# 5. EVALUATE MODEL
# ---------------------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n--- CITYCARE ML MODEL RESULTS ---")

print("Training complaints:", len(X_train))
print("Testing complaints:", len(X_test))

print("Model Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# ---------------------------------------
# 6. SAVE TRAINED MODEL
# ---------------------------------------

with open("complaint_model.pkl", "wb") as file:
    pickle.dump(model, file)

print("\nML model trained and saved successfully!")