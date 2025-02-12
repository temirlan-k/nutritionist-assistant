import asyncio
import json
from datetime import datetime, timedelta
from openai import OpenAI


# 🔥 Укажи свой API-ключ OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key='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',
)


async def fetch_weekly_schedule(
    user, category, goal, comments, duration, current_month, current_week
):
    """Формирует промпт и делает запрос в GPT (1 неделя за раз)."""

    # Определяем дату начала недели
    start_date = datetime.now()
    while start_date.weekday() != 0:  # Ищем ближайший понедельник
        start_date += timedelta(days=1)
    start_date += timedelta(weeks=(current_month - 1) * 4 + (current_week - 1))

    # Формируем промпт
    prompt = f"""
You are an AI-powered nutritionist and fitness coach. Generate a structured plan **only for week {current_week} of month {current_month}**.

## User Details:
- **Goal:** {goal}
- **Category:** {category}
- **Restrictions:** {comments}
- **Physical Data:** {user.get("physical_data", "No data")}

## Schedule Requirements:
- Generate a **detailed 7-day plan (1 week)**
- The first day must be **Monday ({start_date.strftime('%Y-%m-%d')})**
- Each day must include:
  - Meals (Breakfast, Lunch, Dinner)
    - List of foods
    - Portion sizes
    - Calories per meal
  - Workouts
    - Exercise details
    - Sets, reps
    - Calories burned
  - Total daily calories in/out
  - Default status: "not_done"

- Return **only JSON**, no extra formatting.
- Убедись, что JSON строго валидный — без лишних символов и форматирования.
- Your response MUST be a valid JSON object without any additional formatting!
- Do not use code blocks, quotation marks, or any symbols outside of standard JSON syntax.

## Example Response:
{{
  "month": {current_month},
  "week": {current_week},
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
          "food": ["Grilled chicken (6oz)", "Brown rice (1 cup)", "Veggies (2 cups)"],
          "calories": 600
        }},
        {{
          "meal": "dinner",
          "food": ["Salmon (5oz)", "Quinoa (3/4 cup)", "Broccoli (2 cups)"],
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
"""

    # Отправляем запрос в GPT через OpenRouter
    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    # Получаем JSON-ответ
    response = completion.choices[0].message.content
    return response


async def generate_full_schedule(user, category, goal, comments, duration):
    """Основная функция: делает постраничные запросы по неделям и выводит JSON в реальном времени"""

    full_schedule = {"months": []}

    for month in range(1, min(1, 3) + 1):
        month_data = {"month": month, "weeks": []}

        for week in range(1, 5):
            print(f"\n🚀 Генерация: месяц {month}, неделя {week}...")

            # Делаем запрос в GPT для одной недели
            week_json_str = await fetch_weekly_schedule(
                user, category, goal, comments, duration, month, week
            )
            print(week_json_str)
            print("\n 🎉 Ответ получен!")
            try:
                week_data = json.loads(week_json_str)
                month_data["weeks"].append(week_data)
            except json.JSONDecodeError:
                print(f"❌ Ошибка парсинга JSON: месяц {month}, неделя {week}")
                continue
            
            if len(full_schedule["months"]) < month:
                full_schedule["months"].append(month_data)
            else:
                full_schedule["months"][month - 1]["weeks"].append(week_data)


            with open("schedule.json", "w", encoding="utf-8") as f:
                json.dump(full_schedule, f, indent=2, ensure_ascii=False)

    print("\n✅ Готово! Полный план сохранен в `schedule.json`.")
# ✅ Запуск асинхронной генерации
if __name__ == "__main__":
    user_data = {
        "name": "John Doe",
        "physical_data": "Height: 180cm, Weight: 75kg, Age: 30"
    }
    category = "General Fitness"
    goal = "Muscle Gain"
    comments = "No dairy, high protein"
    duration = 3  # Месяцев

    asyncio.run(generate_full_schedule(user_data, category, goal, comments, duration))
