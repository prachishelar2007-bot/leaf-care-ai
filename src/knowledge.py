import re


# ============================================================
# DISEASE KNOWLEDGE BASE
# ============================================================

COMMON_KNOWLEDGE = {

    # --------------------------------------------------------
    # LATE BLIGHT
    # --------------------------------------------------------

    "Late blight": {

        "description": (
            "A fungal-like disease that commonly causes "
            "dark, water-soaked or brown lesions on leaves "
            "and can spread rapidly in cool, wet conditions."
        ),

        "symptoms": [
            "Dark brown or black leaf lesions",
            "Rapid leaf yellowing or collapse",
            "White growth may appear under humid conditions"
        ],

        "causes": [
            "High humidity and prolonged leaf wetness",
            "Cool, wet weather",
            "Infected plant material"
        ],

        "treatment": [
            (
                "Remove severely affected leaves and "
                "dispose of them away from healthy plants."
            ),
            (
                "Improve air circulation and avoid "
                "overhead watering."
            ),
            (
                "Use a locally approved treatment only "
                "according to its product label and "
                "agricultural guidance."
            )
        ],

        "prevention": [
            "Water at soil level.",
            "Avoid overcrowding plants.",
            (
                "Remove infected debris and "
                "sanitize tools."
            )
        ]
    },


    # --------------------------------------------------------
    # EARLY BLIGHT
    # --------------------------------------------------------

    "Early blight": {

        "description": (
            "A common fungal disease producing brown "
            "lesions, often with concentric ring patterns, "
            "on leaves."
        ),

        "symptoms": [
            "Brown circular lesions",
            "Concentric ring or target-like patterns",
            "Yellowing around older lesions"
        ],

        "causes": [
            "Warm, humid conditions",
            "Leaf wetness",
            "Infected crop debris"
        ],

        "treatment": [
            "Remove heavily affected foliage.",
            (
                "Keep leaves dry and improve "
                "plant spacing."
            ),
            (
                "Follow local agricultural guidance "
                "for any approved fungicide."
            )
        ],

        "prevention": [
            "Use clean planting material.",
            "Rotate crops where practical.",
            (
                "Remove crop debris after "
                "harvest."
            )
        ]
    },


    # --------------------------------------------------------
    # POWDERY MILDEW
    # --------------------------------------------------------

    "Powdery mildew": {

        "description": (
            "A fungal disease characterized by a white, "
            "powdery coating on leaf surfaces."
        ),

        "symptoms": [
            "White powder-like patches",
            "Leaf curling or distortion",
            "Yellowing and reduced plant vigor"
        ],

        "causes": [
            "High humidity around foliage",
            "Poor air circulation",
            "Crowded planting"
        ],

        "treatment": [
            "Remove severely infected leaves.",
            (
                "Improve airflow and sunlight "
                "exposure."
            ),
            (
                "Use an approved treatment according "
                "to local label directions."
            )
        ],

        "prevention": [
            "Avoid dense planting.",
            "Water the soil rather than foliage.",
            "Monitor new growth regularly."
        ]
    },


    # --------------------------------------------------------
    # LEAF MOLD
    # --------------------------------------------------------

    "Leaf Mold": {

        "description": (
            "A fungal disease often associated with humid "
            "greenhouse conditions and prolonged moisture "
            "on foliage."
        ),

        "symptoms": [
            "Yellow patches on upper leaf surfaces",
            "Olive or gray growth on the underside",
            "Premature leaf drop"
        ],

        "causes": [
            "High humidity",
            "Poor ventilation",
            "Persistent leaf moisture"
        ],

        "treatment": [
            "Remove affected leaves.",
            (
                "Increase ventilation and "
                "reduce humidity."
            ),
            (
                "Use approved disease-control products "
                "only when necessary and according "
                "to label guidance."
            )
        ],

        "prevention": [
            "Provide good airflow.",
            "Avoid wetting leaves.",
            (
                "Clean greenhouse or growing-area "
                "debris."
            )
        ]
    }
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalize(text):

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        text.lower()
    ).strip()


# ============================================================
# GET DISEASE INFORMATION
# ============================================================

def get_disease_knowledge(
    disease,
    plant
):

    normalized = _normalize(
        disease
    )

    # --------------------------------------------------------
    # SEARCH KNOWN DISEASES
    # --------------------------------------------------------

    for key, value in COMMON_KNOWLEDGE.items():

        normalized_key = _normalize(
            key
        )

        if (
            normalized_key in normalized
            or
            normalized in normalized_key
        ):

            return value

    # --------------------------------------------------------
    # FALLBACK KNOWLEDGE
    # --------------------------------------------------------

    return {

        "description": (
            f"The model classified the uploaded leaf "
            f"as {disease} for {plant}. The exact disease "
            f"profile should be confirmed with a reliable "
            f"agricultural source."
        ),

        "symptoms": [
            (
                "Visible leaf discoloration, spots, "
                "lesions, or other changes may be "
                "associated with this class."
            )
        ],

        "causes": [
            (
                "The exact cause depends on the crop, "
                "environment, pathogen, and growing "
                "conditions."
            )
        ],

        "treatment": [
            (
                "Remove severely affected material "
                "where appropriate."
            ),
            (
                "Improve sanitation, airflow, and "
                "growing conditions."
            ),
            (
                "Consult local agricultural guidance "
                "before applying any chemical treatment."
            )
        ],

        "prevention": [
            "Inspect plants regularly.",
            "Avoid unnecessary leaf wetness.",
            (
                "Maintain good sanitation and "
                "plant spacing."
            )
        ]
    }


# ============================================================
# SMART WATERING MANAGEMENT
# ============================================================

def get_watering_routine(
    plant,
    disease
):

    """
    Provides conservative watering guidance.

    This is a decision-support feature rather than a
    fixed irrigation prescription.
    """

    return {

        "frequency": (
            "Check soil moisture before watering; "
            "do not water on a fixed schedule if "
            "the soil is still wet."
        ),

        "method": (
            "Prefer watering at the soil/root zone "
            "and keep foliage as dry as practical."
        ),

        "best_time": (
            "Morning is generally preferable so "
            "excess surface moisture can dry during "
            "the day."
        ),

        "disease_adjustment": (
            "Because disease can be associated with "
            "excess moisture, avoid overwatering and "
            "prolonged leaf wetness. Adjust frequency "
            "for crop, soil, weather, pot size, and "
            "local conditions."
        ),

        "note": (
            f"This routine is a general care guide "
            f"for {plant} affected by {disease}; "
            "it is not a crop-specific irrigation "
            "prescription."
        )
    }
