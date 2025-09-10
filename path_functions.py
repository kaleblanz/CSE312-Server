from util.response import Response
from util.request import Request
import json
import uuid

from util.database import chat_collection

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
        #response.headers({"Content-Length": len(html_body.encode())})
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
        response.headers({"Content-Type": f"image/{mime_type}; charset=utf-8"})
        #response.headers({"Content-Length": len(img_file.read().encode())})
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())


def render_js(request, handler):
    print("we are in the render_js function")
    response = Response()
    request_path = request.path[1:]
    with open(request_path, "rb") as js_file:
        response.bytes(js_file.read())
        #response.headers({"Content-Type": "text/javascript"})
        response.headers({"Content-Type": "application/javascript; charset=utf-8"})
        #response.headers({"Content-Length": len(js_file.read())})
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())


def create_message_route(request, handler):
    """
    print("we are in the create_message_route function")
    uu = str(uuid.uuid4())
    print(f"value of uu: {uu}   type of uu: {type(uu)}")
    """
    response = Response()

    uuid_author_id = str(uuid.uuid4())
    request_cookies =  request.cookies
    print(f"request_cookies: {request_cookies}")

    body_of_request = request.body.decode()
    body_of_request = json.loads(body_of_request)
    content_of_request = body_of_request["content"]
    #print(f"request.body:{body_of_request}      type:{type(request.body.decode())}")
    #print(f"content_of_request:{content_of_request}")


    if len(request_cookies) == 0:
        print("inside first text")
        #if this is true: this is the first time the user has sent a text (so we create their message dict)
        #add a session id for the new user
        uuid_cookie_value = str(uuid.uuid4())
        response.cookies({"session": uuid_cookie_value})
        message_dict = {"author": uuid_author_id, "id": uuid_cookie_value, "content": content_of_request, "updated": False}
        chat_collection.insert_one(message_dict)
    else:
        print("inside NOT first text")
        #this user has a session cookie already and has already sent a message
        prev_message_from_user = chat_collection.find_one({"id" : request_cookies["session"]})
        #prev_message_from_user = chat_collection.find_one({"messages" : [{"id": request_cookies["session"]}]})
        print(f"prev_message_from_user: {prev_message_from_user}")
        print(f"prev_message_from_user id: {prev_message_from_user['id']}")
        prev_id = prev_message_from_user["id"]
        prev_author_id = prev_message_from_user["author"]
        message_dict = {"author": prev_author_id, "id": prev_id, "content": content_of_request, "updated": False}
        chat_collection.insert_one(message_dict)



    response.set_status(200,"OK")
    response.text("response was sent for create_message_route")
    response.headers({"Content-Type": "text/html; charset=utf-8"})
    #response.headers({"Content-Length": len("response was sent for create_message_route")})
    handler.request.sendall(response.to_data())






def get_message_route(request, handler):
    print("we are in the get_message_route function")
    response = Response()
    #response.headers({"Content-Type": "application/javascript; charset=utf-8"})

    all_data = chat_collection.find({})
    list_ = []
    response_data = {"messages" : list_}

    for data in all_data:
        data.pop("_id")
        data["content"] = data["content"].replace("&","&amp;")
        data["content"] = data["content"].replace("<", "&lt;")
        data["content"] = data["content"].replace(">", "&gt;")
        list_.append(data)
        print(data)

    print(f"response_data: {response_data}")
    #json_all_data = json.dumps(response_data)
    #print(f"json_all_data: {json_all_data}      type(json_all_data): {type(json_all_data)}")
    response.json(response_data)
    print(f"response_data: {response.var_body}")
    response.headers({"Content-Type": "application/json"})
    #response.headers({"Content-Length": len(response.var_body.encode())})
    handler.request.sendall(response.to_data())

