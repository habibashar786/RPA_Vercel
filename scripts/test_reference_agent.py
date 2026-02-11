import asyncio
from src.agents.document_structure.reference_citation_agent import ReferenceCitationAgent
from src.models.agent_messages import AgentRequest

async def main():
    agent = ReferenceCitationAgent()
    request = AgentRequest(
        task_id="test_task",
        agent_name="reference_citation_agent",
        action="process",
        input_data={
            "dependency_analyze_literature": {"papers": [], "citations": []}
        },
    )
    resp = await agent.process_task(request)
    print(resp)

if __name__ == '__main__':
    asyncio.run(main())
