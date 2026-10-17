```
define tools and model 
define state
define toolnode, modelnode
conditional edge function 
build & compile the agent
```

from langchain.tools import tool
from langchain.chat_models import init_chat_model 
from langchain.messages import AnyMessage, SystemMessage, ToolMessage
from typing_extentions import TypedDict, Annotated
import operator 


model = init_chatmodel(
	"claude-sonet-4-6",
	tempreture = 0 			# deterministic results
)

@tool		# decorator 

def multiply(a: int, b: int) -> int:
	return a * b 

def addtion(a: int, b: int) -> int:
	return a + b

def devide(a: int, b: int) -> int:
	return a / b

tools = [multiply, addition, devide]
tool_by_name = {tool.name: tool for tool in tools} 
model_with_tools = model.tool_binds(tools)

class MessageState(TypedDict):
	message: Annotated[list[AnyMessage], operator.add]
	llm_calls: int

def llm_call(state: dict):
	return {
		"messages": [
			model_with_tools.invoke(
			[
				SystemMessge(
					content: "You're helpful assistant tasked with performing arithmatic on set of inputs."
				)		
			]	
			 + state["messages"]
		)
	], 
	llm_calls: state.get('llm_calls', 0) + 1 
}

def tool_node(state: dict):
	results = []
	for tool_call in state["messages"][-1].tool_calls:
		tool = tool_by_name[tool_call['name']]
		observatio = tool.invoke(tool_call['args'])
		result.appned(ToolMeesage(content=observation, tool_call_id = tool_call_id["id"]))
	return {"message": results}


