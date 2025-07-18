from sentence_transformers import SentenceTransformer
import faiss
import os
import numpy as np
from collections import defaultdict
from groq import Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

CANONICAL_SYMPTOMS = [
    {
        "phrase": "chest pain, shortness of breath, palpitations",
        "specialties": ["Cardiology"],
        "context": "Symptoms like chest pain and palpitations are often evaluated by a cardiologist."
    },
    {
        "phrase": "joint pain, bone fracture, difficulty walking",
        "specialties": ["Orthopedics"],
        "context": "Orthopedic specialists treat joint pain, fractures, and mobility issues."
    },
    {
        "phrase": "skin rash, itching, redness",
        "specialties": ["Dermatology"],
        "context": "Dermatologists handle skin rashes, itching, and other skin conditions."
    },
    {
        "phrase": "persistent cough, wheezing, difficulty breathing",
        "specialties": ["Pediatrics"],
        "context": "Pediatricians treat respiratory symptoms and other illnesses in children."
    },
    {
        "phrase": "abdominal pain during pregnancy, irregular periods",
        "specialties": ["Obstetrics and Gynecology"],
        "context": "Obstetricians and gynecologists manage pregnancy-related and menstrual symptoms."
    },
    {
        "phrase": "severe headache, dizziness, numbness",
        "specialties": ["Neurology"],
        "context": "Neurologists evaluate headaches, dizziness, and neurological symptoms."
    },
    {
        "phrase": "blurred vision, eye pain, redness",
        "specialties": ["Ophthalmology"],
        "context": "Ophthalmologists treat vision problems and eye pain."
    },
    {
        "phrase": "ear pain, sore throat, nasal congestion",
        "specialties": ["ENT (Ear, Nose, and Throat)"],
        "context": "ENT specialists handle ear pain, throat issues, and nasal congestion."
    },
]

model = SentenceTransformer('all-MiniLM-L6-v2')
canonical_texts = [entry["phrase"] for entry in CANONICAL_SYMPTOMS]
embeddings = model.encode(canonical_texts, normalize_embeddings=True)
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)

# Remove the print statement
# print("FAISS index ready with", len(canonical_texts), "canonical symptom phrases.")

def retrieve_top_symptoms(user_input, top_k=5):
    query_embedding = model.encode([user_input], normalize_embeddings=True)
    scores, indices = index.search(query_embedding, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        entry = CANONICAL_SYMPTOMS[idx]
        results.append({
            "phrase": entry["phrase"],
            "specialties": entry["specialties"],
            "score": float(score),
            "context": entry["context"]
        })
    return results

def correct_relevance(user_input, candidate):
    prompt = (
        f"User symptom description:\n'{user_input}'\n\n"
        f"Candidate specialty: {', '.join(candidate['specialties'])}\n"
        f"Candidate knowledge: {candidate['context']}\n\n"
        "Does this information appear relevant to the user's symptom? Answer YES or NO."
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    result = response.choices[0].message.content.strip().upper()
    return "YES" in result

def aggregate_specialties(filtered_candidates):
    specialty_scores = defaultdict(float)
    for item in filtered_candidates:
        for specialty in item["specialties"]:
            specialty_scores[specialty] += item["score"]
    sorted_specialties = sorted(
        specialty_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return sorted_specialties

def rank_specialties(user_input, filtered_candidates):
    context_blocks = []
    all_specialties = set()
    for entry in filtered_candidates:
        specialties = ", ".join(entry["specialties"])
        all_specialties.update(entry["specialties"])
        context_blocks.append(f"Specialty: {specialties}\nKnowledge: {entry['context']}\n")
    context_text = "\n".join(context_blocks)
    specialties_list_text = ", ".join(sorted(all_specialties))
    prompt = (
        f"User described symptoms: '{user_input}'.\n\n"
        f"Relevant knowledge:\n\n"
        f"{context_text}\n\n"
        f"You must only select from these specialties: {specialties_list_text}.\n"
        "Based on this information, rank the specialties in order of relevance and return only the top 2 specialties as a comma-separated list."
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        user_text = sys.argv[1]
    else:
        user_text = "My vision has been getting blurry for a few days, I also have headaches, sometimes I feel pressure behind my eyes and a bit of dizziness."
    
    retrieved = retrieve_top_symptoms(user_text)
    
    filtered = []
    for candidate in retrieved:
        if correct_relevance(user_text, candidate):
            filtered.append(candidate)
    
    if not filtered:
        print("No relevant specialties found.")
    else:
        ranked = rank_specialties(user_text, filtered)
        # Return only the specialties, nothing else
        print(ranked)