import os
import json
from neo4j import GraphDatabase
import pandas as pd
from pydantic import BaseModel, model_validator

# Retrieve connection details from environment variables
NEO4J_URL = os.environ.get("NEO4J_URL")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))

class Product(BaseModel):
    name: str
    type: str
    times_sold: int
    
class Game(Product):
    franchise: str
    min_age: int
    category: str
    
    @model_validator(mode='before')
    def swap_type_and_category(cls, values):
        values['type'], values['category'] = values.get('category'), values.get('type')
        return values
    
class Console(Product):
    @model_validator(mode='before')
    def create_type(cls, values):
        values['type'] = values.get('category')
        values.pop('category', None)
        return values

class Accessory(Product):
    category: str

product_model_mapping = {
    "Games"       : Game,
    "Console"     : Console,
    "Accessories" : Accessory,
}

def get_str_properties(model: type[BaseModel]) -> list[str]:
    return [name for name, type_ in model.__annotations__.items() if type_ is str]

def get_product(product: dict, product_section: str) -> Product:
    model = product_model_mapping.get(product_section, Product)
    return model(**product)

def load_product(tx, product_section, product):
    
    model_product = get_product(product, product_section)
    params = model_product.model_dump(exclude_none=True)
    
    set_clauses = [f"p.{param} = ${param}" for param in params]
    print(set_clauses)
    print(params)

    product_query = f"""
    MERGE (p:Product:{model_product.type} {{name: $name}})
    SET {', '.join(set_clauses)}       
    """
    tx.run(
        product_query,
        **params
    )

    stores = [key for key in product if key.startswith("Store")]
    for store_name in stores:
        store_query = """
        MERGE (s:Store {name: $store_name})
        """
        tx.run(store_query, store_name=store_name)
        
        times_sold  = product.get(store_name)
        if not times_sold:
            continue
        
        rel_query = """
        MATCH (p:Product {name: $name})
        MATCH (s:Store {name: $store_name})
        MERGE (p)-[r:SOLD_AT]->(s)
        SET r.times_sold = $times
        """
        tx.run(rel_query, name=product.get("name"), store_name=store_name, times=times_sold)


def load_cooccurrence(tx, product_i, product_j, together_sold):
    # little hack to avoid duplicates (A->B and B->A). it's enforced alphabetical ordering on product names
    if product_i > product_j:
        product_i, product_j = product_j, product_i
    query = """
    MATCH (a:Product {name: $name_a})
    MATCH (b:Product {name: $name_b})
    MERGE (a)-[r:SOLD_TOGETHER]->(b)
    SET r.together_sold = $together_sold
    """
    tx.run(query, name_a=product_i, name_b=product_j, together_sold=together_sold)

def get_str_properties(model: type[BaseModel]) -> list[str]:
    annotations = {}
    for cls in model.__mro__:
        if hasattr(cls, '__annotations__'):
            annotations.update(cls.__annotations__)
    return [name for name, type_ in annotations.items() if type_ is str]

def create_products_fulltext_index(tx):
    product_types = []
    
    # get unique categorical properties with 'n.' prefix
    categorical_properties = set()
    for model in product_model_mapping.values():
        product_types.append(model.__name__)
        for prop in get_str_properties(model):
            categorical_properties.add(f'n.{prop}')
    
    categorical_properties = ','.join(categorical_properties)
    product_types = '|'.join(product_types)
    
    query = f"""
    CREATE FULLTEXT INDEX productSearch 
    FOR (n:{product_types}) 
    ON EACH [{categorical_properties}]
    """
    
    tx.run(query)

def main():
    with driver.session() as session:
        with open("products.json", "r") as f:
            data = json.load(f)

        for product_section, products in data.items():
            for product in products:
                session.execute_write(load_product, product_section, product)
                print(f"Loaded product: {product.get('name')}")

        co_occurrences = pd.read_excel('co_occurrences.xlsx', index_col=0).to_dict()
        processed_co_occurrences = set()
        for product, co_products in co_occurrences.items():
            for co_product, times_sold_together in co_products.items():
                # only need the upper triangle
                if co_product in processed_co_occurrences:
                    continue
                session.execute_write(load_cooccurrence, product, co_product, times_sold_together)
            
            processed_co_occurrences.add(product)
            print(f"Loaded co-occurrence between: {product} and {co_product}")
            
        session.execute_write(create_products_fulltext_index)
        
    driver.close()
    print("Data load complete!")

if __name__ == "__main__":
    main()