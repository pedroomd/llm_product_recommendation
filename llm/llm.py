import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from neo4j_utils import Neo4jDriverManager
from utilities import CustomCypherQueryCorrector, EvaluateLLM
from templates import CYPHER_QUERY_GENERATION_TEMPLATE
from dotenv import load_dotenv
load_dotenv()

neo4j_driver = Neo4jDriverManager.get_instance()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    
def llm_product_search():
  prompt_template = PromptTemplate(
      input_variables=["schema", "question"], 
      template=CYPHER_QUERY_GENERATION_TEMPLATE
  )
  
  graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USER"), 
    password=os.getenv("NEO4J_PASSWORD")
  )

  chain = GraphCypherQAChain.from_llm(
      llm=ChatOpenAI(model_name="gpt-4o", temperature=0),
      graph=graph, 
      allow_dangerous_requests=True,
      verbose=True,
      cypher_prompt=prompt_template,
      validate_cypher=True
  )
  
  # little hack to intercept the query
  chain.cypher_query_corrector = CustomCypherQueryCorrector(schemas=chain.cypher_query_corrector.schemas)
  evaluateLLM = EvaluateLLM.from_json(chain=chain, json_file="llm/llm_evaluation.json")
  
  evaluateLLM.generate_results()

if __name__ == "__main__":
  llm_product_search()

