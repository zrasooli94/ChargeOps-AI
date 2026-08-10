from app.agents.chargeops_graph import (
    build_chargeops_graph,
)


def main() -> None:
    graph = build_chargeops_graph()

    print(
        graph
        .get_graph()
        .draw_mermaid()
    )


if __name__ == "__main__":
    main()