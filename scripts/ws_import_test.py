#!/usr/bin/env python3
"""
WS Import 스모크 테스트

예시
  python scripts/ws_import_test.py --file export.json --mode new
  python scripts/ws_import_test.py --file export.json --mode merge --target room1 --policy skip

옵션
  --ws ws://localhost:8765 (기본)
  --token <access_token> (로그인 환경에서 필요 시)
  --file <export_json_path> (필수)
  --mode new|merge (기본 new)
  --target <room_id> (merge일 때)
  --policy skip|add (기본 skip)
"""

from __future__ import annotations

import argparse
import asyncio
import json

import websockets


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ws", default="ws://localhost:8765")
    p.add_argument("--token", default=None)
    p.add_argument("--file", required=True)
    p.add_argument("--mode", default="new", choices=["new", "merge"])
    p.add_argument("--target", default=None)
    p.add_argument("--policy", default="skip", choices=["skip", "add"])
    args = p.parse_args()

    with open(args.file, encoding="utf-8") as f:
        payload = json.load(f)

    async with websockets.connect(args.ws) as ws:
        # 초기 핸드셰이크 수신
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            print("connected:", msg)
        except Exception:
            pass

        req = {
            "action": "import_data",
            "import_mode": args.mode,
            "target_room_id": args.target,
            "duplicate_policy": args.policy,
            "json_data": payload,
        }
        if args.token:
            req["token"] = args.token

        await ws.send(json.dumps(req, ensure_ascii=False))
        resp = await ws.recv()
        print(resp)


if __name__ == "__main__":
    asyncio.run(main())
