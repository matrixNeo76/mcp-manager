#!/usr/bin/env python3
"""Smoke test: verifica che l'MCP server si avvii e tutti i tool rispondano.

Usage:
    uv run python scripts/smoke_test.py
    uv run python scripts/smoke_test.py --verbose
"""

import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8")

PASS = 0
FAIL = 0


def ok(msg: str):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")


def fail(msg: str):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}")


async def main():
    global PASS, FAIL

    print("=" * 60)
    print("SMOKE TEST - MCP Manager")
    print("=" * 60)

    # 1. Import server
    print("\n--- 1. Import server ---")
    try:
        from mcp_manager.server import server
        ok("server importato")
    except Exception as e:
        fail(f"import fallito: {e}")
        return

    # 2. List tools
    print("\n--- 2. Tool registration ---")
    try:
        tools = await server.list_tools()
        names = sorted(t.name for t in tools)
        ok(f"{len(tools)} tools: {', '.join(names)}")
    except Exception as e:
        fail(f"list_tools fallito: {e}")

    # 3. Test pi_capabilities (no network)
    print("\n--- 3. pi_capabilities ---")
    try:
        text, data = await server.call_tool("pi_capabilities", {})
        result = text[0].text if text else ""
        if len(result) > 100:
            ok(f"restituiti {len(result)} chars")
        else:
            fail(f"output troppo corto: {len(result)} chars")
    except Exception as e:
        fail(f"pi_capabilities: {e}")

    # 4. Test list_local_servers (no config needed)
    print("\n--- 4. list_local_servers ---")
    try:
        text, data = await server.call_tool("list_local_servers", {})
        result = data.get("result", data)
        if isinstance(result, list):
            ok(f"restituita lista di {len(result)} server")
        else:
            fail(f"tipo inaspettato: {type(result)}")
    except Exception as e:
        fail(f"list_local_servers: {e}")

    # 5. Test registry_health (network)
    print("\n--- 5. registry_health ---")
    try:
        text, data = await server.call_tool("registry_health", {})
        if data.get("reachable"):
            ok(f"registry raggiungibile (v{data.get('api_version', '?')})")
        else:
            fail("registry non raggiungibile")
    except Exception as e:
        fail(f"registry_health: {e}")

    # 6. Test search_registry (network)
    print("\n--- 6. search_registry ---")
    try:
        text, data = await server.call_tool("search_registry", {
            "query": "postgres", "limit": 2,
        })
        results = data.get("result", data)
        count = len(results) if isinstance(results, list) else 0
        if count > 0:
            ok(f"trovati {count} server per 'postgres'")
        else:
            fail("nessun risultato per 'postgres'")
    except Exception as e:
        fail(f"search_registry: {e}")

    # 7. Test get_server_details (network)
    print("\n--- 7. get_server_details ---")
    try:
        text, data = await server.call_tool("get_server_details", {
            "server_name": "io.github.containers/kubernetes-mcp-server",
        })
        if data.get("found"):
            ok(f"dettagli server: {data.get('name', '?')}")
        else:
            fail(f"server non trovato: {data.get('error', '?')}")
    except Exception as e:
        fail(f"get_server_details: {e}")

    # Summary
    print(f"\n{'=' * 60}")
    total = PASS + FAIL
    if FAIL == 0:
        print(f"  SMOKE TEST COMPLETATO: {PASS}/{total} PASS")
    else:
        print(f"  SMOKE TEST: {PASS}/{total} PASS, {FAIL}/{total} FAIL")
    print(f"{'=' * 60}")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
