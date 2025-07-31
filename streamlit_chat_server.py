import streamlit as st
import asyncio
import os
import boto3
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_aws import ChatBedrock
from langchain.schema.messages import HumanMessage, SystemMessage, ToolMessage

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit 페이지 설정
st.set_page_config(
    page_title="AWS 전문 채팅 서버",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AWS 전문 어시스턴트")
st.markdown("AWS CLI 명령어와 공식 문서를 활용할 수 있는 AI 어시스턴트")

# 세션 상태 초기화
if "cli_messages" not in st.session_state:
    st.session_state.cli_messages = []
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []
if "role_arn" not in st.session_state:
    st.session_state.role_arn = ""

# 탭 생성
tab1, tab2 = st.tabs(["💻 AWS CLI", "📚 AWS 문서"])
async def invoke_cli_agent(user_input: str):
    """MCP 클라이언트를 사용하여 에이전트 호출"""
    # MCP Client 초기화
    env_vars = {'AWS_REGION': 'ap-northeast-2'}
    
    # Assume Role 처리
    if st.session_state.role_arn:
        try:
            sts_client = boto3.client('sts', region_name='ap-northeast-2')
            assumed_role = sts_client.assume_role(
                RoleArn=st.session_state.role_arn,
                RoleSessionName='streamlit-mcp-session'
            )
            credentials = assumed_role['Credentials']
            
            env_vars.update({
                'AWS_ACCESS_KEY_ID': credentials['AccessKeyId'],
                'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
                'AWS_SESSION_TOKEN': credentials['SessionToken']
            })
            logger.info(f"Successfully assumed role: {st.session_state.role_arn}")
        except Exception as e:
            logger.error(f"Failed to assume role: {e}")
            st.error(f"Role assume 실패: {str(e)}")
            return "Role assume에 실패했습니다. 권한을 확인해주세요."
    
    mcp_client = MultiServerMCPClient({
        'aws_api': {
            'transport': 'stdio',
            'command': 'uvx',
            'args': ['awslabs.aws-api-mcp-server@latest'],
            'env': env_vars
        }
    })
    
    tools = await mcp_client.get_tools()
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    logger.info(f"Total tools loaded: {len(tools)}")
    
    # Bedrock 클라이언트 설정 (원래 자격 증명 사용)
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-2')
    
    chat_model = ChatBedrock(
        client=bedrock_runtime,
        model_id='apac.anthropic.claude-3-5-sonnet-20241022-v2:0',
        model_kwargs={'temperature': 0.3, 'max_tokens': 4096}
    )
    
    model = chat_model.bind_tools(tools)
    
    messages = [
        SystemMessage(content="AWS 데이터를 가져오기 위해 call_aws 도구를 사용하고, 결과를 사용자가 이해하기 쉬운 형태로 정리해주세요."),
        HumanMessage(content=user_input)
    ]
    logger.info(f"Sending messages to model: {len(messages)} messages")
    
    response = await model.ainvoke(messages)
    logger.info(f"Initial response: {response}")
    
    # 도구 실행
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"Tool calls detected: {len(response.tool_calls)}")
        messages.append(response)
        
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            for tool in tools:
                if tool.name == tool_name:
                    result = await tool.ainvoke(tool_args)
                    logger.info(f"Tool result: {str(result)}")
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call['id'],
                        name=tool_name
                    ))
                    break
        
        final_response = await model.ainvoke(messages)
        logger.info(f"Final response content: {final_response.content}")
        logger.info(f"Final response type: {type(final_response)}")
        if hasattr(final_response, 'content') and final_response.content:
            return final_response.content
        else:
            return "응답 생성에 실패했습니다."
    else:
        logger.info("No tool calls detected")
        return response.content

async def invoke_doc_agent(user_input: str):
    """문서 전용 MCP 에이전트"""
    mcp_client = MultiServerMCPClient({
        'documentation': {
            'transport': 'stdio',
            'command': 'uvx',
            'args': ['awslabs.aws-documentation-mcp-server@latest'],
            'env': {'FASTMCP_LOG_LEVEL': 'ERROR'}
        }
    })
    
    tools = await mcp_client.get_tools()
    logger.info(f"Doc tools: {[tool.name for tool in tools]}")
    logger.info(f"Doc total tools loaded: {len(tools)}")
    
    # Bedrock 클라이언트 설정 (원래 자격 증명 사용)
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-2')
        
    chat_model = ChatBedrock(
        client=bedrock_runtime,
        model_id='apac.anthropic.claude-3-5-sonnet-20241022-v2:0',
        model_kwargs={
            'temperature': 0.1,
            'max_tokens': 4096,
            'tool_choice': {'type': 'auto'}
        }
    )
    
    model = chat_model.bind_tools(tools)
    
    messages = [
        SystemMessage(content="당신은 AWS 문서 전문 AI 어시스턴트입니다. 반드시 다음 단계를 따르세요:\n1. search_documentation 도구로 문서 검색\n2. 가장 관련성 높은 문서를 read_documentation 도구로 상세 내용 가져오기\n3. 실제 문서 내용만을 기반으로 한국어 답변\n\n중요: 반드시 다음 형식으로 답변하세요:\n\n## 답변\n(실제 문서 내용 기반 답변)\n\n## 참고 문서\n- [문서제목](URL)\n- [문서제목](URL)\n\n참고 문서 섹션을 절대 빠뜨리지 마세요!"),
        HumanMessage(content=f"질문: {user_input}\n\n필수 작업:\n1. search_documentation 도구로 문서 검색\n2. 가장 관련성 높은 URL을 read_documentation 도구로 상세 내용 읽기\n3. 읽은 내용으로만 답변 작성\n\n두 도구를 모두 사용해야 합니다!")
    ]
    logger.info(f"Doc sending messages to model with system prompt")
    
    # 진행 상태 표시
    progress_container = st.container()
    with progress_container:
        st.markdown("### 🤖 AI 에이전트 작업 진행상황")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
    status_text.text("💭 사용자 질문을 분석하고 있습니다...")
    progress_bar.progress(10)
    
    response = await model.ainvoke(messages)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        status_text.text(f"✅ 분석 완료! {response.tool_calls[0]['name']} 도구를 사용합니다.")
        progress_bar.progress(20)
    else:
        status_text.text("⚠️ 도구 없이 직접 답변합니다.")
    
    logger.info(f"Doc initial response: {response}")
    
    # 도구 호출 루프 - 여러 번 반복 가능
    current_response = response
    max_iterations = 5
    iteration = 0
    
    while hasattr(current_response, 'tool_calls') and current_response.tool_calls and iteration < max_iterations:
        iteration += 1
        logger.info(f"Doc tool calls detected (iteration {iteration}): {len(current_response.tool_calls)}")
        messages.append(current_response)
        
        for tool_call in current_response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            logger.info(f"Doc executing tool: {tool_name} with args: {tool_args}")
            
            for tool in tools:
                if tool.name == tool_name:
                    result = await tool.ainvoke(tool_args)
                    result_str = str(result)
                    logger.info(f"Doc tool result length: {len(result_str)}")
                    logger.info(f"Doc tool FULL result START: {result_str} :END")
                    
                    # 진행 상태 업데이트
                    progress_value = 20 + (iteration * 30)
                    progress_bar.progress(min(progress_value, 80))
                    
                    if tool_name == 'search_documentation':
                        status_text.text("🔍 AWS 공식 문서를 검색하고 있습니다...")
                    elif tool_name == 'read_documentation':
                        status_text.text("📄 선택된 문서의 상세 내용을 읽고 있습니다...")
                    
                    # 도구 실행 결과를 사용자 친화적으로 표시
                    if tool_name == 'search_documentation':
                        try:
                            import json
                            if isinstance(result, list) and len(result) > 0:
                                doc_count = len(result)
                                status_text.text(f"✅ {doc_count}개의 관련 문서를 발견했습니다!")
                                
                                # 간단한 문서 목록 표시
                                with st.expander(f"📁 발견된 {doc_count}개 문서 보기", expanded=False):
                                    for i, item in enumerate(result[:5], 1):
                                        if isinstance(item, str):
                                            item_data = json.loads(item)
                                            st.markdown(f"{i}. **{item_data.get('title', 'Unknown')}**")
                                            st.markdown(f"   🔗 [{item_data.get('url', '#')}]({item_data.get('url', '#')})")
                                            if item_data.get('context'):
                                                st.markdown(f"   📝 {item_data.get('context')[:100]}...")
                                            st.markdown("---")
                        except:
                            status_text.text("✅ 문서 검색을 완료했습니다.")
                    
                    elif tool_name == 'read_documentation':
                        content_length = len(result_str)
                        status_text.text(f"✅ 문서 내용을 성공적으로 읽었습니다! ({content_length:,}문자)")
                        
                        # 읽은 문서 내용 미리보기
                        if content_length > 1000:
                            with st.expander("📄 읽은 문서 내용 미리보기", expanded=False):
                                st.markdown(f"**문서 내용 미리보기:**")
                                st.text_area("", value=result_str[:500] + "...", height=200, disabled=True)
                                st.markdown(f"*전체 {content_length:,}문자 중 500문자 표시*")
                    messages.append(ToolMessage(
                        content=result_str,
                        tool_call_id=tool_call['id'],
                        name=tool_name
                    ))
                    break
        
        # 다음 응답 받기
        logger.info(f"Doc getting next response from model (iteration {iteration})")
        
        # AI 사고 단계 - 간단하게 진행 상태만 표시
        if iteration < max_iterations:
            status_text.text("🤖 AI가 다음 단계를 계획하고 있습니다...")
            current_response = await model.ainvoke(messages)
            
            if hasattr(current_response, 'tool_calls') and current_response.tool_calls:
                next_tool = current_response.tool_calls[0]['name']
                if next_tool == 'read_documentation':
                    status_text.text("📄 가장 관련성 높은 문서를 선택했습니다.")
                else:
                    status_text.text(f"✅ 다음 단계: {next_tool}")
            else:
                status_text.text("✅ 모든 정보 수집 완료! 답변을 작성합니다.")
                progress_bar.progress(90)
        else:
            current_response = await model.ainvoke(messages)
        
        logger.info(f"Doc response object: {current_response}")
    
    # 최종 답변 완료
    progress_bar.progress(100)
    if current_response.content:
        status_text.text("✅ 답변 생성이 완료되었습니다!")
        # 진행 상태 숨기기 (선택사항)
        # progress_container.empty()
    else:
        status_text.text("❌ 답변 생성에 실패했습니다.")
        st.error("다시 시도해주세요.")
    
    logger.info(f"Doc final response length: {len(current_response.content)}")
    logger.info(f"Doc final response preview: {current_response.content[:200]}...")
    return current_response.content



def run_async_agent(user_input: str, agent_type: str):
    """비동기 에이전트를 동기적으로 실행"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if agent_type == 'cli':
            return loop.run_until_complete(invoke_cli_agent(user_input))
        else:
            return loop.run_until_complete(invoke_doc_agent(user_input))
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"
    finally:
        loop.close()

# AWS CLI 탭
with tab1:
    st.markdown("### 💻 AWS CLI 명령어 실행")
    st.markdown("AWS CLI 명령어를 사용하여 실제 AWS 리소스 정보를 가져옵니다.")
    
    # CLI 채팅 메시지 표시
    for message in st.session_state.cli_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # CLI 사용자 입력
    if cli_prompt := st.chat_input("메시지를 입력하세요... (AWS CLI)", key="cli_input"):
        st.session_state.cli_messages.append({"role": "user", "content": cli_prompt})
        with st.chat_message("user"):
            st.markdown(cli_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("응답 생성 중..."):
                try:
                    response = run_async_agent(cli_prompt, 'cli')
                    st.markdown(response)
                    st.session_state.cli_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)
                    st.session_state.cli_messages.append({"role": "assistant", "content": error_msg})

# AWS 문서 탭
with tab2:
    st.markdown("### 📚 AWS 공식 문서 검색")
    st.markdown("AWS 공식 문서를 검색하고 상세 내용을 가져옵니다.")
    
    # 문서 채팅 메시지 표시
    for message in st.session_state.doc_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 문서 사용자 입력
    if doc_prompt := st.chat_input("메시지를 입력하세요... (AWS 문서)", key="doc_input"):
        st.session_state.doc_messages.append({"role": "user", "content": doc_prompt})
        with st.chat_message("user"):
            st.markdown(doc_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("응답 생성 중..."):
                try:
                    response = run_async_agent(doc_prompt, 'doc')
                    st.markdown(response)
                    st.session_state.doc_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)
                    st.session_state.doc_messages.append({"role": "assistant", "content": error_msg})



# 사이드바에 설정 옵션
with st.sidebar:
    st.header("⚙️ 설정")
    
    # Role ARN 입력
    role_arn = st.text_input(
        "AWS Role ARN (선택사항)",
        value=st.session_state.role_arn,
        placeholder="arn:aws:iam::123456789012:role/MyRole"
    )
    if role_arn != st.session_state.role_arn:
        st.session_state.role_arn = role_arn
        st.rerun()
    
    if st.button("대화 기록 초기화 (CLI)"):
        st.session_state.cli_messages = []
        st.rerun()
    
    if st.button("대화 기록 초기화 (문서)"):
        st.session_state.doc_messages = []
        st.rerun()
    
    if st.button("대화 기록 초기화 (파일시스템)"):
        st.session_state.fs_messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 정보")
    st.markdown("- **MCP 프로토콜**: 표준 MCP 사용")
    st.markdown("- **MCP 서버**: AWS API + Documentation + Filesystem")
    st.markdown("- **모델**: Claude 3.5 Sonnet")
    st.markdown("- **리전**: ap-northeast-2")
    st.markdown("- **기능**: AWS CLI + 문서 검색 + 파일 관리")
    
    st.markdown("---")
    st.markdown("### 💡 CLI 사용 예시")
    st.markdown("- 'S3 버킷 목록 보여줘'")
    st.markdown("- 'EC2 인스턴스 상태 확인해줘'")
    st.markdown("- 'Lambda 함수 목록 알려줘'")
    
    st.markdown("### 📚 문서 사용 예시")
    st.markdown("- 'S3 버킷 생성 방법 문서 찾아줘'")
    st.markdown("- 'Lambda 함수 배포 가이드 검색해줘'")
    st.markdown("- 'EC2 인스턴스 타입 비교 문서 보여줘'")
    