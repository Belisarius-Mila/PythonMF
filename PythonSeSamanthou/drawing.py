"""Shared drawing canvas for lessons and the workshop."""


def draw_commands(canvas, commands, font_family="Arial"):
    canvas.delete("all")
    w, h = max(canvas.winfo_width(), 10), max(canvas.winfo_height(), 10)
    scale = max(0.01, min((w - 24) / 500, (h - 24) / 360))
    ox, oy = (w - 500 * scale) / 2, (h - 360 * scale) / 2
    point = lambda x, y: (ox + x * scale, oy + y * scale)
    canvas.create_rectangle(*point(0, 0), *point(500, 360), fill="white", outline="#cdd7e2", tags="page")
    for x in range(0, 501, 50):
        canvas.create_line(*point(x, 0), *point(x, 360), fill="#edf1f5", tags="grid")
    for y in range(0, 361, 50):
        canvas.create_line(*point(0, y), *point(500, y), fill="#edf1f5", tags="grid")
    canvas.create_text(*point(8, 8), text="(0, 0)", anchor="nw", fill="#7b8ba2", font=(font_family, 9), tags="grid")
    canvas.create_text(*point(492, 352), text="(500, 360)", anchor="se", fill="#7b8ba2", font=(font_family, 9), tags="grid")
    for item in commands:
        kind, *a = item
        if kind == "background":
            canvas.itemconfigure("page", fill=a[0])
            canvas.delete("grid")
        elif kind == "circle":
            x, y, radius, color = a
            canvas.create_oval(*point(x - radius, y - radius), *point(x + radius, y + radius), fill=color, outline="")
        elif kind == "rect":
            x1, y1, x2, y2, color = a
            canvas.create_rectangle(*point(x1, y1), *point(x2, y2), fill=color, outline="")
        elif kind == "line":
            x1, y1, x2, y2, color = a
            canvas.create_line(*point(x1, y1), *point(x2, y2), fill=color, width=max(1, 3 * scale))
        elif kind == "text":
            x, y, text, color = a
            canvas.create_text(*point(x, y), text=text, fill=color, font=(font_family, max(8, int(16 * scale))))
