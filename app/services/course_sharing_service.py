"""Course sharing and personal save system service."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class CourseSharingService:
    """Service for course sharing link generation and management."""

    def __init__(self, db: Session):
        self.db = db
        self.share_cache = {}  # In-memory cache for share links

    def create_share_link(
        self,
        course_id: str,
        user_id: str,
        course_data: Dict[str, Any],
        share_settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create shareable link for a course.

        Args:
            course_id: Course identifier
            user_id: Course owner user ID
            course_data: Course content and metadata
            share_settings: Sharing configuration

        Returns:
            Share link information and access configuration
        """
        try:
            # Generate secure share ID
            share_id = self._generate_share_id(course_id, user_id)

            # Calculate expiration
            expire_days = share_settings.get("expire_days", 30)
            expires_at = datetime.utcnow() + timedelta(days=expire_days)

            # Create share configuration
            share_config = {
                "share_id": share_id,
                "course_id": course_id,
                "owner_user_id": user_id,
                "public_access": share_settings.get("public_access", True),
                "allow_copy": share_settings.get("allow_copy", True),
                "allow_comments": share_settings.get("allow_comments", True),
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "access_count": 0,
                "is_active": True,
            }

            # Store course data for sharing
            share_data = {
                "share_config": share_config,
                "course_content": {
                    "title": course_data.get("title", "Untitled Course"),
                    "description": course_data.get("description", ""),
                    "places": course_data.get("places", []),
                    "total_places": len(course_data.get("places", [])),
                    "estimated_duration": self._calculate_total_duration(
                        course_data.get("places", [])
                    ),
                    "course_type": course_data.get("course_type", "general"),
                },
            }

            # Cache share data
            self.share_cache[share_id] = share_data

            # Generate shareable URL
            share_link = f"https://hotly.app/shared/{share_id}"

            result = {
                "share_link": share_link,
                "share_id": share_id,
                "expires_at": expires_at.isoformat(),
                "access_level": "public"
                if share_settings.get("public_access")
                else "private",
                "permissions": {
                    "can_copy": share_settings.get("allow_copy", True),
                    "can_comment": share_settings.get("allow_comments", True),
                    "can_view": True,
                },
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Share link created for course {course_id}: {share_id}")
            return result

        except Exception as e:
            logger.error(f"Error creating share link: {e}")
            raise

    def access_shared_course(
        self, share_id: str, accessing_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Access shared course via share link.

        Args:
            share_id: Share link identifier
            accessing_user_id: Optional user accessing the course

        Returns:
            Shared course information
        """
        try:
            # Check if share exists and is valid
            if share_id not in self.share_cache:
                raise ValueError("Share link not found or expired")

            share_data = self.share_cache[share_id]
            share_config = share_data["share_config"]

            # Check expiration
            expires_at = datetime.fromisoformat(share_config["expires_at"])
            if datetime.utcnow() > expires_at:
                # Remove expired share
                del self.share_cache[share_id]
                raise ValueError("Share link has expired")

            # Check if share is active
            if not share_config["is_active"]:
                raise ValueError("Share link has been revoked")

            # Update access count
            share_config["access_count"] += 1
            share_config["last_accessed_at"] = datetime.utcnow().isoformat()

            if accessing_user_id:
                share_config["last_accessed_by"] = accessing_user_id

            # Prepare response data
            course_content = share_data["course_content"]

            shared_course_data = {
                "course_title": course_content["title"],
                "course_description": course_content["description"],
                "places": course_content["places"],
                "total_places": course_content["total_places"],
                "estimated_duration": course_content["estimated_duration"],
                "course_type": course_content["course_type"],
                "created_by": share_config["owner_user_id"],
                "shared_at": share_config["created_at"],
                "access_permissions": {
                    "can_copy": share_config["allow_copy"],
                    "can_comment": share_config["allow_comments"],
                },
                "sharing_stats": {
                    "total_views": share_config["access_count"],
                    "share_created": share_config["created_at"],
                },
            }

            logger.info(
                f"Shared course {share_id} accessed (total views: {share_config['access_count']})"
            )
            return shared_course_data

        except Exception as e:
            logger.error(f"Error accessing shared course: {e}")
            raise

    def revoke_share_link(
        self, share_id: str, user_id: str, reason: str = "user_request"
    ) -> Dict[str, Any]:
        """
        Revoke share link within 1 second requirement.

        Args:
            share_id: Share link to revoke
            user_id: User requesting revocation
            reason: Reason for revocation

        Returns:
            Revocation confirmation
        """
        try:
            # Validate ownership
            if share_id not in self.share_cache:
                raise ValueError("Share link not found")

            share_data = self.share_cache[share_id]
            share_config = share_data["share_config"]

            if share_config["owner_user_id"] != user_id:
                raise ValueError("Only course owner can revoke share link")

            # Immediate revocation
            share_config["is_active"] = False
            share_config["revoked_at"] = datetime.utcnow().isoformat()
            share_config["revoked_by"] = user_id
            share_config["revocation_reason"] = reason

            revocation_result = {
                "share_id": share_id,
                "revoked": True,
                "revoked_at": share_config["revoked_at"],
                "reason": reason,
                "link_invalidated": True,
                "access_count_final": share_config["access_count"],
            }

            logger.info(f"Share link {share_id} revoked by {user_id}, reason: {reason}")
            return revocation_result

        except Exception as e:
            logger.error(f"Error revoking share link: {e}")
            raise

    def _generate_share_id(self, course_id: str, user_id: str) -> str:
        """Generate secure share ID."""
        # Create unique share ID using course, user, and timestamp
        timestamp = str(datetime.utcnow().timestamp())
        random_bytes = secrets.token_bytes(16)

        # Combine data for hashing
        combined = f"{course_id}_{user_id}_{timestamp}_{random_bytes.hex()}"

        # Generate secure hash
        hash_object = hashlib.sha256(combined.encode())
        share_id = hash_object.hexdigest()[:12]  # Use first 12 characters

        return f"share_{share_id}"

    def _calculate_total_duration(self, places: List[Dict[str, Any]]) -> int:
        """Calculate total course duration in minutes."""
        total_duration = 0

        for place in places:
            visit_duration = place.get("duration_minutes", 60)  # Default 1 hour
            total_duration += visit_duration

        # Add travel time between places (estimate 15 min average)
        if len(places) > 1:
            travel_time = (len(places) - 1) * 15
            total_duration += travel_time

        return total_duration


class PersonalCourseStorageService:
    """Service for personal course storage and organization."""

    def __init__(self, db: Session):
        self.db = db
        self.user_folders = {}  # In-memory cache for user folders

    def save_course_to_favorites(
        self,
        course_id: str,
        user_id: str,
        save_type: str = "favorite",
        folder_name: Optional[str] = None,
        private_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save course to user's personal favorites.

        Args:
            course_id: Course to save
            user_id: User saving the course
            save_type: Type of save (favorite, wishlist, archive)
            folder_name: Target folder for organization
            private_notes: Personal notes about the course

        Returns:
            Save operation result
        """
        try:
            # Generate unique save ID
            save_id = str(uuid4())

            save_record = {
                "save_id": save_id,
                "course_id": course_id,
                "user_id": user_id,
                "save_type": save_type,
                "folder_name": folder_name or "기본 폴더",
                "private_notes": private_notes or "",
                "saved_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "access_count": 0,
            }

            # Store in user's personal collection
            user_key = f"user_{user_id}_saved_courses"
            if user_key not in self.user_folders:
                self.user_folders[user_key] = []

            # Check for duplicates
            existing_save = next(
                (
                    save
                    for save in self.user_folders[user_key]
                    if save["course_id"] == course_id and save["is_active"]
                ),
                None,
            )

            if existing_save:
                # Update existing save
                existing_save.update(
                    {
                        "folder_name": folder_name or existing_save["folder_name"],
                        "private_notes": private_notes
                        or existing_save["private_notes"],
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                save_result = existing_save
            else:
                # Add new save
                self.user_folders[user_key].append(save_record)
                save_result = save_record

            result = {
                "saved": True,
                "save_id": save_result["save_id"],
                "saved_to_folder": save_result["folder_name"],
                "save_type": save_result["save_type"],
                "saved_at": save_result.get("saved_at", save_result.get("updated_at")),
                "total_saved_courses": len(self.user_folders[user_key]),
            }

            logger.info(f"Course {course_id} saved to {save_type} by user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error saving course to favorites: {e}")
            raise

    def create_personal_folder(
        self,
        user_id: str,
        folder_name: str,
        folder_description: str = "",
        folder_color: str = "#95A5A6",
        is_private: bool = True,
    ) -> Dict[str, Any]:
        """
        Create personal folder for course organization.

        Args:
            user_id: User creating folder
            folder_name: Name of the folder
            folder_description: Description of folder purpose
            folder_color: Folder color code
            is_private: Whether folder is private

        Returns:
            Created folder information
        """
        try:
            folder_id = str(uuid4())

            folder_data = {
                "folder_id": folder_id,
                "folder_name": folder_name,
                "folder_description": folder_description,
                "folder_color": folder_color,
                "is_private": is_private,
                "owner_user_id": user_id,
                "course_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Store folder metadata
            user_folders_key = f"user_{user_id}_folders"
            if user_folders_key not in self.user_folders:
                self.user_folders[user_folders_key] = []

            self.user_folders[user_folders_key].append(folder_data)

            result = {
                "folder_id": folder_id,
                "folder_name": folder_name,
                "folder_created": True,
                "total_folders": len(self.user_folders[user_folders_key]),
                "created_at": folder_data["created_at"],
            }

            logger.info(f"Personal folder '{folder_name}' created for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error creating personal folder: {e}")
            raise

    def organize_courses_in_folder(
        self,
        folder_id: str,
        user_id: str,
        course_ids: List[str],
        organization_type: str = "move",
    ) -> Dict[str, Any]:
        """
        Organize courses within a personal folder.

        Args:
            folder_id: Target folder ID
            user_id: User organizing courses
            course_ids: List of course IDs to organize
            organization_type: move or copy operation

        Returns:
            Organization operation result
        """
        try:
            # Validate folder ownership
            user_folders_key = f"user_{user_id}_folders"
            if user_folders_key not in self.user_folders:
                raise ValueError("User has no folders")

            target_folder = next(
                (
                    folder
                    for folder in self.user_folders[user_folders_key]
                    if folder["folder_id"] == folder_id
                ),
                None,
            )

            if not target_folder:
                raise ValueError("Folder not found")

            # Process course organization
            organized_courses = []
            user_courses_key = f"user_{user_id}_saved_courses"

            if user_courses_key in self.user_folders:
                for course_id in course_ids:
                    # Find course in user's saved courses
                    course_save = next(
                        (
                            save
                            for save in self.user_folders[user_courses_key]
                            if save["course_id"] == course_id
                        ),
                        None,
                    )

                    if course_save:
                        if organization_type == "move":
                            course_save["folder_name"] = target_folder["folder_name"]
                            course_save["updated_at"] = datetime.utcnow().isoformat()
                        elif organization_type == "copy":
                            # Create copy in target folder
                            copied_save = {**course_save}
                            copied_save["save_id"] = str(uuid4())
                            copied_save["folder_name"] = target_folder["folder_name"]
                            copied_save["copied_at"] = datetime.utcnow().isoformat()
                            self.user_folders[user_courses_key].append(copied_save)

                        organized_courses.append(course_id)

            # Update folder metadata
            target_folder["updated_at"] = datetime.utcnow().isoformat()
            target_folder["course_count"] = len(
                [
                    save
                    for save in self.user_folders.get(user_courses_key, [])
                    if save["folder_name"] == target_folder["folder_name"]
                ]
            )

            organization_result = {
                "folder_id": folder_id,
                "courses_moved": len(organized_courses)
                if organization_type == "move"
                else 0,
                "courses_copied": len(organized_courses)
                if organization_type == "copy"
                else 0,
                "organization_type": organization_type,
                "folder_updated_at": target_folder["updated_at"],
                "new_course_count": target_folder["course_count"],
            }

            logger.info(
                f"Organized {len(organized_courses)} courses in folder {folder_id}"
            )
            return organization_result

        except Exception as e:
            logger.error(f"Error organizing courses in folder: {e}")
            raise

    def add_to_wishlist(
        self,
        course_id: str,
        user_id: str,
        priority: str = "medium",
        planned_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add course to user's wishlist.

        Args:
            course_id: Course to add to wishlist
            user_id: User adding to wishlist
            priority: Wishlist priority (low, medium, high)
            planned_date: Planned visit date
            notes: Personal notes

        Returns:
            Wishlist addition result
        """
        try:
            wishlist_entry = {
                "wishlist_id": str(uuid4()),
                "course_id": course_id,
                "user_id": user_id,
                "priority": priority,
                "planned_date": planned_date,
                "notes": notes or "",
                "added_at": datetime.utcnow().isoformat(),
                "status": "planned",  # planned, visited, cancelled
                "reminder_set": False,
            }

            # Store in user's wishlist
            user_wishlist_key = f"user_{user_id}_wishlist"
            if user_wishlist_key not in self.user_folders:
                self.user_folders[user_wishlist_key] = []

            self.user_folders[user_wishlist_key].append(wishlist_entry)

            result = {
                "added_to_wishlist": True,
                "wishlist_id": wishlist_entry["wishlist_id"],
                "priority": priority,
                "planned_date": planned_date,
                "total_wishlist_items": len(self.user_folders[user_wishlist_key]),
                "added_at": wishlist_entry["added_at"],
            }

            logger.info(
                f"Course {course_id} added to wishlist with {priority} priority"
            )
            return result

        except Exception as e:
            logger.error(f"Error adding to wishlist: {e}")
            raise


class CourseInteractionService:
    """Service for course likes, comments, and ratings."""

    def __init__(self, db: Session):
        self.db = db
        self.interactions_cache = {}

    def handle_course_like(
        self, course_id: str, user_id: str, action: str
    ) -> Dict[str, Any]:
        """
        Handle course like/unlike action.

        Args:
            course_id: Course to like/unlike
            user_id: User performing action
            action: like or unlike

        Returns:
            Like action result with updated counts
        """
        try:
            course_likes_key = f"course_{course_id}_likes"

            if course_likes_key not in self.interactions_cache:
                self.interactions_cache[course_likes_key] = {
                    "total_likes": 0,
                    "liked_by": [],
                    "like_history": [],
                }

            likes_data = self.interactions_cache[course_likes_key]
            user_already_liked = user_id in likes_data["liked_by"]

            if action == "like" and not user_already_liked:
                likes_data["liked_by"].append(user_id)
                likes_data["total_likes"] += 1
                likes_data["like_history"].append(
                    {
                        "user_id": user_id,
                        "action": "like",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                liked = True

            elif action == "unlike" and user_already_liked:
                likes_data["liked_by"].remove(user_id)
                likes_data["total_likes"] -= 1
                likes_data["like_history"].append(
                    {
                        "user_id": user_id,
                        "action": "unlike",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                liked = False

            else:
                # No change needed
                liked = user_already_liked

            result = {
                "course_id": course_id,
                "liked": liked,
                "total_likes": likes_data["total_likes"],
                "user_action": action,
                "action_timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Course {course_id} {action} by user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error handling course like: {e}")
            raise

    def add_course_comment(
        self,
        course_id: str,
        user_id: str,
        comment_text: str,
        rating: Optional[int] = None,
        is_public: bool = True,
    ) -> Dict[str, Any]:
        """
        Add comment to a course.

        Args:
            course_id: Course to comment on
            user_id: User adding comment
            comment_text: Comment content
            rating: Optional rating (1-5)
            is_public: Whether comment is public

        Returns:
            Comment creation result
        """
        try:
            # Validate rating if provided
            if rating is not None and not (1 <= rating <= 5):
                raise ValueError("Rating must be between 1 and 5")

            comment_id = str(uuid4())

            comment_data = {
                "comment_id": comment_id,
                "course_id": course_id,
                "user_id": user_id,
                "comment_text": comment_text,
                "rating": rating,
                "is_public": is_public,
                "posted_at": datetime.utcnow().isoformat(),
                "edited": False,
                "like_count": 0,
            }

            # Store comment
            course_comments_key = f"course_{course_id}_comments"
            if course_comments_key not in self.interactions_cache:
                self.interactions_cache[course_comments_key] = []

            self.interactions_cache[course_comments_key].append(comment_data)

            # Update course rating if rating provided
            if rating is not None:
                self._update_course_rating(course_id, rating)

            result = {
                "comment_id": comment_id,
                "posted": True,
                "posted_at": comment_data["posted_at"],
                "is_public": is_public,
                "total_comments": len(self.interactions_cache[course_comments_key]),
            }

            logger.info(f"Comment added to course {course_id} by user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error adding course comment: {e}")
            raise

    def get_course_ratings_summary(self, course_id: str) -> Dict[str, Any]:
        """
        Get aggregated ratings for a course.

        Args:
            course_id: Course to get ratings for

        Returns:
            Rating summary and distribution
        """
        try:
            course_ratings_key = f"course_{course_id}_ratings"

            if course_ratings_key not in self.interactions_cache:
                # No ratings yet
                return {
                    "average_rating": 0.0,
                    "total_ratings": 0,
                    "rating_distribution": {str(i): 0 for i in range(1, 6)},
                }

            ratings_data = self.interactions_cache[course_ratings_key]
            ratings_list = ratings_data.get("ratings", [])

            if not ratings_list:
                return {
                    "average_rating": 0.0,
                    "total_ratings": 0,
                    "rating_distribution": {str(i): 0 for i in range(1, 6)},
                }

            # Calculate statistics
            total_ratings = len(ratings_list)
            average_rating = sum(ratings_list) / total_ratings

            # Calculate distribution
            distribution = {str(i): 0 for i in range(1, 6)}
            for rating in ratings_list:
                distribution[str(rating)] += 1

            rating_summary = {
                "average_rating": round(average_rating, 2),
                "total_ratings": total_ratings,
                "rating_distribution": distribution,
                "calculated_at": datetime.utcnow().isoformat(),
            }

            return rating_summary

        except Exception as e:
            logger.error(f"Error getting course ratings: {e}")
            raise

    def _update_course_rating(self, course_id: str, new_rating: int):
        """Update course rating aggregation."""
        course_ratings_key = f"course_{course_id}_ratings"

        if course_ratings_key not in self.interactions_cache:
            self.interactions_cache[course_ratings_key] = {
                "ratings": [],
                "updated_at": datetime.utcnow().isoformat(),
            }

        self.interactions_cache[course_ratings_key]["ratings"].append(new_rating)
        self.interactions_cache[course_ratings_key][
            "updated_at"
        ] = datetime.utcnow().isoformat()


class CourseDiscoveryService:
    """Service for course discovery and trending analysis."""

    def __init__(self, db: Session):
        self.db = db
        self.discovery_cache = {}

    def discover_public_courses(
        self,
        location: Dict[str, float],
        radius_km: float = 10.0,
        category: Optional[str] = None,
        min_rating: float = 0.0,
        sort_by: str = "popularity",
    ) -> Dict[str, Any]:
        """
        Discover public courses based on criteria.

        Args:
            location: Search center location
            radius_km: Search radius in kilometers
            category: Filter by place category
            min_rating: Minimum course rating
            sort_by: Sorting criteria

        Returns:
            Discovered courses matching criteria
        """
        try:
            # Mock discovery for development
            # In production, would query actual course database

            mock_courses = [
                {
                    "course_id": f"discovered_course_{i}",
                    "title": f"발견된 코스 {i}",
                    "description": f"코스 {i} 설명",
                    "creator_name": f"사용자{i}",
                    "places_count": 3 + (i % 3),
                    "average_rating": 4.0 + (i % 2) * 0.5,
                    "total_ratings": 10 + i * 2,
                    "total_saves": 5 + i,
                    "distance_km": 2.0 + (i % 5),
                    "estimated_duration": 120 + (i % 3) * 30,
                    "created_at": f"2024-01-{10+i:02d}T12:00:00Z",
                }
                for i in range(8)
            ]

            # Apply filters
            filtered_courses = []
            for course in mock_courses:
                # Distance filter
                if course["distance_km"] <= radius_km:
                    # Rating filter
                    if course["average_rating"] >= min_rating:
                        filtered_courses.append(course)

            # Apply sorting
            if sort_by == "popularity":
                filtered_courses.sort(key=lambda x: x["total_saves"], reverse=True)
            elif sort_by == "rating":
                filtered_courses.sort(key=lambda x: x["average_rating"], reverse=True)
            elif sort_by == "distance":
                filtered_courses.sort(key=lambda x: x["distance_km"])

            discovery_result = {
                "courses": filtered_courses,
                "total_count": len(filtered_courses),
                "search_criteria": {
                    "location": location,
                    "radius_km": radius_km,
                    "category": category,
                    "min_rating": min_rating,
                    "sort_by": sort_by,
                },
                "discovered_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Discovered {len(filtered_courses)} courses in {radius_km}km radius"
            )
            return discovery_result

        except Exception as e:
            logger.error(f"Error discovering courses: {e}")
            raise

    def get_trending_courses(
        self,
        time_period: str = "week",
        location_filter: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get trending courses based on engagement metrics.

        Args:
            time_period: Trending period (week, month, all_time)
            location_filter: Geographic filter
            limit: Maximum courses to return

        Returns:
            Trending courses with ranking criteria
        """
        try:
            # Mock trending data
            trending_courses = [
                {
                    "course_id": f"trending_{i}",
                    "title": f"인기 코스 #{i+1}",
                    "trend_score": 95 - i * 5,
                    "recent_saves": 25 - i * 2,
                    "recent_views": 150 - i * 10,
                    "engagement_rate": 0.85 - i * 0.05,
                    "location": location_filter or "seoul",
                    "trending_reason": "high_engagement"
                    if i < 3
                    else "growing_popularity",
                }
                for i in range(limit)
            ]

            trending_result = {
                "trending_courses": trending_courses,
                "ranking_criteria": {
                    "time_period": time_period,
                    "factors": ["saves", "views", "engagement_rate", "recent_growth"],
                    "location_filter": location_filter,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                "total_trending": len(trending_courses),
            }

            logger.info(
                f"Retrieved {len(trending_courses)} trending courses for {time_period}"
            )
            return trending_result

        except Exception as e:
            logger.error(f"Error getting trending courses: {e}")
            raise

    def recommend_courses_from_saves(
        self,
        user_id: str,
        saved_courses_count: int,
        preferred_categories: List[str],
        activity_radius_km: float = 15.0,
    ) -> Dict[str, Any]:
        """
        Recommend courses based on user's save history.

        Args:
            user_id: User to recommend for
            saved_courses_count: Number of courses user has saved
            preferred_categories: User's preferred place categories
            activity_radius_km: User's typical activity radius

        Returns:
            Personalized course recommendations
        """
        try:
            # Generate personalized recommendations
            recommendations = []

            for i, category in enumerate(preferred_categories):
                recommendations.extend(
                    [
                        {
                            "course_id": f"rec_{category}_{j}",
                            "title": f"{category} 추천 코스 {j+1}",
                            "category_match": category,
                            "similarity_score": 0.9 - (i * 0.1) - (j * 0.05),
                            "reason": f"'{category}' 카테고리 선호도 기반",
                            "estimated_interest": "high" if j == 0 else "medium",
                        }
                        for j in range(2)  # 2 recommendations per category
                    ]
                )

            recommendation_result = {
                "recommended_courses": recommendations[:6],  # Top 6 recommendations
                "recommendation_reason": f"Based on {saved_courses_count} saved courses and category preferences",
                "confidence_score": min(0.7 + (saved_courses_count * 0.05), 0.95),
                "personalization_factors": {
                    "save_history": saved_courses_count,
                    "category_preferences": preferred_categories,
                    "activity_radius": activity_radius_km,
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Generated {len(recommendations)} recommendations for user {user_id}"
            )
            return recommendation_result

        except Exception as e:
            logger.error(f"Error recommending courses: {e}")
            raise


class CourseAnalyticsService:
    """Service for course sharing analytics and insights."""

    def __init__(self):
        self.analytics_cache = {}

    def get_sharing_analytics(
        self, course_id: str, owner_user_id: str, analytics_period: str = "30_days"
    ) -> Dict[str, Any]:
        """
        Get comprehensive sharing analytics for course.

        Args:
            course_id: Course to analyze
            owner_user_id: Course owner
            analytics_period: Analysis time period

        Returns:
            Detailed sharing analytics
        """
        try:
            # Mock analytics data
            analytics_data = {
                "total_shares": 15,
                "unique_viewers": 45,
                "total_views": 67,
                "save_rate": 0.35,  # 35% of viewers saved the course
                "engagement_score": 0.78,
                "geographic_distribution": {
                    "seoul": 0.6,
                    "busan": 0.2,
                    "incheon": 0.1,
                    "other": 0.1,
                },
                "view_sources": {
                    "direct_link": 0.4,
                    "discovery": 0.3,
                    "search": 0.2,
                    "recommendations": 0.1,
                },
                "peak_activity_hours": [19, 20, 21],  # 7-9 PM
                "analytics_period": analytics_period,
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Generated sharing analytics for course {course_id}")
            return analytics_data

        except Exception as e:
            logger.error(f"Error generating sharing analytics: {e}")
            raise

    def analyze_course_trends(
        self,
        analysis_period: str = "7_days",
        location_filter: Optional[Dict[str, str]] = None,
        category_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze course trends and popularity patterns.

        Args:
            analysis_period: Period for trend analysis
            location_filter: Geographic filter for analysis
            category_filter: Category filter for analysis

        Returns:
            Course trend analysis results
        """
        try:
            # Mock trend analysis
            trend_data = {
                "trending_categories": [
                    {
                        "category": "restaurant",
                        "growth_rate": 0.25,
                        "total_courses": 150,
                    },
                    {"category": "cafe", "growth_rate": 0.18, "total_courses": 120},
                    {"category": "shopping", "growth_rate": 0.12, "total_courses": 80},
                ],
                "growth_metrics": {
                    "new_courses_created": 23,
                    "new_shares_generated": 67,
                    "new_users_engaging": 145,
                    "overall_growth_rate": 0.15,
                },
                "popular_locations": [
                    {"location": "강남구", "course_count": 89, "avg_rating": 4.3},
                    {"location": "홍대", "course_count": 76, "avg_rating": 4.1},
                    {"location": "명동", "course_count": 65, "avg_rating": 4.0},
                ],
                "analysis_metadata": {
                    "period": analysis_period,
                    "location_filter": location_filter,
                    "category_filter": category_filter,
                    "analyzed_at": datetime.utcnow().isoformat(),
                },
            }

            logger.info(f"Course trend analysis completed for {analysis_period}")
            return trend_data

        except Exception as e:
            logger.error(f"Error analyzing course trends: {e}")
            raise

    def generate_user_course_insights(
        self,
        user_id: str,
        insight_type: str = "personal_summary",
        time_range: str = "month",
    ) -> Dict[str, Any]:
        """
        Generate personalized course insights for user.

        Args:
            user_id: User to generate insights for
            insight_type: Type of insights to generate
            time_range: Time range for analysis

        Returns:
            Personalized course insights
        """
        try:
            # Mock user insights
            insights_data = {
                "courses_created": 3,
                "courses_saved": 12,
                "courses_shared": 5,
                "favorite_categories": ["restaurant", "cafe", "culture"],
                "sharing_activity": {
                    "links_generated": 5,
                    "total_link_views": 34,
                    "courses_copied_from_shares": 8,
                },
                "engagement_patterns": {
                    "most_active_day": "saturday",
                    "preferred_course_length": "3-4 places",
                    "average_course_duration": "4 hours",
                },
                "social_metrics": {
                    "followers": 23,
                    "following": 45,
                    "course_likes_received": 67,
                    "comments_made": 15,
                },
                "insights_metadata": {
                    "user_id": user_id,
                    "insight_type": insight_type,
                    "time_range": time_range,
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }

            logger.info(f"Generated {insight_type} insights for user {user_id}")
            return insights_data

        except Exception as e:
            logger.error(f"Error generating user insights: {e}")
            raise
