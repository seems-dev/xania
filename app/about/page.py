from xania.renderer.elements import Div, H1, P

def Page():
    return Div(
        H1("About Us", class_name="text-3xl font-bold mb-4"),
        P("We are building the future of Python web frameworks.", class_name="text-gray-400"),
    )
