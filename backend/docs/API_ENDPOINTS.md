# Hotly App - API Endpoints Documentation

**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** October 7, 2025

---

## Table of Contents

1. [Authentication](#authentication)
2. [Places](#places)
3. [Courses](#courses)
4. [Search](#search)
5. [Map](#map)
6. [Personalization](#personalization)
7. [Preferences](#preferences)
8. [Content & Link Analysis](#content--link-analysis)
9. [AI Services](#ai-services)
10. [Onboarding](#onboarding)
11. [Notifications](#notifications)
12. [User Data](#user-data)
13. [Autocomplete](#autocomplete)
14. [Advanced Filters](#advanced-filters)
15. [Search Ranking](#search-ranking)
16. [Search Optimization](#search-optimization)
17. [Preference Setup](#preference-setup)
18. [Performance](#performance)
19. [CDN](#cdn)

---

## Authentication

All endpoints (except login/register) require authentication via JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

### POST `/auth/register`

Register a new user account.

**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "fullName": "John Doe",
  "phoneNumber": "+821012345678"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "fullName": "John Doe",
  "createdAt": "2025-10-07T10:00:00Z"
}
```

---

### POST `/auth/login`

Authenticate user and receive JWT token.

**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "fullName": "John Doe"
  }
}
```

---

### POST `/auth/refresh`

Refresh access token using refresh token.

**Authentication:** Refresh token required

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `200 OK`
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "Bearer",
  "expiresIn": 3600
}
```

---

### POST `/auth/logout`

Logout and invalidate tokens.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

### GET `/auth/me`

Get current authenticated user information.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "fullName": "John Doe",
  "phoneNumber": "+821012345678",
  "createdAt": "2025-10-07T10:00:00Z",
  "preferences": {...}
}
```

---

## Places

Endpoints for managing and discovering places.

### GET `/places`

Get list of places with filtering and pagination.

**Authentication:** Required

**Query Parameters:**
- `category` (string, optional): Filter by category (cafe, restaurant, etc.)
- `region` (string, optional): Filter by region
- `lat` (float, optional): Latitude for proximity search
- `lng` (float, optional): Longitude for proximity search
- `radius` (float, optional): Search radius in km (default: 5)
- `limit` (int, optional): Results per page (default: 20, max: 100)
- `offset` (int, optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "places": [
    {
      "id": "uuid",
      "name": "Cafe Name",
      "description": "Cozy cafe in Hongdae",
      "category": "cafe",
      "address": "Seoul, Mapo-gu...",
      "location": {
        "lat": 37.5563,
        "lng": 126.9224
      },
      "rating": 4.5,
      "reviewCount": 127,
      "priceRange": "$$",
      "tags": ["cozy", "wifi", "dessert"],
      "images": ["url1", "url2"],
      "isBookmarked": false,
      "distance": 0.8
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0
}
```

---

### GET `/places/{place_id}`

Get detailed information about a specific place.

**Authentication:** Required

**Path Parameters:**
- `place_id` (string): Place ID

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Cafe Name",
  "description": "Detailed description...",
  "category": "cafe",
  "address": "Full address",
  "location": {
    "lat": 37.5563,
    "lng": 126.9224
  },
  "rating": 4.5,
  "reviewCount": 127,
  "priceRange": "$$",
  "tags": ["cozy", "wifi", "dessert"],
  "images": ["url1", "url2"],
  "openingHours": {
    "monday": "09:00-22:00",
    "tuesday": "09:00-22:00"
  },
  "amenities": ["wifi", "parking", "outdoor_seating"],
  "socialLinks": {
    "instagram": "instagram.com/...",
    "naverBlog": "blog.naver.com/..."
  },
  "isBookmarked": false,
  "visitCount": 3,
  "lastVisited": "2025-10-01T14:30:00Z"
}
```

---

### POST `/places`

Create a new place (user-contributed).

**Authentication:** Required

**Request Body:**
```json
{
  "name": "New Cafe",
  "description": "Great coffee place",
  "category": "cafe",
  "address": "Seoul, Gangnam-gu...",
  "location": {
    "lat": 37.4979,
    "lng": 127.0276
  },
  "priceRange": "$$",
  "tags": ["coffee", "dessert"],
  "socialLinks": {
    "instagram": "instagram.com/newcafe"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "New Cafe",
  "createdBy": "user-uuid",
  "status": "pending_review",
  "createdAt": "2025-10-07T10:00:00Z"
}
```

---

### PUT `/places/{place_id}`

Update place information.

**Authentication:** Required (Owner or Admin)

**Request Body:** Same as POST `/places`

**Response:** `200 OK`

---

### DELETE `/places/{place_id}`

Delete a place.

**Authentication:** Required (Owner or Admin)

**Response:** `204 No Content`

---

### POST `/places/{place_id}/bookmark`

Bookmark a place.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Place bookmarked successfully",
  "isBookmarked": true
}
```

---

### DELETE `/places/{place_id}/bookmark`

Remove bookmark from a place.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Bookmark removed successfully",
  "isBookmarked": false
}
```

---

### POST `/places/{place_id}/visit`

Mark a place as visited.

**Authentication:** Required

**Request Body:**
```json
{
  "visitDate": "2025-10-07T14:30:00Z",
  "rating": 4.5,
  "review": "Great experience!",
  "images": ["url1", "url2"]
}
```

**Response:** `201 Created`
```json
{
  "visitId": "uuid",
  "placeId": "uuid",
  "visitDate": "2025-10-07T14:30:00Z",
  "rating": 4.5
}
```

---

## Courses

Endpoints for managing dating/outing courses (collections of places).

### GET `/courses`

Get list of courses.

**Authentication:** Required

**Query Parameters:**
- `type` (string, optional): Filter by course type (date, friend, family, solo)
- `region` (string, optional): Filter by region
- `duration` (int, optional): Expected duration in hours
- `budget` (string, optional): Budget range (low, medium, high)
- `limit` (int, optional): Results per page (default: 20)
- `offset` (int, optional): Pagination offset

**Response:** `200 OK`
```json
{
  "courses": [
    {
      "id": "uuid",
      "name": "Romantic Hongdae Date Course",
      "description": "Perfect 3-hour date course in Hongdae",
      "type": "date",
      "places": [
        {
          "order": 1,
          "placeId": "uuid",
          "placeName": "Cafe A",
          "estimatedDuration": 60
        },
        {
          "order": 2,
          "placeId": "uuid",
          "placeName": "Restaurant B",
          "estimatedDuration": 90
        }
      ],
      "totalDuration": 180,
      "totalDistance": 2.5,
      "estimatedBudget": {
        "min": 50000,
        "max": 80000
      },
      "rating": 4.7,
      "usedCount": 234,
      "createdBy": "user-uuid",
      "isBookmarked": false,
      "tags": ["romantic", "food", "cafe"]
    }
  ],
  "total": 89,
  "limit": 20,
  "offset": 0
}
```

---

### GET `/courses/{course_id}`

Get detailed information about a specific course.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Romantic Hongdae Date Course",
  "description": "Detailed description...",
  "type": "date",
  "places": [...],
  "totalDuration": 180,
  "totalDistance": 2.5,
  "estimatedBudget": {...},
  "rating": 4.7,
  "reviews": [...],
  "usedCount": 234,
  "route": {
    "optimized": true,
    "waypoints": [...]
  },
  "tips": ["Best to visit on weekdays", "Make reservations in advance"],
  "isBookmarked": false
}
```

---

### POST `/courses`

Create a new course.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "My Custom Course",
  "description": "Great places to visit",
  "type": "date",
  "placeIds": ["uuid1", "uuid2", "uuid3"],
  "customOrder": [1, 2, 3],
  "tags": ["romantic", "food"]
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "My Custom Course",
  "createdAt": "2025-10-07T10:00:00Z",
  "optimizationSuggestions": [
    "Consider swapping places 2 and 3 to reduce travel distance"
  ]
}
```

---

### PUT `/courses/{course_id}`

Update course information.

**Authentication:** Required (Owner or Admin)

**Response:** `200 OK`

---

### DELETE `/courses/{course_id}`

Delete a course.

**Authentication:** Required (Owner or Admin)

**Response:** `204 No Content`

---

### POST `/courses/{course_id}/bookmark`

Bookmark a course.

**Authentication:** Required

**Response:** `200 OK`

---

### POST `/courses/{course_id}/use`

Mark a course as used/completed.

**Authentication:** Required

**Request Body:**
```json
{
  "completedAt": "2025-10-07T18:00:00Z",
  "rating": 4.5,
  "review": "Had a wonderful time!",
  "actualBudget": 65000,
  "actualDuration": 195
}
```

**Response:** `201 Created`

---

### GET `/courses/{course_id}/optimize`

Get optimization suggestions for a course.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "originalRoute": [...],
  "optimizedRoute": [...],
  "improvements": {
    "distanceReduction": 0.8,
    "timeReduction": 15,
    "costReduction": 5000
  },
  "suggestions": [
    "Swap place 2 and 3 to save 15 minutes",
    "Visit during off-peak hours for better experience"
  ]
}
```

---

## Search

Advanced search endpoints with personalization and ranking.

### GET `/search`

Universal search across places and courses.

**Authentication:** Required

**Query Parameters:**
- `q` (string, required): Search query
- `type` (string, optional): Result type (place, course, all) - default: all
- `category` (string, optional): Filter by category
- `region` (string, optional): Filter by region
- `lat` (float, optional): Latitude for proximity
- `lng` (float, optional): Longitude for proximity
- `limit` (int, optional): Results per page (default: 20)
- `offset` (int, optional): Pagination offset

**Response:** `200 OK`
```json
{
  "query": "hongdae cafe",
  "results": {
    "places": [...],
    "courses": [...]
  },
  "total": {
    "places": 45,
    "courses": 12
  },
  "suggestions": ["홍대 카페", "홍대 맛집"],
  "filters": {
    "categories": ["cafe", "restaurant"],
    "regions": ["Mapo-gu", "Yongsan-gu"]
  },
  "responseTime": 156
}
```

---

### GET `/search/places`

Search for places only.

**Authentication:** Required

**Query Parameters:** Same as `/search`

**Response:** `200 OK`
```json
{
  "query": "hongdae cafe",
  "places": [...],
  "total": 45,
  "facets": {
    "categories": {
      "cafe": 32,
      "dessert": 13
    },
    "priceRanges": {
      "$": 15,
      "$$": 25,
      "$$$": 5
    }
  },
  "responseTime": 98
}
```

---

### GET `/search/courses`

Search for courses only.

**Authentication:** Required

**Query Parameters:** Same as `/search`

**Response:** `200 OK`

---

### POST `/search/save`

Save a search query for future reference.

**Authentication:** Required

**Request Body:**
```json
{
  "query": "hongdae cafe",
  "filters": {
    "category": "cafe",
    "region": "Mapo-gu"
  },
  "name": "My Favorite Hongdae Cafes"
}
```

**Response:** `201 Created`

---

## Map

Location-based and map-related endpoints.

### GET `/map/places`

Get places for map display with clustering.

**Authentication:** Required

**Query Parameters:**
- `lat` (float, required): Center latitude
- `lng` (float, required): Center longitude
- `zoom` (int, required): Map zoom level (1-20)
- `bounds` (string, optional): Map bounds "lat1,lng1,lat2,lng2"
- `category` (string, optional): Filter by category

**Response:** `200 OK`
```json
{
  "places": [...],
  "clusters": [
    {
      "lat": 37.5563,
      "lng": 126.9224,
      "count": 15,
      "bounds": {...}
    }
  ],
  "total": 234
}
```

---

### GET `/map/route`

Get optimized route between multiple places.

**Authentication:** Required

**Query Parameters:**
- `placeIds` (string, required): Comma-separated place IDs
- `optimize` (boolean, optional): Optimize route order (default: true)
- `transportMode` (string, optional): walk, drive, transit (default: walk)

**Response:** `200 OK`
```json
{
  "route": {
    "waypoints": [...],
    "totalDistance": 3.5,
    "totalDuration": 45,
    "transportMode": "walk"
  },
  "optimized": true,
  "originalOrder": [1, 2, 3],
  "optimizedOrder": [1, 3, 2]
}
```

---

### GET `/map/nearby`

Find places near a location.

**Authentication:** Required

**Query Parameters:**
- `lat` (float, required): Latitude
- `lng` (float, required): Longitude
- `radius` (float, optional): Search radius in km (default: 1, max: 10)
- `category` (string, optional): Filter by category
- `limit` (int, optional): Max results (default: 20)

**Response:** `200 OK`

---

## Personalization

User personalization and recommendation endpoints.

### GET `/personalization/recommendations`

Get personalized place/course recommendations.

**Authentication:** Required

**Query Parameters:**
- `type` (string, optional): place or course (default: place)
- `limit` (int, optional): Number of recommendations (default: 10)
- `context` (string, optional): Context (morning, afternoon, evening, weekend)

**Response:** `200 OK`
```json
{
  "recommendations": [...],
  "explanations": [
    "Recommended based on your cafe preferences",
    "Similar to places you've bookmarked"
  ],
  "confidenceScore": 0.87,
  "personalizationFactors": {
    "categoryPreference": 0.35,
    "locationHistory": 0.25,
    "timeContext": 0.20,
    "socialSignals": 0.20
  }
}
```

---

### GET `/personalization/trending`

Get trending places in user's preferred areas.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "trending": [...],
  "timeWindow": "24h",
  "personalizedRanking": true
}
```

---

### POST `/personalization/feedback`

Submit feedback on recommendations.

**Authentication:** Required

**Request Body:**
```json
{
  "recommendationId": "uuid",
  "placeId": "uuid",
  "feedback": "helpful",
  "action": "bookmarked"
}
```

**Response:** `200 OK`

---

## Preferences

User preference management endpoints.

### GET `/preferences`

Get user's current preferences.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "categories": {
    "cafe": 0.8,
    "restaurant": 0.7,
    "bar": 0.3
  },
  "regions": ["Mapo-gu", "Gangnam-gu"],
  "budget": {
    "category": "medium",
    "perPlace": {
      "min": 10000,
      "max": 30000
    }
  },
  "companionType": "partner",
  "activityLevel": "moderate",
  "updatedAt": "2025-10-07T10:00:00Z"
}
```

---

### PUT `/preferences`

Update user preferences.

**Authentication:** Required

**Request Body:**
```json
{
  "categories": {
    "cafe": 0.9,
    "restaurant": 0.8
  },
  "regions": ["Mapo-gu"],
  "budget": {
    "category": "high"
  }
}
```

**Response:** `200 OK`

---

### POST `/preferences/reset`

Reset preferences to default.

**Authentication:** Required

**Response:** `200 OK`

---

## Content & Link Analysis

Social media content extraction and analysis.

### POST `/link-analysis/analyze`

Analyze a social media link (Instagram, Naver Blog, YouTube).

**Authentication:** Required

**Request Body:**
```json
{
  "url": "https://www.instagram.com/p/ABC123/",
  "extractImages": true,
  "performAIAnalysis": true
}
```

**Response:** `200 OK`
```json
{
  "url": "https://www.instagram.com/p/ABC123/",
  "platform": "instagram",
  "content": {
    "title": "Amazing cafe in Hongdae",
    "description": "Visited this cozy place...",
    "images": ["url1", "url2"],
    "author": "username",
    "publishedAt": "2025-10-06T12:00:00Z"
  },
  "analysis": {
    "category": "cafe",
    "confidence": 0.92,
    "location": {
      "name": "Hongdae",
      "coordinates": {...}
    },
    "sentiment": "positive",
    "tags": ["cozy", "coffee", "dessert"]
  },
  "extractedPlace": {
    "name": "Cafe Name",
    "address": "Extracted address",
    "suggestedCategory": "cafe"
  }
}
```

---

### POST `/content/extract`

Extract content from URL without AI analysis.

**Authentication:** Required

**Request Body:**
```json
{
  "url": "https://blog.naver.com/user/post123"
}
```

**Response:** `200 OK`
```json
{
  "content": {...},
  "metadata": {...}
}
```

---

## AI Services

AI-powered features and analysis.

### POST `/ai/analyze-place`

AI-based place analysis from text/images.

**Authentication:** Required

**Request Body:**
```json
{
  "text": "Great cafe with amazing coffee and desserts",
  "images": ["url1", "url2"],
  "context": "instagram_post"
}
```

**Response:** `200 OK`
```json
{
  "category": "cafe",
  "confidence": 0.89,
  "attributes": {
    "ambiance": "cozy",
    "priceRange": "$$",
    "specialties": ["coffee", "desserts"]
  },
  "tags": ["cozy", "dessert", "coffee"],
  "sentiment": "positive"
}
```

---

### POST `/ai/generate-description`

Generate place description using AI.

**Authentication:** Required

**Request Body:**
```json
{
  "placeName": "Cafe ABC",
  "category": "cafe",
  "features": ["wifi", "outdoor seating", "desserts"],
  "tone": "friendly"
}
```

**Response:** `200 OK`
```json
{
  "description": "Cafe ABC is a charming spot perfect for...",
  "shortDescription": "Cozy cafe with great wifi and desserts",
  "tags": ["cozy", "wifi", "dessert"]
}
```

---

## Onboarding

User onboarding workflow endpoints.

### POST `/onboarding/start`

Start onboarding process.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "onboardingType": "quick"
}
```

**Response:** `200 OK`
```json
{
  "onboardingId": "uuid",
  "steps": [
    {
      "stepId": 1,
      "type": "category_selection",
      "required": true
    },
    {
      "stepId": 2,
      "type": "location_setup",
      "required": false
    }
  ],
  "estimatedMinutes": 3
}
```

---

### POST `/onboarding/complete-step`

Complete an onboarding step.

**Authentication:** Required

**Request Body:**
```json
{
  "onboardingId": "uuid",
  "stepId": 1,
  "data": {
    "selectedCategories": ["cafe", "restaurant"]
  }
}
```

**Response:** `200 OK`
```json
{
  "stepCompleted": true,
  "nextStep": 2,
  "progress": 0.5
}
```

---

### POST `/onboarding/complete`

Complete onboarding process.

**Authentication:** Required

**Request Body:**
```json
{
  "onboardingId": "uuid"
}
```

**Response:** `200 OK`
```json
{
  "completed": true,
  "profileReady": true,
  "recommendationsAvailable": true
}
```

---

## Notifications

User notification management.

### GET `/notifications`

Get user notifications.

**Authentication:** Required

**Query Parameters:**
- `unreadOnly` (boolean, optional): Show only unread (default: false)
- `limit` (int, optional): Results per page (default: 20)
- `offset` (int, optional): Pagination offset

**Response:** `200 OK`
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "new_recommendation",
      "title": "New places match your preferences",
      "body": "Check out 5 new cafes in Hongdae",
      "data": {
        "placeIds": ["uuid1", "uuid2"]
      },
      "isRead": false,
      "createdAt": "2025-10-07T10:00:00Z"
    }
  ],
  "unreadCount": 5,
  "total": 50
}
```

---

### PUT `/notifications/{notification_id}/read`

Mark notification as read.

**Authentication:** Required

**Response:** `200 OK`

---

### POST `/notifications/read-all`

Mark all notifications as read.

**Authentication:** Required

**Response:** `200 OK`

---

### DELETE `/notifications/{notification_id}`

Delete a notification.

**Authentication:** Required

**Response:** `204 No Content`

---

## User Data

User profile and data management.

### GET `/user-data/profile`

Get user profile.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "fullName": "John Doe",
  "phoneNumber": "+821012345678",
  "avatar": "url",
  "createdAt": "2025-01-01T00:00:00Z",
  "statistics": {
    "placesBookmarked": 45,
    "placesVisited": 23,
    "coursesCreated": 5,
    "coursesCompleted": 12
  }
}
```

---

### PUT `/user-data/profile`

Update user profile.

**Authentication:** Required

**Request Body:**
```json
{
  "fullName": "John Smith",
  "phoneNumber": "+821098765432",
  "avatar": "new_url"
}
```

**Response:** `200 OK`

---

### GET `/user-data/bookmarks`

Get user's bookmarked places.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "bookmarks": [...],
  "total": 45
}
```

---

### GET `/user-data/visits`

Get user's visit history.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "visits": [...],
  "total": 23
}
```

---

### GET `/user-data/export`

Export all user data (GDPR compliance).

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "profile": {...},
  "preferences": {...},
  "bookmarks": [...],
  "visits": [...],
  "courses": [...],
  "exportedAt": "2025-10-07T10:00:00Z"
}
```

---

### DELETE `/user-data/account`

Delete user account and all data.

**Authentication:** Required

**Request Body:**
```json
{
  "password": "confirmPassword",
  "confirmDeletion": true
}
```

**Response:** `200 OK`
```json
{
  "message": "Account deletion scheduled",
  "deletionDate": "2025-10-14T10:00:00Z"
}
```

---

## Autocomplete

Advanced autocomplete and search suggestions.

### GET `/autocomplete/suggestions`

Get autocomplete suggestions.

**Authentication:** Required

**Query Parameters:**
- `q` (string, required): Search query (min 1 char)
- `limit` (int, optional): Max suggestions (default: 10, max: 20)
- `includePersonal` (boolean, optional): Include personal suggestions (default: true)
- `includeTrending` (boolean, optional): Include trending suggestions (default: true)
- `includePopular` (boolean, optional): Include popular suggestions (default: true)
- `categories` (array[string], optional): Filter by categories
- `lat` (float, optional): Latitude for location-based suggestions
- `lng` (float, optional): Longitude for location-based suggestions

**Response:** `200 OK`
```json
{
  "suggestions": [
    {
      "text": "홍대 카페",
      "type": "personal",
      "score": 0.95,
      "category": "cafe",
      "address": "Seoul, Mapo-gu",
      "metadata": {
        "visitCount": 3,
        "lastSearched": "2025-10-05T10:00:00Z"
      }
    },
    {
      "text": "강남 맛집",
      "type": "trending",
      "score": 0.88,
      "category": "restaurant"
    }
  ],
  "categories": ["cafe", "restaurant"],
  "total": 10,
  "query": "홍",
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

### GET `/autocomplete/trending`

Get trending searches.

**Authentication:** Required

**Query Parameters:**
- `limit` (int, optional): Max results (default: 10, max: 50)
- `timeWindow` (int, optional): Time window in hours (default: 24, max: 168)

**Response:** `200 OK`
```json
{
  "trendingSearches": [
    {
      "query": "홍대 카페",
      "count": 1547,
      "type": "trending"
    }
  ],
  "total": 10,
  "timeWindowHours": 24,
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

### GET `/autocomplete/personal-history`

Get personal search history.

**Authentication:** Required

**Query Parameters:**
- `limit` (int, optional): Max results (default: 20, max: 100)

**Response:** `200 OK`
```json
{
  "searchHistory": [
    {
      "query": "홍대 카페",
      "frequency": 5,
      "lastSearched": "2025-10-06T14:00:00Z",
      "type": "personal_history"
    }
  ],
  "total": 15,
  "userId": "uuid",
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

### GET `/autocomplete/analytics`

Get search analytics.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "trendingSearches": [...],
  "popularCategories": {
    "cafe": 0.45,
    "restaurant": 0.35
  },
  "userSearchPatterns": {
    "peakHours": [12, 18, 20],
    "commonCategories": ["cafe", "restaurant"]
  },
  "performanceMetrics": {
    "avgResponseTime": 45,
    "cacheHitRate": 0.78
  },
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

### POST `/autocomplete/cache/optimize`

Optimize autocomplete cache (Admin only).

**Authentication:** Required (Admin)

**Response:** `200 OK`
```json
{
  "message": "Cache optimization completed",
  "optimizationResult": {
    "entriesRemoved": 1234,
    "cacheSize": "45MB"
  },
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

### DELETE `/autocomplete/history/clear`

Clear personal search history.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Search history cleared",
  "deleted": true,
  "userId": "uuid",
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

### GET `/autocomplete/health`

Check autocomplete service health.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "elasticsearch": "healthy"
  },
  "timestamp": "2025-10-07T10:00:00Z"
}
```

---

## Advanced Filters

Multi-filter search with facets and suggestions.

### POST `/advanced-filters/search`

Advanced filter search.

**Authentication:** Required

**Request Body:**
```json
{
  "query": "cafe",
  "categories": ["cafe", "dessert"],
  "regions": ["Mapo-gu"],
  "tags": ["cozy", "wifi"],
  "priceRanges": ["$", "$$"],
  "ratingMin": 4.0,
  "location": {
    "lat": 37.5563,
    "lng": 126.9224,
    "radius": 2.0
  },
  "visitStatus": "not_visited",
  "sortBy": "rating",
  "includeFacets": true,
  "limit": 20,
  "offset": 0
}
```

**Response:** `200 OK`
```json
{
  "places": [...],
  "pagination": {
    "total": 156,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  },
  "appliedFilters": {
    "categories": ["cafe", "dessert"],
    "ratingMin": 4.0
  },
  "facets": {
    "categories": {
      "cafe": 89,
      "dessert": 45
    },
    "priceRanges": {
      "$": 23,
      "$$": 67,
      "$$$": 12
    },
    "regions": {
      "Mapo-gu": 78,
      "Yongsan-gu": 45
    }
  },
  "suggestions": {
    "relaxFilters": ["Try removing rating filter"],
    "alternativeCategories": ["restaurant", "bar"]
  },
  "queryInfo": {
    "source": "elasticsearch",
    "processingTime": 145
  },
  "performance": {
    "totalTimeMs": 156,
    "cacheHit": false
  }
}
```

---

### GET `/advanced-filters/facets`

Get filter facet information.

**Authentication:** Required

**Query Parameters:**
- `category` (string, optional): Filter by category
- `region` (string, optional): Filter by region
- `useCache` (boolean, optional): Use cache (default: true)

**Response:** `200 OK`
```json
{
  "facets": {
    "categories": {...},
    "regions": {...},
    "priceRanges": {...},
    "tags": {...}
  },
  "appliedFilters": {},
  "source": "elasticsearch"
}
```

---

### GET `/advanced-filters/suggestions`

Get filter suggestions.

**Authentication:** Required

**Query Parameters:**
- `categories` (array[string], optional): Current categories
- `regions` (array[string], optional): Current regions
- `tags` (array[string], optional): Current tags
- `ratingMin` (float, optional): Current min rating

**Response:** `200 OK`
```json
{
  "currentResults": 3,
  "suggestions": {
    "relaxRating": "Try lowering rating to 3.5",
    "alternativeRegions": ["Gangnam-gu", "Jongno-gu"],
    "popularAlternatives": [...]
  },
  "appliedFilters": {...}
}
```

---

### POST `/advanced-filters/saved`

Save filter combination.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "My Favorite Cafes",
  "filterCriteria": {...},
  "isPublic": false
}
```

**Response:** `201 Created`
```json
{
  "id": "filter-uuid",
  "name": "My Favorite Cafes",
  "filterCriteria": {...},
  "isPublic": false,
  "useCount": 0,
  "createdAt": "2025-10-07T10:00:00Z",
  "lastUsed": null
}
```

---

### GET `/advanced-filters/saved`

Get saved filters.

**Authentication:** Required

**Query Parameters:**
- `includePublic` (boolean, optional): Include public filters (default: false)

**Response:** `200 OK`
```json
{
  "savedFilters": [...]
}
```

---

### GET `/advanced-filters/analytics`

Get filter usage analytics.

**Authentication:** Required

**Query Parameters:**
- `days` (int, optional): Analysis period in days (default: 30, max: 90)

**Response:** `200 OK`
```json
{
  "popularFilters": [...],
  "filterEffectiveness": {...},
  "userBehavior": {...},
  "performanceStats": {...}
}
```

---

## Search Ranking

Personalized search ranking and ML-powered scoring.

### POST `/search-ranking/rank`

Rank search results with personalization.

**Authentication:** Required

**Request Body:**
```json
{
  "searchResults": [...],
  "query": "hongdae cafe",
  "context": {
    "timeOfDay": "afternoon",
    "dayOfWeek": "saturday",
    "weather": "sunny",
    "userLocation": {...}
  },
  "maxResults": 20,
  "personalizationStrength": 0.7,
  "diversityThreshold": 0.3
}
```

**Response:** `200 OK`
```json
{
  "rankedResults": [...],
  "totalResults": 20,
  "personalizationApplied": true,
  "rankingMetadata": {
    "algorithmVersion": "v2.1.0",
    "personalizationStrength": 0.7,
    "diversityApplied": true,
    "contextFactors": ["timeOfDay", "userLocation"],
    "mlModelUsed": true
  },
  "processingTimeMs": 234,
  "cacheHit": false
}
```

---

### POST `/search-ranking/feedback`

Submit user feedback on ranking.

**Authentication:** Required

**Request Body:**
```json
{
  "placeId": "uuid",
  "feedbackType": "click",
  "queryContext": "hongdae cafe",
  "sessionId": "session-uuid",
  "timestamp": "2025-10-07T10:00:00Z",
  "additionalData": {
    "position": 3,
    "scrollDepth": 0.45
  }
}
```

**Response:** `202 Accepted`
```json
{
  "message": "Feedback successfully submitted",
  "feedbackId": "fb_uuid_timestamp"
}
```

---

### GET `/search-ranking/profile`

Get user ranking profile.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "preferredCategories": {
    "cafe": 0.85,
    "restaurant": 0.65
  },
  "behaviorPatterns": {
    "peakSearchTimes": [12, 18],
    "avgSessionDuration": 245
  },
  "interactionHistory": {
    "totalClicks": 234,
    "totalBookmarks": 45
  },
  "personalizationMetrics": {
    "profileCompleteness": 0.78,
    "engagementScore": 0.82
  }
}
```

---

### PUT `/search-ranking/profile`

Update user ranking profile.

**Authentication:** Required

**Request Body:**
```json
{
  "preferredCategories": {...},
  "behaviorPatterns": {...}
}
```

**Response:** `200 OK`

---

### POST `/search-ranking/analytics`

Get ranking analytics.

**Authentication:** Required

**Request Body:**
```json
{
  "dateFrom": "2025-10-01",
  "dateTo": "2025-10-07"
}
```

**Response:** `200 OK`
```json
{
  "period": {...},
  "metrics": {
    "totalSearches": 1247,
    "avgClickThroughRate": 0.68,
    "avgConversionRate": 0.34,
    "personalizationEffectiveness": 0.82,
    "userSatisfactionScore": 4.2
  },
  "trends": [...],
  "recommendations": [
    "Increase personalization weight by 10%"
  ]
}
```

---

### GET `/search-ranking/model/metrics`

Get ML model performance metrics.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "modelVersion": "ranking_v2.1.0",
  "accuracy": 0.85,
  "precision": 0.82,
  "recall": 0.78,
  "f1Score": 0.80,
  "trainingDate": "2025-10-04T00:00:00Z",
  "performanceMetrics": {
    "avgNdcg": 0.78,
    "clickThroughRate": 0.68,
    "processingLatencyP95": 245.0
  }
}
```

---

### POST `/search-ranking/config`

Update ranking configuration (Admin only).

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "userId": "uuid",
  "rankingWeights": {...},
  "personalizationEnabled": true,
  "diversitySettings": {...},
  "cacheSettings": {...}
}
```

**Response:** `200 OK`

---

### POST `/search-ranking/explain/{place_id}`

Explain ranking for a specific place.

**Authentication:** Required

**Query Parameters:**
- `query` (string, optional): Search query

**Response:** `200 OK`
```json
{
  "placeId": "uuid",
  "finalRank": 2,
  "finalScore": 0.87,
  "factors": {
    "baseRelevance": {
      "score": 0.78,
      "weight": 0.25,
      "contribution": 0.195,
      "explanation": "High match with search query"
    },
    "personalization": {
      "score": 0.92,
      "weight": 0.35,
      "contribution": 0.322,
      "explanation": "Matches your cafe preferences"
    }
  },
  "summary": "Highly relevant based on preferences",
  "confidenceLevel": "high",
  "alternativeSuggestions": [...]
}
```

---

### DELETE `/search-ranking/cache`

Clear ranking cache.

**Authentication:** Required

**Query Parameters:**
- `userId` (string, optional): Clear specific user cache

**Response:** `200 OK`

---

## Search Optimization

UI/UX optimization and performance features.

### POST `/search-optimization/search/optimized`

Optimized search with caching and pagination.

**Authentication:** Required

**Query Parameters:**
- `query` (string, required): Search query
- `page` (int, optional): Page number (default: 1)
- `pageSize` (int, optional): Results per page (default: 20, max: 100)
- `cacheStrategy` (string, optional): conservative, balanced, aggressive (default: balanced)
- `enablePagination` (boolean, optional): Enable pagination (default: true)
- `enableResponseOptimization` (boolean, optional): Enable optimization (default: true)

**Response:** `200 OK`
```json
{
  "items": [...],
  "pagination": {
    "currentPage": 1,
    "totalPages": 5,
    "hasNext": true,
    "hasPrevious": false,
    "nextCursor": "cursor_token"
  },
  "optimizationApplied": ["response_optimization", "pagination"],
  "responseTimeMs": 98,
  "cacheHit": true,
  "nextCursor": "cursor_token",
  "hasMore": true,
  "preloadedNext": false
}
```

---

### GET `/search-optimization/search/infinite-scroll`

Infinite scroll search.

**Authentication:** Required

**Query Parameters:**
- `query` (string, required): Search query
- `cursor` (string, optional): Pagination cursor
- `pageSize` (int, optional): Results per page (default: 20, max: 50)

**Response:** `200 OK`
```json
{
  "items": [...],
  "nextCursor": "next_cursor_token",
  "hasMore": true,
  "total": 234,
  "responseTimeMs": 87
}
```

---

### GET `/search-optimization/autocomplete`

Optimized autocomplete.

**Authentication:** Required

**Query Parameters:**
- `query` (string, required): Partial query (alias: `q`)
- `maxSuggestions` (int, optional): Max suggestions (default: 5, max: 20)
- `enablePersonalization` (boolean, optional): Enable personalization (default: true)

**Response:** `200 OK`
```json
{
  "suggestions": ["suggestion1", "suggestion2"],
  "isPersonalized": true,
  "cacheHit": true,
  "responseTimeMs": 23
}
```

---

### POST `/search-optimization/performance/metrics`

Record client performance metrics.

**Authentication:** Required

**Request Body:**
```json
{
  "sessionId": "session-uuid",
  "query": "hongdae cafe",
  "responseTimeMs": 234,
  "resultCount": 20,
  "cacheHit": false,
  "errorOccurred": false,
  "errorMessage": null
}
```

**Response:** `200 OK`

---

### GET `/search-optimization/performance/analysis`

Get search performance analysis.

**Authentication:** Required

**Query Parameters:**
- `days` (int, optional): Analysis period (default: 7, max: 30)

**Response:** `200 OK`
```json
{
  "avgResponseTime": 156,
  "cacheHitRate": 0.73,
  "errorRate": 0.02,
  "performanceTrend": "improving",
  "recentAlerts": [...]
}
```

---

### POST `/search-optimization/ui-config`

Update search UI config.

**Authentication:** Required

**Request Body:**
```json
{
  "resultsPerPage": 20,
  "enableInfiniteScroll": true,
  "enableAutocomplete": true,
  "theme": "light"
}
```

**Response:** `200 OK`

---

### GET `/search-optimization/ui-config`

Get search UI config.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "resultsPerPage": 20,
  "enableInfiniteScroll": true,
  "enableAutocomplete": true,
  "theme": "light"
}
```

---

### GET `/search-optimization/realtime-search`

Real-time search (as-you-type).

**Authentication:** Required

**Query Parameters:**
- `query` (string, required): Search query (alias: `q`)
- `searchType` (string, optional): instant or as_you_type (default: instant)

**Response:** `200 OK`
```json
{
  "results": [...],
  "responseTimeMs": 45,
  "total": 12
}
```

---

### GET `/search-optimization/history`

Get search history.

**Authentication:** Required

**Query Parameters:**
- `limit` (int, optional): Max results (default: 10, max: 50)

**Response:** `200 OK`
```json
{
  "history": [
    {
      "query": "hongdae cafe",
      "timestamp": "2025-10-07T10:00:00Z",
      "resultCount": 45
    }
  ],
  "total": 15
}
```

---

### DELETE `/search-optimization/history`

Clear search history.

**Authentication:** Required

**Response:** `200 OK`

---

### GET `/search-optimization/popular`

Get popular queries.

**Authentication:** None

**Query Parameters:**
- `limit` (int, optional): Max results (default: 10, max: 50)

**Response:** `200 OK`
```json
{
  "popularQueries": [
    {
      "query": "hongdae cafe",
      "count": 1234,
      "trend": "rising"
    }
  ],
  "total": 10,
  "updatedAt": "2025-10-07T10:00:00Z"
}
```

---

### POST `/search-optimization/cache/warm`

Warm search cache (pre-cache popular queries).

**Authentication:** Required

**Request Body:**
```json
{
  "queries": ["hongdae cafe", "gangnam restaurant"]
}
```

**Response:** `200 OK`
```json
{
  "message": "Cache warming completed",
  "warmedQueries": 2,
  "failedQueries": 0,
  "totalQueries": 2
}
```

---

### POST `/search-optimization/feedback`

Submit search feedback.

**Authentication:** Required

**Request Body:**
```json
{
  "query": "hongdae cafe",
  "rating": 4,
  "feedbackType": "relevance",
  "comments": "Good results"
}
```

**Response:** `200 OK`

---

## Preference Setup

Comprehensive preference setup and survey endpoints.

### POST `/preference-setup/initial-categories`

Setup initial category preferences.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "selectedCategories": ["cafe", "restaurant", "bar"],
  "selectionReason": "personal_interest",
  "confidenceLevel": 0.8
}
```

**Response:** `200 OK`
```json
{
  "userId": "uuid",
  "categories": {
    "cafe": 0.33,
    "restaurant": 0.33,
    "bar": 0.33
  },
  "setupComplete": true
}
```

---

### POST `/preference-setup/location-setup`

Configure location preferences.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "preferredAreas": {
    "Mapo-gu": 0.8,
    "Gangnam-gu": 0.6
  },
  "travelRangeKm": 5.0,
  "transportationPreferences": ["walk", "subway"]
}
```

**Response:** `200 OK`

---

### POST `/preference-setup/budget-setup`

Setup budget preferences.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "budgetCategory": "medium",
  "perPlaceRange": {
    "min": 10000,
    "max": 30000
  },
  "totalCourseBudget": {
    "min": 50000,
    "max": 100000
  },
  "budgetFlexibility": 0.2
}
```

**Response:** `200 OK`

---

### POST `/preference-setup/companion-setup`

Configure companion preferences.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "primaryCompanionType": "partner",
  "groupSizePreference": 2,
  "socialComfortLevel": 0.7,
  "specialNeeds": []
}
```

**Response:** `200 OK`

---

### POST `/preference-setup/activity-setup`

Configure activity level.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "activityIntensity": "moderate",
  "walkingTolerance": {
    "maxDistance": 3.0,
    "preferredPace": "normal"
  },
  "timeAvailability": {
    "typical": 180,
    "weekend": 240
  },
  "physicalConsiderations": []
}
```

**Response:** `200 OK`

---

### POST `/preference-setup/complete-survey`

Complete preference survey.

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "surveyVersion": "standard",
  "responses": [
    {
      "questionId": "q1",
      "answer": "cafe"
    }
  ],
  "completionTimeMinutes": 3.5
}
```

**Response:** `200 OK`
```json
{
  "surveyCompleted": true,
  "profileGenerated": true,
  "recommendationReadiness": 0.85
}
```

---

### POST `/preference-setup/quick-setup`

Quick preference setup (minimal configuration).

**Authentication:** Required

**Request Body:**
```json
{
  "userId": "uuid",
  "categories": ["cafe", "restaurant"],
  "budget": "medium"
}
```

**Response:** `200 OK`
```json
{
  "userId": "uuid",
  "categories": ["cafe", "restaurant"],
  "budgetLevel": "medium",
  "quickSetupCompleted": true,
  "profileType": "minimal",
  "recommendationReadiness": true,
  "setupTimeSeconds": 30
}
```

---

## Performance

Performance monitoring and metrics endpoints.

### GET `/performance/dashboard`

Get performance dashboard data.

**Authentication:** Admin recommended

**Response:** `200 OK`
```json
{
  "currentMetrics": {
    "responseTime": 145.3,
    "cacheHitRate": 0.73,
    "errorRate": 0.02,
    "activeConnections": 234,
    "requestsPerSecond": 45
  },
  "alerts": [
    {
      "severity": "warning",
      "message": "Response time above threshold",
      "timestamp": "2025-10-07T10:00:00Z"
    }
  ],
  "performanceRanking": [...],
  "slowQueries": [...],
  "trendAnalysis": {
    "trend": "stable",
    "changePercent": 2.3
  }
}
```

---

### POST `/performance/metrics`

Update performance metrics.

**Authentication:** Internal/Admin

**Request Body:**
```json
{
  "responseTime": 156.7,
  "cacheHitRate": 0.75,
  "errorRate": 0.01,
  "activeConnections": 250,
  "requestsPerSecond": 48,
  "memoryUsageMb": 512.5,
  "cpuUsagePercent": 45.2
}
```

**Response:** `201 Created`

---

### POST `/performance/query-performance`

Record query performance.

**Authentication:** Internal

**Request Body:**
```json
{
  "query": "SELECT * FROM places WHERE...",
  "executionTimeMs": 245.6,
  "rowsAffected": 156
}
```

**Response:** `201 Created`

---

### POST `/performance/endpoint-performance`

Record endpoint performance.

**Authentication:** Internal

**Request Body:**
```json
{
  "endpoint": "/api/v1/places",
  "method": "GET",
  "responseTimeMs": 156.3,
  "statusCode": 200
}
```

**Response:** `201 Created`

---

### GET `/performance/cache-stats`

Get cache statistics.

**Authentication:** Admin recommended

**Response:** `200 OK`
```json
{
  "overall": {
    "hitRate": 0.73,
    "totalRequests": 12456
  },
  "l1Memory": {
    "hitRate": 0.89,
    "size": "128MB"
  },
  "l2Disk": {
    "hitRate": 0.65,
    "size": "2GB"
  },
  "l3Redis": {
    "hitRate": 0.58,
    "size": "512MB"
  }
}
```

---

### GET `/performance/performance-ranking`

Get API endpoint performance ranking.

**Authentication:** Admin recommended

**Query Parameters:**
- `limit` (int, optional): Max endpoints (default: 10, max: 100)

**Response:** `200 OK`
```json
{
  "ranking": [
    {
      "endpoint": "/api/v1/places",
      "avgResponseTime": 98.5,
      "requestCount": 5678,
      "errorRate": 0.01,
      "performanceScore": 0.92
    }
  ],
  "totalEndpoints": 45,
  "generatedAt": "2025-10-07T10:00:00Z"
}
```

---

### GET `/performance/slow-queries`

Get slow queries.

**Authentication:** Admin

**Query Parameters:**
- `limit` (int, optional): Max queries (default: 10, max: 50)
- `thresholdMs` (float, optional): Slow query threshold (default: 100)

**Response:** `200 OK`
```json
{
  "slowQueries": [
    {
      "query": "SELECT...",
      "executionTimeMs": 567.8,
      "count": 45,
      "optimizationSuggestion": "Add index on column X"
    }
  ],
  "thresholdMs": 100,
  "totalFound": 8
}
```

---

### GET `/performance/scaling-recommendations`

Get scaling recommendations.

**Authentication:** Admin

**Response:** `200 OK`
```json
{
  "recommendations": [
    {
      "type": "horizontal_scaling",
      "priority": "high",
      "reason": "CPU usage consistently above 80%",
      "suggestedAction": "Add 2 more instances"
    }
  ],
  "generatedAt": "2025-10-07T10:00:00Z"
}
```

---

### DELETE `/performance/metrics/clear`

Clear performance metrics.

**Authentication:** Admin

**Response:** `200 OK`

---

### GET `/performance/health`

Performance monitoring system health.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-10-07T10:00:00Z",
  "metricsCollector": {
    "apiMetricsCount": 12456,
    "cacheMetricsCount": 5678
  },
  "dashboard": {
    "currentMetricsAvailable": true,
    "alertsCount": 2
  }
}
```

---

## CDN

CDN upload, cache management, and resource optimization.

### POST `/cdn/upload`

Upload file to CDN.

**Authentication:** Required

**Request Body:**
```json
{
  "localPath": "/path/to/file.jpg",
  "cdnPath": "images/places/file.jpg",
  "contentType": "image/jpeg"
}
```

**Response:** `200 OK`
```json
{
  "cdnUrl": "https://cdn.hotly.app/images/places/file.jpg",
  "fileHash": "sha256hash",
  "fileSize": 524288,
  "uploadedAt": "2025-10-07T10:00:00Z"
}
```

---

### POST `/cdn/invalidate`

Invalidate CDN cache.

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "paths": [
    "/images/places/*",
    "/static/css/main.css"
  ]
}
```

**Response:** `200 OK`
```json
{
  "invalidationId": "inv-uuid",
  "status": "in_progress",
  "estimatedCompletion": "2025-10-07T10:05:00Z"
}
```

---

### GET `/cdn/invalidation/{invalidation_id}/status`

Check cache invalidation status.

**Authentication:** Required

**Path Parameters:**
- `invalidation_id` (string): Invalidation request ID

**Response:** `200 OK`
```json
{
  "invalidationId": "inv-uuid",
  "status": "completed",
  "completedAt": "2025-10-07T10:04:32Z",
  "pathsInvalidated": 156
}
```

---

### POST `/cdn/optimize/image`

Optimize image.

**Authentication:** Required

**Request Body:**
```json
{
  "imagePath": "/path/to/image.jpg",
  "quality": 85,
  "formats": ["webp", "jpeg"]
}
```

**Response:** `200 OK`
```json
{
  "originalSize": 524288,
  "variants": {
    "webp": {
      "url": "...",
      "size": 234567
    },
    "jpeg": {
      "url": "...",
      "size": 345678
    }
  },
  "totalSizeSaved": 178721
}
```

---

### POST `/cdn/optimize/css`

Minify CSS.

**Authentication:** Required

**Request Body:**
```json
{
  "cssContent": "body { color: red; }"
}
```

**Response:** `200 OK`
```json
{
  "minifiedContent": "body{color:red}",
  "originalSize": 23,
  "minifiedSize": 16,
  "compressionRatio": 0.30
}
```

---

### POST `/cdn/optimize/javascript`

Bundle and minify JavaScript.

**Authentication:** Required

**Request Body:**
```json
{
  "entryFiles": ["app.js", "utils.js"],
  "outputPath": "bundle.min.js",
  "minify": true
}
```

**Response:** `200 OK`
```json
{
  "bundledContent": "...",
  "originalSize": 45678,
  "bundledSize": 23456,
  "compressionRatio": 0.49
}
```

---

### GET `/cdn/cache-headers`

Generate cache headers.

**Authentication:** Required

**Query Parameters:**
- `filePath` (string, required): File path
- `cacheDuration` (int, optional): Cache duration in seconds

**Response:** `200 OK`
```json
{
  "headers": {
    "Cache-Control": "public, max-age=31536000",
    "ETag": "hash",
    "Expires": "2026-10-07T10:00:00Z"
  }
}
```

---

### POST `/cdn/preload-hints`

Generate preload hints.

**Authentication:** Required

**Request Body:**
```json
{
  "criticalResources": [
    {
      "url": "/css/main.css",
      "type": "style"
    },
    {
      "url": "/js/app.js",
      "type": "script"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "preloadTags": [
    "<link rel=\"preload\" href=\"/css/main.css\" as=\"style\">",
    "<link rel=\"preload\" href=\"/js/app.js\" as=\"script\">"
  ]
}
```

---

### GET `/cdn/versioned-url`

Generate versioned resource URL.

**Authentication:** Required

**Query Parameters:**
- `filePath` (string, required): File path
- `contentHash` (string, optional): Content hash

**Response:** `200 OK`
```json
{
  "versionedUrl": "/static/css/main.abc123.css",
  "originalPath": "/static/css/main.css",
  "generatedAt": "2025-10-07T10:00:00Z"
}
```

---

### GET `/cdn/health`

CDN service health check.

**Authentication:** None

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-10-07T10:00:00Z",
  "cdnManager": {
    "uploadedFilesCount": 1234,
    "invalidationRequestsCount": 45
  },
  "resourceOptimizer": {
    "optimizedImagesCount": 567,
    "bundledFilesCount": 23
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service temporarily unavailable"
}
```

---

## Rate Limiting

Most endpoints have rate limiting applied:

- **Anonymous users:** 100 requests/hour
- **Authenticated users:** 1000 requests/hour
- **Premium users:** 5000 requests/hour
- **Search endpoints:** 200 requests/minute
- **Upload endpoints:** 50 requests/hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1696675200
```

---

## Pagination

Most list endpoints support pagination with the following parameters:

- `limit`: Number of results per page (default varies by endpoint)
- `offset`: Number of results to skip

**Cursor-based pagination** is available for some endpoints:
- `cursor`: Pagination cursor token
- `nextCursor`: Token for next page (in response)

---

## Filtering & Sorting

Common filter parameters across endpoints:

- `category`: Filter by category
- `region`: Filter by region
- `priceRange`: Filter by price range
- `rating`: Minimum rating
- `tags`: Filter by tags

Common sort parameters:

- `sortBy`: Field to sort by (relevance, rating, distance, recent, name, popular)
- `sortOrder`: asc or desc

---

## Caching

The API uses multi-layer caching:

- **L1 (Memory):** Ultra-fast in-memory cache (~10ms)
- **L2 (Redis):** Distributed cache (~50ms)
- **L3 (CDN):** Edge caching for static content

Cache-related headers:
```
X-Cache-Hit: true
X-Cache-Layer: L1
Cache-Control: public, max-age=3600
```

---

## Versioning

The API uses URL versioning: `/api/v1/`

When breaking changes are introduced, a new version will be released (e.g., `/api/v2/`).
Older versions are supported for at least 6 months after deprecation.

---

## Additional Resources

- **OpenAPI/Swagger Documentation:** `/docs`
- **ReDoc Documentation:** `/redoc`
- **API Status Page:** `https://status.hotly.app`
- **Developer Portal:** `https://developers.hotly.app`

---

**Last Updated:** October 7, 2025
**Documentation Version:** 1.0.0
