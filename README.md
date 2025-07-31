# AWS MCP Streamlit Chat Server

AWS CLI와 공식 문서를 활용하는 AI 어시스턴트 애플리케이션

## 🚀 주요 기능

### 💻 AWS CLI 탭
- **실시간 AWS 리소스 조회**: EC2, S3, Lambda 등 AWS 서비스 정보를 실시간으로 가져옴
- **Assume Role 지원**: 다른 AWS 계정의 Role을 assume하여 권한 위임 실행
- **결과 자동 정리**: JSON 응답을 사용자 친화적인 테이블 형태로 자동 변환

### 📚 AWS 문서 탭
- **공식 문서 검색**: AWS 공식 문서에서 관련 정보 검색
- **상세 내용 읽기**: 선택된 문서의 전체 내용을 읽고 요약
- **진행 상황 표시**: AI 에이전트의 작업 진행 상황을 실시간으로 표시

## 🏗️ 아키텍처

```
Streamlit UI
    ├── AWS CLI 탭
    │   ├── MCP Client (AWS API Server)
    │   ├── Assume Role (STS)
    │   └── Claude 3.5 Sonnet (Cross Region)
    └── AWS 문서 탭
        ├── MCP Client (Documentation Server)
        └── Claude 3.5 Sonnet (Cross Region)
```

## 🔧 기술 스택

- **Frontend**: Streamlit
- **AI Model**: Claude 3.5 Sonnet (Cross Region)
- **MCP Protocol**: 
  - `awslabs.aws-api-mcp-server` (AWS CLI 명령어 실행)
  - `awslabs.aws-documentation-mcp-server` (AWS 문서 검색)
- **AWS Services**: Bedrock, STS
- **Python Libraries**: 
  - `langchain-mcp-adapters`
  - `langchain-aws`
  - `boto3`

## ⚙️ 설정

### 환경 변수
- `AWS_REGION`: ap-northeast-2 (기본값)
- `AWS_ACCESS_KEY_ID`: AWS 액세스 키
- `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 키
- `AWS_SESSION_TOKEN`: 세션 토큰 (Assume Role 시 자동 설정)

### Assume Role 설정
사이드바에서 AWS Role ARN을 입력하면 자동으로 assume role 수행:
```
arn:aws:iam::ACCOUNT-ID:role/ROLE-NAME
```

## 🚀 실행 방법

```bash
# 의존성 설치
pip install streamlit langchain-mcp-adapters langchain-aws boto3

# 애플리케이션 실행
streamlit run streamlit_chat_server.py
```

## 💡 사용 예시

### AWS CLI 탭
- "EC2 인스턴스 목록 보여줘"
- "S3 버킷 상태 확인해줘"
- "Lambda 함수 목록 알려줘"

### AWS 문서 탭
- "S3 버킷 생성 방법 문서 찾아줘"
- "Lambda 함수 배포 가이드 검색해줘"
- "EC2 인스턴스 타입 비교 문서 보여줘"

## 🔒 보안 고려사항

- **Bedrock 접근**: 원본 AWS 자격 증명 사용 (Assume Role 미적용)
- **MCP 서버**: Assume Role 자격 증명 사용
- **세션 관리**: 각 요청마다 새로운 세션 생성

## 📊 결과 표시 형식

```markdown
## 📊 결과 요약
- **총 개수**: 3개
- **실행 명령어**: `aws ec2 describe-instances`

## 📋 상세 목록
| 인스턴스 ID | 타입 | 상태 | 이름 | 퍼블릭 IP |
|------------|------|------|------|-----------|
| i-xxx | t3.medium | 🟢 running | test | 43.201.76.105 |

## 💡 추가 정보
현재 리전: ap-northeast-2 (서울)
```

## 🐛 트러블슈팅

### 응답이 비어있는 경우
- Claude 모델 응답 확인
- MCP 서버 연결 상태 확인
- AWS 권한 설정 확인

### Assume Role 실패
- Role ARN 형식 확인
- Trust Policy 설정 확인
- 권한 정책 확인

## 📝 로그 레벨

- `INFO`: 일반적인 실행 정보
- `ERROR`: 오류 발생 시 상세 정보
- MCP 서버 로그: `FASTMCP_LOG_LEVEL=ERROR`