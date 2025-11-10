#!/usr/bin/env python3
"""WebSocket 클라이언트 테스트"""

import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://localhost:8765"

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket 연결 성공")

            # 컨텍스트 설정
            set_context = {
                "action": "set_context",
                "data": {
                    "world": "테스트 세계",
                    "situation": "간단한 테스트입니다.",
                    "user_character": "테스터",
                    "characters": [{"name": "테스트봇", "description": "테스트용 캐릭터입니다."}],
                    "narrator_mode": "no_narrator",
                    "adult_mode": False,
                },
            }

            await websocket.send(json.dumps(set_context))
            response = await websocket.recv()
            print(f"✓ 컨텍스트 설정 완료: {response}")

            # 채팅 메시지 전송
            chat_msg = {"action": "chat", "prompt": "안녕하세요?"}

            print("\n채팅 메시지 전송 중...")
            await websocket.send(json.dumps(chat_msg))

            # 스트리밍 응답 수신
            response_chunks = []
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(message)

                    # 디버깅: 받은 메시지 출력
                    print(
                        f"\n[DEBUG] 받은 메시지: action={data.get('action')}, type={data.get('type')}"
                    )

                    action = data.get("action")

                    if action == "chat_stream":
                        # stream_callback에서 보낸 데이터
                        stream_data = data.get("data", {})
                        print(f"[DEBUG] stream_data type: {stream_data.get('type')}")

                        # assistant 메시지 추출
                        if stream_data.get("type") == "assistant":
                            message_obj = stream_data.get("message", {})
                            content = message_obj.get("content", [])
                            for item in content:
                                if item.get("type") == "text":
                                    chunk = item.get("text", "")
                                    response_chunks.append(chunk)
                                    print(chunk, end="", flush=True)
                    elif action == "chat_complete":
                        print("\n\n✓ 채팅 완료")
                        break
                    elif action == "error":
                        print(f"\n✗ 에러: {data.get('data', {}).get('error')}")
                        break
                except TimeoutError:
                    print("\n✗ 타임아웃")
                    break

            full_response = "".join(response_chunks)
            if full_response:
                print(f"\n전체 응답 길이: {len(full_response)} 문자")
                return True
            else:
                print("\n✗ 응답을 받지 못했습니다")
                return False

    except Exception as e:
        print(f"✗ 에러: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
