def format_time(t):
    """Format seconds into a human readable form.
    """
    m, s = divmod(t, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:2.0f}hr {m:2.0f}min {s:4.1f}s"
    elif m:
        return f"{m:2.0f}min {s:4.1f}s"
    else:
        if s > 1:
            return f"{s:4.1f}s"
        elif s * 1000 > 1:
            return f"{s*1000:4.1f}ms"
        else:
            return f"{s*1e6:4.1f}μs"
