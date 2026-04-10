from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class NewsItem:
    title: str
    url: str
    content_text: str
    date: Optional[datetime] = None