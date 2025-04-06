"""
This module contains templates for parsing and generating Cypher queries.
"""

from textwrap import dedent

CYPHER_STRING_QUERY_PARSER_TEMPLATE = dedent("""
    You are an expert in parsing Cypher queries. Your task is to extract all string literals 
    (enclosed in single or double quotes) from a query and map them either to nodes (when a node 
    is being searched/filtered) or to properties.

    1. Node Extraction:
        - A node is defined as a pattern following this format: `(n:Label {{property: "string_value"}})`
        - For example, in `(c:Console {{name: 'Switch'}})`, you should extract this as a node and add it 
          to the "Nodes" list in the final dictionary as a list: `["Console", "name", "Switch"]`.

    2. Property Extraction:
        - In a Cypher query, properties often appear in the WHERE clause. When you encounter a string literal 
          that does not belong to the node definition above, treat it as a property.
        - Only include properties when they are filtered using exact string matching. The operators that indicate 
          an exact match include:
            - `=`
            - `<>`
            - `!=`
            - `IN`
            - `NOT IN`
        - For example, in `WHERE g.name <> "Mario Kart 8 Deluxe"`, you should capture the property as: 
          `("name", "Mario Kart 8 Deluxe")`.
        - Do not extract strings from comparisons that do not use the exact matching operators (e.g., `CONTAINS`, 
          `STARTS WITH`, etc.), nor from numeric comparisons.

    3. Final Output:
        - Return a dictionary with two keys:
            - "Nodes": A list of lists, each sublist containing `[Label, property_name, string_value]`.
            - "Properties": A list of lists, each sublist containing `[property_name, string_value]`.

    Example Query:

    MATCH (c:Console {{name: "Switch"}})-[r:SOLD_TOGETHER]-(g:Game {{name: "Pokemon"}})
    WHERE g.min_age <= 7
      AND g.category IN ['Party', 'Adventure']
      AND g.name <> "Mario Kart 8 Deluxe"
      AND g.franchise = 'mario'
    MATCH (g)-[:SOLD_AT]->(:Store {{name: "Store C"}})
    RETURN c, r, g

    Example Output:
    {{
        "Nodes": [
            ["Console", "name", "Switch"],
            ["Game", "name", "Pokemon"],
            ["Store", "name", "Store C"]
        ],
        "Properties": [
            ["category", "Party"],
            ["category", "Adventure"],
            ["name", "Mario Kart 8 Deluxe"],
            ["franchise", "mario"]
        ]
    }}

    Output only a JSON dictionary and nothing else. Do not include any additional text, explanations, or comments in your final output.
    User query: 
    {question}
""").strip()


CYPHER_QUERY_GENERATION_TEMPLATE = dedent("""
    Task: You are an expert in creating Cypher queries for querying a Neo4j database based on user prompts.
    Use only the provided relationship types and properties in the schema.
    If no relevant Cypher query can be constructed for the given prompt (because it's not related to the schema), respond with a query that returns no results.
    
    Schema:
    {schema}

    Additional schema notes:
        - Always use undirected relationships (-[r]-).
        - Consider any mentioned product as a seed for a co-occurrence search using the SOLD_TOGETHER relationship. 
          Products sold together are likely to be similar.
        - Instead of using the EXISTS() function, use property checks like IS NOT NULL to determine whether a property exists.
        - Avoid escaping or delimiting identifiers with backticks, especially when combining or checking multiple labels. 
          Use functions like labels() for checking label membership. Replace this: 
              (rec:`Game OR rec`:Product)
          with: 
              ('Game' IN labels(rec) OR 'Product' IN labels(rec))
        - Try to use ORDER BY (DESC or ASC based on the prompt) at the end of your queries to return the most relevant results first.
        
    
    Do not's:
        - Do not use any other relationship types or properties that are not provided.
        - Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
        - Do not include any text except the generated Cypher statement.
        - Do not parameterize any query value; always use the provided values from the prompt.

    The question is:
    {question}
""").strip()
