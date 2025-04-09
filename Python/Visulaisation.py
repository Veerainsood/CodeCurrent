import json
import networkx as nx
import matplotlib.pyplot as plt

with open("function_analysis.json", "r") as f:
    data = json.load(f)

G = nx.DiGraph()

for func in data["uniqueFunctions"]:
    G.add_node(func["id"], label=func["name"])

for call in data["functionCalls"]:
    if "calleeId" in call:
        G.add_edge(call["callerId"], call["calleeId"])

plt.figure(figsize=(10, 6))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G, "label"), node_color="lightblue", edge_color="gray", node_size=2000, font_size=10)

plt.title("Function Call Graph")
plt.show()
