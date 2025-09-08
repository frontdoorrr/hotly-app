"""
Elasticsearch index schemas and mappings for search functionality.

Defines the structure and configuration for various search indices
including Korean language support with Nori analyzer.
"""

from typing import Any, Dict


class SearchIndexSchemas:
    """Collection of Elasticsearch index schemas."""

    @staticmethod
    def get_places_mapping() -> Dict[str, Any]:
        """
        Get mapping for places search index.

        Supports Korean text search with Nori analyzer,
        geographic search, and various filtering options.
        """
        return {
            "properties": {
                # Basic place information
                "id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "korean",
                    "search_analyzer": "korean",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {
                            "type": "search_as_you_type",
                            "analyzer": "korean",
                        },
                        "ngram": {
                            "type": "text",
                            "analyzer": "korean_ngram",
                        },
                    },
                },
                "description": {
                    "type": "text",
                    "analyzer": "korean",
                    "search_analyzer": "korean",
                },
                "address": {
                    "type": "text",
                    "analyzer": "korean",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {
                            "type": "search_as_you_type",
                            "analyzer": "korean",
                        },
                    },
                },
                # Geographic information
                "location": {"type": "geo_point"},
                "district": {"type": "keyword"},
                "city": {"type": "keyword"},
                # Categories and tags
                "category": {
                    "type": "keyword",
                    "fields": {"text": {"type": "text", "analyzer": "korean"}},
                },
                "tags": {
                    "type": "keyword",
                    "fields": {"text": {"type": "text", "analyzer": "korean"}},
                },
                "auto_category": {"type": "keyword"},
                # Metadata
                "status": {"type": "keyword"},
                "rating": {"type": "float"},
                "visit_count": {"type": "integer"},
                "last_visited_at": {"type": "date"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                # Search boosting fields
                "popularity_score": {"type": "float"},
                "relevance_score": {"type": "float"},
                # Additional search fields
                "search_keywords": {
                    "type": "text",
                    "analyzer": "korean",
                },
                "menu_items": {
                    "type": "text",
                    "analyzer": "korean",
                },
                "operating_hours": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "keyword"},
                        "open_time": {"type": "keyword"},
                        "close_time": {"type": "keyword"},
                        "is_closed": {"type": "boolean"},
                    },
                },
                "price_range": {"type": "keyword"},
                "phone": {"type": "keyword"},
                "website": {"type": "keyword"},
                # Social features
                "share_count": {"type": "integer"},
                "like_count": {"type": "integer"},
                "comment_count": {"type": "integer"},
            }
        }

    @staticmethod
    def get_places_settings() -> Dict[str, Any]:
        """Get settings for places search index with Korean support."""
        return {
            "index": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "max_result_window": 50000,  # Allow deep pagination
            },
            "analysis": {
                "analyzer": {
                    "korean": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": [
                            "lowercase",
                            "nori_part_of_speech",
                            "nori_readingform",
                            "korean_stop",
                            "korean_synonym",
                        ],
                    },
                    "korean_ngram": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": [
                            "lowercase",
                            "nori_part_of_speech",
                            "edge_ngram_filter",
                        ],
                    },
                    "korean_search": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase", "nori_part_of_speech", "korean_stop"],
                    },
                },
                "tokenizer": {
                    "nori_tokenizer": {
                        "type": "nori_tokenizer",
                        "decompound_mode": "mixed",
                        "user_dictionary_rules": [
                            # Add custom dictionary rules for place names
                            "홍대입구 홍대",
                            "강남역 강남",
                            "신촌역 신촌",
                            "명동역 명동",
                        ],
                    }
                },
                "filter": {
                    "nori_part_of_speech": {
                        "type": "nori_part_of_speech",
                        "stoptags": [
                            "E",
                            "IC",
                            "J",
                            "MAG",
                            "MAJ",
                            "MM",
                            "SP",
                            "SSC",
                            "SSO",
                            "SC",
                            "SE",
                            "XPN",
                            "XSA",
                            "XSN",
                            "XSV",
                        ],
                    },
                    "korean_stop": {
                        "type": "stop",
                        "stopwords": [
                            "의",
                            "가",
                            "이",
                            "은",
                            "들",
                            "는",
                            "좀",
                            "잘",
                            "걍",
                            "과",
                            "도",
                            "를",
                            "으로",
                            "자",
                            "에",
                            "와",
                            "한",
                            "하다",
                        ],
                    },
                    "korean_synonym": {
                        "type": "synonym",
                        "synonyms": [
                            "카페,커피숍,까페",
                            "맛집,음식점,레스토랑",
                            "펍,술집,주점",
                            "노래방,KTV,가라오케",
                        ],
                    },
                    "edge_ngram_filter": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 15,
                    },
                },
            },
        }

    @staticmethod
    def get_course_mapping() -> Dict[str, Any]:
        """Get mapping for course search index."""
        return {
            "properties": {
                "id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "korean",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "search_as_you_type"},
                    },
                },
                "description": {"type": "text", "analyzer": "korean"},
                "course_type": {"type": "keyword"},
                "duration_hours": {"type": "float"},
                "total_cost": {"type": "integer"},
                "difficulty": {"type": "keyword"},
                "places": {
                    "type": "nested",
                    "properties": {
                        "place_id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "korean"},
                        "order": {"type": "integer"},
                        "estimated_time": {"type": "integer"},
                    },
                },
                "tags": {"type": "keyword"},
                "rating": {"type": "float"},
                "view_count": {"type": "integer"},
                "like_count": {"type": "integer"},
                "share_count": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "center_location": {"type": "geo_point"},
                "bounding_box": {"type": "geo_shape"},
            }
        }

    @staticmethod
    def get_users_mapping() -> Dict[str, Any]:
        """Get mapping for user search index (for mentions, etc.)."""
        return {
            "properties": {
                "id": {"type": "keyword"},
                "username": {
                    "type": "text",
                    "analyzer": "keyword_lowercase",
                    "fields": {"suggest": {"type": "search_as_you_type"}},
                },
                "display_name": {
                    "type": "text",
                    "analyzer": "korean",
                    "fields": {"suggest": {"type": "search_as_you_type"}},
                },
                "bio": {"type": "text", "analyzer": "korean"},
                "interests": {"type": "keyword"},
                "location": {"type": "geo_point"},
                "follower_count": {"type": "integer"},
                "following_count": {"type": "integer"},
                "place_count": {"type": "integer"},
                "course_count": {"type": "integer"},
                "created_at": {"type": "date"},
                "last_active_at": {"type": "date"},
                "is_verified": {"type": "boolean"},
                "privacy_level": {"type": "keyword"},
            }
        }

    @staticmethod
    def get_suggestion_mapping() -> Dict[str, Any]:
        """Get mapping for search suggestions and autocompletion."""
        return {
            "properties": {
                "suggest": {
                    "type": "completion",
                    "analyzer": "korean",
                    "preserve_separators": True,
                    "preserve_position_increments": True,
                    "max_input_length": 50,
                    "contexts": [
                        {"name": "category", "type": "category"},
                        {"name": "location", "type": "geo", "precision": "5km"},
                    ],
                },
                "text": {"type": "keyword"},
                "category": {"type": "keyword"},
                "popularity": {"type": "integer"},
                "type": {"type": "keyword"},  # place, course, user, tag
                "metadata": {"type": "object"},
            }
        }

    @classmethod
    def get_all_schemas(cls) -> Dict[str, Dict[str, Any]]:
        """Get all index schemas and settings."""
        return {
            "places": {
                "mapping": cls.get_places_mapping(),
                "settings": cls.get_places_settings(),
            },
            "courses": {
                "mapping": cls.get_course_mapping(),
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
            },
            "users": {
                "mapping": cls.get_users_mapping(),
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
            },
            "suggestions": {
                "mapping": cls.get_suggestion_mapping(),
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
            },
        }
