from xania.renderer.elements import Div, H1, P
from xania.example.counter import Counter

def Page():
    return Div(
        H1("Welcome to Xania App Router!", class_name="text-4xl font-bold mb-4"),
        P("This page is rendered via the file-system router.", class_name="text-gray-400 mb-8"),
        Counter(id="home-counter"),
    )
