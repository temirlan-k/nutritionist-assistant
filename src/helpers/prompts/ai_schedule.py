from datetime import datetime, timedelta
import json
from typing import List

from src.models.user import User, PhysicalData
from src.models.category import Category


async def get_ai_schedule_prompts(physical_data:PhysicalData, category: Category, goal: str, comments: str, duration: int, month: int, week: int) -> str:
    # Convert duration to integer and validate
    months = min(int(duration), 3)  # Cap at 3 months
    
    prompt = f"""
You are an AI-powered professional nutritionist and fitness coach with expertise in personalized meal and workout planning.
Your task is to generate a structured {months} month meal and fitness schedule based on the user's personal data and goals.

## User Details:
- **Goal:** {goal}
- **Category:** {category.name}
- **Restrictions:** {comments}
- **Physical Data:** {physical_data.weight}kg, {physical_data.height}cm, {physical_data.age} years old

## Schedule Structure Requirements:
1. Each month MUST contain exactly:
   - 4 weeks
   - 28 days
2. Each week MUST:
   - Start on Monday
   - Contain exactly 7 days
3. Day numbers MUST:
   - Start from 1
   - Continue sequentially without breaks
   - End at {months * 28} (total days)

## Instructions:
- Return a valid JSON object with no additional formatting or text
- Structure: Months → Weeks → Days
- Each day MUST contain:
  - Meals (Breakfast, Lunch, Dinner)
    - Include food items
    - Include portion sizes
    - Include calories per meal
  - Workouts
    - Exercise details
    - Sets and reps
    - Calories burned
  - Total daily calorie intake
  - Total daily calories burned
  - Status (default: "not_done")

## Example Response:
{{
  "months": [
    {{
      "month": 1,
      "weeks": [
        {{
          "week": 1,
          "days": [
            {{
              "day_number": 1,
              "day_of_week": "Monday",
              "meals": [
                {{
                  "meal": "breakfast",
                  "food": ["Oatmeal (1 cup)", "Banana (1 medium)", "Almonds (1oz)"],
                  "calories": 400
                }},
                {{
                  "meal": "lunch",
                  "food": ["Grilled chicken breast (6oz)", "Brown rice (1 cup)", "Steamed vegetables (2 cups)"],
                  "calories": 600
                }},
                {{
                  "meal": "dinner",
                  "food": ["Salmon fillet (5oz)", "Quinoa (3/4 cup)", "Roasted broccoli (2 cups)"],
                  "calories": 500
                }}
              ],
              "total_calories": 1500,
              "workout": [
                {{
                  "exercise": "Squats",
                  "sets": 3,
                  "reps": 15,
                  "calories_burned": 50
                }},
                {{
                  "exercise": "Push-ups",
                  "sets": 3,
                  "reps": 20,
                  "calories_burned": 40
                }}
              ],
              "total_calories_burned": 90,
              "status": "not_done"
            }}
          ]
        }}
      ]
    }}
  ]
}}

IMPORTANT VALIDATION RULES:
1. Month numbers must be sequential (1 to {months})
2. Week numbers must be sequential within each month (1 to 4)
3. Day numbers must be sequential across all months (1 to {months * 28})
4. All weeks must start with Monday
5. Each month must have exactly 28 days (4 weeks)
6. Meals and workouts must align with the user's goals and restrictions
"""
    return prompt

async def fetch_weekly_schedule_prompt(physical_data:PhysicalData, category: str, goal, comments, duration,current_month, current_week):
    now = datetime.now()
    days_until_monday = (7 - now.weekday()) % 7 
    start_date = now + timedelta(days=days_until_monday)
    
    weeks_offset = (current_month - 1) * 4 + (current_week - 1)
    start_date += timedelta(weeks=weeks_offset)

    prompt = f"""
You are an AI-powered nutritionist and fitness coach. Generate a structured plan ONLY for week {current_week} of month {current_month}.

## User Details:
- Goal: {goal}
- Category: {category}
- Restrictions/Comments: {comments}
- Physical Data: {physical_data.weight}kg, {physical_data.height}cm, {physical_data.age} years old

## Schedule Requirements:
- Generate a detailed 7-day plan (1 week).
- The first day must be Monday ({start_date.strftime('%Y-%m-%d')}).
- Each day must include:
  - Meals: Breakfast, Lunch, Dinner. For each meal, list:
      - A list of food items with portion sizes.
      - Calories per meal.
  - Workout details:
      - List of exercises with sets, reps, and calories burned per exercise.
  - Total daily calories consumed and burned.
  - A default status field set to "not_done".
  
- Return ONLY valid JSON. Do not include any markdown, code blocks, or extra text.
- Your JSON MUST follow this schema exactly:
{{
  "month": {current_month},
  "week": {current_week},
  "days": [
    {{
      "date": "YYYY-MM-DD",
      "day_number": 1,
      "day_of_week": "Monday",
      "meals": [
        {{
          "meal": "breakfast",
          "food": ["Example food item (portion)"],
          "calories": 0
        }},
        {{
          "meal": "lunch",
          "food": ["Example food item (portion)"],
          "calories": 0
        }},
        {{
          "meal": "dinner",
          "food": ["Example food item (portion)"],
          "calories": 0
        }}
      ],
      "total_calories": 0,
      "workout": [
        {{
          "exercise": "Exercise Name",
          "sets": 0,
          "reps": 0,
          "calories_burned": 0
        }}
      ],
      "total_calories_burned": 0,
      "status": "not_done"
    }},
    ... (6 more day objects)
  ]
}}
IMPORTANT VALIDATION RULES:
 All weeks must start with Monday
 Each month must have exactly 28 days (4 weeks)
 Meals and workouts must align with the user's goals and restrictions
  Make sure that your response is a valid JSON object with no additional text.
"""
    return prompt