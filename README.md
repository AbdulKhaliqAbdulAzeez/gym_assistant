# 🏋️ AI-Powered Gym Assistant

> Your personal AI fitness coach powered by OpenAI GPT-4o and Embeddings API

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-193%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)](htmlcov/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A fully-featured CLI application that generates personalized workout plans, meal plans, and provides exercise recommendations using OpenAI's GPT-4o and text-embedding-3-large models. Built with Test-Driven Development (TDD) principles and enterprise-grade logging.

---

## 🎉 Project Status

**✅ MVP COMPLETE + ALL POST-MVP ENHANCEMENTS (Items 1-8)**

This is a **production-ready** CLI application with:
- 193 passing tests (83% code coverage)
- Enterprise-grade logging and error handling
- Persistent user profiles and history
- Comprehensive configuration management
- Full OpenAI GPT-4o and Embeddings API integration
- Professional documentation and implementation guides

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
- Persistent storage with JSON-based user profiles
- Workout and meal plan history tracking
- Cancel profile setup at any prompt by typing `back`

### 📊 **Advanced Features**
- Configurable logging with rotation and multiple destinations
- Comprehensive error handling with detailed feedback
- Environment-based configuration management
- Persistent storage with configurable history limits
- 193 passing tests with 83% code coverage

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repository
git clone https://github.com/AbdulKhaliqAbdulAzeez/gym_assistant.git
cd gym_assistant

# Create virtual environment (recommended)
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your-api-key-here" > .env
# Or copy the example file if it exists
# cp .env.example .env
# Then edit .env and add your OpenAI API key
```

**Dependencies (from requirements.txt):**
- openai>=1.3.0 - OpenAI API client
- python-dotenv>=1.0.0 - Environment variable management
- pytest>=7.4.0 - Testing framework
- pytest-cov>=4.1.0 - Test coverage
- pytest-mock>=3.11.0 - Mocking for tests
- numpy>=1.24.0 - Vector operations

### Configuration

Create a `.env` file in the project root with your OpenAI API key:

```env
# Required
OPENAI_API_KEY=your-api-key-here

# Optional - OpenAI Settings
OPENAI_DEFAULT_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Optional - Logging Settings
GYM_ASSISTANT_DISABLE_LOGGING=false
GYM_ASSISTANT_LOG_CONSOLE=true
GYM_ASSISTANT_LOG_FILE=true
GYM_ASSISTANT_LOG_LEVEL=INFO
GYM_ASSISTANT_LOG_DIR=./logs

# Optional - Storage Settings
GYM_ASSISTANT_STORAGE_DIR=./data
GYM_ASSISTANT_STORAGE_ENABLED=true
GYM_ASSISTANT_HISTORY_LIMIT=50

# Optional - Parser Settings
GYM_ASSISTANT_PARSER_MAX_RETRIES=3
GYM_ASSISTANT_DEFAULT_DIFFICULTY=moderate
```

All configuration options can be set via environment variables or will use sensible defaults.

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
│   ├── models.py              # Data models (dataclasses) - 88 stmts, 100% coverage
│   ├── client.py              # OpenAI API client wrapper - 54 stmts, 93% coverage
│   ├── parser.py              # Parse AI responses - 178 stmts, 88% coverage
│   ├── workout_service.py     # Workout generation service - 44 stmts, 89% coverage
│   ├── nutrition_service.py   # Meal planning service - 77 stmts, 94% coverage
│   ├── embedding_service.py   # Vector similarity search - 97 stmts, 90% coverage
│   ├── storage.py             # User profile & history storage - 93 stmts, 94% coverage
│   ├── config.py              # Configuration management - 66 stmts, 97% coverage
│   ├── defaults.py            # Default constants - 17 stmts, 100% coverage
│   ├── main.py                # CLI interface - 485 stmts, 72% coverage
│   └── logging_config.py      # Enterprise logging - 33 stmts, 24% coverage
│
├── tests/
│   ├── conftest.py            # Shared test fixtures
│   ├── test_models.py         # Model tests
│   ├── test_client.py         # API client tests
│   ├── test_parser.py         # Parser tests
│   ├── test_workout_service.py
│   ├── test_nutrition_service.py
│   ├── test_embedding_service.py
│   ├── test_storage.py        # Storage layer tests
│   ├── test_config.py         # Configuration tests
│   ├── test_main.py           # CLI integration tests
│   └── test_integration_end_to_end.py  # Full E2E tests
│
├── data/                       # User profiles & history (gitignored)
├── logs/                       # Application logs (gitignored)
├── htmlcov/                    # Coverage reports
├── docs/                       # Project documentation
│   ├── DAY_8_SUMMARY.md
│   ├── POST_MVP_ITEMS_6_7_SUMMARY.md
│   ├── POST_MVP_ITEM_8_SUMMARY.md
│   └── WEB_INTERFACE_IMPLEMENTATION_GUIDE.md
├── requirements.txt
├── pytest.ini
├── BUILD_PROGRESS.md           # Development progress tracking
├── GYM_ASSISTANT_HANDOFF.md    # Project handoff document
├── .env                        # Environment variables (gitignored)
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
- **Python 3.12+**: Core language with type hints and dataclasses
- **pytest**: Testing framework with 193 tests and pytest-cov for coverage
- **numpy**: Vector operations for cosine similarity calculations
- **python-dotenv**: Environment variable management
- **JSON**: User data persistence and configuration storage

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

Current coverage: **83%** (1,232 statements, 215 missing)

| Module               | Statements | Missing | Coverage |
| -------------------- | ---------- | ------- | -------- |
| models.py            | 88         | 0       | 100%     |
| defaults.py          | 17         | 0       | 100%     |
| config.py            | 66         | 2       | 97%      |
| nutrition_service.py | 77         | 5       | 94%      |
| storage.py           | 93         | 6       | 94%      |
| client.py            | 54         | 4       | 93%      |
| embedding_service.py | 97         | 10      | 90%      |
| workout_service.py   | 44         | 5       | 89%      |
| parser.py            | 178        | 22      | 88%      |
| main.py              | 485        | 136     | 72%      |
| logging_config.py    | 33         | 25      | 24%      |

### Test Organization

- **Unit Tests**: Each module has comprehensive unit tests with mocking
- **Integration Tests**: End-to-end workflow testing covering full user journeys
- **Configuration Tests**: Comprehensive testing of environment variable handling
- **Storage Tests**: User profile and history persistence validation
- **TDD Approach**: All code written test-first following Red-Green-Refactor
- **193 Total Tests**: 100% passing, no skipped tests
- **No External API Calls**: All OpenAI API interactions are mocked in tests

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

| Operation               | Cost per Request | Typical Usage    |
| ----------------------- | ---------------- | ---------------- |
| Generate Workout        | ~$0.01-0.02      | Once per session |
| Generate Meal Plan      | ~$0.02-0.03      | Once per session |
| Find Similar Exercises  | ~$0.001          | Multiple times   |
| Build Exercise Database | ~$0.05-0.10      | One-time setup   |

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

## 📚 Documentation

This project includes comprehensive documentation:

- **[BUILD_PROGRESS.md](BUILD_PROGRESS.md)** - Day-by-day development progress and implementation details
- **[GYM_ASSISTANT_HANDOFF.md](GYM_ASSISTANT_HANDOFF.md)** - Project handoff document with architecture and design decisions
- **[Web Interface Guide](docs/WEB_INTERFACE_IMPLEMENTATION_GUIDE.md)** - Step-by-step guide to build a web interface for this project
- **[Day 8 Summary](docs/DAY_8_SUMMARY.md)** - Polish and documentation phase completion
- **[Post-MVP Items 6-7](docs/POST_MVP_ITEMS_6_7_SUMMARY.md)** - Storage and configuration enhancements
- **[Post-MVP Item 8](docs/POST_MVP_ITEM_8_SUMMARY.md)** - Additional feature implementations

## ️ Development Journey

This project was built using **Test-Driven Development (TDD)** methodology over an 8-day development cycle:

- **Day 1**: Models Layer - Core data structures
- **Day 2**: Client Layer - OpenAI API integration
- **Day 3**: Parser Layer - Response parsing and validation
- **Day 4**: Workout Service - Exercise and workout generation
- **Day 5**: Embedding Service - Semantic search functionality
- **Day 6**: Nutrition Service - Meal planning and BMR/TDEE calculations
- **Day 7**: CLI Interface - User interaction and main menu
- **Day 8**: Polish - Logging, error handling, and documentation

**Post-MVP Enhancements:**
- ✅ Configuration management system with environment variables
- ✅ Persistent storage layer with JSON-based user profiles
- ✅ Workout and meal plan history tracking
- ✅ Enterprise-grade logging with rotation and multiple destinations
- ✅ Comprehensive error handling and user feedback
- ✅ Web interface implementation guide

## 🔮 Future Enhancements

### Potential Next Steps

- [ ] Web interface implementation (see [Web Interface Guide](docs/WEB_INTERFACE_IMPLEMENTATION_GUIDE.md))
- [ ] RESTful API with Flask or FastAPI
- [ ] Database integration (PostgreSQL/SQLite)
- [ ] User authentication and authorization
- [ ] Progress tracking dashboard with charts
- [ ] Exercise demonstration videos (YouTube integration)
- [ ] Social features (share workouts with friends)
- [ ] Mobile app (React Native)
- [ ] Wearable device integration (Apple Watch, Fitbit)
- [ ] Advanced analytics and AI-powered insights
- [ ] Meal prep shopping lists with grocery store integration
- [ ] Recipe database with user submissions
- [ ] Multi-language support

---

## 🎓 Educational Value

This project demonstrates:

- ✅ **Test-Driven Development (TDD)** - 193 tests written before implementation
- ✅ **Clean Architecture** - Separation of concerns with distinct layers
- ✅ **SOLID Principles** - Single responsibility, dependency injection
- ✅ **Enterprise Patterns** - Logging, configuration management, error handling
- ✅ **API Integration** - OpenAI GPT-4o and Embeddings API
- ✅ **Type Safety** - Full type hints throughout the codebase
- ✅ **Defensive Programming** - Input validation and error handling
- ✅ **Documentation** - Comprehensive README and inline documentation

Perfect for IS218 students learning professional software development practices!

---

**Built with ❤️ using AI and Test-Driven Development**

**Last Updated**: October 16, 2025  
**Course**: IS218 - Advanced Python Programming  
**Status**: ✅ MVP Complete + All Post-MVP Enhancements (Items 1-8)
