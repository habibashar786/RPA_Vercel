import asyncio
import json

from src.api import main
from src.models.proposal_schema import ProposalRequest

async def run():
    try:
        await main.initialize_system()
        request = ProposalRequest(
            topic="Automated testing of a mock research proposal generation system",
            key_points=[
                "Background and motivation",
                "Research objectives",
                "Expected contributions",
            ],
        )
        print("Starting proposal generation (in-process)...")
        proposal = await main.orchestrator.generate_proposal(request)
        print(json.dumps(proposal.model_dump(), indent=2))
    except Exception as e:
        print("ERROR during proposal generation:", e)
    finally:
        try:
            await main.shutdown_system()
        except Exception:
            pass

if __name__ == '__main__':
    asyncio.run(run())
