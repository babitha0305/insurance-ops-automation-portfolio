"""Spawns the server over stdio as an MCP client and checks the tools end to end."""
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [t.name for t in (await s.list_tools()).tools]
            print("tools:", tools)
            out = json.loads((await s.call_tool("run_quality_checks", {})).content[0].text)
            print("checks:", out)
            rec = json.loads((await s.call_tool("reconcile_to_ledger", {})).content[0].text)
            print("unexplained variance:", [x["unexplained"] for x in rec])
            res = (await s.read_resource("bordereau://summary")).contents[0].text
            print("resource:", res)
            assert set(tools) == {"run_quality_checks", "list_flagged_records", "reconcile_to_ledger"}
            assert out["issues"]["duplicate"] == 27 and all(abs(x["unexplained"]) < 0.01 for x in rec)
            print("ALL MCP TESTS PASSED")
asyncio.run(main())
