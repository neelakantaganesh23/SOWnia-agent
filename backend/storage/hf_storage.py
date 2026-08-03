"""Hugging Face Datasets storage for review results.

Push/pull review results to a private HF Dataset repository.
Uses JSONL append pattern for each completed review.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from huggingface_hub import HfApi, hf_hub_download, upload_file
from huggingface_hub.utils import RepositoryNotFoundError

from backend.config import settings

logger = logging.getLogger(__name__)


class HFStorage:
    """Store and retrieve review results on Hugging Face Datasets Hub.

    Each review is stored as a JSON line in a JSONL file.
    The dataset is a private repo on HF Hub.
    """

    REVIEWS_FILE = "data/reviews.jsonl"

    def __init__(self):
        self.api = HfApi(token=settings.HF_TOKEN)
        self.repo_id = settings.HF_DATASET_REPO

    def _ensure_repo_exists(self) -> None:
        """Create the dataset repository if it doesn't exist."""
        try:
            self.api.repo_info(repo_id=self.repo_id, repo_type="dataset")
            logger.debug(f"Dataset repo '{self.repo_id}' exists.")
        except RepositoryNotFoundError:
            logger.info(f"Creating dataset repo '{self.repo_id}'...")
            self.api.create_repo(
                repo_id=self.repo_id,
                repo_type="dataset",
                private=True,
            )
            # Initialize with empty JSONL file
            self._upload_content("", self.REVIEWS_FILE, "Initialize dataset")

    def _upload_content(
        self, content: str, path_in_repo: str, commit_message: str
    ) -> None:
        """Upload content to the HF dataset repository.

        Args:
            content: Text content to upload.
            path_in_repo: Path within the repository.
            commit_message: Git commit message.
        """
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        self.api.upload_file(
            path_or_fileobj=temp_path,
            path_in_repo=path_in_repo,
            repo_id=self.repo_id,
            repo_type="dataset",
            commit_message=commit_message,
        )

        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)

    def save_review(self, review_data: Dict[str, Any]) -> None:
        """Save a completed review to HF Datasets.

        Appends the review as a new line in the JSONL file.

        Args:
            review_data: Review data dictionary to store.
        """
        if not settings.HF_TOKEN or "your_" in settings.HF_TOKEN:
            logger.debug("HF_TOKEN not set or placeholder used; skipping HF Datasets persistence.")
            return

        self._ensure_repo_exists()

        # Ensure timestamp is serializable
        if "timestamp" in review_data:
            if isinstance(review_data["timestamp"], datetime):
                review_data["timestamp"] = review_data["timestamp"].isoformat()

        try:
            # Download existing JSONL
            existing_content = self._download_reviews_file()
        except Exception:
            existing_content = ""

        # Append new review
        new_line = json.dumps(review_data, default=str)
        if existing_content and not existing_content.endswith("\n"):
            existing_content += "\n"
        updated_content = existing_content + new_line + "\n"

        # Upload updated file
        review_id = review_data.get("review_id", "unknown")
        self._upload_content(
            updated_content,
            self.REVIEWS_FILE,
            f"Add review {review_id}",
        )
        logger.info(f"Review {review_id} saved to HF Datasets.")

    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific review by ID.

        Args:
            review_id: UUID of the review to retrieve.

        Returns:
            Review data dictionary, or None if not found.
        """
        reviews = self.list_reviews()
        for review in reviews:
            if review.get("review_id") == review_id:
                return review
        return None

    def list_reviews(self) -> List[Dict[str, Any]]:
        """List all stored reviews.

        Returns:
            List of review data dictionaries, newest first.
        """
        if not settings.HF_TOKEN or "your_" in settings.HF_TOKEN:
            return []

        try:
            content = self._download_reviews_file()
        except Exception as e:
            logger.warning(f"Could not download reviews: {e}")
            return []

        reviews: List[Dict[str, Any]] = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    reviews.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSONL line: {line[:50]}...")

        # Sort by timestamp (newest first)
        reviews.sort(
            key=lambda r: r.get("timestamp", ""),
            reverse=True,
        )
        return reviews

    def delete_review(self, review_id: str) -> bool:
        """Delete a review by ID.

        Rewrites the JSONL file without the deleted review.

        Args:
            review_id: UUID of the review to delete.

        Returns:
            True if the review was found and deleted.
        """
        reviews = self.list_reviews()
        filtered = [r for r in reviews if r.get("review_id") != review_id]

        if len(filtered) == len(reviews):
            logger.warning(f"Review {review_id} not found for deletion.")
            return False

        # Rewrite file without the deleted review
        content = "\n".join(json.dumps(r, default=str) for r in filtered)
        if content:
            content += "\n"

        self._upload_content(
            content,
            self.REVIEWS_FILE,
            f"Delete review {review_id}",
        )
        logger.info(f"Review {review_id} deleted from HF Datasets.")
        return True

    def _download_reviews_file(self) -> str:
        """Download the reviews JSONL file content.

        Returns:
            File content as a string.
        """
        try:
            file_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.REVIEWS_FILE,
                repo_type="dataset",
                token=settings.HF_TOKEN,
            )
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.debug(f"Reviews file not found or error: {e}")
            return ""


# Singleton storage instance
hf_storage = HFStorage()
