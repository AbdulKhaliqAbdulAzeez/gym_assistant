# 🏋️ AI-Powered Gym Assistant

> Your personal AI fitness coach powered by OpenAI GPT-4o and Embeddings API

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-161%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-88%25-green.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An intelligent gym assistant that generates personalized workout plans, meal plans, and provides exercise recommendations using advanced AI and semantic search.

---

## ✨ Features

### 🏋️ **Personalized Workout Generation**
- AI-generated workouts tailored to your fitness level, goals, and available equipment
- Multiple workout types: Strength, Cardio, HIIT, Flexibility
- Detailed instructions and safety tips for each exercise
- Warm-up and cool-down routines included
- Calorie burn estimates

### 🍽️ **Smart Nutrition Planning**
- BMR/TDEE calculation using Mifflin-St Jeor equation
- Macro nutrient targets based on your goals (muscle building, weight loss, maintenance)
- Personalized meal plans with detailed recipes
- Dietary restrictions support (vegetarian, vegan, gluten-free, dairy-free)
- Budget-conscious meal planning (low/medium/high)
- Cuisine preference customization

### 🔍 **Exercise Similarity Search**
- Semantic search using OpenAI embeddings (text-embedding-3-large)
- Find alternative exercises for similar muscle groups
- Filter by equipment availability and difficulty level
- Injury-aware recommendations

### 👤 **User Profile Management**
- Track fitness metrics (age, weight, height, BMI)
- Set and update fitness goals
- Manage equipment inventory
- Track injuries and limitations
- Cancel profile setup at any prompt by typing `back`

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd gym_assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key-here
LOG_LEVEL=INFO
```

Optional logging controls (set as needed):

```env
# Disable all application logging
GYM_ASSISTANT_DISABLE_LOGGING=true

# Or fine-tune destinations
GYM_ASSISTANT_LOG_CONSOLE=false
GYM_ASSISTANT_LOG_FILE=false
GYM_ASSISTANT_LOG_LEVEL=DEBUG
GYM_ASSISTANT_LOG_DIR=./logs
```

### Running the Application

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run the CLI
python -m src.main
```

### 💸 OpenAI API Usage & Costs

- Each workout or meal plan request sends a GPT-4o prompt and response (≈2K–3K output tokens per plan). At the current $5 / 1M input tokens and $15 / 1M output tokens, expect roughly $0.02 per plan.
- Default self-serve rate limits are about 10 requests per minute; space requests to avoid HTTP 429 errors or paused billing usage.
- Review your usage frequently at [OpenAI Dashboard](https://platform.openai.com/usage), especially before batching many plans.
- Configure automated tests or demos with smaller prompts (or set `GYM_ASSISTANT_DISABLE_LOGGING=true`) to reduce accidental API spend.

---

## 📖 Usage Examples

### Generate a Workout Plan

```
1. Select "Generate Workout Plan" from the menu
2. Choose workout type (strength/cardio/hiit/flexibility)
3. Set duration (e.g., 45 minutes)
4. Specify target muscle groups (optional)
5. Get your personalized workout!
```

**Example Output:**

```
💪 YOUR WORKOUT PLAN
============================================================

📋 Upper Body Strength Training
⏱️  Duration: 45 minutes
📊 Difficulty: intermediate
🎯 Target Muscles: chest, triceps, shoulders
🔥 Est. Calories: 350

------------------------------------------------------------
EXERCISES
------------------------------------------------------------

1. Barbell Bench Press
   💪 Muscles: chest, triceps
   📊 Difficulty: intermediate
   🔢 Sets: 4
   🔁 Reps: 8-12
   ⏸️  Rest: 90s
   🏋️  Equipment: barbell, bench

   📖 Instructions:
      Lie on bench, grip bar slightly wider than shoulders,
      lower to chest, press back up explosively

   ⚠️  Safety Tips:
      • Keep feet flat on floor
      • Use spotter for heavy weights
      • Don't bounce bar off chest
```

### Create a Meal Plan

```
1. Select "Generate Meal Plan" from the menu
2. Specify dietary restrictions (if any)
3. Choose cuisine preferences (optional)
4. Set budget level (low/medium/high)
5. Receive your personalized nutrition plan!
```

**Example Output:**

```
🍽️  YOUR MEAL PLAN
============================================================

📅 Date: 2025-10-14

------------------------------------------------------------
DAILY TOTALS
------------------------------------------------------------
🔥 Calories: 2500 kcal
🥩 Protein: 180g
🍞 Carbs: 280g
🥑 Fats: 70g

------------------------------------------------------------
MEALS
------------------------------------------------------------

🌅 1. Protein Pancakes with Berries (BREAKFAST)
   🔥 450 kcal
   Protein: 30g | Carbs: 50g | Fats: 12g
   ⏱️  Prep time: 15 min

   🛒 Ingredients:
      • 3 eggs
      • 1 scoop protein powder
      • 1/2 cup oats
      • 1 cup mixed berries

   📖 Instructions:
      Blend eggs, protein powder, and oats. Cook on
      griddle for 3-4 minutes per side. Top with berries.
```

### Find Similar Exercises

```
1. Select "Find Similar Exercises" from the menu
2. Describe the exercise you're looking for
   (e.g., "upper body push movement")
3. Specify number of results (default: 5)
4. Browse alternative exercises!
```

---

## 🏗️ Architecture

### Project Structure

```
gym_assistant/
├── src/
│   ├── __init__.py
│   ├── models.py              # Data models (dataclasses)
│   ├── client.py              # OpenAI API client wrapper
│   ├── parser.py              # Parse AI responses
│   ├── workout_service.py     # Workout generation service
│   ├── embedding_service.py   # Vector similarity search
│   ├── nutrition_service.py   # Meal planning service
│   ├── main.py                # CLI interface
│   └── logging_config.py      # Logging configuration
│
├── tests/
│   ├── test_models.py         # 13 tests
│   ├── test_client.py         # 14 tests
│   ├── test_parser.py         # 23 tests
│   ├── test_workout_service.py    # 21 tests
│   ├── test_embedding_service.py  # 29 tests
│   ├── test_nutrition_service.py  # 28 tests
│   └── test_main.py           # 30 tests
│
├── logs/                       # Application logs
├── docs/                       # Additional documentation
├── requirements.txt
├── pytest.ini
├── .env                        # Environment variables (gitignored)
├── .env.example                # Template
└── README.md
```

### Component Layers

```
┌─────────────────────┐
│   CLI Interface     │  main.py
│  (User Interaction) │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────┐
│     Service Layer               │
│  - WorkoutService               │
│  - NutritionService             │
│  - EmbeddingService             │
│  (Business Logic)               │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────┐
│   Parser Layer      │
│  (Data Validation)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Client Layer      │
│  (OpenAI API Calls) │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Models Layer      │
│  (Data Structures)  │
└─────────────────────┘
```

### Key Technologies

- **OpenAI GPT-4o**: Text generation for workouts and meal plans
- **OpenAI text-embedding-3-large**: Vector embeddings for exercise similarity
- **Python 3.12+**: Core language with type hints
- **pytest**: Testing framework with 158 tests
- **numpy**: Vector operations for cosine similarity

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_workout_service.py

# Run with verbose output
pytest -v
```

### Test Coverage

Current coverage: **88%** (835 statements, 104 missing)

| Module | Statements | Coverage |
|--------|-----------|----------|
| models.py | 88 | 100% |
| nutrition_service.py | 77 | 94% |
| client.py | 48 | 92% |
| embedding_service.py | 97 | 90% |
| workout_service.py | 44 | 89% |
| parser.py | 180 | 88% |
| main.py | 301 | 81% |

### Test Organization

- **Unit Tests**: Each module has comprehensive unit tests with mocking
- **Integration Tests**: End-to-end workflow testing in test_main.py
- **TDD Approach**: All code written test-first following Red-Green-Refactor
- **158 Total Tests**: 100% passing, no skipped tests

---

## 🔧 Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests in watch mode
pytest-watch

# Format code (if using black)
black src/ tests/

# Type checking (if using mypy)
mypy src/
```

### Design Principles

1. **Test-Driven Development**: Write tests first, then implementation
2. **Single Responsibility**: Each class/function has one clear purpose
3. **Dependency Injection**: Services accept dependencies for testability
4. **Defensive Programming**: Validate inputs, handle errors gracefully
5. **Type Hints**: Full type annotations for IDE support and documentation

### Adding New Features

1. Write tests first (TDD RED phase)
2. Implement minimum code to pass tests (TDD GREEN phase)
3. Refactor for quality and maintainability
4. Update documentation
5. Verify test coverage remains high

---

## 📊 API Usage and Costs

### OpenAI API Calls

The application makes the following API calls:

- **Workout Generation**: 1 GPT-4o completion per workout (~1000-2000 tokens)
- **Meal Plan Generation**: 1 GPT-4o completion per plan (~1500-2500 tokens)
- **Exercise Embeddings**: 1 embedding per exercise description (~50-100 tokens)
- **Exercise Search**: 1 embedding per query (~20-50 tokens)

### Cost Estimates (as of Oct 2025)

| Operation | Cost per Request | Typical Usage |
|-----------|-----------------|---------------|
| Generate Workout | ~$0.01-0.02 | Once per session |
| Generate Meal Plan | ~$0.02-0.03 | Once per session |
| Find Similar Exercises | ~$0.001 | Multiple times |
| Build Exercise Database | ~$0.05-0.10 | One-time setup |

**Note**: Actual costs depend on GPT-4o pricing. Check [OpenAI Pricing](https://openai.com/pricing) for current rates.

---

## 🐛 Troubleshooting

### Common Issues

#### "No OpenAI API key provided"

**Solution**: Make sure your `.env` file exists and contains:

```env
OPENAI_API_KEY=sk-...your-key...
```

#### "Rate limit exceeded"

**Solution**: The client includes exponential backoff retry logic. If you still see this error, wait a few minutes or upgrade your OpenAI API plan.

#### "Import errors"

**Solution**: Ensure you're using Python 3.12+ and all dependencies are installed:

```bash
python --version  # Should be 3.12 or higher
pip install -r requirements.txt
```

#### Tests fail with API errors

**Solution**: Tests use mocking and should not make real API calls. If you see actual API errors during tests, check that mocks are properly configured.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o and embeddings API
- **pytest** for excellent testing framework
- **numpy** for vector operations

---

## 📧 Contact

For questions, suggestions, or issues:

- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review test files for usage examples

---

## 🗺️ Roadmap

### Potential Future Enhancements

- [ ] Web interface (Flask/FastAPI)
- [ ] Progress tracking and workout history
- [ ] Exercise demonstration videos (YouTube integration)
- [ ] Social features (share workouts with friends)
- [ ] Mobile app (React Native)
- [ ] Wearable device integration (Apple Watch, Fitbit)
- [ ] Advanced analytics and insights
- [ ] Meal prep shopping lists
- [ ] Recipe database with user submissions

---

**Built with ❤️ using AI and Test-Driven Development**

**Last Updated**: January 14, 2025
