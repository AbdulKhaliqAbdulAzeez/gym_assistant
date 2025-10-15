# 🌐 Web Interface Implementation Guide

> Step-by-step guide to transform the AI-Powered Gym Assistant from a CLI application to a modern web application

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Technology Stack Options](#technology-stack-options)
3. [Architecture Design](#architecture-design)
4. [Implementation Steps](#implementation-steps)
5. [Frontend Development](#frontend-development)
6. [Backend API Development](#backend-api-development)
7. [Authentication & User Management](#authentication--user-management)
8. [Database Integration](#database-integration)
9. [Deployment](#deployment)
10. [Testing Strategy](#testing-strategy)
11. [Security Considerations](#security-considerations)

---

## 🎯 Overview

This guide will help you convert the existing CLI-based gym assistant into a full-stack web application while preserving all current functionality:

- ✅ User profile management
- ✅ Personalized workout generation
- ✅ Smart nutrition planning
- ✅ Exercise similarity search
- ✅ BMR/TDEE calculations
- ✅ Dietary restrictions and preferences

---

## 🛠️ Technology Stack Options

### Option 1: Flask + React (Recommended for Learning)

**Backend:** Flask (Python web framework)
- Lightweight and easy to learn
- Seamlessly integrates with existing Python codebase
- Built-in development server
- RESTful API support

**Frontend:** React.js
- Component-based architecture
- Large ecosystem and community
- Modern UI development

**Why this stack?**
- Minimal changes to existing Python code
- Great for IS218 students learning web development
- Quick prototyping and deployment

### Option 2: FastAPI + Next.js (Modern & Production-Ready)

**Backend:** FastAPI
- Automatic API documentation (Swagger/OpenAPI)
- Async support for better performance
- Type hints and data validation with Pydantic
- Modern Python web framework

**Frontend:** Next.js (React framework)
- Server-side rendering (SSR)
- Built-in routing
- Optimized performance
- Full-stack capabilities

**Why this stack?**
- Industry-standard modern stack
- Better performance and scalability
- Built-in API documentation

### Option 3: Django + Vue.js (All-in-One Framework)

**Backend:** Django
- Complete web framework (ORM, admin panel, auth)
- "Batteries included" philosophy
- Excellent for database-heavy applications

**Frontend:** Vue.js
- Gentle learning curve
- Reactive data binding
- Lightweight

---

## 🏗️ Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (SPA)                        │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐   │
│  │  Profile   │  │  Workout   │  │    Nutrition        │   │
│  │  Manager   │  │  Generator │  │    Planner          │   │
│  └────────────┘  └────────────┘  └─────────────────────┘   │
│         │               │                    │               │
└─────────┼───────────────┼────────────────────┼───────────────┘
          │               │                    │
          └───────────────┴────────────────────┘
                          │ HTTP/REST
┌─────────────────────────┼────────────────────────────────────┐
│                    Backend API Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Routes/Controllers                   │   │
│  │  • /api/users     • /api/workouts                    │   │
│  │  • /api/nutrition • /api/exercises                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Business Logic (Existing Code)            │   │
│  │  • WorkoutService    • NutritionService              │   │
│  │  • EmbeddingService  • Storage                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                    │
└──────────────────────────┼────────────────────────────────────┘
                           │
┌──────────────────────────┼────────────────────────────────────┐
│                    Data Layer                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  PostgreSQL │  │   JSON Files  │  │  OpenAI API      │    │
│  │  (Users DB) │  │  (Exercises)  │  │  (GPT-4o)        │    │
│  └─────────────┘  └──────────────┘  └──────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### API Design Philosophy

- **RESTful principles**: Use HTTP methods appropriately (GET, POST, PUT, DELETE)
- **JSON responses**: Standardized response format
- **Error handling**: Consistent error messages
- **Authentication**: JWT tokens or session-based auth
- **Rate limiting**: Protect against abuse

---

## 📝 Implementation Steps

### Phase 1: Backend API Development (Week 1-2)

#### Step 1.1: Set Up Web Framework

**For Flask:**

```bash
# Add to requirements.txt
flask>=3.0.0
flask-cors>=4.0.0
flask-jwt-extended>=4.5.0
python-jose>=3.3.0
```

Create `src/api/__init__.py`:
```python
from flask import Flask
from flask_cors import CORS
from src.config import get_config

def create_app():
    app = Flask(__name__)
    config = get_config()
    
    # Enable CORS for frontend
    CORS(app)
    
    # Load configuration
    app.config['SECRET_KEY'] = config.secret_key
    
    # Register blueprints (routes)
    from src.api.routes import user_routes, workout_routes, nutrition_routes
    app.register_blueprint(user_routes, url_prefix='/api/users')
    app.register_blueprint(workout_routes, url_prefix='/api/workouts')
    app.register_blueprint(nutrition_routes, url_prefix='/api/nutrition')
    
    return app
```

**For FastAPI:**

```bash
# Add to requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
pydantic>=2.0.0
```

Create `src/api/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import users, workouts, nutrition

app = FastAPI(
    title="AI Gym Assistant API",
    description="Personalized fitness and nutrition planning powered by AI",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["workouts"])
app.include_router(nutrition.router, prefix="/api/nutrition", tags=["nutrition"])
```

#### Step 1.2: Create API Routes

Create `src/api/routes/user_routes.py`:
```python
"""User management endpoints"""
from flask import Blueprint, request, jsonify
from src.models import UserProfile, GymAssistantError
from src.storage import Storage

user_routes = Blueprint('users', __name__)
storage = Storage()

@user_routes.route('/', methods=['POST'])
def create_user():
    """Create a new user profile"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'age', 'weight_kg', 'height_cm', 'gender']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create UserProfile
        profile = UserProfile(
            user_id=data.get('user_id'),
            name=data['name'],
            age=data['age'],
            weight_kg=data['weight_kg'],
            height_cm=data['height_cm'],
            gender=data['gender'],
            fitness_goal=data.get('fitness_goal'),
            equipment=data.get('equipment', []),
            injuries=data.get('injuries', [])
        )
        
        # Save to storage
        storage.save_user(profile)
        
        return jsonify({
            'success': True,
            'user_id': profile.user_id,
            'message': 'User profile created successfully'
        }), 201
        
    except GymAssistantError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@user_routes.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile by ID"""
    try:
        profile = storage.get_user(user_id)
        if not profile:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(profile.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_routes.route('/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user profile"""
    try:
        data = request.get_json()
        profile = storage.get_user(user_id)
        
        if not profile:
            return jsonify({'error': 'User not found'}), 404
        
        # Update fields
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        storage.save_user(profile)
        
        return jsonify({
            'success': True,
            'message': 'User profile updated'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_routes.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user profile"""
    try:
        storage.delete_user(user_id)
        return jsonify({
            'success': True,
            'message': 'User profile deleted'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Create `src/api/routes/workout_routes.py`:
```python
"""Workout generation endpoints"""
from flask import Blueprint, request, jsonify
from src.models import WorkoutRequest, GymAssistantError
from src.workout_service import WorkoutService
from src.storage import Storage

workout_routes = Blueprint('workouts', __name__)
workout_service = WorkoutService()
storage = Storage()

@workout_routes.route('/generate', methods=['POST'])
def generate_workout():
    """Generate a personalized workout plan"""
    try:
        data = request.get_json()
        
        # Get user profile
        user_id = data.get('user_id')
        profile = storage.get_user(user_id)
        
        if not profile:
            return jsonify({'error': 'User not found'}), 404
        
        # Create workout request
        workout_request = WorkoutRequest(
            user_profile=profile,
            workout_type=data.get('workout_type', 'strength'),
            duration_minutes=data.get('duration_minutes', 45),
            focus_areas=data.get('focus_areas', []),
            intensity=data.get('intensity', 'moderate')
        )
        
        # Generate workout
        workout = workout_service.generate_workout(workout_request)
        
        # Save workout history (optional)
        storage.save_workout_history(user_id, workout)
        
        return jsonify({
            'success': True,
            'workout': workout.to_dict()
        }), 200
        
    except GymAssistantError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate workout'}), 500

@workout_routes.route('/history/<user_id>', methods=['GET'])
def get_workout_history(user_id):
    """Get user's workout history"""
    try:
        history = storage.get_workout_history(user_id)
        return jsonify({
            'success': True,
            'workouts': [w.to_dict() for w in history]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Create `src/api/routes/nutrition_routes.py`:
```python
"""Nutrition planning endpoints"""
from flask import Blueprint, request, jsonify
from src.models import NutritionRequest, GymAssistantError
from src.nutrition_service import NutritionService
from src.storage import Storage

nutrition_routes = Blueprint('nutrition', __name__)
nutrition_service = NutritionService()
storage = Storage()

@nutrition_routes.route('/generate', methods=['POST'])
def generate_meal_plan():
    """Generate a personalized meal plan"""
    try:
        data = request.get_json()
        
        # Get user profile
        user_id = data.get('user_id')
        profile = storage.get_user(user_id)
        
        if not profile:
            return jsonify({'error': 'User not found'}), 404
        
        # Create nutrition request
        nutrition_request = NutritionRequest(
            user_profile=profile,
            diet_type=data.get('diet_type', 'balanced'),
            meals_per_day=data.get('meals_per_day', 3),
            dietary_restrictions=data.get('dietary_restrictions', []),
            cuisine_preference=data.get('cuisine_preference', 'any'),
            budget=data.get('budget', 'medium')
        )
        
        # Generate meal plan
        meal_plan = nutrition_service.generate_meal_plan(nutrition_request)
        
        # Save to history
        storage.save_meal_plan_history(user_id, meal_plan)
        
        return jsonify({
            'success': True,
            'meal_plan': meal_plan.to_dict()
        }), 200
        
    except GymAssistantError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to generate meal plan'}), 500

@nutrition_routes.route('/calculate-tdee', methods=['POST'])
def calculate_tdee():
    """Calculate TDEE for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        profile = storage.get_user(user_id)
        
        if not profile:
            return jsonify({'error': 'User not found'}), 404
        
        tdee = nutrition_service.calculate_tdee(profile)
        
        return jsonify({
            'success': True,
            'bmr': tdee['bmr'],
            'tdee': tdee['tdee'],
            'activity_level': tdee['activity_level']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### Step 1.3: Update Models for API Serialization

Add to `src/models.py`:
```python
def to_dict(self) -> dict:
    """Convert model to dictionary for JSON serialization"""
    # Add this method to UserProfile, Workout, NutritionPlan, Exercise
    pass
```

#### Step 1.4: Run the API Server

Create `src/api/server.py`:
```python
"""Development server entry point"""
from src.api import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
```

Run the server:
```bash
python -m src.api.server
```

---

### Phase 2: Frontend Development (Week 3-4)

#### Step 2.1: Initialize React Project

```bash
# Create frontend directory
npx create-react-app frontend
cd frontend

# Install dependencies
npm install axios react-router-dom @mui/material @emotion/react @emotion/styled
npm install recharts formik yup
```

#### Step 2.2: Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Profile/
│   │   │   ├── ProfileForm.jsx
│   │   │   └── ProfileView.jsx
│   │   ├── Workout/
│   │   │   ├── WorkoutGenerator.jsx
│   │   │   ├── WorkoutCard.jsx
│   │   │   └── ExerciseList.jsx
│   │   ├── Nutrition/
│   │   │   ├── MealPlanGenerator.jsx
│   │   │   ├── MealCard.jsx
│   │   │   └── TDEECalculator.jsx
│   │   ├── Common/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── Loading.jsx
│   │   └── Auth/
│   │       ├── Login.jsx
│   │       └── Register.jsx
│   ├── services/
│   │   ├── api.js
│   │   ├── userService.js
│   │   ├── workoutService.js
│   │   └── nutritionService.js
│   ├── context/
│   │   └── UserContext.jsx
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Dashboard.jsx
│   │   ├── WorkoutPage.jsx
│   │   └── NutritionPage.jsx
│   ├── utils/
│   │   └── helpers.js
│   ├── App.jsx
│   └── index.js
├── package.json
└── .env
```

#### Step 2.3: Create API Service

Create `src/services/api.js`:
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

Create `src/services/workoutService.js`:
```javascript
import api from './api';

export const workoutService = {
  generateWorkout: async (workoutData) => {
    const response = await api.post('/workouts/generate', workoutData);
    return response.data;
  },

  getWorkoutHistory: async (userId) => {
    const response = await api.get(`/workouts/history/${userId}`);
    return response.data;
  },

  findSimilarExercises: async (exerciseName, filters) => {
    const response = await api.post('/workouts/similar', {
      exercise_name: exerciseName,
      ...filters,
    });
    return response.data;
  },
};
```

#### Step 2.4: Create React Components

Create `src/components/Workout/WorkoutGenerator.jsx`:
```javascript
import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import { workoutService } from '../../services/workoutService';

const WorkoutGenerator = ({ userId }) => {
  const [formData, setFormData] = useState({
    workout_type: 'strength',
    duration_minutes: 45,
    intensity: 'moderate',
    focus_areas: [],
  });
  const [workout, setWorkout] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await workoutService.generateWorkout({
        user_id: userId,
        ...formData,
      });
      setWorkout(result.workout);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate workout');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Generate Workout Plan
          </Typography>

          <form onSubmit={handleSubmit}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Workout Type</InputLabel>
              <Select
                value={formData.workout_type}
                onChange={(e) =>
                  setFormData({ ...formData, workout_type: e.target.value })
                }
              >
                <MenuItem value="strength">Strength</MenuItem>
                <MenuItem value="cardio">Cardio</MenuItem>
                <MenuItem value="hiit">HIIT</MenuItem>
                <MenuItem value="flexibility">Flexibility</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              margin="normal"
              label="Duration (minutes)"
              type="number"
              value={formData.duration_minutes}
              onChange={(e) =>
                setFormData({ ...formData, duration_minutes: e.target.value })
              }
            />

            <FormControl fullWidth margin="normal">
              <InputLabel>Intensity</InputLabel>
              <Select
                value={formData.intensity}
                onChange={(e) =>
                  setFormData({ ...formData, intensity: e.target.value })
                }
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="moderate">Moderate</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>

            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Workout'}
            </Button>
          </form>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {workout && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6">{workout.name}</Typography>
            <Typography variant="body2" color="textSecondary">
              {workout.description}
            </Typography>
            {/* Render exercises */}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default WorkoutGenerator;
```

#### Step 2.5: Create Main App Component

Update `src/App.jsx`:
```javascript
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Navbar from './components/Common/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import WorkoutPage from './pages/WorkoutPage';
import NutritionPage from './pages/NutritionPage';
import { UserProvider } from './context/UserContext';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <UserProvider>
        <Router>
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/workout" element={<WorkoutPage />} />
            <Route path="/nutrition" element={<NutritionPage />} />
          </Routes>
        </Router>
      </UserProvider>
    </ThemeProvider>
  );
}

export default App;
```

---

### Phase 3: Database Integration (Week 5)

#### Step 3.1: Choose Database

**Option A: SQLite (Simple, file-based)**
```bash
# Already included in Python
```

**Option B: PostgreSQL (Production-ready)**
```bash
pip install psycopg2-binary sqlalchemy alembic
```

#### Step 3.2: Create Database Models

Create `src/database/models.py`:
```python
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    age = Column(Integer)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    gender = Column(String)
    fitness_goal = Column(String)
    equipment = Column(JSON)  # List of equipment
    injuries = Column(JSON)  # List of injuries
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workouts = relationship("WorkoutHistory", back_populates="user")
    meal_plans = relationship("MealPlanHistory", back_populates="user")

class WorkoutHistory(Base):
    __tablename__ = 'workout_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    workout_type = Column(String)
    duration_minutes = Column(Integer)
    exercises = Column(JSON)  # List of exercises
    calories_burned = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="workouts")

class MealPlanHistory(Base):
    __tablename__ = 'meal_plan_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    diet_type = Column(String)
    meals = Column(JSON)  # List of meals
    total_calories = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="meal_plans")
```

#### Step 3.3: Database Connection

Create `src/database/connection.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_config

config = get_config()
engine = create_engine(config.database_url)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### Phase 4: Authentication & Authorization (Week 6)

#### Step 4.1: Implement JWT Authentication

```bash
pip install pyjwt bcrypt
```

Create `src/auth/jwt_handler.py`:
```python
import jwt
from datetime import datetime, timedelta
from src.config import get_config

config = get_config()

def create_access_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, config.secret_key, algorithm='HS256')

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')
```

#### Step 4.2: Protected Routes

Create `src/auth/middleware.py`:
```python
from functools import wraps
from flask import request, jsonify
from src.auth.jwt_handler import verify_token

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        try:
            payload = verify_token(token)
            request.user_id = payload['user_id']
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
    
    return decorated
```

---

### Phase 5: Deployment (Week 7)

#### Step 5.1: Backend Deployment (Heroku)

```bash
# Create Procfile
web: gunicorn src.api.server:app

# Install gunicorn
pip install gunicorn
pip freeze > requirements.txt

# Deploy
heroku create gym-assistant-api
heroku config:set OPENAI_API_KEY=your-key
git push heroku main
```

#### Step 5.2: Frontend Deployment (Vercel/Netlify)

```bash
# Build frontend
cd frontend
npm run build

# Deploy to Vercel
npm install -g vercel
vercel --prod

# Or deploy to Netlify
npm install -g netlify-cli
netlify deploy --prod
```

#### Step 5.3: Database Deployment

```bash
# Heroku PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev
heroku config:get DATABASE_URL
```

---

## 🧪 Testing Strategy

### Backend Testing

```python
# tests/test_api.py
import pytest
from src.api import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_user(client):
    response = client.post('/api/users/', json={
        'name': 'Test User',
        'age': 25,
        'weight_kg': 70,
        'height_cm': 175,
        'gender': 'male'
    })
    assert response.status_code == 201
    assert b'User profile created' in response.data
```

### Frontend Testing

```javascript
// src/components/__tests__/WorkoutGenerator.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import WorkoutGenerator from '../Workout/WorkoutGenerator';

test('renders workout generator form', () => {
  render(<WorkoutGenerator userId="test-123" />);
  expect(screen.getByText('Generate Workout Plan')).toBeInTheDocument();
});
```

---

## 🔒 Security Considerations

### Backend Security Checklist

- [ ] Validate all user inputs
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Use HTTPS in production
- [ ] Sanitize database queries (prevent SQL injection)
- [ ] Implement CORS properly
- [ ] Use secure password hashing (bcrypt)
- [ ] Implement JWT token expiration
- [ ] Add request size limits
- [ ] Log security events

### Frontend Security Checklist

- [ ] Store tokens securely (httpOnly cookies preferred)
- [ ] Validate forms on client side
- [ ] Sanitize user-generated content
- [ ] Implement CSP headers
- [ ] Use HTTPS only
- [ ] Prevent XSS attacks
- [ ] Implement proper error handling (don't leak sensitive info)

---

## 📚 Additional Resources

### Learning Resources

- **Flask**: [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
- **FastAPI**: [FastAPI Documentation](https://fastapi.tiangolo.com/)
- **React**: [React Official Tutorial](https://react.dev/learn)
- **Material-UI**: [MUI Documentation](https://mui.com/)
- **SQLAlchemy**: [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)

### Example Projects

- [Real Python - Flask Tutorial](https://realpython.com/tutorials/flask/)
- [Traversy Media - React Crash Course](https://www.youtube.com/watch?v=w7ejDZ8SWv8)
- [FastAPI Full Stack Template](https://github.com/tiangolo/full-stack-fastapi-postgresql)

---

## 🎯 Next Steps

1. **Choose your tech stack** based on your learning goals and timeline
2. **Start with Phase 1** - Get the API running locally
3. **Build incrementally** - Test each feature as you build
4. **Add authentication** once basic CRUD operations work
5. **Deploy early** to catch deployment issues
6. **Iterate based on user feedback**

---

## 💡 Pro Tips

- **Start small**: Get a single endpoint working end-to-end before building all features
- **Use version control**: Commit frequently with meaningful messages
- **Test manually first**: Use Postman or curl to test API endpoints
- **Read error messages**: They usually tell you exactly what's wrong
- **Check the browser console**: Frontend errors are logged there
- **Use environment variables**: Never commit API keys or secrets
- **Document as you go**: Future you will thank present you

---

## 📞 Getting Help

If you get stuck:

1. Read the error message carefully
2. Check the official documentation
3. Search Stack Overflow
4. Ask in class discussion forums
5. Reach out to professor or TAs

---

## 📄 License

This guide is part of the AI-Powered Gym Assistant project for IS218.

**Good luck building your web interface! 🚀**
