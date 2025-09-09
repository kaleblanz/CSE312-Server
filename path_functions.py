from util.response import Response
from util.request import Request

def render_index_html(request, handler):
    response = Response()
    layout_html = ""

    #request path of given request
    request_path = request.path
    print(f"request_path in index html: {request_path}")
    #open the template html file and copy it
    with open("public/layout/layout.html") as layout_file:
        layout_html = layout_file.read()

    print(f"layout_html: {layout_html}")
    #if the path is /, get index.html
    if request_path == "/":
        request_path = "/index"
    #create the file path
    file_path = "public" + request_path + ".html"
    with open(file_path, "rb") as html_file:
        #the body of the response is reading the html file
        html_body = html_file.read()
        print(f"html_body: {html_body}")

        layout_html = layout_html.replace("{{content}}",html_body.decode())

        print(f"layout_html after replacement: {layout_html}")

        response.bytes(layout_html.encode())

        response.headers({"Content-Type": "text/html; charset=utf-8"})
        response.set_status(200,"OK")
        handler.request.sendall(response.to_data())



def render_images(request, handler):
    print("we are in the render_images function")
    response = Response()
    mime_type = request.path.split(".")[1]
    #gets rid of the starting / in the path
    request_path = request.path[1:]
    print(f"request.path:{request_path}")
    print(f"mime:{mime_type}")
    with open(request_path, "rb") as img_file:
        # the body of the response is reading the html file
        response.bytes(img_file.read())
        response.headers({"Content-Type": f"image/{mime_type}"})
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())


def render_js(request, handler):
    print("we are in the render_js function")
    response = Response()
    request_path = request.path[1:]
    with open(request_path, "rb") as js_file:
        response.bytes(js_file.read())
        response.headers({"Content-Type": "application/javascript"})
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())
