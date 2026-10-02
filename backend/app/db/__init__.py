"""
Database access package for tickets, analyses, and audit history.
"""
from app.db.repository import BaseRepository, get_repository

__all__ = ["BaseRepository", "get_repository"]
