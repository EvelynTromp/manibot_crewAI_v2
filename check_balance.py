import asyncio
from core.manifold_client import ManifoldClient

async def check_balance():
    client = ManifoldClient("6a40ae0d-1de0-4217-acb8-124728eebcfc")
    me_data = await client._make_request("GET", "me")
    print(f"User ID: {me_data.get('id')}")
    print(f"Username: {me_data.get('username')}")
    print(f"Balance: M${me_data.get('balance')}")

if __name__ == "__main__":
    asyncio.run(check_balance())