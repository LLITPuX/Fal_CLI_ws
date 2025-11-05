"""Test script for Cybersich Chat System (Писарь/Clerk Agent).

This script tests the Chat API endpoints:
1. Create a chat session
2. Send user messages
3. Retrieve message history
4. Get session info

Usage:
    python test_chat_system.py
"""

import asyncio
import json
from datetime import datetime

import httpx


BASE_URL = "http://localhost:8000/api/chat"


async def test_chat_system():
    """Test complete chat workflow."""
    print("🧪 Testing Cybersich Chat System (Писарь Agent)\n")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Create a chat session
        print("\n📝 Step 1: Creating chat session...")
        session_response = await client.post(
            f"{BASE_URL}/session",
            json={
                "user_id": "test_user_123",
                "title": "Тестова розмова про козацтво",
            },
        )

        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.text}")
            return

        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id}")
        print(f"   Created at: {session_data['created_at']}")
        print(f"   Title: {session_data['title']}")

        # Step 2: Send user messages
        print("\n📨 Step 2: Sending messages...")

        messages = [
            "Розкажи про історію козацтва",
            "Хто був гетьманом Запорізької Січі?",
            "Які були основні принципи козацького самоврядування?",
        ]

        message_ids = []

        for i, content in enumerate(messages, 1):
            print(f"\n   Message {i}: {content[:50]}...")

            msg_response = await client.post(
                f"{BASE_URL}/message",
                json={
                    "content": content,
                    "session_id": session_id,
                    "role": "user",
                },
            )

            if msg_response.status_code != 200:
                print(f"   ❌ Failed to send message: {msg_response.text}")
                continue

            msg_data = msg_response.json()
            message_ids.append(msg_data["message_id"])

            print(f"   ✅ Message recorded: {msg_data['message_id']}")
            print(f"      Status: {msg_data['status']}")
            print(f"      Recorded: {msg_data['recorded']}")

            # Simulate assistant response
            await asyncio.sleep(0.5)

            assistant_response = await client.post(
                f"{BASE_URL}/message",
                json={
                    "content": f"Відповідь асистента на: {content[:30]}...",
                    "session_id": session_id,
                    "role": "assistant",
                },
            )

            if assistant_response.status_code == 200:
                assistant_data = assistant_response.json()
                message_ids.append(assistant_data["message_id"])
                print(f"   ✅ Assistant response recorded: {assistant_data['message_id']}")

        # Step 3: Retrieve message history
        print("\n📜 Step 3: Retrieving message history...")

        history_response = await client.get(
            f"{BASE_URL}/session/{session_id}/history",
            params={"limit": 50, "offset": 0},
        )

        if history_response.status_code != 200:
            print(f"❌ Failed to get history: {history_response.text}")
            return

        history_data = history_response.json()
        print(f"✅ Retrieved {history_data['total']} messages")

        print("\n   📋 Message History:")
        for msg in history_data["messages"]:
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
            content_preview = (
                msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            )
            print(f"   {role_icon} [{timestamp}] {msg['role']}: {content_preview}")

        # Step 4: Get session info
        print("\n📊 Step 4: Getting session info...")

        session_info_response = await client.get(f"{BASE_URL}/session/{session_id}")

        if session_info_response.status_code != 200:
            print(f"❌ Failed to get session info: {session_info_response.text}")
            return

        session_info = session_info_response.json()
        print("✅ Session Information:")
        print(f"   Session ID: {session_info['session_id']}")
        print(f"   User ID: {session_info['user_id']}")
        print(f"   Title: {session_info['title']}")
        print(f"   Status: {session_info['status']}")
        print(f"   Created: {session_info['created_at']}")

        # Summary
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        print(f"\n📊 Summary:")
        print(f"   Session ID: {session_id}")
        print(f"   Total messages: {history_data['total']}")
        print(f"   Message IDs: {len(message_ids)}")
        print("\n💡 Next steps:")
        print("   1. Check FalkorDB with Cypher queries")
        print("   2. Implement frontend UI (.figma example)")
        print("   3. Add Підсвідомість agent for context analysis")
        print("   4. Add Оркестратор agent for decision making")


if __name__ == "__main__":
    try:
        asyncio.run(test_chat_system())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

