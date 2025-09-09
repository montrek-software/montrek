import re
from dataclasses import dataclass
from enum import Enum

import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout  # pygraphviz backend


# ---------- Layouts ----------
class NetworkLayout:
    def pos(self, graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
        raise NotImplementedError("method must be implemented")


class LRNetworkLayout(NetworkLayout):
    """Graphviz (dot) laid out Left→Right."""

    def pos(self, graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
        return graphviz_layout(
            graph,
            prog="dot",
            args="-Grankdir=LR -Gnodesep=0.6 -Granksep=0.7 -Gsplines=true",
        )


class TBNetworkLayout(NetworkLayout):
    """Graphviz (dot) laid out Top→Bottom."""

    def pos(self, graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
        return graphviz_layout(
            graph,
            prog="dot",
            args="-Grankdir=TB -Gnodesep=0.6 -Granksep=0.7 -Gsplines=true",
        )


class SpringNetworkLayout(NetworkLayout):
    """Force-directed fallback (no Graphviz required)."""

    def pos(self, graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
        return nx.spring_layout(graph, seed=42)  # deterministic


# ---------- Registry via Enum ----------
@dataclass(frozen=True)
class LayoutSpec:
    cls: type[NetworkLayout]
    aliases: tuple[str, ...]  # all names users can pass


class LayoutKind(Enum):
    LR = LayoutSpec(
        cls=LRNetworkLayout,
        aliases=("lr", "left_right", "left-right", "graphviz_lr"),
    )
    TB = LayoutSpec(
        cls=TBNetworkLayout,
        aliases=("tb", "top_bottom", "top-bottom", "graphviz_tb"),
    )
    SPRING = LayoutSpec(
        cls=SpringNetworkLayout,
        aliases=("spring", "force", "force_directed", "force-directed"),
    )


# ---------- Factory ----------
class NetworkLayoutsFactory:
    @staticmethod
    def _norm(s: str) -> str:
        """Case-insensitive, strip spaces/underscores/hyphens."""
        return re.sub(r"[\s_-]+", "", s).lower()

    @classmethod
    def _build_lookup(cls) -> dict[str, LayoutKind]:
        lookup: dict[str, LayoutKind] = {}
        for kind in LayoutKind:
            for alias in kind.value.aliases:
                lookup[cls._norm(alias)] = kind
        return lookup

    @classmethod
    def get(cls, layout: str) -> NetworkLayout:
        if not layout or not isinstance(layout, str):
            raise ValueError("layout must be a non-empty string")

        lookup = cls._build_lookup()
        key = cls._norm(layout)
        kind = lookup.get(key)
        if not kind:
            # List ALL accepted names (aliases) in the error message
            all_names = sorted({alias for k in LayoutKind for alias in k.value.aliases})
            raise ValueError(
                f"Unknown layout '{layout}'. Available layouts: {', '.join(all_names)}"
            )
        return kind.value.cls()
