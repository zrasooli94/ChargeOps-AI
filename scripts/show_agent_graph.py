from app.agents.chargeops_graph import (
    chargeops_graph,
)


def main() -> None:
    print(
        chargeops_graph
        .get_graph()
        .draw_mermaid()
    )


if __name__ == "__main__":
    main()