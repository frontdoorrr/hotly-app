# TRD: 코스 공유 및 협업 기능

## 1. 기술 개요
**목적:** PRD 05-sharing-system 요구사항을 충족하기 위한 실시간 협업 공유 시스템의 기술적 구현 방안

**핵심 기술 스택:**
- 실시간 통신: WebSocket + Socket.IO
- 링크 관리: Short URL Service + Redis Cache
- 협업 엔진: Operational Transform (OT) + Conflict Resolution
- 권한 관리: RBAC (Role-Based Access Control)
- API: FastAPI + GraphQL (실시간 구독)

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처
```
[Mobile/Web Client]
    ↓ WebSocket/HTTP
[API Gateway + Load Balancer]
    ↓
[Sharing Service] ↔ [Real-time Collaboration Engine]
    ↓                        ↓
[Permission Manager] ↔ [WebSocket Manager]
    ↓                        ↓
[Share Link Service] ↔ [Comment/Edit Sync Service]
    ↓                        ↓
[PostgreSQL] + [Redis] ↔ [WebSocket Cluster]
```

### 2-2. 마이크로서비스 구성
```
1. Share Management Service
   - 공유 링크 생성/관리
   - 권한 체크 및 접근 제어
   - 만료 관리

2. Real-time Collaboration Service
   - WebSocket 연결 관리
   - 실시간 동기화
   - 충돌 해결

3. Comment System Service
   - 댓글 CRUD
   - 반응(좋아요/싫어요) 관리
   - 스팸 필터링

4. Notification Service
   - 공유/댓글 알림
   - 이메일/푸시 알림 전송
   - 알림 설정 관리
```

---

## 3. API 설계

### 3-1. 공유 링크 관리 API
```python
# 공유 링크 생성
class ShareLinkCreateRequest(BaseModel):
    course_id: str
    permission_level: PermissionLevel
    expires_at: Optional[datetime] = None
    allow_comments: bool = True
    allow_edit: bool = False
    password: Optional[str] = None

class PermissionLevel(str, Enum):
    VIEW_ONLY = "view"
    COMMENT = "comment"
    EDIT = "edit"

class ShareLinkResponse(BaseModel):
    share_id: str
    share_url: str
    qr_code_url: str
    permission_level: PermissionLevel
    expires_at: Optional[datetime]
    created_at: datetime

# 공유 링크 접근
class ShareAccessRequest(BaseModel):
    share_id: str
    password: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

class ShareAccessResponse(BaseModel):
    course: SharedCourseDetail
    permission: UserPermission
    can_edit: bool
    can_comment: bool
    access_token: str  # WebSocket 인증용

class SharedCourseDetail(BaseModel):
    id: str
    name: str
    places: List[SharedPlaceDetail]
    created_by: UserInfo
    shared_at: datetime
    comments_count: int
    participants_count: int

class UserPermission(BaseModel):
    level: PermissionLevel
    can_view: bool
    can_comment: bool
    can_edit: bool
    can_share: bool
```

### 3-2. 실시간 협업 API (WebSocket)
```python
# WebSocket 메시지 스키마
class WSMessage(BaseModel):
    type: WSMessageType
    share_id: str
    user_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime

class WSMessageType(str, Enum):
    # 연결 관리
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"

    # 코스 편집
    COURSE_EDIT_START = "course_edit_start"
    COURSE_EDIT_END = "course_edit_end"
    COURSE_UPDATE = "course_update"

    # 댓글 시스템
    COMMENT_ADD = "comment_add"
    COMMENT_UPDATE = "comment_update"
    COMMENT_DELETE = "comment_delete"
    COMMENT_REACTION = "comment_reaction"

    # 시스템 알림
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    PERMISSION_CHANGE = "permission_change"

# 코스 편집 메시지
class CourseEditMessage(BaseModel):
    operation: EditOperation
    place_id: Optional[str]
    position: Optional[int]
    data: Optional[Dict[str, Any]]

class EditOperation(str, Enum):
    ADD_PLACE = "add_place"
    REMOVE_PLACE = "remove_place"
    REORDER_PLACES = "reorder_places"
    UPDATE_PLACE = "update_place"
    UPDATE_COURSE_INFO = "update_course_info"

# 댓글 메시지
class CommentMessage(BaseModel):
    comment_id: Optional[str]
    place_id: Optional[str]  # 전체 코스 댓글의 경우 None
    content: str
    parent_id: Optional[str]  # 대댓글의 경우
    mentions: List[str] = []  # @사용자명
```

### 3-3. 댓글 시스템 API
```python
class CommentCreateRequest(BaseModel):
    share_id: str
    place_id: Optional[str] = None  # None이면 전체 코스 댓글
    content: str = Field(..., min_length=1, max_length=500)
    parent_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    content: str
    author: UserInfo
    place_id: Optional[str]
    parent_id: Optional[str]
    replies_count: int
    reactions: Dict[str, int]  # {"👍": 3, "❤️": 1}
    created_at: datetime
    updated_at: Optional[datetime]

class CommentReactionRequest(BaseModel):
    comment_id: str
    reaction: str = Field(..., regex=r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+$')
    action: ReactionAction

class ReactionAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"
```

---

## 4. 실시간 협업 엔진

### 4-1. WebSocket 연결 관리
```python
class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocketConnection]] = {}
        self.user_sessions: Dict[str, UserSession] = {}
        self.redis_client = Redis.from_url(settings.REDIS_URL)

    async def connect(self, websocket: WebSocket, share_id: str, access_token: str):
        # 토큰 검증
        user_info = await self._verify_access_token(access_token)
        if not user_info:
            await websocket.close(code=1008, reason="Invalid access token")
            return

        # 권한 확인
        permissions = await self._get_user_permissions(share_id, user_info.user_id)
        if not permissions.can_view:
            await websocket.close(code=1008, reason="Access denied")
            return

        # 연결 등록
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_info.user_id,
            share_id=share_id,
            permissions=permissions,
            connected_at=datetime.utcnow()
        )

        if share_id not in self.connections:
            self.connections[share_id] = set()
        self.connections[share_id].add(connection)

        self.user_sessions[user_info.user_id] = UserSession(
            user_id=user_info.user_id,
            share_id=share_id,
            connection=connection
        )

        # 접속 알림
        await self._broadcast_to_share(share_id, WSMessage(
            type=WSMessageType.USER_JOIN,
            share_id=share_id,
            user_id=user_info.user_id,
            data={"user_info": user_info.dict()},
            timestamp=datetime.utcnow()
        ), exclude_user=user_info.user_id)

        # 현재 접속자 목록 전송
        active_users = await self._get_active_users(share_id)
        await self._send_to_connection(connection, WSMessage(
            type=WSMessageType.CONNECT,
            share_id=share_id,
            data={"active_users": active_users},
            timestamp=datetime.utcnow()
        ))

    async def disconnect(self, user_id: str):
        if user_id not in self.user_sessions:
            return

        session = self.user_sessions[user_id]
        share_id = session.share_id

        # 연결 해제
        if share_id in self.connections:
            self.connections[share_id].discard(session.connection)
            if not self.connections[share_id]:
                del self.connections[share_id]

        del self.user_sessions[user_id]

        # 접속 해제 알림
        await self._broadcast_to_share(share_id, WSMessage(
            type=WSMessageType.USER_LEAVE,
            share_id=share_id,
            user_id=user_id,
            data={},
            timestamp=datetime.utcnow()
        ))

    async def handle_message(self, user_id: str, message: WSMessage):
        if user_id not in self.user_sessions:
            return

        session = self.user_sessions[user_id]

        # 권한 체크
        if not await self._check_message_permission(session, message):
            await self._send_error(session.connection, "Permission denied")
            return

        # 메시지 타입별 처리
        if message.type == WSMessageType.COURSE_UPDATE:
            await self._handle_course_edit(session, message)
        elif message.type == WSMessageType.COMMENT_ADD:
            await self._handle_comment_add(session, message)
        elif message.type == WSMessageType.COMMENT_REACTION:
            await self._handle_comment_reaction(session, message)
        elif message.type == WSMessageType.HEARTBEAT:
            await self._handle_heartbeat(session)

    async def _handle_course_edit(self, session: UserSession, message: WSMessage):
        if not session.permissions.can_edit:
            await self._send_error(session.connection, "Edit permission required")
            return

        try:
            # 편집 내용 검증
            edit_data = CourseEditMessage.parse_obj(message.data)

            # 데이터베이스 업데이트
            await self._apply_course_edit(session.share_id, edit_data, session.user_id)

            # 편집 히스토리 기록
            await self._record_edit_history(session.share_id, session.user_id, edit_data)

            # 다른 사용자들에게 브로드캐스트
            await self._broadcast_to_share(
                session.share_id,
                message,
                exclude_user=session.user_id
            )

        except Exception as e:
            logger.error(f"Course edit failed: {e}")
            await self._send_error(session.connection, "Edit operation failed")

    async def _broadcast_to_share(self, share_id: str, message: WSMessage, exclude_user: str = None):
        if share_id not in self.connections:
            return

        connections = self.connections[share_id].copy()

        for connection in connections:
            if exclude_user and connection.user_id == exclude_user:
                continue

            try:
                await self._send_to_connection(connection, message)
            except ConnectionClosed:
                # 연결이 끊어진 경우 정리
                self.connections[share_id].discard(connection)
                if connection.user_id in self.user_sessions:
                    del self.user_sessions[connection.user_id]
```

### 4-2. 충돌 해결 시스템
```python
class ConflictResolver:
    def __init__(self):
        self.operation_transforms = {
            EditOperation.ADD_PLACE: self._transform_add_place,
            EditOperation.REMOVE_PLACE: self._transform_remove_place,
            EditOperation.REORDER_PLACES: self._transform_reorder_places,
            EditOperation.UPDATE_PLACE: self._transform_update_place,
        }

    async def resolve_concurrent_edits(
        self,
        share_id: str,
        pending_operations: List[EditOperationWithContext]
    ) -> List[EditOperationWithContext]:
        """동시 편집 충돌 해결"""

        if len(pending_operations) <= 1:
            return pending_operations

        # 타임스탬프 순으로 정렬
        sorted_operations = sorted(pending_operations, key=lambda op: op.timestamp)

        resolved_operations = []

        for i, current_op in enumerate(sorted_operations):
            # 이전 연산들과의 충돌 해결
            for j in range(i):
                previous_op = sorted_operations[j]
                current_op = await self._apply_operational_transform(
                    current_op, previous_op
                )

            resolved_operations.append(current_op)

        return resolved_operations

    async def _apply_operational_transform(
        self,
        current_op: EditOperationWithContext,
        previous_op: EditOperationWithContext
    ) -> EditOperationWithContext:
        """Operational Transform 적용"""

        transform_func = self.operation_transforms.get(current_op.operation.operation)
        if not transform_func:
            return current_op

        return await transform_func(current_op, previous_op)

    async def _transform_add_place(
        self,
        current_op: EditOperationWithContext,
        previous_op: EditOperationWithContext
    ) -> EditOperationWithContext:
        """장소 추가 연산의 변환"""

        if previous_op.operation.operation == EditOperation.ADD_PLACE:
            # 두 사용자가 동시에 장소를 추가하는 경우
            if current_op.operation.position >= previous_op.operation.position:
                # 이전 추가로 인한 위치 조정
                current_op.operation.position += 1

        elif previous_op.operation.operation == EditOperation.REMOVE_PLACE:
            # 이전에 장소가 제거된 경우
            if current_op.operation.position > previous_op.operation.position:
                current_op.operation.position -= 1

        return current_op

    async def _transform_remove_place(
        self,
        current_op: EditOperationWithContext,
        previous_op: EditOperationWithContext
    ) -> EditOperationWithContext:
        """장소 제거 연산의 변환"""

        if previous_op.operation.operation == EditOperation.REMOVE_PLACE:
            if current_op.operation.place_id == previous_op.operation.place_id:
                # 동일한 장소를 제거하려는 경우 - 무효화
                current_op.is_valid = False
            elif current_op.operation.position > previous_op.operation.position:
                # 이전 제거로 인한 위치 조정
                current_op.operation.position -= 1

        elif previous_op.operation.operation == EditOperation.ADD_PLACE:
            if current_op.operation.position >= previous_op.operation.position:
                current_op.operation.position += 1

        return current_op

    async def _transform_reorder_places(
        self,
        current_op: EditOperationWithContext,
        previous_op: EditOperationWithContext
    ) -> EditOperationWithContext:
        """장소 순서 변경 연산의 변환"""

        if previous_op.operation.operation in [EditOperation.ADD_PLACE, EditOperation.REMOVE_PLACE]:
            # 장소 추가/제거가 있었던 경우 순서 재계산 필요
            await self._recalculate_reorder_positions(current_op, previous_op)

        return current_op
```

---

## 5. 권한 관리 시스템

### 5-1. RBAC 구현
```python
class PermissionManager:
    def __init__(self):
        self.redis_client = Redis.from_url(settings.REDIS_URL)
        self.db = get_database()

    async def create_share_permissions(
        self,
        share_id: str,
        owner_id: str,
        permission_level: PermissionLevel
    ) -> SharePermissions:
        """공유 권한 설정 생성"""

        permissions = SharePermissions(
            share_id=share_id,
            owner_id=owner_id,
            default_permission=permission_level,
            user_permissions={},
            created_at=datetime.utcnow()
        )

        await self._save_permissions(permissions)
        return permissions

    async def check_user_permission(
        self,
        share_id: str,
        user_id: Optional[str],
        required_action: PermissionAction
    ) -> bool:
        """사용자 권한 확인"""

        # 캐시에서 권한 정보 조회
        cache_key = f"permission:{share_id}:{user_id or 'anonymous'}"
        cached_permission = await self.redis_client.get(cache_key)

        if cached_permission:
            user_permission = UserPermission.parse_raw(cached_permission)
        else:
            user_permission = await self._calculate_user_permission(share_id, user_id)
            await self.redis_client.setex(
                cache_key,
                3600,  # 1시간 캐시
                user_permission.json()
            )

        return self._has_permission(user_permission, required_action)

    async def _calculate_user_permission(
        self,
        share_id: str,
        user_id: Optional[str]
    ) -> UserPermission:
        """사용자 권한 계산"""

        share_info = await self.db.fetch_row(
            "SELECT * FROM shares WHERE share_id = $1",
            share_id
        )
        if not share_info:
            raise ShareNotFoundError(f"Share {share_id} not found")

        # 만료 확인
        if share_info.get("expires_at") and share_info["expires_at"] < datetime.utcnow():
            raise ShareExpiredError(f"Share {share_id} has expired")

        # 소유자 확인
        if user_id and user_id == share_info["created_by"]:
            return UserPermission(
                level=PermissionLevel.EDIT,
                can_view=True,
                can_comment=True,
                can_edit=True,
                can_share=True,
                can_delete=True
            )

        # 개별 사용자 권한 확인
        if user_id and user_id in share_info.get("user_permissions", {}):
            user_level = share_info["user_permissions"][user_id]
        else:
            user_level = share_info.get("default_permission", PermissionLevel.VIEW_ONLY)

        return self._create_permission_from_level(user_level)

    def _create_permission_from_level(self, level: PermissionLevel) -> UserPermission:
        """권한 레벨에 따른 UserPermission 객체 생성"""

        base_permissions = {
            "level": level,
            "can_view": True,
            "can_comment": False,
            "can_edit": False,
            "can_share": False,
            "can_delete": False
        }

        if level == PermissionLevel.COMMENT:
            base_permissions.update({
                "can_comment": True
            })
        elif level == PermissionLevel.EDIT:
            base_permissions.update({
                "can_comment": True,
                "can_edit": True,
                "can_share": True
            })

        return UserPermission(**base_permissions)

    def _has_permission(self, user_permission: UserPermission, action: PermissionAction) -> bool:
        """특정 액션에 대한 권한 확인"""

        permission_mapping = {
            PermissionAction.VIEW: user_permission.can_view,
            PermissionAction.COMMENT: user_permission.can_comment,
            PermissionAction.EDIT: user_permission.can_edit,
            PermissionAction.SHARE: user_permission.can_share,
            PermissionAction.DELETE: user_permission.can_delete,
        }

        return permission_mapping.get(action, False)

class PermissionAction(str, Enum):
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    SHARE = "share"
    DELETE = "delete"
```

---

## 6. 공유 링크 서비스

### 6-1. 단축 URL 생성기
```python
class ShareLinkGenerator:
    def __init__(self):
        self.redis_client = Redis.from_url(settings.REDIS_URL)
        self.base_url = settings.BASE_SHARE_URL

    def generate_share_id(self) -> str:
        """고유한 공유 ID 생성"""

        # 8자리 alphanumeric 생성
        characters = string.ascii_letters + string.digits

        while True:
            share_id = ''.join(random.choices(characters, k=8))

            # 중복 확인
            if not await self._is_share_id_exists(share_id):
                return share_id

    async def create_share_link(self, request: ShareLinkCreateRequest, owner_id: str) -> ShareLinkResponse:
        """공유 링크 생성"""

        share_id = self.generate_share_id()

        # 공유 정보 저장
        share_data = {
            "share_id": share_id,
            "course_id": request.course_id,
            "created_by": owner_id,
            "permission_level": request.permission_level,
            "expires_at": request.expires_at,
            "allow_comments": request.allow_comments,
            "allow_edit": request.allow_edit,
            "password_hash": await self._hash_password(request.password) if request.password else None,
            "created_at": datetime.utcnow(),
            "access_count": 0,
            "last_accessed_at": None
        }

        await self.db.execute(
            """
            INSERT INTO shares (share_id, course_id, created_by, permission_level, expires_at,
                              allow_comments, allow_edit, password_hash, created_at, access_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            share_data["share_id"], share_data["course_id"], share_data["created_by"],
            share_data["permission_level"], share_data["expires_at"], share_data["allow_comments"],
            share_data["allow_edit"], share_data["password_hash"], share_data["created_at"], 0
        )

        # 캐시에도 저장
        await self.redis_client.setex(
            f"share:{share_id}",
            86400,  # 24시간
            json.dumps(share_data, default=str)
        )

        # QR 코드 생성
        qr_code_url = await self._generate_qr_code(share_id)

        return ShareLinkResponse(
            share_id=share_id,
            share_url=f"{self.base_url}/share/{share_id}",
            qr_code_url=qr_code_url,
            permission_level=request.permission_level,
            expires_at=request.expires_at,
            created_at=share_data["created_at"]
        )

    async def get_share_info(self, share_id: str) -> Optional[Dict[str, Any]]:
        """공유 정보 조회"""

        # 캐시에서 먼저 조회
        cached = await self.redis_client.get(f"share:{share_id}")
        if cached:
            return json.loads(cached)

        # DB에서 조회
        share_info = await self.db.fetch_row(
            "SELECT * FROM shares WHERE share_id = $1",
            share_id
        )
        if share_info:
            # 캐시에 저장
            await self.redis_client.setex(
                f"share:{share_id}",
                86400,
                json.dumps(share_info, default=str)
            )

        return share_info

    async def increment_access_count(self, share_id: str):
        """접근 횟수 증가"""

        current_time = datetime.utcnow()

        # DB 업데이트
        await self.db.execute(
            """
            UPDATE shares
            SET access_count = access_count + 1, last_accessed_at = $1
            WHERE share_id = $2
            """,
            current_time, share_id
        )

        # 캐시 무효화
        await self.redis_client.delete(f"share:{share_id}")

    async def _generate_qr_code(self, share_id: str) -> str:
        """QR 코드 생성"""

        share_url = f"{self.base_url}/share/{share_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)

        # QR 코드 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")

        # S3에 업로드
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        qr_code_key = f"qr_codes/{share_id}.png"
        await self._upload_to_s3(qr_code_key, img_buffer.getvalue(), "image/png")

        return f"{settings.CDN_BASE_URL}/{qr_code_key}"
```

### 6-2. 링크 메타데이터 생성
```python
class ShareMetadataGenerator:
    def __init__(self):
        self.template_engine = Jinja2Templates(directory="templates")

    async def generate_og_metadata(self, share_id: str) -> Dict[str, str]:
        """Open Graph 메타데이터 생성"""

        share_info = await self._get_share_info(share_id)
        if not share_info:
            raise ShareNotFoundError(f"Share {share_id} not found")

        course_info = await self._get_course_info(share_info["course_id"])
        thumbnail_url = await self._generate_course_thumbnail(course_info)

        metadata = {
            "og:title": f"{course_info['name']} - 데이트 코스",
            "og:description": self._generate_course_description(course_info),
            "og:image": thumbnail_url,
            "og:url": f"{settings.BASE_SHARE_URL}/share/{share_id}",
            "og:type": "article",
            "og:site_name": "ArchyAI",

            # Twitter Card
            "twitter:card": "summary_large_image",
            "twitter:title": f"{course_info['name']} - 데이트 코스",
            "twitter:description": self._generate_course_description(course_info),
            "twitter:image": thumbnail_url,

            # 추가 메타데이터
            "description": self._generate_course_description(course_info),
            "keywords": "데이트코스,데이트,연인,커플,추천"
        }

        return metadata

    async def _generate_course_thumbnail(self, course_info: Dict[str, Any]) -> str:
        """코스 썸네일 이미지 생성"""

        # 캔버스 생성
        img_width, img_height = 1200, 630  # OG 이미지 표준 크기
        img = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(img)

        # 폰트 로딩
        title_font = ImageFont.truetype("fonts/NotoSansKR-Bold.ttf", 48)
        desc_font = ImageFont.truetype("fonts/NotoSansKR-Regular.ttf", 24)

        # 제목 그리기
        title_text = course_info['name'][:20]  # 20자 제한
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_x = (img_width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 150), title_text, font=title_font, fill='black')

        # 장소 개수 그리기
        place_count = len(course_info.get('places', []))
        desc_text = f"{place_count}개 장소 • {course_info.get('total_duration', 0)}분"
        desc_bbox = draw.textbbox((0, 0), desc_text, font=desc_font)
        desc_x = (img_width - (desc_bbox[2] - desc_bbox[0])) // 2
        draw.text((desc_x, 220), desc_text, font=desc_font, fill='gray')

        # 장소 아이콘들 그리기
        if place_count > 0:
            self._draw_place_icons(draw, course_info['places'][:5], img_width)

        # 브랜드 로고 추가
        logo_text = "ArchyAI"
        logo_font = ImageFont.truetype("fonts/NotoSansKR-Bold.ttf", 32)
        draw.text((50, img_height - 80), logo_text, font=logo_font, fill='#007AFF')

        # S3에 업로드
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG', quality=95)
        img_buffer.seek(0)

        thumbnail_key = f"share_thumbnails/{course_info['id']}.png"
        await self._upload_to_s3(thumbnail_key, img_buffer.getvalue(), "image/png")

        return f"{settings.CDN_BASE_URL}/{thumbnail_key}"

    def _generate_course_description(self, course_info: Dict[str, Any]) -> str:
        """코스 설명 텍스트 생성"""

        places = course_info.get('places', [])
        if not places:
            return "특별한 데이트 코스를 공유합니다."

        place_names = [place['name'] for place in places[:3]]
        description = " → ".join(place_names)

        if len(places) > 3:
            description += f" 외 {len(places) - 3}곳"

        return f"{description}으로 이어지는 데이트 코스입니다."
```

---

## 7. 댓글 및 반응 시스템

### 7-1. 댓글 관리
```python
class CommentManager:
    def __init__(self):
        self.db = get_database()
        self.spam_filter = SpamFilter()
        self.websocket_manager = WebSocketManager()

    async def add_comment(
        self,
        request: CommentCreateRequest,
        user_id: str
    ) -> CommentResponse:
        """댓글 추가"""

        # 스팸 필터링
        if await self.spam_filter.is_spam(request.content, user_id):
            raise SpamDetectedError("Comment detected as spam")

        # 댓글 생성
        comment_id = str(ObjectId())
        comment_data = {
            "_id": ObjectId(comment_id),
            "share_id": request.share_id,
            "place_id": request.place_id,
            "content": request.content,
            "author_id": user_id,
            "parent_id": request.parent_id,
            "reactions": {},
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "is_deleted": False
        }

        await self.db.execute(
            """
            INSERT INTO comments (id, share_id, place_id, content, author_id, parent_id,
                                reactions, created_at, is_deleted)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            comment_id, comment_data["share_id"], comment_data["place_id"],
            comment_data["content"], comment_data["author_id"], comment_data["parent_id"],
            json.dumps(comment_data["reactions"]), comment_data["created_at"], False
        )

        # 작성자 정보 조회
        author_info = await self._get_user_info(user_id)

        # 응답 생성
        comment_response = CommentResponse(
            id=comment_id,
            content=request.content,
            author=author_info,
            place_id=request.place_id,
            parent_id=request.parent_id,
            replies_count=0,
            reactions={},
            created_at=comment_data["created_at"]
        )

        # 실시간 브로드캐스트
        await self.websocket_manager.broadcast_to_share(
            request.share_id,
            WSMessage(
                type=WSMessageType.COMMENT_ADD,
                share_id=request.share_id,
                user_id=user_id,
                data=comment_response.dict(),
                timestamp=datetime.utcnow()
            )
        )

        # 알림 발송
        await self._send_comment_notification(request.share_id, comment_response)

        return comment_response

    async def add_reaction(
        self,
        request: CommentReactionRequest,
        user_id: str
    ) -> Dict[str, int]:
        """댓글에 반응 추가/제거"""

        comment = await self.db.comments.find_one({"_id": ObjectId(request.comment_id)})
        if not comment:
            raise CommentNotFoundError(f"Comment {request.comment_id} not found")

        reactions = comment.get("reactions", {})
        user_reactions = reactions.get(user_id, [])

        if request.action == ReactionAction.ADD:
            if request.reaction not in user_reactions:
                user_reactions.append(request.reaction)
        else:  # REMOVE
            if request.reaction in user_reactions:
                user_reactions.remove(request.reaction)

        # 빈 리스트면 사용자 제거
        if user_reactions:
            reactions[user_id] = user_reactions
        else:
            reactions.pop(user_id, None)

        # 업데이트
        await self.db.comments.update_one(
            {"_id": ObjectId(request.comment_id)},
            {"$set": {"reactions": reactions}}
        )

        # 반응 집계
        reaction_counts = self._aggregate_reactions(reactions)

        # 실시간 브로드캐스트
        await self.websocket_manager.broadcast_to_share(
            comment["share_id"],
            WSMessage(
                type=WSMessageType.COMMENT_REACTION,
                share_id=comment["share_id"],
                user_id=user_id,
                data={
                    "comment_id": request.comment_id,
                    "reaction": request.reaction,
                    "action": request.action,
                    "reaction_counts": reaction_counts
                },
                timestamp=datetime.utcnow()
            )
        )

        return reaction_counts

    def _aggregate_reactions(self, reactions: Dict[str, List[str]]) -> Dict[str, int]:
        """반응 집계"""

        counts = {}
        for user_reactions in reactions.values():
            for reaction in user_reactions:
                counts[reaction] = counts.get(reaction, 0) + 1

        return counts

    async def get_comments_for_share(
        self,
        share_id: str,
        place_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommentResponse]:
        """공유 코스의 댓글 목록 조회"""

        query = {
            "share_id": share_id,
            "is_deleted": False
        }

        if place_id:
            query["place_id"] = place_id
        else:
            query["place_id"] = None  # 전체 코스 댓글

        comments = await self.db.comments.find(query)\
            .sort("created_at", -1)\
            .skip(offset)\
            .limit(limit)\
            .to_list(length=None)

        # 댓글 응답 변환
        comment_responses = []
        for comment in comments:
            author_info = await self._get_user_info(comment["author_id"])
            replies_count = await self._get_replies_count(str(comment["_id"]))
            reaction_counts = self._aggregate_reactions(comment.get("reactions", {}))

            comment_responses.append(CommentResponse(
                id=str(comment["_id"]),
                content=comment["content"],
                author=author_info,
                place_id=comment.get("place_id"),
                parent_id=comment.get("parent_id"),
                replies_count=replies_count,
                reactions=reaction_counts,
                created_at=comment["created_at"],
                updated_at=comment.get("updated_at")
            ))

        return comment_responses
```

### 7-2. 스팸 필터링
```python
class SpamFilter:
    def __init__(self):
        self.redis_client = Redis.from_url(settings.REDIS_URL)
        self.banned_keywords = self._load_banned_keywords()
        self.rate_limits = {
            "comments_per_minute": 10,
            "comments_per_hour": 100
        }

    async def is_spam(self, content: str, user_id: str) -> bool:
        """스팸 여부 판단"""

        # 키워드 필터링
        if self._contains_banned_keywords(content):
            await self._record_spam_attempt(user_id, "banned_keywords")
            return True

        # 길이 체크
        if len(content) < 2 or len(content) > 500:
            return True

        # 반복 체크
        if self._is_repetitive_content(content):
            await self._record_spam_attempt(user_id, "repetitive")
            return True

        # 속도 제한 체크
        if await self._check_rate_limit(user_id):
            await self._record_spam_attempt(user_id, "rate_limit")
            return True

        # URL 스팸 체크
        if self._contains_suspicious_urls(content):
            await self._record_spam_attempt(user_id, "suspicious_url")
            return True

        return False

    def _contains_banned_keywords(self, content: str) -> bool:
        """금지 키워드 포함 여부"""

        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.banned_keywords)

    def _is_repetitive_content(self, content: str) -> bool:
        """반복적인 내용 여부"""

        # 동일 문자가 5번 이상 반복
        if re.search(r'(.)\1{4,}', content):
            return True

        # 동일 단어가 3번 이상 반복
        words = content.split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
            if word_counts[word] >= 3:
                return True

        return False

    async def _check_rate_limit(self, user_id: str) -> bool:
        """속도 제한 확인"""

        # 분당 제한 확인
        minute_key = f"comment_rate:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        minute_count = await self.redis_client.get(minute_key)

        if minute_count and int(minute_count) >= self.rate_limits["comments_per_minute"]:
            return True

        # 시간당 제한 확인
        hour_key = f"comment_rate:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        hour_count = await self.redis_client.get(hour_key)

        if hour_count and int(hour_count) >= self.rate_limits["comments_per_hour"]:
            return True

        # 카운트 증가
        await self.redis_client.incr(minute_key)
        await self.redis_client.expire(minute_key, 60)
        await self.redis_client.incr(hour_key)
        await self.redis_client.expire(hour_key, 3600)

        return False

    def _contains_suspicious_urls(self, content: str) -> bool:
        """의심스러운 URL 포함 여부"""

        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)

        if len(urls) > 2:  # URL이 2개 초과
            return True

        # 알려진 스팸 도메인 체크
        spam_domains = ['bit.ly', 'tinyurl.com', 'short.link']  # 예시
        for url in urls:
            domain = urlparse(url).netloc
            if any(spam_domain in domain for spam_domain in spam_domains):
                return True

        return False
```

---

## 8. 성능 최적화

### 8-1. WebSocket 연결 최적화
```python
class WebSocketOptimizer:
    def __init__(self):
        self.connection_pool = ConnectionPool()
        self.message_queue = MessageQueue()
        self.heartbeat_manager = HeartbeatManager()

    async def optimize_connection(self, connection: WebSocketConnection):
        """WebSocket 연결 최적화"""

        # 압축 설정
        await self._enable_compression(connection)

        # 배치 메시지 처리
        await self._setup_message_batching(connection)

        # 하트비트 최적화
        await self.heartbeat_manager.setup_adaptive_heartbeat(connection)

    async def _enable_compression(self, connection: WebSocketConnection):
        """메시지 압축 활성화"""

        if connection.supports_compression:
            connection.compression_enabled = True
            connection.compression_threshold = 1024  # 1KB 이상 메시지만 압축

    async def _setup_message_batching(self, connection: WebSocketConnection):
        """메시지 배치 처리 설정"""

        connection.batch_buffer = []
        connection.batch_timeout = 100  # 100ms
        connection.max_batch_size = 10

        # 배치 타이머 설정
        asyncio.create_task(self._batch_message_sender(connection))

    async def _batch_message_sender(self, connection: WebSocketConnection):
        """배치 메시지 전송"""

        while connection.is_active:
            await asyncio.sleep(connection.batch_timeout / 1000)

            if connection.batch_buffer:
                batched_message = {
                    "type": "batch",
                    "messages": connection.batch_buffer.copy(),
                    "timestamp": datetime.utcnow().isoformat()
                }

                await connection.send(batched_message)
                connection.batch_buffer.clear()

class HeartbeatManager:
    def __init__(self):
        self.base_interval = 30  # 30초 기본 간격
        self.adaptive_intervals = {}

    async def setup_adaptive_heartbeat(self, connection: WebSocketConnection):
        """적응형 하트비트 설정"""

        connection.heartbeat_interval = self.base_interval
        connection.missed_heartbeats = 0
        connection.last_heartbeat = datetime.utcnow()

        asyncio.create_task(self._heartbeat_loop(connection))

    async def _heartbeat_loop(self, connection: WebSocketConnection):
        """하트비트 루프"""

        while connection.is_active:
            await asyncio.sleep(connection.heartbeat_interval)

            try:
                await connection.send({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # 응답 대기
                response = await asyncio.wait_for(
                    connection.wait_for_pong(),
                    timeout=10.0
                )

                if response:
                    connection.missed_heartbeats = 0
                    await self._adjust_heartbeat_interval(connection)
                else:
                    await self._handle_missed_heartbeat(connection)

            except asyncio.TimeoutError:
                await self._handle_missed_heartbeat(connection)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def _adjust_heartbeat_interval(self, connection: WebSocketConnection):
        """하트비트 간격 조정"""

        # 연결 품질에 따라 간격 조정
        if connection.latency < 100:  # 100ms 미만
            connection.heartbeat_interval = min(60, connection.heartbeat_interval + 5)
        elif connection.latency > 500:  # 500ms 초과
            connection.heartbeat_interval = max(15, connection.heartbeat_interval - 5)

    async def _handle_missed_heartbeat(self, connection: WebSocketConnection):
        """하트비트 누락 처리"""

        connection.missed_heartbeats += 1

        if connection.missed_heartbeats >= 3:
            logger.warning(f"Connection {connection.user_id} missed 3 heartbeats, closing")
            await connection.close()
        else:
            # 간격 단축
            connection.heartbeat_interval = max(10, connection.heartbeat_interval - 5)
```

### 8-2. 데이터베이스 최적화
```python
class ShareDatabaseOptimizer:
    def __init__(self):
        self.db = get_database()
        self.query_cache = {}

    async def optimize_share_queries(self):
        """공유 관련 쿼리 최적화"""

        # 인덱스 생성
        await self._create_indexes()

        # 쿼리 계획 최적화
        await self._optimize_query_plans()

    async def _create_indexes(self):
        """인덱스 생성"""

        # 공유 컬렉션 인덱스
        await self.db.shares.create_index([
            ("share_id", 1)
        ], unique=True)

        await self.db.shares.create_index([
            ("created_by", 1),
            ("created_at", -1)
        ])

        await self.db.shares.create_index([
            ("expires_at", 1)
        ], expireAfterSeconds=0)

        # 댓글 컬렉션 인덱스
        await self.db.comments.create_index([
            ("share_id", 1),
            ("place_id", 1),
            ("created_at", -1)
        ])

        await self.db.comments.create_index([
            ("share_id", 1),
            ("parent_id", 1)
        ])

        # 편집 히스토리 인덱스
        await self.db.edit_history.create_index([
            ("share_id", 1),
            ("timestamp", -1)
        ])

    async def get_share_with_cache(self, share_id: str) -> Optional[Dict[str, Any]]:
        """캐시된 공유 정보 조회"""

        # 캐시 확인
        cache_key = f"share_detail:{share_id}"
        cached = await self.redis_client.get(cache_key)

        if cached:
            return json.loads(cached)

        # 집계 파이프라인으로 모든 정보 한 번에 조회
        pipeline = [
            {"$match": {"share_id": share_id}},
            {"$lookup": {
                "from": "courses",
                "localField": "course_id",
                "foreignField": "_id",
                "as": "course_info"
            }},
            {"$lookup": {
                "from": "comments",
                "localField": "share_id",
                "foreignField": "share_id",
                "as": "comments"
            }},
            {"$addFields": {
                "comments_count": {"$size": "$comments"},
                "recent_comments": {
                    "$slice": [
                        {"$sortArray": {
                            "input": "$comments",
                            "sortBy": {"created_at": -1}
                        }},
                        5
                    ]
                }
            }},
            {"$project": {
                "comments": 0  # 전체 댓글 배열 제외
            }}
        ]

        result = await self.db.shares.aggregate(pipeline).to_list(1)

        if result:
            share_info = result[0]
            # 캐시 저장 (5분)
            await self.redis_client.setex(
                cache_key,
                300,
                json.dumps(share_info, default=str)
            )
            return share_info

        return None
```

---

## 9. 모니터링 및 로깅

### 9-1. 공유 시스템 메트릭
```python
from prometheus_client import Counter, Histogram, Gauge

class SharingMetrics:
    def __init__(self):
        self.share_creates = Counter(
            'share_creates_total',
            'Total share link creations',
            ['permission_level']
        )

        self.share_accesses = Counter(
            'share_accesses_total',
            'Total share link accesses',
            ['share_id', 'user_type']  # owner, collaborator, anonymous
        )

        self.websocket_connections = Gauge(
            'websocket_connections_current',
            'Current WebSocket connections',
            ['share_id']
        )

        self.collaboration_events = Counter(
            'collaboration_events_total',
            'Total collaboration events',
            ['event_type', 'share_id']
        )

        self.comment_operations = Counter(
            'comment_operations_total',
            'Total comment operations',
            ['operation', 'share_id']
        )

        self.message_latency = Histogram(
            'websocket_message_latency_seconds',
            'WebSocket message processing latency',
            ['message_type']
        )

    def record_share_creation(self, permission_level: str):
        self.share_creates.labels(permission_level=permission_level).inc()

    def record_share_access(self, share_id: str, user_type: str):
        self.share_accesses.labels(share_id=share_id, user_type=user_type).inc()

    def update_websocket_connections(self, share_id: str, count: int):
        self.websocket_connections.labels(share_id=share_id).set(count)

    def record_collaboration_event(self, event_type: str, share_id: str):
        self.collaboration_events.labels(
            event_type=event_type,
            share_id=share_id
        ).inc()

class SharingAnalytics:
    def __init__(self):
        self.db = get_database()
        self.metrics = SharingMetrics()

    async def track_sharing_usage(self):
        """공유 사용량 분석"""

        # 일일 공유 생성량
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_shares = await self.db.shares.count_documents({
            "created_at": {"$gte": today}
        })

        # 활성 공유 링크 수
        active_shares = await self.db.shares.count_documents({
            "$or": [
                {"expires_at": None},
                {"expires_at": {"$gt": datetime.utcnow()}}
            ]
        })

        # 평균 접근 횟수
        avg_access = await self.db.shares.aggregate([
            {"$group": {
                "_id": None,
                "avg_access": {"$avg": "$access_count"}
            }}
        ]).to_list(1)

        analytics_data = {
            "daily_shares": daily_shares,
            "active_shares": active_shares,
            "avg_access_per_share": avg_access[0]["avg_access"] if avg_access else 0,
            "timestamp": datetime.utcnow()
        }

        # 분석 결과 저장
        await self.db.sharing_analytics.insert_one(analytics_data)

        return analytics_data

    async def analyze_collaboration_patterns(self, share_id: str):
        """협업 패턴 분석"""

        # 편집 히스토리 분석
        edit_history = await self.db.edit_history.find({
            "share_id": share_id
        }).sort("timestamp", 1).to_list(None)

        # 댓글 분석
        comments = await self.db.comments.find({
            "share_id": share_id
        }).sort("created_at", 1).to_list(None)

        # 패턴 분석
        patterns = {
            "total_edits": len(edit_history),
            "total_comments": len(comments),
            "unique_editors": len(set(edit["user_id"] for edit in edit_history)),
            "unique_commenters": len(set(comment["author_id"] for comment in comments)),
            "edit_frequency": self._calculate_edit_frequency(edit_history),
            "comment_frequency": self._calculate_comment_frequency(comments),
            "peak_activity_hours": self._find_peak_activity_hours(edit_history + comments)
        }

        return patterns
```

---

## 10. 테스트 전략

### 10-1. 단위 테스트 (TDD)
```python
class TestSharingSystem:
    @pytest.fixture
    async def share_service(self):
        return ShareLinkGenerator()

    @pytest.fixture
    async def websocket_manager(self):
        return WebSocketManager()

    async def test_share_link_creation(self, share_service):
        # Given
        request = ShareLinkCreateRequest(
            course_id="test_course_123",
            permission_level=PermissionLevel.COMMENT,
            allow_comments=True,
            allow_edit=False
        )
        owner_id = "user_123"

        # When
        response = await share_service.create_share_link(request, owner_id)

        # Then
        assert len(response.share_id) == 8
        assert response.share_url.endswith(f"/share/{response.share_id}")
        assert response.permission_level == PermissionLevel.COMMENT
        assert response.qr_code_url is not None
        assert response.created_at is not None

    async def test_share_access_permission_check(self, share_service):
        # Given
        share_id = "test1234"
        await self._create_test_share(share_id, PermissionLevel.VIEW_ONLY)

        # When - VIEW permission
        can_view = await share_service.check_permission(share_id, None, PermissionAction.VIEW)
        can_comment = await share_service.check_permission(share_id, None, PermissionAction.COMMENT)

        # Then
        assert can_view is True
        assert can_comment is False

    async def test_websocket_connection_and_broadcast(self, websocket_manager):
        # Given
        mock_websocket1 = MockWebSocket()
        mock_websocket2 = MockWebSocket()
        share_id = "test_share"

        # When - 두 사용자 연결
        await websocket_manager.connect(mock_websocket1, share_id, "valid_token_1")
        await websocket_manager.connect(mock_websocket2, share_id, "valid_token_2")

        # 메시지 브로드캐스트
        test_message = WSMessage(
            type=WSMessageType.COMMENT_ADD,
            share_id=share_id,
            user_id="user_1",
            data={"comment": "test comment"},
            timestamp=datetime.utcnow()
        )

        await websocket_manager.handle_message("user_1", test_message)

        # Then
        assert len(websocket_manager.connections[share_id]) == 2
        # user_2만 메시지를 받아야 함 (발송자 제외)
        assert mock_websocket2.received_messages[-1]["type"] == WSMessageType.COMMENT_ADD
        assert len(mock_websocket1.received_messages) == 1  # 연결 메시지만

    async def test_concurrent_edit_conflict_resolution(self):
        # Given
        resolver = ConflictResolver()

        # 동시에 같은 위치에 장소 추가하는 시나리오
        op1 = EditOperationWithContext(
            operation=CourseEditMessage(
                operation=EditOperation.ADD_PLACE,
                position=2,
                data={"place_id": "place_1"}
            ),
            user_id="user_1",
            timestamp=datetime.utcnow()
        )

        op2 = EditOperationWithContext(
            operation=CourseEditMessage(
                operation=EditOperation.ADD_PLACE,
                position=2,
                data={"place_id": "place_2"}
            ),
            user_id="user_2",
            timestamp=datetime.utcnow() + timedelta(milliseconds=100)
        )

        # When
        resolved = await resolver.resolve_concurrent_edits("test_share", [op1, op2])

        # Then
        assert len(resolved) == 2
        assert resolved[0].operation.position == 2  # 첫 번째는 그대로
        assert resolved[1].operation.position == 3  # 두 번째는 한 칸 밀림

    async def test_comment_spam_filtering(self):
        # Given
        spam_filter = SpamFilter()
        user_id = "test_user"

        # When & Then - 다양한 스팸 시나리오

        # 금지 키워드
        assert await spam_filter.is_spam("이것은 광고입니다", user_id) is True

        # 반복 문자
        assert await spam_filter.is_spam("ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ", user_id) is True

        # 정상 댓글
        assert await spam_filter.is_spam("좋은 코스네요!", user_id) is False

        # 너무 짧은 댓글
        assert await spam_filter.is_spam("ㅋ", user_id) is True

        # URL 스팸
        assert await spam_filter.is_spam("여기 보세요 http://spam.com http://bad.com http://evil.com", user_id) is True
```

### 10-2. 통합 테스트
```python
class TestSharingIntegration:
    @pytest.mark.integration
    async def test_full_sharing_workflow(self, test_client, postgresql, redis_client):
        # Given
        user1_token = await create_test_user_token("user1")
        user2_token = await create_test_user_token("user2")
        course_id = await create_test_course("user1")

        # 1. 공유 링크 생성
        share_response = await test_client.post(
            "/api/v1/shares",
            json={
                "course_id": course_id,
                "permission_level": "comment",
                "allow_comments": True
            },
            headers={"Authorization": f"Bearer {user1_token}"}
        )

        assert share_response.status_code == 201
        share_data = share_response.json()
        share_id = share_data["share_id"]

        # 2. 다른 사용자가 공유 링크 접근
        access_response = await test_client.get(
            f"/api/v1/shares/{share_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert access_response.status_code == 200
        access_data = access_response.json()
        assert access_data["can_comment"] is True
        assert access_data["can_edit"] is False

        # 3. 댓글 작성
        comment_response = await test_client.post(
            f"/api/v1/shares/{share_id}/comments",
            json={
                "content": "멋진 코스네요!",
                "place_id": None
            },
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        assert comment_response.status_code == 201

        # 4. 댓글 목록 조회
        comments_response = await test_client.get(
            f"/api/v1/shares/{share_id}/comments"
        )

        assert comments_response.status_code == 200
        comments = comments_response.json()
        assert len(comments) == 1
        assert comments[0]["content"] == "멋진 코스네요!"

    @pytest.mark.integration
    async def test_real_time_collaboration(self, test_client):
        # Given
        share_id = await create_test_share_with_edit_permission()

        # WebSocket 연결 시뮬레이션
        websocket1 = TestWebSocketClient()
        websocket2 = TestWebSocketClient()

        await websocket1.connect(f"/ws/shares/{share_id}")
        await websocket2.connect(f"/ws/shares/{share_id}")

        # When - user1이 장소 추가
        edit_message = {
            "type": "course_update",
            "data": {
                "operation": "add_place",
                "position": 1,
                "data": {"place_id": "new_place_123"}
            }
        }

        await websocket1.send_json(edit_message)

        # Then - user2가 실시간으로 받아야 함
        received = await websocket2.receive_json(timeout=5)
        assert received["type"] == "course_update"
        assert received["data"]["operation"] == "add_place"
```

### 10-3. 성능 테스트
```python
class TestSharingPerformance:
    @pytest.mark.performance
    async def test_concurrent_websocket_connections(self):
        """동시 WebSocket 연결 성능 테스트"""

        share_id = "perf_test_share"
        connection_count = 100

        # Given
        websockets = []
        for i in range(connection_count):
            ws = TestWebSocketClient()
            websockets.append(ws)

        # When - 동시 연결
        start_time = time.time()

        connect_tasks = [
            ws.connect(f"/ws/shares/{share_id}")
            for ws in websockets
        ]

        await asyncio.gather(*connect_tasks)

        connection_time = time.time() - start_time

        # Then
        assert connection_time < 5.0  # 5초 이내 연결
        assert all(ws.is_connected for ws in websockets)

        # 브로드캐스트 성능 테스트
        broadcast_start = time.time()

        test_message = {
            "type": "comment_add",
            "data": {"comment": "performance test"}
        }

        await websockets[0].send_json(test_message)

        # 모든 연결이 메시지를 받을 때까지 대기
        for ws in websockets[1:]:
            await ws.receive_json(timeout=2)

        broadcast_time = time.time() - broadcast_start

        assert broadcast_time < 2.0  # 2초 이내 브로드캐스트

    @pytest.mark.performance
    async def test_share_link_generation_performance(self):
        """공유 링크 생성 성능 테스트"""

        share_service = ShareLinkGenerator()
        generation_count = 1000

        # When
        start_time = time.time()

        generation_tasks = [
            share_service.create_share_link(
                ShareLinkCreateRequest(
                    course_id=f"course_{i}",
                    permission_level=PermissionLevel.VIEW_ONLY
                ),
                owner_id=f"user_{i}"
            )
            for i in range(generation_count)
        ]

        results = await asyncio.gather(*generation_tasks)

        total_time = time.time() - start_time

        # Then
        assert total_time < 30.0  # 30초 이내에 1000개 생성
        assert len(results) == generation_count
        assert all(len(r.share_id) == 8 for r in results)

        # 중복 ID 검사
        share_ids = [r.share_id for r in results]
        assert len(set(share_ids)) == generation_count  # 모두 unique
```

---

## 11. 배포 및 운영

### 11-1. Docker 구성
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# WebSocket 포트 노출
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python healthcheck.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ws-ping-interval", "20", "--ws-ping-timeout", "10"]
```

### 11-2. Kubernetes 배포
```yaml
# sharing-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sharing-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sharing-service
  template:
    metadata:
      labels:
        app: sharing-service
    spec:
      containers:
      - name: sharing-service
        image: hotly/sharing-service:latest
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 8001
          name: websocket
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: url
        - name: WEBSOCKET_MAX_CONNECTIONS
          value: "1000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "300m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: sharing-service
spec:
  selector:
    app: sharing-service
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: websocket
    port: 8001
    targetPort: 8001
  type: ClusterIP

---
# WebSocket용 별도 서비스
apiVersion: v1
kind: Service
metadata:
  name: sharing-websocket
spec:
  selector:
    app: sharing-service
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer
  sessionAffinity: ClientIP  # 세션 유지
```

---

## 12. 용어 사전 (Technical)
- **WebSocket:** 양방향 실시간 통신을 위한 프로토콜
- **Operational Transform (OT):** 동시 편집 시 충돌을 해결하는 알고리즘
- **RBAC (Role-Based Access Control):** 역할 기반 접근 제어
- **Short URL:** 긴 URL을 짧게 변환한 링크
- **Rate Limiting:** API 호출 횟수 제한
- **Circuit Breaker:** 장애 전파 방지를 위한 패턴
- **Message Batching:** 여러 메시지를 묶어서 전송하는 최적화 기법

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 05-sharing-system 버전과 연동
