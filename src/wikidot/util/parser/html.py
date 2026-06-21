import bs4


def class_values(element: bs4.Tag) -> list[str]:
    class_attr = element.get("class")
    if class_attr is None:
        return []
    if isinstance(class_attr, str):
        return [class_attr]
    return [str(value) for value in class_attr]
