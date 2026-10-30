"""Fictional demo data so the platform runs end to end. Not real patients."""
from .authz import User
from .context import InMemoryHMIS

HMIS = InMemoryHMIS({
    "P123": {
        "name": "Demo Patient", "phone": "0712000000",   # present in the record, never sent to the model
        "conditions": [{"text": "Hypertension", "ref": "dx-1"}, {"text": "Type 2 diabetes", "ref": "dx-2"}],
        "allergies": [{"text": "Penicillin allergy", "ref": "al-1"}],
        "medications": [{"text": "Amlodipine 5 mg daily", "ref": "rx-9"}],
        "results": [{"text": "Creatinine 140 umol/L", "ref": "lab-31", "date": "2026-10-01"},
                    {"text": "Creatinine 210 umol/L", "ref": "lab-58", "date": "2026-10-20"}],
        "encounters": [{"text": "Admitted medical ward; discharged after 7 days", "ref": "enc-4", "date": "2026-10-10"}],
    },
    "P999": {"name": "Other Patient", "conditions": [{"text": "Asthma", "ref": "dx-77"}]},
})

USERS = {
    "dr.amina": User("dr.amina", "doctor", {"P123"}),
    "nurse.joy": User("nurse.joy", "nurse", {"P123"}),
    "ops.kip": User("ops.kip", "operations"),
    "bill.ann": User("bill.ann", "billing"),
    "reg.sam": User("reg.sam", "registration"),
}
