from xania.renderer.elements import Div, H1, P

def Page(id: str = "unknown"):
    return Div(
        H1(f"User Profile: {id}", class_name="text-3xl font-bold mb-4 text-purple-400"),
        P(f"This is a dynamic route generated from app/users/[id]/page.py", class_name="text-gray-400"),
    )
