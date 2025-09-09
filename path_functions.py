from http.client import responses

from util.response import Response
from util.request import Request

def render_index_html(request, handler):
    response = Response()
    with open("public/index.html", "rb") as html_file:
        #the body of the response is reading the html file
        response.bytes(html_file.read())
        response.headers({"Content-Type": "text/html; charset=utf-8"})
        response.set_status(200,"OK")
        handler.request.sendall(response.to_data())

def render_images(request, handler):
    print("we are in the render_images function")
    response = Response()
    mime_type = request.path.split(".")[1]
    print(f"request.path:{request.path}")
    print(f"mime:{mime_type}")
    with open("/public/imgs/jumping-cat.gif", "rb") as img_file:
        # the body of the response is reading the html file
        response.bytes(img_file.read())
        response.headers({"Content-Type": f"image/{mime_type}"})
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())