import asyncio
import json
from openai import AsyncOpenAI
from src.helpers.prompts.aI_schedule_analyzer import get_ai_progress_analysis_prompt
from src.models.category import Category
from src.models.sessions import DayPlan, UserCategorySession
from src.models.user import PhysicalData, User
from typing import  Dict, List, Optional
from logging import getLogger
from src.helpers.prompts.ai_schedule import get_ai_schedule_prompts,fetch_weekly_schedule_prompt

logger = getLogger(__name__)

class AIScheduleGenerator:
    def __init__(self, api_key: str = "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", base_url: str = "https://openrouter.ai/api/v1"):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
    
    async def analyze_progress(
        self,
        user: User,
        user_data: UserCategorySession,
        category: Category,
        physical_data: PhysicalData,
        weight_after: int,
        day_plans: List[DayPlan|dict]
    ) -> Optional[dict]:
        """Анализирует прогресс пользователя после завершения плана."""
        try:
            prompt = await get_ai_progress_analysis_prompt(user_data, category, user, physical_data, weight_after,day_plans)

            completion = await self.client.chat.completions.create(
                model="openai/gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI-powered fitness and nutrition analyst."},
                    {"role": "user", "content": prompt},
                ],
            )

            response = completion.choices[0].message.content
            analysis = json.loads(response) 

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from AI: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during progress analysis: {e}")
            raise


    async def fetch_weekly_schedule(
        self,
        physical_data: PhysicalData,
        category: str,
        goal: str,
        comments: str,
        duration: int,
        month: int,
        week: int
    ) -> Optional[str]:
        """Fetch the schedule for a particular week."""
        try:
            prompt = await fetch_weekly_schedule_prompt(
                physical_data, category, goal, comments, duration,month, week
            )

            completion = await self.client.chat.completions.create(
                model="openai/gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )

            response = completion.choices[0].message.content
            json.loads(response)  
            return response

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from AI: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating schedule: {e}")
            raise

    async def generate_full_schedule(
        self,
        physical_data: PhysicalData,
        category: str,
        goal: str,
        comments: str,
        duration: int
    ) -> list:
        """Generate a complete schedule for all weeks."""
        schedules = []

        tasks = []
        
        for month in range(1, min(duration, 3) + 1):
            for week in range(1, 5):
                logger.info(f"🚀 Generating: month {month}, week {week}...")
                tasks.append(self.fetch_weekly_schedule(
                    physical_data, category, goal, comments, duration, month, week
                ))
                logger.info(f"🎉 Generated: month {month}, week {week}.")

        week_schedules = await asyncio.gather(*tasks)

        for week_schedule in week_schedules:
            if week_schedule:
                print(json.loads(week_schedule))
                schedules.append(json.loads(week_schedule))  # Добавление полученных данных
            else:
                logger.warning("Failed to generate schedule for a week.")
        
        return schedules
