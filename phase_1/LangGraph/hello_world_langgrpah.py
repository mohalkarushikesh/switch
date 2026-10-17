from langgrpah.graph import StateGraph, MessageState, START, END

def mock_llm(State: MessageState): 
	return {"messages": [{"role": "ai", "content": "hello world"}]}

graph = StateGraph(MessageState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)

graph = graph.compile()

graph.invoke({"messages": [{"role": "user", "content": "hello"}]})




 