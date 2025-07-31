# 🤖 Multi-Agent MCP Chat Server

**Model Context Protocol (MCP)** 기반의 다중 에이전트 AI 어시스턴트 애플리케이션

## ✨ 주요 특징

- **2개의 전문화된 AI 에이전트**: 각각 다른 MCP 서버를 사용하여 특화된 기능 제공
- **실시간 진행 상황 표시**: AI 에이전트의 작업 과정을 시각적으로 확인
- **독립적인 채팅 세션**: 각 탭별로 별도의 대화 히스토리 관리
- **Claude 3.5 Sonnet 통합**: AWS Bedrock을 통한 고성능 AI 모델 활용

## 🏗️ 아키텍처

```
Streamlit UI
├── 💻 AWS CLI 탭
│   ├── MCP Client (awslabs.aws-api-mcp-server)
│   ├── AWS STS (Assume Role 지원)
│   └── Claude 3.5 Sonnet
└── 📚 AWS 문서 탭
    ├── MCP Client (awslabs.aws-documentation-mcp-server)
    ├── 실시간 진행 상황 표시
    └── Claude 3.5 Sonnet
```

## 🎯 에이전트별 기능

### 💻 AWS CLI 에이전트
- **실시간 AWS 리소스 관리**: EC2, S3, Lambda, RDS 등 모든 AWS 서비스
- **Cross-Account 접근**: Assume Role을 통한 다중 계정 관리
- **스마트 결과 정리**: JSON 응답을 사용자 친화적인 형태로 자동 변환

### 📚 AWS 문서 에이전트
- **지능형 문서 검색**: AWS 공식 문서에서 관련 정보 자동 탐색
- **상세 내용 분석**: 선택된 문서의 전체 내용을 읽고 요약
- **진행 상황 시각화**: 검색 → 읽기 → 분석 과정을 실시간 표시
- **참고 문서 링크**: 답변과 함께 원본 문서 URL 제공



## 🔧 기술 스택

### Core Technologies
- **Frontend**: Streamlit (웹 UI)
- **AI Model**: Claude 3.5 Sonnet (AWS Bedrock)
- **Protocol**: Model Context Protocol (MCP)
- **Language**: Python 3.10+

### MCP Servers
- `awslabs.aws-api-mcp-server@latest` - AWS CLI 명령어 실행
- `awslabs.aws-documentation-mcp-server@latest` - AWS 문서 검색

### Python Dependencies
```
streamlit
langchain-mcp-adapters
langchain-aws
boto3
asyncio
```

## ⚙️ 설정 및 실행

### 1. 환경 설정
```bash
# AWS 자격 증명 설정
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="ap-northeast-2"

# 선택사항: AWS Profile 사용
export AWS_PROFILE="your-profile"
```

### 2. 의존성 설치
```bash
pip install streamlit langchain-mcp-adapters langchain-aws boto3
```

### 3. 애플리케이션 실행
```bash
streamlit run streamlit_chat_server.py
```

### 4. Assume Role 설정 (선택사항)
사이드바에서 Role ARN 입력:
```
arn:aws:iam::123456789012:role/CrossAccountRole
```

## 💡 사용 예시

### 💻 AWS CLI 에이전트
```
"EC2 인스턴스 목록을 테이블 형태로 보여줘"
"S3 버킷의 암호화 설정 상태를 확인해줘"
"Lambda 함수들의 메모리 사용량을 비교해줘"
"RDS 인스턴스의 백업 설정을 조회해줘"
```

### 📚 AWS 문서 에이전트
```
"ECS Fargate 서비스 생성 방법을 단계별로 알려줘"
"Lambda 함수의 환경 변수 설정 모범 사례는?"
"S3 버킷 정책과 IAM 정책의 차이점을 설명해줘"
"CloudFormation 템플릿 작성 가이드를 찾아줘"
```



## 🔒 보안 고려사항

### AWS 권한 관리
- **최소 권한 원칙**: 필요한 AWS 서비스에만 접근 권한 부여
- **Assume Role 활용**: 임시 자격 증명을 통한 안전한 Cross-Account 접근
- **세션 격리**: 각 요청마다 독립적인 세션 생성



## 📊 모니터링 및 로깅

### 로그 레벨
- `INFO`: 일반적인 실행 정보 및 도구 호출 내역
- `ERROR`: 오류 발생 시 상세 스택 트레이스
- `DEBUG`: MCP 서버 통신 및 응답 상세 정보

### 진행 상황 추적
- **AWS 문서 탭**: 검색 → 문서 선택 → 내용 읽기 → 답변 생성 과정 시각화
- **실시간 상태 업데이트**: 각 단계별 진행률 및 상태 메시지 표시

## 🐛 트러블슈팅

### AWS 관련 오류
```bash
# 자격 증명 확인
aws sts get-caller-identity

# 권한 확인
aws iam get-user
aws sts assume-role --role-arn <ROLE_ARN> --role-session-name test
```

### MCP 서버 연결 오류
- **네트워크 연결**: 인터넷 연결 및 방화벽 설정 확인
- **패키지 설치**: `uvx` 도구 및 MCP 서버 패키지 설치 상태 확인
- **환경 변수**: AWS 자격 증명 및 리전 설정 확인

### 일반적인 해결 방법
1. **애플리케이션 재시작**: Streamlit 서버 재시작
2. **세션 초기화**: 사이드바의 "대화 기록 초기화" 버튼 사용
3. **로그 확인**: 터미널에서 상세 오류 메시지 확인

## 🚀 확장 가능성

### 추가 가능한 MCP 서버
- **GitHub**: 코드 저장소 관리
- **Slack**: 팀 커뮤니케이션
- **Database**: PostgreSQL, MySQL 연동
- **Kubernetes**: 클러스터 관리

### 커스텀 MCP 서버 개발
- MCP 프로토콜 표준을 따라 자체 서버 개발 가능
- 기업 내부 시스템과의 연동 확장

---

**Made with ❤️ using Model Context Protocol**