from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

chat = ChatGroq(temperature=0, groq_api_key="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", model_name="mixtral-8x7b-32768")

system = "You are a helpful assistant."
human = "{text}"
prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

chain = prompt | chat
response = chain.invoke({"text": "Explain the importance of low latency LLMs."})
print(response.content)