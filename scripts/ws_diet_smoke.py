"""End-to-end smoke test of the per-agent diet edit loop."""
import asyncio
import json

import websockets


async def main():
    async with websockets.connect("ws://127.0.0.1:8000/api/ws") as ws:
        # Switch to Cable news era and check outlets are exposed
        await ws.send(json.dumps({"type": "load", "scenario": "elite_dynamics"}))

        outlets = None
        for _ in range(4):
            raw = await asyncio.wait_for(ws.recv(), timeout=3)
            msg = json.loads(raw)
            if msg.get("type") == "loaded":
                outlets = msg["viz"].get("outlets")
                print(f"loaded: {msg['key']} · outlets: "
                      f"{[o['name'] for o in (outlets or [])]}")

        assert outlets, "no outlets in viz payload"
        fox = next((o for o in outlets if o["name"] == "Fox News"), None)
        msnbc = next((o for o in outlets if o["name"] == "MSNBC"), None)
        assert fox and msnbc, "expected Fox News and MSNBC outlets"
        print(f"Fox at {fox['position']} · MSNBC at {msnbc['position']}")

        async def wait_for_type(t):
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=4)
                msg = json.loads(raw)
                if msg.get("type") == t:
                    return msg

        # Pick agent 0 and wait for its inspect reply
        await ws.send(json.dumps({"type": "select_agent", "id": 0}))
        ins = await wait_for_type("inspect")
        a0 = ins["agent"]
        print(f"agent 0 init: x={a0['x']:.3f} y={a0['y']:.3f} "
              f"party={a0['party']} diet={a0['media_diet']}")
        assert isinstance(a0["media_diet"], dict), "expected dict diet for elite_dynamics"

        # Force this agent into 100% Fox News
        await ws.send(json.dumps({
            "type": "set_diet",
            "agent_id": 0,
            "diet": {fox["id"]: 1.0},
        }))
        ins2 = await wait_for_type("inspect")
        print(f"after set_diet: diet={ins2['agent']['media_diet']}")

        # Play 60 ticks and watch the agent drift toward Fox's position
        await ws.send(json.dumps({"type": "play"}))
        last_inspect = None
        ticks = 0
        deadline = asyncio.get_event_loop().time() + 12
        while ticks < 80 and asyncio.get_event_loop().time() < deadline:
            raw = await asyncio.wait_for(ws.recv(), timeout=3)
            msg = json.loads(raw)
            if msg.get("type") == "tick":
                ticks = msg["t"]
            elif msg.get("type") == "inspect":
                last_inspect = msg["agent"]
        await ws.send(json.dumps({"type": "pause"}))

        if last_inspect:
            print(f"agent 0 after {ticks} ticks: x={last_inspect['x']:.3f} "
                  f"y={last_inspect['y']:.3f}")
            dx = last_inspect["x"] - a0["x"]
            dy = last_inspect["y"] - a0["y"]
            print(f"  drift: Δx={dx:+.3f} Δy={dy:+.3f} "
                  f"(toward Fox={fox['position']} should be +x, +y from anywhere)")


if __name__ == "__main__":
    asyncio.run(main())
