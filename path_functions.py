from util.response import Response
from util.request import Request
import json
import uuid

from util.database import chat_collection
from util.database import user_collection
from util.auth import extract_credentials,validate_password
import bcrypt
import hashlib

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

    response = Response()

    uuid_author_id = str(uuid.uuid4())
    request_cookies =  request.cookies
    #print(f"request_cookies: {request_cookies}")

    body_of_request = request.body.decode()
    body_of_request = json.loads(body_of_request)
    content_of_request = body_of_request["content"]

    #handle authenticated users
    if "auth_token" in request_cookies:
        #user is authenticated
        uuid_new_id = str(uuid.uuid4())
        print(f"request_cookies[auth_token]:{request_cookies['auth_token']}")
        hash_auth_token = hashlib.sha256( (request_cookies['auth_token']).encode()).hexdigest()
        user = user_collection.find_one({"auth_token": hash_auth_token } )
        print(f"user:{user}")
        message_dict = {"author": user["username"], "id": uuid_new_id, "content": content_of_request,"updated": False}
        print(f"message_dict:{message_dict}")
        chat_collection.insert_one(message_dict)

        response.set_status(200, "OK")
        response.text("response was sent for create_message_route")
        response.headers({"Content-Type": "text/html; charset=utf-8"})
        handler.request.sendall(response.to_data())
        return

    #user is a guest, give them their session cookie
    if len(request_cookies) == 0:
        #print("inside first text")
        #if this is true: this is the first time the user has sent a text (so we create their message dict)
        #add a session id for the new user
        uuid_cookie_value = str(uuid.uuid4())
        response.cookies({"session": uuid_cookie_value + "; Path=/"})
        # store the hashed session in the db
        hash_session_cookie = hashlib.sha256(uuid_cookie_value.encode()).hexdigest()

        message_dict = {"author": uuid_author_id, "id": uuid_cookie_value, "content": content_of_request, "updated": False, "session" : hash_session_cookie}
        chat_collection.insert_one(message_dict)
    #docker/local error
    elif chat_collection.find_one({"id": request_cookies['session']}) is None:
        #true for if a user sends a msg on docker, but then trys to send one on local
        uuid_cookie_value = str(uuid.uuid4())
        response.cookies({"session": uuid_cookie_value+ "; Path=/"})
        #store the hashed session in the db
        hash_session_cookie = hashlib.sha256(uuid_cookie_value.encode()).hexdigest()

        message_dict = {"author": uuid_author_id, "id": uuid_cookie_value, "content": content_of_request, "updated": False,"session": hash_session_cookie}
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
        #hash_session_cookie = hashlib.sha256(prev_message_from_user["session"].encode()).hexdigest()
        #session cookie is already hashed
        message_dict = {"author": prev_author_id, "id": uuid_new_id, "content": content_of_request, "updated": False, "session":prev_message_from_user["session"]}
        chat_collection.insert_one(message_dict)



    response.set_status(200,"OK")
    response.text("response was sent for create_message_route")
    response.headers({"Content-Type": "text/html; charset=utf-8"})
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

    #print(f"split_path: {split_path}")
    #print(f"token from prev message: {request_token}")

    #find a message with the same id as the token
    prev_message_from_user = chat_collection.find_one({"id" : request_token})

    print(f"prev_message_from_user: {prev_message_from_user}")
    #true when there is a message from the token
    #i think this is not needed
    if prev_message_from_user is not None:

        #find the id of the old message
        old_message_author_id = prev_message_from_user["author"]

        #print(f"old_message_author_id: {old_message_author_id}")
        #print(f"request_cookies: {request.cookies}")

        #handles the case of where a user is trying to edit before sending their first text
        if len(request.cookies) == 0:
            response.set_status(403, "Forbidden")
            response.text("this ain't your text homie")
            handler.request.sendall(response.to_data())
            return

        #guest trying to edit their chat:
        if "session" in request.cookies:
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

            #update the collection with the id of request token (id of the message we want to change)
            chat_collection.update_one({"id":request_token}, {"$set": {"content": new_content_of_request, "updated":True}})

            #send a 200 response
            response.set_status(200, "OK")
            response.text("you edited your message")
            handler.request.sendall(response.to_data())
            return

        # authenticated user trying to edit their chat:
        if "auth_token" in request.cookies:
            # the current cookie of the user trying to edit
            current_user_cookie = request.cookies["auth_token"]
            print(f"current_user_cookie:{current_user_cookie}")

            # the author_id of the user who made the edit request
            hash_auth = hashlib.sha256(current_user_cookie.encode()).hexdigest()
            current_user_name = user_collection.find_one({"auth_token": hash_auth})["username"]

            # print(f"current_user_author_id: {current_user_author_id}")

            # return 403 if the old author and current author don't match
            if old_message_author_id != current_user_name:
                response.set_status(403, "Forbidden")
                response.text("this ain't your text homie")
                handler.request.sendall(response.to_data())
                return

            # print(f"request_body: {request.body}")
            # the new info we want to replace it with
            new_content_of_request = json.loads(request.body.decode())['content']

            # update the collection with the id of request token (id of the message we want to change)
            chat_collection.update_one({"id": request_token}, {"$set": {"content": new_content_of_request, "updated": True}})

            # send a 200 response
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

    #the user is authenticated who is trying to delete
    if "auth_token" in request_cookies:
        hash_auth = hashlib.sha256(request_cookies["auth_token"].encode()).hexdigest()
        username = user_collection.find_one({"auth_token" : hash_auth})["username"]
        print(f"username trying to in delete:{username}")
        message_trying_to_be_deleted = chat_collection.find_one({"id" : message_id})
        #print(f"message_trying_to_be_deleted:{message_trying_to_be_deleted}")
        #true when the 2 users DONT have the same name
        if username != message_trying_to_be_deleted["author"]:
            response.set_status(403, "Forbidden")
            response.text("you are authenticated, but not your text")
            handler.request.sendall(response.to_data())
            return
        else:
            #this is the users text and it will be deleted
            chat_collection.delete_one({"id" : message_id})
            response.set_status(200, "OK")
            response.text("you deleted your authenticated text")
            handler.request.sendall(response.to_data())
            return



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
    #print("inside post_registration_route")
    username,password = extract_credentials(request)
    #print(f"username:{username}")
    #print(f"password:{password}")
    is_password_valid = validate_password(password)
    #print(f"is_password_valid:{is_password_valid}")
    if is_password_valid == False:
        response = Response()
        response.set_status(400, "Bad Request")
        response.text("your password does not meet the criteria")
        handler.request.sendall(response.to_data())
        return
    #if the password is valid
    #store the username and a salted hash of the password in DB
    #when a user registers, generate a unique id like how chat messages do

    #search if username is already taken
    user = user_collection.find_one({"username" : username})
    if user is not None:
        response = Response()
        response.set_status(400, "Bad Request")
        response.text("username is already taken")
        handler.request.sendall(response.to_data())
        return

    #generate the salt
    salt = bcrypt.gensalt()

    #hash the password
    hash_pass = bcrypt.hashpw(password.encode(),salt)



    user_info = {"username":username, "password":hash_pass, "id": str(uuid.uuid4()), "auth_token":""}
    print(f"user info:{user_info}")

    user_collection.insert_one(user_info)

    response = Response()
    response.set_status(200, "OK")
    response.text("account registered, please go ahead and login")
    handler.request.sendall(response.to_data())




def post_login_route(request, handler):
    """
    *if the salted hash of the password matches what I have in DB, the user is authenticated

    *when a user logs in, set authentication token called "auth_token" as a cookie with HttpOnly directive (set a max age)
    * store a hash of this auth_token in my DB so we can verify on subsequent requests

    * if login is success -> response with 200 code, o/w response with 400 code
    """
    response = Response()
    print("inside post_login_route")
    username,entered_password = extract_credentials(request)
    print(f"username:{username}")
    print(f"password:{entered_password}")

    #print(f"request.path: {request.path}         request.body: {request.body}")

    #find the user's account
    user = user_collection.find_one({"username":username})
    print(f"user:{user}")

    #if username does not exist in the DB
    if user is None:
        response.set_status(400, "Bad Request")
        response.text("username does not exist")
        handler.request.sendall(response.to_data())
        return



    #compare the entered password with user's salted hash password in our DB
    #result_bool is true -> passwords are the same, False->passwords do not match
    result_bool = bcrypt.checkpw(entered_password.encode(),user["password"])
    print(f"result_bool:{result_bool}")
    #return 400 because the passwords do not match
    if result_bool == False:
        response.set_status(400, "Bad Request")
        response.text("passwords do not match")
        handler.request.sendall(response.to_data())
        return

    #create our authentication token
    auth_token = str(uuid.uuid4())
    #add a cookie that is our auth token with the HttpOnly and max age directive
    response.cookies({"auth_token":auth_token + "; HttpOnly; Max-Age=7200; Path=/"})
    print(f"response.var_cookies:{response.var_cookies}")

    #hash the auth token and update the users DB
    hashed_auth_token = hashlib.sha256(auth_token.encode()).hexdigest()
    print(f"hashed_auth_token:{hashed_auth_token}")
    #add the hashed auth_token to the users account
    result = user_collection.update_one({"username":username},{"$set":{"auth_token":hashed_auth_token}})
    print(f"result about update:{result}")
    #result about update:UpdateResult({'n': 0, 'nModified': 0, 'ok': 1.0, 'updatedExisting': False}, acknowledged=True)

    """
    the user is now authenticated, we will now switch all of their messages
    from their random name to their user name
    and delete their session cookie and now they only have the auth cookie
    """
    if "session" in request.cookies:
        #print("HERE 1")
        request_session = request.cookies["session"]
        #get all of the old geusts texts
        hash_request_session = hashlib.sha256(request_session.encode()).hexdigest()
        old_msg_from_session = chat_collection.find_one({"session" : hash_request_session})
        if old_msg_from_session is not None:
            #print("HERE 2")
            guest_username = old_msg_from_session['author']
            #print(f"old_msg_from_session:{old_msg_from_session}")
            #print(f"guest_username:{guest_username}     username:{username}")
            all_user_old_msg = chat_collection.update_many({"author": guest_username } , {"$set" : {"author" : username}})
            #print(f"alluseroldmsg:{all_user_old_msg}")


    # delete the session cookie now that we are authenticated
    response.cookies({"session": "L; Max-Age=0"})
    response.set_status(200, "OK")
    response.text("you are now authenticated")
    handler.request.sendall(response.to_data())




def get_logout_route(request, handler):
    """
    * used by the logout button in frontend
    * users auth_token must be removed from their cookies and invalidated by the server
    * to remove a cookie, set a cookie with the same name and max-age of 0
    """
    print("inside get_logout_route")
    print(f"request.cookies:{request.cookies}")
    print(f"request.path:{request.path}")
    print(f"request.body:{request.body}")

    response = Response()
    #print(f"extract_credentials(request):{extract_credentials(request)}")
    #set the auth_token of the user to expire
    if "auth_token" in request.cookies:
        #get the auth_token
        auth_token = request.cookies["auth_token"]
        #hash the auth token with sha256
        hash_auth_token = hashlib.sha256(auth_token.encode()).hexdigest()
        user_collection.update_one({"auth_token": hash_auth_token}, {"$set": {"auth_token": ""}})


    response.cookies({"auth_token":"L; Max-Age=0"})

    response.set_status(302,"Found")
    response.headers({"Location":"/"})
    handler.request.sendall(response.to_data())



def return_profile_route(request, handler):
    response = Response()
    request_cookies = request.cookies
    if "auth_token" in request_cookies:
        #user is authenticated
        hash_auth = hashlib.sha256(request_cookies["auth_token"].encode()).hexdigest()
        user_info = user_collection.find_one({"auth_token" : hash_auth})

        response.set_status(200, "OK")
        response.json({"username" : user_info["username"], "id" : user_info["id"]})
        handler.request.sendall(response.to_data())

    else:
        #user is not authenticated
        response.set_status(401, "Unauthorized")
        #empty json object?
        response.json({})
        handler.request.sendall(response.to_data())

def filer_search_users_route(request, handler):
    response = Response()
    print(f"request.body:{request.body}")
    print(f"request.path:{request.path}")
    user = request.path.split("/")[3].split("?")[1]
    print(f"user:{user}")
    input_name = user.split("=")[1]

    #return empty if no username was given
    if len(input_name) == 0:
        response.set_status(200,"OK")
        response.json({"users" : []})
        handler.request.sendall(response.to_data())
        return
    else:
        list_of_user_dict = []
        #get all users in the DB
        all_users = user_collection.find({})
        for user in all_users:
            username = user["username"]
            id = user["id"]
            #TRUE if the username starts with input string
            if username.startswith(input_name):
                user_dict = {"id" : id,"username" : username}
                list_of_user_dict.append(user_dict)
        output = {"users" : list_of_user_dict}
        response.json(output)
        response.set_status(200,"OK")
        handler.request.sendall(response.to_data())

def update_profile_route(request, handler):
    """
    * receive a request containing a username and password in same format as reg/login endpoints
    * when you receive the request, update the users username and password to the provided values

    * endpoint must pass valid_password() for new password (return 400 AND DON'T UPDATE)

    * empty password means only change username
    """
    response = Response()
    hash_auth = hashlib.sha256(request.cookies["auth_token"].encode()).hexdigest()
    username,password = request.body.decode().split("&")
    username = username.split("=")[1]
    password = password.split("=")[1]
    password = password.lstrip().rstrip()
    username = username.lstrip().rstrip()


    #update just the username
    if len(password) == 0:
        #update the username only
        user_collection.update_one({"auth_token" : hash_auth}, {"$set" : {"username" : username}})
        response.text("updated your username")
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())
        return
    #the password is invalid
    elif validate_password(password) == False:
        #true when the password doesn't meet the criteira
        response.text("your password does not meet the criteria")
        response.set_status(400,"Bad Request")
        handler.request.sendall(response.to_data())
        return
    #the usernane is already taken
    elif (user_collection.find_one({"username": username})) is not None:
        # search if username is already taken
        response = Response()
        response.set_status(400, "Bad Request")
        response.text("username is already taken")
        handler.request.sendall(response.to_data())
        return
    else:
        #new password is valid
        #gen a new salt
        salt = bcrypt.gensalt()
        #salted hash of the new passowrd
        salt_hashed_new_password = bcrypt.hashpw(password.encode(),salt)
        print(f"passworddd:{password}")
        result = user_collection.update_one({"auth_token" : hash_auth}, {"$set" : {"username" : username, "password" : salt_hashed_new_password}})
        print(f"reesult in updateprofile:{result}")
        response.text("updated your username and password")
        response.set_status(200, "OK")
        handler.request.sendall(response.to_data())
        return








"""
def main():
    #old_password = "abc"
    #new_password = "abc"
    #generate salt
    #salt = bcrypt.gensalt()
    #print(f"salt:{salt}")

    #hash the password
    #hashed_pass = bcrypt.hashpw(old_password.encode(),salt)
    #print(f"hashed_pass:{hashed_pass}")

    #result = bcrypt.checkpw(new_password.encode(),hashed_pass)
    #print(f"result:{result}")

    auth_token = "d8ahdbs(D80"
    hash_auth = hashlib.sha256(auth_token.encode()).hexdigest()
    print(f"hashauth:{hash_auth}")

    auth_token2 = "d8ahdbs(D80"
    hash_auth2 = hashlib.sha256(auth_token2.encode()).hexdigest()
    print(f"hashauth:{hash_auth2}")




if __name__ == "__main__":
    main()
"""