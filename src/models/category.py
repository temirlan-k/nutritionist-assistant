
from beanie import Document, Link
from typing import Optional


class Category(Document):
    name: str
    description: str

    class Settings:
        collection = "categories"


