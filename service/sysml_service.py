def generate_sysml(graph):


    lines=[]


    lines.append(
        "package VehicleSystem {"
    )


    lines.append(
        ""
    )


    for node in graph.nodes:


        lines.append(

            f"part def {node} {{"

        )


        lines.append(
            "}"
        )



    lines.append("")


    for source,target,data in graph.edges(data=True):


        lines.append(

            f"flow {source} to {target};"

        )


    lines.append(
        "}"
    )


    return "\n".join(lines)