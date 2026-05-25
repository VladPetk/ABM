"""Quick WebSocket smoke test against the live server."""
import asyncio
import json

import websockets


async def main():
    async with websockets.connect("ws://127.0.0.1:8000/api/ws") as ws:
        # Drain initial three messages: scenarios, loaded, first tick
        for _ in range(3):
            raw = await ws.recv()
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "tick":
                a = msg.get("agents", [])
                print(f"  tick: t={msg['t']}, {len(a)} agents, "
                      f"metrics keys={list(msg['metrics'].keys())}")
            elif t == "loaded":
                print(f"  loaded: {msg['key']}  params={len(msg['detail']['params'])}")
            elif t == "scenarios":
                print(f"  scenarios: {[i['key'] for i in msg['items']]}")
            else:
                print(f"  ?: {t}")

        # Step once
        await ws.send(json.dumps({"type": "step"}))
        raw = await ws.recv()
        msg = json.loads(raw)
        print(f"  after step: t={msg['t']}")

        # Mutate a param
        await ws.send(json.dumps({"type": "param", "name": "epsilon", "value": 0.7}))
        # No reply expected, but next step should reflect

        # Switch scenario
        await ws.send(json.dumps({"type": "load", "scenario": "elite_dynamics", "params": {"n_agents": 200}}))
        for _ in range(2):
            raw = await ws.recv()
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "loaded":
                print(f"  switched: {msg['key']}, defaults={list(msg['detail']['defaults'].keys())[:4]}")
            elif t == "tick":
                print(f"  first tick after switch: t={msg['t']}, agents={len(msg['agents'])}, "
                      f"parties={list(msg['parties'].keys())}")


if __name__ == "__main__":
    asyncio.run(main())
