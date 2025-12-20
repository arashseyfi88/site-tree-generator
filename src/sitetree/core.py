from __future__ import annotations

import os
import urllib.request

import pandas as pd
import arabic_reshaper
from bidi.algorithm import get_display
from anytree import Node
from matplotlib import pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

# Persistent reshaper config (more stable)
_ARABIC_RESHAPER = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": True,
    }
)

def shape_text(text: str) -> str:
    text = str(text)
    # Apply shaping only for Arabic/Persian text
    if any("\u0600" <= ch <= "\u06FF" for ch in text):
        reshaped = _ARABIC_RESHAPER.reshape(text)
        # Force RTL direction
        return get_display(reshaped, base_dir="R")
    return text


def _get_font_properties() -> fm.FontProperties:
    """
    Use a Persian-capable font if possible (Vazirmatn), otherwise fallback to DejaVu Sans.
    """
    # Try to use Vazirmatn for best Persian rendering (downloads once in Colab or local cache)
    font_path = os.path.join(os.getcwd(), "Vazirmatn-Regular.ttf")
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(
                "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf",
                font_path
            )
        except Exception:
            font_path = None

    if font_path and os.path.exists(font_path):
        return fm.FontProperties(fname=font_path)

    # Fallback (usually available)
    return fm.FontProperties(fname=fm.findfont("DejaVu Sans"))


def assign_vertical_positions_fixed(node, depth=0, pos_dict=None, spacing_y=3):
    if pos_dict is None:
        pos_dict = {"y": 0, "positions": {}}

    children = list(node.children)

    if not children:
        y = pos_dict["y"]
        pos_dict["positions"][node] = (depth, y)
        pos_dict["y"] += spacing_y
    else:
        for child in children:
            assign_vertical_positions_fixed(child, depth + 1, pos_dict, spacing_y)
        child_y = [pos_dict["positions"][c][1] for c in children]
        pos_dict["positions"][node] = (depth, sum(child_y) / len(child_y))

    return pos_dict["positions"]


def collect_all_nodes(root_nodes):
    out = []
    for r in root_nodes.values():
        out.append(r)
        out.extend(list(r.descendants))
    # unique preserve order
    seen = set()
    uniq = []
    for n in out:
        if id(n) not in seen:
            uniq.append(n)
            seen.add(id(n))
    return uniq


def draw_tree_boxes_right_and_children_from_box_right(
    root_nodes,
    font_prop,
    output_pdf: str,
    spacing_y=3,
    fontsize=10,
    padding_px=10,
    box_gap_data=0.25,
    child_gap_data=0.8,
    dpi=150,
    show: bool = False,
):
    all_nodes = collect_all_nodes(root_nodes)

    # ---- 4.1 compute Y positions and depth (from vertical layout)
    y_positions = {}
    depth_map = {}
    offset_y = 0

    for root in root_nodes.values():
        pos = assign_vertical_positions_fixed(root, spacing_y=spacing_y)
        max_y = max(y for _, y in pos.values())

        for node, (depth, y) in pos.items():
            y_positions[node] = y + offset_y
            depth_map[node] = depth

        offset_y += max_y + spacing_y + 3

    # ---- 4.2 PASS 1: measure box sizes in data units
    rough_dx = 5.0
    rough_xline = {n: depth_map.get(n, 0) * rough_dx for n in all_nodes}

    max_y = max(y_positions.values()) if all_nodes else 10
    max_depth = max(depth_map.values()) if depth_map else 0

    fig_w = max(12, (max_depth * rough_dx + 20) * 0.6)
    fig_h = max(10, (max_y + 8) * 0.35)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.axis("off")
    ax.set_xlim(-10, max_depth * rough_dx + 20)
    ax.set_ylim(-(max_y + 5), 5)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    box_size = {}  # node -> (bw, bh) in data units

    for n in all_nodes:
        x_line = rough_xline[n]
        y = y_positions[n]

        if depth_map.get(n, 0) == 0:
            tx = x_line - box_gap_data
            ha = "right"
        else:
            tx = x_line + box_gap_data
            ha = "left"

        t = ax.text(
            tx,
            -y,
            n.name,
            ha=ha,
            va="center",
            fontsize=fontsize,
            fontproperties=font_prop,
            alpha=0,
        )
        fig.canvas.draw()
        bb = t.get_window_extent(renderer=renderer)

        x0, y0 = bb.x0 - padding_px, bb.y0 - padding_px
        x1, y1 = bb.x1 + padding_px, bb.y1 + padding_px

        (dx0, dy0) = inv.transform((x0, y0))
        (dx1, dy1) = inv.transform((x1, y1))

        bw = abs(dx1 - dx0)
        bh = abs(dy1 - dy0)
        box_size[n] = (bw, bh)

        t.remove()

    plt.close(fig)

    # ---- 4.3 PASS 2: compute final x_line recursively
    x_line = {}
    box_left = {}
    box_bottom = {}

    def layout_x(node, current_line_x):
        bw, bh = box_size[node]
        y = y_positions[node]

        if depth_map[node] == 0:
            left = current_line_x - box_gap_data - bw
        else:
            left = current_line_x + box_gap_data

        x_line[node] = current_line_x
        box_left[node] = left
        box_bottom[node] = -y - (bh / 2)

        right_edge = left + bw
        child_line_x = right_edge + child_gap_data

        for c in node.children:
            layout_x(c, child_line_x)

    for r in root_nodes.values():
        layout_x(r, 0.0)

    # ---- 4.4 DRAW final
    xs, ys = [], []
    for n in all_nodes:
        bw, bh = box_size[n]
        xs += [box_left[n], box_left[n] + bw, x_line[n]]
        ys += [box_bottom[n], box_bottom[n] + bh]

    xmin, xmax = min(xs) - 1.0, max(xs) + 3.0
    ymin, ymax = min(ys) - 1.0, max(ys) + 1.0

    fig_w = max(12, (xmax - xmin) * 0.6)
    fig_h = max(10, (ymax - ymin) * 0.6)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.axis("off")

    # lines first
    for parent in all_nodes:
        children = list(parent.children)
        if not children:
            continue

        pbw, _ = box_size[parent]
        p_left = box_left[parent]
        p_right = p_left + pbw
        py = -y_positions[parent]

        bx = x_line[children[0]]  # shared child line x

        child_ys = [-y_positions[c] for c in children]
        y_min = min(child_ys)
        y_max = max(child_ys)

        ax.plot([p_right, bx], [py, py], color="blue", lw=1, zorder=1)
        ax.plot([bx, bx], [y_min, y_max], color="blue", lw=1, zorder=1)

        for c in children:
            cy = -y_positions[c]
            ax.plot([bx, box_left[c]], [cy, cy], color="blue", lw=1, zorder=1)

    # short ticks from each node line to its box
    for n in all_nodes:
        y = -y_positions[n]
        bw, _ = box_size[n]
        if depth_map[n] == 0:
            ax.plot([x_line[n], box_left[n] + bw], [y, y], color="blue", lw=1, zorder=1)
        else:
            ax.plot([x_line[n], box_left[n]], [y, y], color="blue", lw=1, zorder=1)

    # boxes + centered text
    for n in all_nodes:
        bw, bh = box_size[n]
        left = box_left[n]
        bottom = box_bottom[n]

        box = FancyBboxPatch(
            (left, bottom),
            bw,
            bh,
            boxstyle="round,pad=0",
            facecolor="white",
            edgecolor="black",
            linewidth=1,
            zorder=2,
        )
        ax.add_patch(box)

        ax.text(
            left + bw / 2,
            bottom + bh / 2,
            n.name,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontproperties=font_prop,
            zorder=3,
        )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    plt.tight_layout()
    plt.savefig(output_pdf, format="pdf")

    if show:
        plt.show()
    else:
        plt.close(fig)


def generate_pdf(excel_path: str, output_pdf: str = "site_tree.pdf", show: bool = False) -> None:
    # Read & clean
    df = pd.read_excel(excel_path, header=None).fillna("")
    df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
    df = df[~(df == "").all(axis=1)]
    df = df.drop_duplicates()

    # Build tree (FIXED: key depends on parent)
    paths = df.values.tolist()
    node_map = {}   # key: (parent_id, label) -> Node
    root_nodes = {}

    for path in paths:
        previous = None
        for level in path:
            text = str(level).strip()
            if not text:
                continue

            label = shape_text(text)
            parent_key = id(previous) if previous is not None else None
            key = (parent_key, label)

            if key not in node_map:
                node = Node(label, parent=previous)
                node_map[key] = node
                if previous is None:
                    root_nodes[label] = node
            else:
                node = node_map[key]

            previous = node

    # Font (Persian-capable if possible)
    font_prop = _get_font_properties()

    # Draw
    draw_tree_boxes_right_and_children_from_box_right(
        root_nodes,
        font_prop=font_prop,
        output_pdf=output_pdf,
        spacing_y=3,
        fontsize=10,
        padding_px=10,
        box_gap_data=0.25,
        child_gap_data=0.8,
        dpi=150,
        show=show,
    )
