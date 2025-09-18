from util.response import Response
from util.request import Request
import json
import uuid

from util.database import chat_collection
from util.database import user_collection
from util.auth import extract_credentials,validate_password
import bcrypt

def render_index_html(request, handler):
    response = Response()
    layout_html = ""

    #request path of given request
    request_path = request.path
    #print(f"request_path in index html: {request_path}")
    #open the template html file and copy it
    with open("public/layout/layout.html") as layout_file:
        layout_html = layout_file.read()

    #print(f"layout_html: {layout_html}")
    #if the path is /, get index.html
    if request_path == "/":
        request_path = "/index"
    #create the file path
    file_path = "public" + request_path + ".html"
    with open(file_path, "rb") as html_file:
        #the body of the response is reading the html file
        html_body = html_file.read()
        #print(f"html_body: {html_body}")

        layout_html = layout_html.replace("{{content}}",html_body.decode())

        #print(f"layout_html after replacement: {layout_html}")

        response.bytes(layout_html.encode())

        response.headers({"Content-Type": "text/html; charset=utf-8"})
        #response.headers({"Content-Length": len(html_body.encode())})
        response.set_status(200,"OK")
        handler.request.sendall(response.to_data())



def render_images(request, handler):
    #print("we are in the render_images function")
    response = Response()
    mime_type = request.path.split(".")[1]
    #gets rid of the starting / in the path
    if mime_type == "ico":
        mime_type = "x-icon"
    if mime_type == "jpg":
        mime_type = "jpeg"
    request_path = request.path[1:]
    #print(f"request.path:{request_path}")
    #print(f"mime:{mime_type}")
    with open(request_path, "rb") as img_file:
        # the body of the response is reading the html file
        response.bytes(img_file.read())
        response.headers({"Content-Type": f"image/{mime_type}"})
        #response.headers({"Content-Type": f"image/{mime_type}; charset=utf-8"})
        #response.headers({"Content-Length": len(img_file.read().encode())})
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())


def render_js(request, handler):
    #print("we are in the render_js function")
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
    #print(f"request_cookies: {request_cookies}")

    body_of_request = request.body.decode()
    body_of_request = json.loads(body_of_request)
    content_of_request = body_of_request["content"]
    #print(f"request.body:{body_of_request}      type:{type(request.body.decode())}")
    #print(f"content_of_request:{content_of_request}")

    """
    print("all data in create:")
    all_data = chat_collection.find({})
    for data in all_data:
        print(data)
"""


    if len(request_cookies) == 0:
        #print("inside first text")
        #if this is true: this is the first time the user has sent a text (so we create their message dict)
        #add a session id for the new user
        uuid_cookie_value = str(uuid.uuid4())
        response.cookies({"session": uuid_cookie_value})
        message_dict = {"author": uuid_author_id, "id": uuid_cookie_value, "content": content_of_request, "updated": False}
        chat_collection.insert_one(message_dict)
    elif chat_collection.find_one({"id": request_cookies['session']}) is None:
        #true for if a user sends a msg on docker, but then trys to send one on local
        uuid_cookie_value = str(uuid.uuid4())
        response.cookies({"session": uuid_cookie_value})
        message_dict = {"author": uuid_author_id, "id": uuid_cookie_value, "content": content_of_request,"updated": False}
        chat_collection.insert_one(message_dict)
    else:
        #print("inside NOT first text")
        #this user has a session cookie already and has already sent a message
        print(f"request_cookies: {request_cookies}")
        prev_message_from_user = chat_collection.find_one({"id" : request_cookies["session"]})
        #prev_message_from_user = chat_collection.find_one({"messages" : [{"id": request_cookies["session"]}]})
        #print(f"prev_message_from_user: {prev_message_from_user}")
        #print(f"prev_message_from_user id: {prev_message_from_user['id']}")
        #prev_id = prev_message_from_user["id"]
        prev_author_id = prev_message_from_user["author"]
        uuid_new_id = str(uuid.uuid4())
        message_dict = {"author": prev_author_id, "id": uuid_new_id, "content": content_of_request, "updated": False}
        chat_collection.insert_one(message_dict)



    response.set_status(200,"OK")
    response.text("response was sent for create_message_route")
    response.headers({"Content-Type": "text/html; charset=utf-8"})
    #response.headers({"Content-Length": len("response was sent for create_message_route")})
    handler.request.sendall(response.to_data())






def get_message_route(request, handler):
    #print("we are in the get_message_route function")
    response = Response()
    #response.headers({"Content-Type": "application/javascript; charset=utf-8"})

    all_data = chat_collection.find({})
    list_ = []
    response_data = {"messages" : list_}

    for data in all_data:
        data.pop("_id")
        #print(f"data inside get_message_route: {data}")
        if "content" in data:
            data["content"] = data["content"].replace("&","&amp;")
            data["content"] = data["content"].replace("<", "&lt;")
            data["content"] = data["content"].replace(">", "&gt;")
            list_.append(data)
        #print(data)

    #print(f"response_data: {response_data}")
    #json_all_data = json.dumps(response_data)
    #print(f"json_all_data: {json_all_data}      type(json_all_data): {type(json_all_data)}")
    response.json(response_data)
    #print(f"response_data: {response.var_body}")
    response.headers({"Content-Type": "application/json"})
    #response.headers({"Content-Type": "application/json"})
    #response.headers({"Content-Length": len(response.var_body.encode())})
    handler.request.sendall(response.to_data())


def update_message_route(request, handler):
    """
    * update the boolean to true in the message
    * send a response of 403 forbidden if user tries to update a message that is not theirs
    * check for html injection (replace & < >)?
    * Request (JSON) : {"content": string}
    * add httponly
    """
    response = Response()
    print("inside the update_message_route function")
    print(f"request_path in update_message:{request.path}")

    #path from request
    split_path = request.path.split("/")

    #get the token from old message
    request_token = split_path[3]

    print(f"split_path: {split_path}")
    print(f"token from prev message: {request_token}")

    #find a message with the same id as the token
    prev_message_from_user = chat_collection.find_one({"id" : request_token})

    print(f"prev_message_from_user: {prev_message_from_user}")
    #true when there is a message from the token
    #i think this is not needed
    if prev_message_from_user is not None:

        #find the id of the old message
        old_message_author_id = prev_message_from_user["author"]

        print(f"old_message_author_id: {old_message_author_id}")
        print(f"request_cookies: {request.cookies}")

        #handles the case of where a user is trying to edit before sending their first text
        if len(request.cookies) == 0:
            response.set_status(403, "Forbidden")
            response.text("this ain't your text homie")
            handler.request.sendall(response.to_data())
            return

        #the current cookie of the user trying to edit
        current_user_cookie = request.cookies["session"]

        #the author_id of the user who made the edit request
        current_user_author_id = chat_collection.find_one({"id" : current_user_cookie})["author"]

        #print(f"current_user_author_id: {current_user_author_id}")

        #return 403 if the old author and current author don't match
        if old_message_author_id != current_user_author_id:
            response.set_status(403, "Forbidden")
            response.text("this ain't your text homie")
            handler.request.sendall(response.to_data())
            return

        #print(f"request_body: {request.body}")
        #the new info we want to replace it with
        new_content_of_request = json.loads(request.body.decode())['content']


        #new_content_of_request = new_content_of_request.replace("&", "&amp;")
        #new_content_of_request = new_content_of_request.replace("<", "&lt;")
        #new_content_of_request = new_content_of_request.replace(">", "&gt;")

        #update the collection with the id of request token (id of the message we want to change)
        chat_collection.update_one({"id":request_token}, {"$set": {"content": new_content_of_request, "updated":True}})

        #send a 200 response
        response.set_status(200, "OK")
        response.text("you edited your message")
        handler.request.sendall(response.to_data())
        return

    else:
        response.set_status(403, "Forbidden")
        response.text("this ain't your text homie")
        handler.request.sendall(response.to_data())
        return





def delete_message_route(request, handler):
    response = Response()

    print("inside the delete_message_route function")
    request_body = request.body
    #print(f"request_body: {request_body}")
    request_cookies = request.cookies
    #print(f"request_cookies: {request_cookies}")
    request_path = request.path
    #print(f"request_path: {request_path}")

    #the user's cookie who made the delete request
    user_cookie_trying_to_delete = request_cookies.get("session")
    print(f"user_cookie_trying_to_delete: {user_cookie_trying_to_delete}")

    #the id of the message trying to be deleted
    message_id = request.path.split("/")[3]
    print(f"message_id: {message_id}")

    #if a user trys to delete without having a cookie
    if user_cookie_trying_to_delete is None:
        response.set_status(403, "Forbidden")
        response.text("you have no cookie")
        handler.request.sendall(response.to_data())
        return

    #a message sent by the user trying to delete this random message
    active_user_prev_message = chat_collection.find_one({"id": user_cookie_trying_to_delete})
    print(f"active_user_prev_message: {active_user_prev_message}")

    #the message dict that holds the data of the specific message trying to be deleted
    old_message_dict = chat_collection.find_one({"id" : message_id})
    print(f"old_message_dict: {old_message_dict}")
    if old_message_dict is None or active_user_prev_message is None:
        response.set_status(403, "Forbidden")
        response.text("can't delete")
        handler.request.sendall(response.to_data())
        return

    #if the 2 author id's dont =, they are different users and return error
    if old_message_dict['author'] != active_user_prev_message["author"]:
        response.set_status(403, "Forbidden")
        response.text("naughtyyyy boyyyy")
        handler.request.sendall(response.to_data())
        return

    #delete the message
    chat_collection.delete_one({"id" : message_id})
    response.set_status(200, "OK")
    response.text("you deleted your message message")
    handler.request.sendall(response.to_data())





def post_registration_route(request, handler):
    print("inside post_registration_route")
    username,password = extract_credentials(request)
    print(f"username:{username}")
    print(f"password:{password}")
    is_password_valid = validate_password(password)
    print(f"is_password_valid:{is_password_valid}")
    if is_password_valid == False:
        response = Response()
        response.set_status(400, "Bad Request")
        response.text("your password does not meet the criteria")
        handler.request.sendall(response.to_data())
    #if the password is valid
    #store the username and a salted hash of the password in DB
    #when a user registers, generate a unique id like how chat messages do

    #generate the salt
    salt = bcrypt.gensalt()

    #hash the password
    hash_pass = bcrypt.hashpw(password.encode(),salt)



    user_info = {"username":username, "password":hash_pass, "id": str(uuid.uuid4())}
    print(f"user info:{user_info}")

    user_collection.insert_one(user_info)

    response = Response()
    response.set_status(200, "OK")
    response.text("account registered, please go ahead and login")
    handler.request.sendall(response.to_data())




def post_login_route(request, handler):
    print("inside post_login_route")


def get_logout_route(request, handler):
    print("inside get_logout_route")



"""
def main():
    old_password = "abc"
    new_password = "abc"

    #generate salt
    salt = bcrypt.gensalt()
    print(f"salt:{salt}")

    #hash the password
    hashed_pass = bcrypt.hashpw(old_password.encode(),salt)
    print(f"hashed_pass:{hashed_pass}")

    result = bcrypt.checkpw(new_password.encode(),hashed_pass)
    print(f"result:{result}")



if __name__ == "__main__":
    main()
"""