from typing import Optional

from beanie import Document, Link


class Category(Document):
    name: str
    description: str

    class Settings:
        collection = "categories"
