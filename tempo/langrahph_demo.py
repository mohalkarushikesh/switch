from langgraph.graph import StateGraph, END
from typing import TypedDict

# state graph for tempo
class State(TypedDict):
    input: str
    output: str

# node 
def process(state: State) -> State:
    return {"output": state["input"].upper()}

# build the graph   
graph = StateGraph(State)
graph.add_node("process", process)
graph.set_entry_point("process")
graph.add_edge("process", END)

# compile & run 
app = graph.compile()
result = app.invoke({"input": "hello, buddy!"})
print(result["output"])  # Output: {'input': 'hello', 'output': 'HELLO'}
