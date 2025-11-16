import asyncio
import time

import httpx

API_URL = "http://127.0.0.1:8000/api/v1/tasks/"

# In a real scenario, you would generate this token programmatically.
AUTH_TOKEN = "your_jwt_token_here"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

NUM_REQUESTS = 100
CONCURRENCY = 10


async def fetch_tasks(client: httpx.AsyncClient):
    try:
        response = await client.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        return response.elapsed.total_seconds()
    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
        return None


async def run_benchmark():
    print(
        f"Starting benchmark with {NUM_REQUESTS} requests "
        f"and concurrency of {CONCURRENCY}..."
    )

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def rate_limited_fetch():
            async with semaphore:
                return await fetch_tasks(client)

        start_time = time.time()
        tasks = [rate_limited_fetch() for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

    # --- Analysis ---
    successful_requests = [r for r in results if r is not None]
    total_time = end_time - start_time
    num_successful = len(successful_requests)

    print("\n--- Benchmark Report ---")
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Total requests sent: {NUM_REQUESTS}")
    print(f"Successful requests: {num_successful}")
    print(f"Failed requests: {NUM_REQUESTS - num_successful}")

    if num_successful > 0:
        rps = num_successful / total_time
        avg_latency = sum(successful_requests) / num_successful
        max_latency = max(successful_requests)
        min_latency = min(successful_requests)

        print(f"Requests per second (RPS): {rps:.2f}")
        print(f"Average latency: {avg_latency*1000:.2f} ms")
        print(f"Min latency: {min_latency*1000:.2f} ms")
        print(f"Max latency: {max_latency*1000:.2f} ms")

    print("--- End of Report ---")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
