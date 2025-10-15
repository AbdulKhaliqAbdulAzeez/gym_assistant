# 🏋️ AI Gym Assistant Project - Handoff Document

**Date:** October 14, 2025  
**Project Status:** Planning & Design Complete, Ready for Implementation  
**Methodology:** Test-Driven Development (TDD)  
**Reference Project:** `enterprise_ai_demo1_websearch`

---

## 📋 Project Overview

### Vision
Build an AI-powered personal gym assistant that generates personalized workout plans, meal plans, and provides exercise recommendations using OpenAI's GPT-4o/4.1 and text-embedding-3-large APIs.

### Core Features
1. **Personalized Workout Generation** - Based on user profile, goals, fitness level, available equipment
2. **Custom Meal Planning** - Nutrition plans aligned with fitness goals and dietary restrictions
3. **Exercise Similarity Search** - Find alternative exercises using semantic search (vector embeddings)
4. **Form Guidance & Safety** - Detailed instructions and safety tips for each exercise
5. **Interactive CLI** - User-friendly command-line interface

---

## 🏗️ Architecture Design

### Component Structure (Following TDD Pattern)
```
gym_assistant/
├── src/
│   ├── __init__.py
│   ├── models.py              # Data models (dataclasses)
│   ├── client.py              # OpenAI API client wrapper
│   ├── parser.py              # Parse AI responses → structured data
│   ├── workout_service.py     # Workout generation orchestration
│   ├── embedding_service.py   # Vector search & similarity
│   ├── nutrition_service.py   # Meal planning orchestration
│   ├── main.py                # CLI interface
│   └── logging_config.py      # Enterprise logging setup
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures
│   ├── test_models.py         # Model unit tests
│   ├── test_client.py         # Client unit tests (mocked)
│   ├── test_parser.py         # Parser unit tests
│   ├── test_workout_service.py
│   ├── test_embedding_service.py
│   ├── test_nutrition_service.py
│   └── test_main.py           # Integration tests
│
├── docs/                       # Documentation
├── logs/                       # Application logs
├── requirements.txt
├── pytest.ini
├── .env                        # API keys (not in git)
├── .env.example                # Template
└── README.md
```

### Layer Responsibilities

**1. Models Layer (`models.py`)**
- Define all data structures using `@dataclass`
- No business logic, just data containers
- Type hints for all fields
- Computed properties (e.g., BMI calculation)

**2. Client Layer (`client.py`)**
- Handle ALL OpenAI API communication
- Two main methods: `generate_completion()` and `generate_embedding()`
- Error handling with retries (rate limits)
- Load API key from environment

**3. Parser Layer (`parser.py`)**
- Transform AI responses (JSON/text) into typed models
- Defensive programming (handle missing fields)
- Validation and sanitization
- Provide sensible defaults

**4. Service Layer (workout/nutrition/embedding services)**
- Orchestrate business logic
- Build prompts for AI
- Validate outputs
- Coordinate between client and parser

**5. Interface Layer (`main.py`)**
- CLI menus and user interaction
- Display formatted output
- Handle user input validation

---

## 📊 Data Models Defined

### User Profile
```python
@dataclass
class UserProfile:
    user_id: str
    age: int
    weight_kg: float
    height_cm: float
    gender: str                    # "M", "F", "Other"
    fitness_level: str             # "beginner", "intermediate", "advanced"
    goals: List[str]               # ["build_muscle", "lose_weight", "endurance"]
    injuries: Optional[List[str]] = None
    equipment_available: Optional[List[str]] = None
    
    @property
    def bmi(self) -> float:
        """Calculate Body Mass Index"""
        return self.weight_kg / (self.height_cm / 100) ** 2
```

### Exercise & Workout
```python
@dataclass
class Exercise:
    name: str
    muscle_groups: List[str]       # ["chest", "triceps", "shoulders"]
    equipment: List[str]           # ["dumbbells", "bench"]
    difficulty: str                # "beginner", "intermediate", "advanced"
    sets: int
    reps: str                      # "10-12" or "30 seconds"
    rest_seconds: int
    instructions: str              # How to perform
    safety_tips: Optional[str] = None

@dataclass
class Workout:
    workout_id: str
    title: str
    duration_minutes: int
    exercises: List[Exercise]
    warmup: str
    cooldown: str
    difficulty: str
    target_muscles: List[str]
    calories_estimate: int
    created_at: datetime = field(default_factory=datetime.now)
```

### Nutrition
```python
@dataclass
class Meal:
    name: str
    meal_type: str                 # "breakfast", "lunch", "dinner", "snack"
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    ingredients: List[str]
    instructions: str
    prep_time_minutes: int

@dataclass
class NutritionPlan:
    plan_id: str
    date: str
    meals: List[Meal]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fats_g: float
    notes: Optional[str] = None
```

### Request Models
```python
@dataclass
class WorkoutRequest:
    user_profile: UserProfile
    workout_type: str              # "strength", "cardio", "yoga", "hiit"
    duration_minutes: int
    target_muscles: Optional[List[str]] = None
    model: str = "gpt-4o"
    reasoning_effort: str = "medium"

@dataclass
class NutritionRequest:
    user_profile: UserProfile
    dietary_restrictions: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None
    budget_level: str = "medium"   # "low", "medium", "high"
    model: str = "gpt-4o"
```

### Embeddings
```python
@dataclass
class ExerciseEmbedding:
    exercise_name: str
    description: str
    embedding: List[float]         # 3072-dimensional vector
    metadata: Dict[str, Any]       # {"difficulty": "intermediate", ...}
```

### Error Handling
```python
class GymAssistantError(Exception):
    """Base exception for gym assistant errors"""
    def __init__(self, message: str, error_type: str):
        self.message = message
        self.error_type = error_type  # "api_error", "validation_error", etc.
        super().__init__(self.message)
```

---

## 🔧 APIs Being Used

### OpenAI GPT-4o/4.1 (Text Generation)
- **Purpose:** Generate workout plans and meal plans
- **Model:** `gpt-4o` (default) or `gpt-4o-mini` (faster/cheaper)
- **Key Parameters:**
  - `temperature`: 0.7 (creative but consistent)
  - `max_tokens`: 2000+
  - `response_format`: JSON mode for structured outputs

### OpenAI Embeddings (text-embedding-3-large)
- **Purpose:** Semantic search for exercise similarity
- **Model:** `text-embedding-3-large`
- **Output:** 3072-dimensional vectors
- **Use Cases:**
  - Find exercises similar to a query
  - Recommend alternatives for injuries
  - Search by muscle group or equipment

---

## 🧪 TDD Implementation Plan

### Phase 1: Foundation (Week 1, Days 1-3) ⭐ START HERE

#### Day 1: Models + Tests
**File:** `tests/test_models.py` (write FIRST)
```python
# Example test structure
def test_user_profile_creation():
    """Test creating a user profile with valid data"""
    
def test_user_profile_calculates_bmi():
    """Test BMI property calculation"""
    
def test_exercise_creation():
    """Test creating an exercise"""
    
def test_workout_with_exercises():
    """Test workout contains multiple exercises"""
    
def test_meal_creation():
    """Test meal with macros"""
    
def test_nutrition_plan_calculates_totals():
    """Test nutrition plan sums macros correctly"""
```

**Then:** Implement `src/models.py` to pass all tests

#### Day 2: Client + Tests
**File:** `tests/test_client.py` (write FIRST)
```python
def test_client_initialization():
    """Test client loads API key from env"""
    
def test_generate_completion_success(mock_openai):
    """Test GPT-4o API call with mock"""
    
def test_generate_embedding_success(mock_openai):
    """Test embeddings API call with mock"""
    
def test_client_retries_on_rate_limit():
    """Test exponential backoff on rate limit errors"""
    
def test_client_raises_on_auth_error():
    """Test proper error handling for auth failures"""
```

**Then:** Implement `src/client.py`
```python
class GymAssistantClient:
    def __init__(self, api_key: Optional[str] = None):
        # Load from env or parameter
        
    def generate_completion(self, prompt: str, model: str = "gpt-4o") -> str:
        # Call OpenAI Chat Completions API
        
    def generate_embedding(self, text: str) -> List[float]:
        # Call OpenAI Embeddings API
```

#### Day 3: Parser + Tests
**File:** `tests/test_parser.py`
```python
def test_parse_workout_from_json():
    """Test parsing AI JSON response into Workout object"""
    
def test_parse_handles_missing_fields():
    """Test parser provides defaults for missing data"""
    
def test_parse_validates_ranges():
    """Test parser validates sets/reps in valid ranges"""
```

**Then:** Implement `src/parser.py`

---

### Phase 2: Services (Week 1, Days 4-6)

#### Day 4: Workout Service
```python
class WorkoutService:
    def generate_workout(self, request: WorkoutRequest) -> Workout:
        """
        1. Build prompt from user profile + request
        2. Call client.generate_completion()
        3. Parse response
        4. Validate workout
        """
```

#### Day 5: Embedding Service
```python
class EmbeddingService:
    def find_similar_exercises(self, query: str, top_k: int = 5) -> List[Exercise]:
        """
        1. Generate embedding for query
        2. Compute cosine similarity with database
        3. Return top_k matches
        """
    
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate similarity between vectors"""
```

#### Day 6: Nutrition Service
```python
class NutritionService:
    def generate_meal_plan(self, request: NutritionRequest) -> NutritionPlan:
        """Generate daily meal plan"""
    
    def calculate_macros(self, user: UserProfile) -> Dict[str, float]:
        """Calculate protein/carbs/fats based on goals"""
```

---

### Phase 3: Integration (Week 2)

#### Day 7: CLI Interface
```python
def main():
    """Interactive gym assistant CLI"""
    # Menu:
    # 1. Generate Workout Plan
    # 2. Create Meal Plan
    # 3. Find Similar Exercises
    # 4. View Profile
    # 5. Exit
```

#### Day 8: Polish & Documentation
- Logging configuration
- Error messages
- README updates
- Coverage report

---

## 💡 Key Implementation Notes

### Prompt Engineering Example (Workout Generation)
```python
prompt = f"""
You are an expert personal trainer. Create a {duration_minutes}-minute {workout_type} workout.

USER PROFILE:
- Age: {user.age}, Gender: {user.gender}
- Weight: {user.weight_kg}kg, Height: {user.height_cm}cm
- Fitness Level: {user.fitness_level}
- Goals: {', '.join(user.goals)}
- Equipment: {', '.join(user.equipment_available)}
- Injuries to avoid: {', '.join(user.injuries)}

REQUIREMENTS:
1. Include {num_exercises} exercises
2. Target these muscle groups: {target_muscles}
3. Provide sets, reps, rest time, instructions, safety tips
4. Include warm-up and cool-down routines
5. Estimate total calorie burn

Return as JSON following this exact structure:
{{
  "title": "...",
  "duration_minutes": {duration_minutes},
  "exercises": [
    {{
      "name": "Exercise Name",
      "muscle_groups": ["chest", "triceps"],
      "equipment": ["dumbbells"],
      "difficulty": "{user.fitness_level}",
      "sets": 4,
      "reps": "8-10",
      "rest_seconds": 90,
      "instructions": "Step by step...",
      "safety_tips": "Keep back straight..."
    }}
  ],
  "warmup": "5 minutes of...",
  "cooldown": "5 minutes of...",
  "target_muscles": ["{target_muscles}"],
  "calories_estimate": 350
}}
"""
```

### Embedding Search Example
```python
# User query: "Find exercises like push-ups"
query_text = "push-ups upper body bodyweight chest triceps"
query_embedding = client.generate_embedding(query_text)

# Compare with database (cosine similarity)
similarities = []
for exercise_embed in exercise_database:
    sim = cosine_similarity(query_embedding, exercise_embed.embedding)
    similarities.append((sim, exercise_embed.exercise_name))

# Sort and return top 5
similarities.sort(reverse=True)
top_exercises = similarities[:5]
```

### Macro Calculation Logic
```python
def calculate_macros(user: UserProfile) -> Dict[str, float]:
    """Calculate daily macros based on goals"""
    
    # Base calorie calculation (simplified)
    bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age
    bmr += 5 if user.gender == "M" else -161
    
    # Activity multiplier
    tdee = bmr * 1.55  # Moderate activity
    
    if "build_muscle" in user.goals:
        calories = tdee + 300  # Surplus
        protein_g = user.weight_kg * 2.2
        carbs_ratio = 0.40
        fats_ratio = 0.30
    elif "lose_weight" in user.goals:
        calories = tdee - 500  # Deficit
        protein_g = user.weight_kg * 2.0
        carbs_ratio = 0.30
        fats_ratio = 0.35
    else:
        calories = tdee
        protein_g = user.weight_kg * 1.8
        carbs_ratio = 0.40
        fats_ratio = 0.30
    
    protein_calories = protein_g * 4
    remaining = calories - protein_calories
    carbs_g = (remaining * carbs_ratio) / 4
    fats_g = (remaining * fats_ratio) / 9
    
    return {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fats_g": fats_g
    }
```

---

## 🧪 Testing Strategy

### Test Coverage Goals
- **Models:** 100% (all fields, validation, properties)
- **Client:** 100% (mocked API calls, error handling)
- **Parser:** 100% (valid inputs, missing fields, malformed data)
- **Services:** 95%+ (business logic, orchestration)
- **Main:** 80%+ (user flows, integration)

### Fixture Strategy (in `conftest.py`)
```python
@pytest.fixture
def sample_user():
    """Standard test user profile"""
    return UserProfile(
        user_id="test123",
        age=28,
        weight_kg=75.0,
        height_cm=175.0,
        gender="M",
        fitness_level="intermediate",
        goals=["build_muscle"],
        equipment_available=["dumbbells", "resistance_bands"]
    )

@pytest.fixture
def sample_exercise():
    """Standard test exercise"""
    return Exercise(
        name="Dumbbell Bench Press",
        muscle_groups=["chest", "triceps"],
        equipment=["dumbbells"],
        difficulty="intermediate",
        sets=4,
        reps="8-10",
        rest_seconds=90,
        instructions="Lie on bench, press dumbbells up...",
        safety_tips="Keep back flat on bench"
    )

@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock OpenAI API responses"""
    # Mock implementation here
```

### Mocking OpenAI API
```python
# In tests, mock the OpenAI client
@pytest.fixture
def mock_openai_response():
    """Mock successful API response"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "title": "Upper Body Strength",
                    "exercises": [...],
                    # ... full workout JSON
                })
            }
        }]
    }

def test_generate_workout(mock_openai_response, monkeypatch):
    """Test workout generation with mocked API"""
    monkeypatch.setattr(
        "openai.OpenAI.chat.completions.create",
        lambda *args, **kwargs: mock_openai_response
    )
    # Test code here
```

---

## 📝 Configuration Files

### requirements.txt
```
openai>=1.3.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
numpy>=1.24.0
```

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --strict-markers --tb=short
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests
    slow: Slow running tests
```

### .env (DO NOT COMMIT - example values)
```bash
OPENAI_API_KEY=sk-proj-xxxxx...
DEFAULT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
LOG_LEVEL=INFO
```

---

## 🎯 Current Status

### ✅ Completed
- [x] Project design and architecture defined
- [x] All data models specified
- [x] Component responsibilities documented
- [x] TDD implementation plan created
- [x] Prompt engineering examples provided
- [x] Testing strategy defined
- [x] Documentation written (`GYM_ASSISTANT_DESIGN.md`, `GYM_ASSISTANT_QUICKSTART.md`)

### 🔄 Ready to Start
- [ ] **NEXT STEP:** Create project directory structure
- [ ] **THEN:** Write `tests/test_models.py` (TDD RED phase)
- [ ] **THEN:** Implement `src/models.py` (TDD GREEN phase)

### 📋 Implementation Checklist (Week 1)
- [ ] Day 1: Models (`test_models.py` + `models.py`)
- [ ] Day 2: Client (`test_client.py` + `client.py`)
- [ ] Day 3: Parser (`test_parser.py` + `parser.py`)
- [ ] Day 4: Workout Service
- [ ] Day 5: Embedding Service
- [ ] Day 6: Nutrition Service
- [ ] Day 7: CLI Interface
- [ ] Day 8: Testing & Documentation

---

## 🔑 Key Design Decisions

### 1. Why TDD?
- Ensures every component is testable
- Provides living documentation
- Prevents regressions
- Forces good design (separation of concerns)

### 2. Why Dataclasses?
- Automatic `__init__`, `__repr__`, `__eq__`
- Type hints for IDE support
- Immutable option with `frozen=True`
- Less boilerplate than regular classes

### 3. Why Separate Services?
- **Single Responsibility Principle** - Each service does ONE thing
- **Testability** - Can test each service in isolation
- **Maintainability** - Easy to update workout logic without touching nutrition
- **Extensibility** - Can add new services (e.g., ProgressTrackingService) later

### 4. Why Parser Layer?
- **Defensive Programming** - AI responses can be unpredictable
- **Validation** - Ensure data meets requirements before using
- **Transformation** - Convert between representations (JSON ↔ dataclass)
- **Error Handling** - Single place to handle parsing failures

### 5. Why Embeddings for Exercise Search?
- **Semantic Understanding** - "exercises like squats" vs "squat OR lunge OR leg press"
- **Flexibility** - Users can describe what they want naturally
- **Context-Aware** - Understands "low impact" means avoid jumping
- **Scalable** - Can search thousands of exercises efficiently

---

## 📚 Reference Resources

### Pattern Reference
- **See:** `/home/kepler/classes/is218/projects/enterprise_ai_demo1_websearch/`
- **Key files to study:**
  - `src/models.py` - Dataclass patterns
  - `src/client.py` - API client wrapper pattern
  - `src/parser.py` - Defensive parsing pattern
  - `tests/test_*.py` - Test structure patterns
  - `tests/conftest.py` - Fixture patterns

### OpenAI API Documentation
- **Chat Completions:** https://platform.openai.com/docs/guides/text-generation
- **Embeddings:** https://platform.openai.com/docs/guides/embeddings
- **Structured Outputs (JSON mode):** https://platform.openai.com/docs/guides/structured-outputs

### Testing Resources
- **pytest docs:** https://docs.pytest.org/
- **pytest-mock:** https://pytest-mock.readthedocs.io/
- **Coverage:** https://pytest-cov.readthedocs.io/

---

## 🚀 Quick Start Commands (for next AI/developer)

```bash
# Navigate to project location
cd /home/kepler/classes/is218/projects/

# Create project structure (run setup commands from GYM_ASSISTANT_QUICKSTART.md)
mkdir gym_assistant && cd gym_assistant
# ... (see detailed commands in quickstart doc)

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with OpenAI API key: sk-proj-_ZeB5re00_SzmZrWR9X81vOsSiLEK...

# Start TDD workflow
# 1. Write test in tests/test_models.py
# 2. Run pytest tests/test_models.py -v (should FAIL)
# 3. Implement in src/models.py
# 4. Run pytest tests/test_models.py -v (should PASS)
```

---

## 💬 Common Questions & Answers

**Q: Why not use a framework like Flask/FastAPI?**  
A: Starting with CLI keeps it simple for learning. Can add web interface later as Phase 4.

**Q: Should we store workouts in a database?**  
A: Phase 1-2 focus on generation. Phase 3-4 can add persistence (SQLite or JSON files).

**Q: How do we handle rate limits from OpenAI?**  
A: Client layer implements exponential backoff retry logic (see `enterprise_ai_demo1_websearch/src/client.py`).

**Q: What if the AI returns invalid JSON?**  
A: Parser layer handles this with try/except and provides defaults (defensive programming).

**Q: How many exercises should be in the database for embeddings?**  
A: Start with 50-100 exercises in Phase 1. Can expand to 500+ later with a JSON file.

---

## 🎯 Success Criteria

### Minimum Viable Product (MVP)
- [ ] Can generate a personalized workout plan
- [ ] Can generate a meal plan
- [ ] CLI allows user to input profile and preferences
- [ ] 50+ tests, 90%+ coverage
- [ ] All tests passing
- [ ] Works with OpenAI API (real calls)

### Full Product (v1.0)
- [ ] Exercise similarity search working
- [ ] Interactive CLI with menus
- [ ] Logging and error handling
- [ ] Save/load user profiles
- [ ] 80+ tests, 95%+ coverage
- [ ] Professional documentation

---

## 📞 Handoff Notes for Next AI

### What I've Done
1. ✅ Analyzed the reference project (`enterprise_ai_demo1_websearch`)
2. ✅ Designed complete architecture following TDD patterns
3. ✅ Defined all data models (10+ dataclasses)
4. ✅ Created detailed implementation plan (8-day roadmap)
5. ✅ Provided prompt engineering examples
6. ✅ Wrote comprehensive documentation (3 docs: DESIGN, QUICKSTART, HANDOFF)
7. ✅ Identified user's OpenAI API key for use

### What's Next (Immediate Actions)
1. **Create project directory structure** using commands from quickstart
2. **Write first test** in `tests/test_models.py` (see Day 1 plan)
3. **Run pytest** and see it fail (TDD RED phase)
4. **Implement `UserProfile` dataclass** in `src/models.py`
5. **Run pytest again** and see it pass (TDD GREEN phase)
6. **Continue with more model tests** (Exercise, Workout, Meal, etc.)

### User's Environment
- **Location:** `/home/kepler/classes/is218/projects/`
- **Reference Project:** `enterprise_ai_demo1_websearch/` (in same directory)
- **OpenAI API Key:** Available in `.env` file (already configured)
- **Python:** Available with venv support
- **Git:** Available (can initialize new repo)

### Key Documents to Reference
1. **This file** - Complete context and handoff
2. **`GYM_ASSISTANT_DESIGN.md`** - Detailed architecture (900 lines)
3. **`GYM_ASSISTANT_QUICKSTART.md`** - Implementation guide (400 lines)
4. **Reference project** - `enterprise_ai_demo1_websearch/src/*` and `tests/*`

### Suggested First Message to User
*"I've reviewed the handoff document and understand the gym assistant project. I see we're following TDD using the `enterprise_ai_demo1_websearch` as a reference. Would you like me to:*

*1. **Create the project directory structure** (5 minutes)*  
*2. **Write the first test** for `UserProfile` model (TDD RED phase)*  
*3. **Help you set up the development environment***

*Or do you have a different starting point in mind?"*

---

## 📝 Notes

- User has existing OpenAI API key and is familiar with the TDD workflow from the reference project
- User wants to build in a separate directory (not in `enterprise_ai_demo1_websearch`)
- Project should follow exact same patterns as reference: dataclasses, TDD, clean architecture
- OpenAI models to use: `gpt-4o` or `gpt-4o-mini` for text, `text-embedding-3-large` for embeddings
- User is comfortable with command-line tools and git

---

**END OF HANDOFF DOCUMENT**

*This document contains everything needed to continue development. Good luck! 🚀*
