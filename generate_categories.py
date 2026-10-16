import mysql.connector
import pandas as pd
import re

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="court_documents_analysis_by_ai"
)

frame = pd.read_csv("feature_store/parsed_proc_decisions_v2.csv") 
frame = frame.set_index(['code']) 

def cleanup_options(options, parent_option = None, grandparent_option = None):
    new_options = []
    for i, option in enumerate(options):
        if parent_option:
            option = option.replace(parent_option, '')

        if grandparent_option:
            option = option.replace(grandparent_option, '')
        # Replace all occurrences of digit
        option = re.sub(r'\d[\.\)]?', '', option)

        for token in ['на підставі', 'Рішення ,  , ,', 'Ухвала , Ухвала ', 'Ухвала , ', 'Ухвала  , ,', 'Ухвала : , ', 'Ухвала .,', 'Ухвала  :,', 'Процесуальні ухвали,   :,', 'Ухвала  ,  ']:
            if token in option:
                option = option.replace(token, '')

        # Remove leading and trailing punctuation
        while option and option[-1] in ['.', ',', '!', '?', ':', ' ', ';']:
            option = option[:-1]
        while option and option[0] in ['.', ',', '!', '?', ':', ' ', ';']:
            option = option[1:]

        new_options.append(option)
    return new_options

class Node:
    def __init__(self, index, description):
        self.index = index
        self.description = description
        self.children = []
        
    def add_child(self, child_node):
        self.children.append(child_node)
    
root = Node('', 'Root')

def generate_children(node, frame, parent_node=None):
    if len(node.index) > 0:
        current_index = node.index + '.'
        indices = frame.index
        options = [frame.loc[index].description for index in indices if re.match(rf'^{re.escape(current_index)}(\d+)\.?$', index)]
    else:
        indices = frame.index
        #options = [frame.loc[index].description for index in indices if re.match(rf'^(\d+)\.?$', index)]
        options = ['Вирок', 'Постанова', 'Рішення', 'Судовий наказ', 'Ухвала', 'Окрема ухвала', 'Додаткове рішення', '', '', 'Окрема ухвала']
    
    grandparent_option = None
    if parent_node and parent_node.index:  
        grandparent_option = parent_node.description
    options = cleanup_options(options, node.description, grandparent_option)

    for i, option in enumerate(options):
        if len(node.index) > 0:
            child_index = f"{node.index}.{i+1}"
        else:
            child_index = f"{i+1}"
        child_node = Node(child_index, option)
        node.add_child(child_node)
        generate_children(child_node, frame, node)

def print_tree(node, indent=0):

    print('    ' * indent + f"{node.index}: {node.description}")
    for child in node.children:
        print_tree(child, indent + 1)

# --- Save tree to database ---
def save_tree_to_db(node, parent_id=None, cursor=None):
    # Only insert if title (description) is not empty
    if node.description and node.description.strip():
        sql = "INSERT INTO taxonomy (parent_id, code, title) VALUES (%s, %s, %s)"
        cursor.execute(sql, (parent_id, node.index, node.description))
        node_id = cursor.lastrowid
    else:
        node_id = parent_id
    for child in node.children:
        save_tree_to_db(child, node_id, cursor)

def main():
    generate_children(root, frame)
    #print_tree(root)
    # Save tree to DB
    cursor = conn.cursor()
    # Optionally clear table before insert
    cursor.execute("DELETE FROM taxonomy")
    save_tree_to_db(root, None, cursor)
    conn.commit()
    cursor.close()

if __name__ == "__main__":
    main()

#generate_children(root, frame)
#print_tree(root)

