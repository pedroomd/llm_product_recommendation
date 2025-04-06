from pydantic import BaseModel
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector
from neo4j_utils import Neo4jDriverManager
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.base import Chain
import json
import re
from langchain.chains import LLMChain
from termcolor import colored
from report import HTMLReport
from templates import CYPHER_STRING_QUERY_PARSER_TEMPLATE

neo4j_driver = Neo4jDriverManager.get_instance()
pdf_report = HTMLReport.get_instance()

class CustomCypherQueryCorrector(CypherQueryCorrector):
    def __init__(self, schemas: list):
        super().__init__(schemas)
        self.cypher_parser_llm = ChatOpenAI(model_name='o1-mini')
        
    def cypher_string_query_parser(self, query):
        # this function could use a regex-based approach
        # read the CYPHER_STRING_QUERY_PARSER_TEMPLATE to understand what this function returns
        prompt_template = PromptTemplate(
            input_variables=["question"],
            template=CYPHER_STRING_QUERY_PARSER_TEMPLATE
        )
        prompt_template.format(question=query)

        chain = LLMChain(llm=self.cypher_parser_llm, prompt=prompt_template)
        response = chain.invoke(query)
        output = re.sub(r"```(?:json)?", "", response['text'])
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {}
        
    def fuzzy_search(self, search_term: str, property: str, node = '') -> str:
        terms = search_term.split()
        search_param = f"{property}:" + " ".join([f"{term}~" for term in terms])

        node_condition = "WHERE score > 0.1" + (f' AND "{node}" IN labels(node)' if node else "")
        with neo4j_driver.get_session() as session:
            result = session.run(
            f"""CALL db.index.fulltext.queryNodes("productSearch", "{search_param}")
                YIELD node, score
                {node_condition}
                RETURN node.{property} AS property_value, score
                LIMIT 1
                """,
            )
            
            if record := result.single():
                property_value = record.get('property_value')
                return property_value
        return ''

    def validate_query(self, query: str) -> str:
        node_properties_dict = self.cypher_string_query_parser(query)

        end_query = query.replace('"', "'")
        for (node_type, property, value) in node_properties_dict.get('Nodes', []):
            new_value = self.fuzzy_search(search_term=value, property=property, node=node_type)
            if new_value:
                end_query = end_query.replace(f"'{value}'", f"'{new_value}'")
                
        for (property, value) in node_properties_dict.get('Properties', []):
            new_value = self.fuzzy_search(search_term=value, property=property)
            if new_value:
                end_query = end_query.replace(f"'{value}'", f"'{new_value}'")
        
        return end_query
    
    def correct_query(self, query: str) -> str:
        query = super().correct_query(query)
        
        pdf_report.add_to_section("original_query", query)
        print(colored(f"Original query: {query}", "red"))
        
        corrected_query = self.validate_query(query)
        pdf_report.add_to_section("corrected_query", corrected_query)
        return corrected_query
    

class QuestionItem(BaseModel):
    question: str
    answer: list[str]
  
class EvaluateLLM(BaseModel):
    chain: Chain
    question_items: list[QuestionItem]
    
    @classmethod
    def from_json(cls, chain: Chain, json_file: str):
        with open(json_file, "r") as f:
            data = json.load(f)
            question_items = [QuestionItem(**item) for item in data]
            return cls(chain=chain, question_items=question_items)
  
    def generate_results(self):
        for question_item in self.question_items:
            pdf_report.new_section()
            pdf_report.add_to_section("question", question_item.question)
            print(colored(f"Question: {question_item.question}", "yellow"))
            
            response = self.chain.invoke(question_item.question).get('result', '')
            
            response_evaluation = "✅"
            for answer_item in question_item.answer:
                if answer_item.lower() not in response.lower():
                    response_evaluation = "❌"
                    break
            print(response_evaluation)
            print("Expected Response: ", question_item.answer)
            print("Actual Response: ", response)
            
            pdf_report.add_to_section("expected_answer", question_item.answer)
            pdf_report.add_to_section("actual_answer", f"{response_evaluation} {response}")
            pdf_report.save_section()
            
        pdf_report.generate_report()
