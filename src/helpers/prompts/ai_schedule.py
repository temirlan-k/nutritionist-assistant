from datetime import datetime, timedelta
from typing import List

from src.models.user import User
from src.models.category import Category


async def get_ai_schedule_prompts(user: User, category: Category, goal: str, comments: str, duration: str):
    # Convert duration to integer and validate
    months = min(int(duration), 3)  # Cap at 3 months
    
    # Calculate start date as the next Monday
    start_date = datetime.now()
    while start_date.weekday() != 0:  
        start_date += timedelta(days=1)

    prompt = f"""
You are an AI-powered professional nutritionist and fitness coach with expertise in personalized meal and workout planning.
Your task is to generate a structured {months} month meal and fitness schedule based on the user's personal data and goals.

## User Details:
- **Goal:** {goal}
- **Category:** {category.name}
- **Restrictions:** {comments}
- **Physical Data:** {user.physical_data if user.physical_data else 'No data'}

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
              "date": "{start_date.strftime('%Y-%m-%d')}",
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