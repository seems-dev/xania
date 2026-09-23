from xania.renderer.elements import Div, Nav, A, Slot

def Layout(children):
    return Div(
        Nav(
            A("Home", href="/", class_name="mr-4 text-blue-400 hover:underline"),
            A("About", href="/about", class_name="mr-4 text-blue-400 hover:underline"),
            A("User 123", href="/users/123", class_name="text-blue-400 hover:underline"),
            class_name="p-4 bg-gray-900 border-b border-gray-800"
        ),
        Slot(children, name="children", class_name="p-8"),
        class_name="min-h-screen bg-gray-950 text-white font-sans"
    )
